from datetime import datetime, timedelta

from fastapi import APIRouter
from postgrest.exceptions import APIError

from app.database.supabase import supabase
from app.schemas.orden import OrdenCrear


router = APIRouter(prefix="/ordenes", tags=["Órdenes"])


@router.post("/crear")
def crear_orden(orden: OrdenCrear):

    try:

        ordenes = (
            supabase.table("ordenes")
            .select("*")
            .eq("usuario_id", orden.usuario_id)
            .eq("producto", orden.producto)
            .eq("estado", "pendiente")
            .order("creado_en", desc=True)
            .limit(1)
            .execute()
        )

        if ordenes.data:

            orden_existente = ordenes.data[0]

            creado = datetime.fromisoformat(
                orden_existente["creado_en"].replace("Z", "+00:00")
            )

            ahora = datetime.now(creado.tzinfo)

            if ahora - creado < timedelta(minutes=30):

                return {
                    "ok": True,
                    "mensaje": "Orden pendiente reutilizada",
                    "orden": orden_existente,
                }

            supabase.table("ordenes").update(
                {
                    "estado": "expirada"
                }
            ).eq(
                "id",
                orden_existente["id"]
            ).execute()

        fecha = datetime.now().strftime("%Y%m%d%H%M%S")

        numero_orden = (
            f"MC-{fecha}-{orden.usuario_id}"
        )

        datos = {
            "numero_orden": numero_orden,
            "usuario_id": orden.usuario_id,
            "producto": orden.producto,
            "tipo": orden.tipo,
            "valor": orden.valor,
            "metodo_pago": orden.metodo_pago,
            "estado": "pendiente",
        }

        respuesta = (
            supabase.table("ordenes")
            .insert(datos)
            .execute()
        )

        return {
            "ok": True,
            "mensaje": "Orden creada correctamente",
            "orden": respuesta.data[0],
        }

    except APIError as error:

        return {
            "ok": False,
            "mensaje": error.message,
        }