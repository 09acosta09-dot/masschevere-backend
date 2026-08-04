import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from postgrest.exceptions import APIError

from app.database.supabase import supabase


router = APIRouter(
    prefix="/comprobantes",
    tags=["Comprobantes"],
)

BUCKET = "comprobantes"
TAMANO_MAXIMO = 5 * 1024 * 1024

TIPOS_PERMITIDOS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def obtener_token_telegram() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        raise HTTPException(
            status_code=500,
            detail="TELEGRAM_BOT_TOKEN no está configurado.",
        )

    return token


def consultar_telegram(endpoint: str, datos: dict | None = None) -> dict:
    token = obtener_token_telegram()

    url = (
        f"https://api.telegram.org/bot{token}/{endpoint}"
    )

    cuerpo = None
    encabezados = {}

    if datos is not None:
        cuerpo = json.dumps(datos).encode("utf-8")
        encabezados["Content-Type"] = "application/json"

    solicitud = Request(
        url,
        data=cuerpo,
        headers=encabezados,
        method="POST" if datos is not None else "GET",
    )

    try:
        with urlopen(solicitud, timeout=15) as respuesta:
            resultado = json.loads(
                respuesta.read().decode("utf-8")
            )

    except HTTPError as error:
        detalle = error.read().decode(
            "utf-8",
            errors="replace",
        )

        raise HTTPException(
            status_code=500,
            detail=f"Error de Telegram: {detalle}",
        )

    except URLError as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "No fue posible conectar con Telegram: "
                f"{error.reason}"
            ),
        )

    if not resultado.get("ok"):
        raise HTTPException(
            status_code=500,
            detail=resultado.get(
                "description",
                "Telegram devolvió un error.",
            ),
        )

    return resultado


def enviar_notificacion_pago(orden: dict) -> bool:
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not chat_id:
        return False

    valor = int(orden.get("valor") or 0)

    valor_formateado = (
        f"${valor:,.0f}"
        .replace(",", ".")
    )

    mensaje = (
        "🔔 NUEVO PAGO PENDIENTE\n\n"
        f"🧾 Orden: {orden.get('numero_orden', '-')}\n"
        f"📦 Producto: {orden.get('producto', '-')}\n"
        f"💰 Valor: {valor_formateado}\n"
        f"💳 Método: {orden.get('metodo_pago', '-')}\n\n"
        "📷 Comprobante recibido\n\n"
        "👉 https://masschevere.com/admin/"
    )

    consultar_telegram(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": mensaje,
            "disable_web_page_preview": True,
        },
    )

    return True


@router.get("/test")
def test():
    return {
        "ok": True,
        "mensaje": "Ruta de comprobantes funcionando",
    }


@router.get("/telegram/chat-id")
def obtener_chat_id():
    resultado = consultar_telegram("getUpdates")

    actualizaciones = resultado.get("result", [])

    if not actualizaciones:
        raise HTTPException(
            status_code=404,
            detail=(
                "No se encontraron mensajes. "
                "Envía nuevamente un mensaje al bot."
            ),
        )

    ultima_actualizacion = actualizaciones[-1]

    mensaje = (
        ultima_actualizacion.get("message")
        or ultima_actualizacion.get("edited_message")
        or ultima_actualizacion.get("channel_post")
    )

    if not mensaje or not mensaje.get("chat"):
        raise HTTPException(
            status_code=404,
            detail="No fue posible identificar el chat.",
        )

    chat = mensaje["chat"]

    return {
        "ok": True,
        "chat_id": chat["id"],
        "nombre": chat.get("first_name"),
        "username": chat.get("username"),
    }


@router.post("/subir")
async def subir_comprobante(
    orden_id: int = Form(...),
    archivo: UploadFile = File(...),
):
    if archivo.content_type not in TIPOS_PERMITIDOS:
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten imágenes JPG, PNG o WEBP.",
        )

    contenido = await archivo.read()

    if not contenido:
        raise HTTPException(
            status_code=400,
            detail="El archivo está vacío.",
        )

    if len(contenido) > TAMANO_MAXIMO:
        raise HTTPException(
            status_code=400,
            detail="La imagen no puede superar los 5 MB.",
        )

    try:
        consulta_orden = (
            supabase.table("ordenes")
            .select("*")
            .eq("id", orden_id)
            .limit(1)
            .execute()
        )

        if not consulta_orden.data:
            raise HTTPException(
                status_code=404,
                detail="La orden no existe.",
            )

        orden = consulta_orden.data[0]

        estado = str(
            orden.get("estado", "")
        ).lower()

        if estado != "pendiente":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Solo se puede adjuntar comprobante "
                    "a una orden pendiente."
                ),
            )

        extension = TIPOS_PERMITIDOS[
            archivo.content_type
        ]

        nombre_archivo = (
            f"ordenes/{orden_id}/"
            f"{uuid4().hex}{extension}"
        )

        supabase.storage.from_(BUCKET).upload(
            path=nombre_archivo,
            file=contenido,
            file_options={
                "content-type": archivo.content_type,
                "cache-control": "3600",
                "upsert": "false",
            },
        )

        url_publica = (
            supabase.storage
            .from_(BUCKET)
            .get_public_url(nombre_archivo)
        )

        respuesta = (
            supabase.table("ordenes")
            .update({
                "comprobante_url": url_publica,
            })
            .eq("id", orden_id)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=500,
                detail=(
                    "La imagen subió, pero no se pudo "
                    "actualizar la orden."
                ),
            )

        orden_actualizada = respuesta.data[0]

        notificacion_enviada = False

        try:
            notificacion_enviada = (
                enviar_notificacion_pago(
                    orden_actualizada
                )
            )
        except Exception as error:
            print(
                "No fue posible enviar la notificación:",
                str(error),
            )

        return {
            "ok": True,
            "mensaje": "Comprobante subido correctamente",
            "comprobante_url": url_publica,
            "notificacion_enviada": notificacion_enviada,
            "orden": orden_actualizada,
        }

    except HTTPException:
        raise

    except APIError as error:
        raise HTTPException(
            status_code=500,
            detail=error.message,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    finally:
        await archivo.close()