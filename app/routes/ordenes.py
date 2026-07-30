from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query
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
                    "reutilizada": True,
                    "orden": orden_existente,
                }

            (
                supabase.table("ordenes")
                .update({"estado": "expirada"})
                .eq("id", orden_existente["id"])
                .execute()
            )

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

        respuesta = (
            supabase.table("ordenes")
            .insert(datos)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=500,
                detail="La orden no pudo ser registrada"
            )

        return {
            "ok": True,
            "mensaje": "Orden creada correctamente",
            "reutilizada": False,
            "orden": respuesta.data[0],
        }

    except HTTPException:
        raise

    except APIError as error:
        raise HTTPException(
            status_code=500,
            detail=error.message
        )


@router.get("/listar")
def listar_ordenes(
    admin_usuario_id: int = Query(
        ...,
        description="ID del usuario administrador"
    )
):
    try:
        respuesta_admin = (
            supabase.table("usuarios")
            .select("id,rol")
            .eq("id", admin_usuario_id)
            .limit(1)
            .execute()
        )

        if not respuesta_admin.data:
            raise HTTPException(
                status_code=404,
                detail="Usuario administrador no encontrado"
            )

        administrador = respuesta_admin.data[0]

        if str(administrador.get("rol", "")).lower() != "admin":
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para consultar las órdenes"
            )

        respuesta_ordenes = (
            supabase.table("ordenes")
            .select("*")
            .order("creado_en", desc=True)
            .execute()
        )

        return {
            "ok": True,
            "total": len(respuesta_ordenes.data or []),
            "ordenes": respuesta_ordenes.data or [],
        }

    except HTTPException:
        raise

    except APIError as error:
        raise HTTPException(
            status_code=500,
            detail=error.message
        )