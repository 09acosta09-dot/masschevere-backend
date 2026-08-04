from pathlib import Path
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


@router.get("/test")
def test():
    return {
        "ok": True,
        "mensaje": "Ruta de comprobantes funcionando",
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
        orden = (
            supabase.table("ordenes")
            .select("id,usuario_id,estado")
            .eq("id", orden_id)
            .limit(1)
            .execute()
        )

        if not orden.data:
            raise HTTPException(
                status_code=404,
                detail="La orden no existe.",
            )

        estado = str(
            orden.data[0].get("estado", "")
        ).lower()

        if estado != "pendiente":
            raise HTTPException(
                status_code=400,
                detail="Solo se puede adjuntar comprobante a una orden pendiente.",
            )

        extension = TIPOS_PERMITIDOS[archivo.content_type]

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
                detail="La imagen subió, pero no se pudo actualizar la orden.",
            )

        return {
            "ok": True,
            "mensaje": "Comprobante subido correctamente",
            "comprobante_url": url_publica,
            "orden": respuesta.data[0],
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