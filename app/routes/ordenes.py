from datetime import datetime

from fastapi import APIRouter
from postgrest.exceptions import APIError

from app.database.supabase import supabase
from app.schemas.orden import OrdenCrear


router = APIRouter(prefix="/ordenes", tags=["Órdenes"])


@router.post("/crear")
def crear_orden(orden: OrdenCrear):
    fecha = datetime.now().strftime("%Y%m%d%H%M%S")
    numero_orden = f"MC-{fecha}-{orden.usuario_id}"

    datos = {
        "numero_orden": numero_orden,
        "usuario_id": orden.usuario_id,
        "producto": orden.producto,
        "tipo": orden.tipo,
        "valor": orden.valor,
        "metodo_pago": orden.metodo_pago,
        "estado": "pendiente",
    }

    try:
        respuesta = supabase.table("ordenes").insert(datos).execute()

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