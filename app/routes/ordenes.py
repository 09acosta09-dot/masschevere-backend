import calendar
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from postgrest.exceptions import APIError

from app.database.supabase import supabase
from app.schemas.orden import OrdenCrear


router = APIRouter(prefix="/ordenes", tags=["Órdenes"])


PLANES_MEMBRESIA = {
    "Plan Mensual": {
        "meses": 1,
        "tickets": 1,
    },
    "Plan Trimestral": {
        "meses": 3,
        "tickets": 3,
    },
    "Plan Semestral": {
        "meses": 6,
        "tickets": 6,
    },
    "Plan Anual": {
        "meses": 12,
        "tickets": 12,
    },
}


PAQUETES_TICKETS = {
    "Paquete de 10 Tickets": 10,
    "Paquete de 25 Tickets": 25,
    "Paquete de 50 Tickets": 50,
    "Paquete de 100 Tickets": 100,
}


def validar_administrador(admin_usuario_id: int) -> dict:
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
            detail="Usuario administrador no encontrado",
        )

    administrador = respuesta_admin.data[0]

    if str(administrador.get("rol", "")).lower() != "admin":
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para realizar esta acción",
        )

    return administrador


def obtener_orden(orden_id: int) -> dict:
    respuesta_orden = (
        supabase.table("ordenes")
        .select("*")
        .eq("id", orden_id)
        .limit(1)
        .execute()
    )

    if not respuesta_orden.data:
        raise HTTPException(
            status_code=404,
            detail="Orden no encontrada",
        )

    return respuesta_orden.data[0]


def obtener_usuario(usuario_id: int) -> dict:
    respuesta_usuario = (
        supabase.table("usuarios")
        .select(
            "id,plan,estado_plan,vence_plan,tickets"
        )
        .eq("id", usuario_id)
        .limit(1)
        .execute()
    )

    if not respuesta_usuario.data:
        raise HTTPException(
            status_code=404,
            detail="Usuario asociado a la orden no encontrado",
        )

    return respuesta_usuario.data[0]


def convertir_fecha(
    valor: Optional[str],
) -> Optional[datetime]:
    if not valor:
        return None

    try:
        fecha = datetime.fromisoformat(
            str(valor).replace("Z", "+00:00")
        )

        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)

        return fecha

    except (TypeError, ValueError):
        return None


def sumar_meses(
    fecha: datetime,
    cantidad_meses: int,
) -> datetime:
    mes_total = (
        fecha.month - 1 + cantidad_meses
    )

    nuevo_anio = (
        fecha.year + mes_total // 12
    )

    nuevo_mes = (
        mes_total % 12 + 1
    )

    ultimo_dia_mes = calendar.monthrange(
        nuevo_anio,
        nuevo_mes,
    )[1]

    nuevo_dia = min(
        fecha.day,
        ultimo_dia_mes,
    )

    return fecha.replace(
        year=nuevo_anio,
        month=nuevo_mes,
        day=nuevo_dia,
    )


def calcular_actualizacion_usuario(
    orden: dict,
    usuario: dict,
) -> tuple[dict, str]:
    producto = str(
        orden.get("producto", "")
    ).strip()

    tipo = str(
        orden.get("tipo", "")
    ).strip().lower()

    tickets_actuales = int(
        usuario.get("tickets") or 0
    )

    ahora = datetime.now(timezone.utc)

    if tipo == "membresia":
        configuracion = PLANES_MEMBRESIA.get(
            producto
        )

        if not configuracion:
            raise HTTPException(
                status_code=400,
                detail=(
                    "El producto de membresía no está "
                    f"configurado: {producto}"
                ),
            )

        meses = int(
            configuracion["meses"]
        )

        tickets_nuevos = int(
            configuracion["tickets"]
        )

        vencimiento_actual = convertir_fecha(
            usuario.get("vence_plan")
        )

        estado_plan_actual = str(
            usuario.get("estado_plan", "")
        ).upper()

        if (
            vencimiento_actual
            and vencimiento_actual > ahora
            and estado_plan_actual == "ACTIVO"
        ):
            fecha_inicio = vencimiento_actual
        else:
            fecha_inicio = ahora

        nuevo_vencimiento = sumar_meses(
            fecha_inicio,
            meses,
        )

        datos_usuario = {
            "plan": producto,
            "estado_plan": "ACTIVO",
            "vence_plan": nuevo_vencimiento.isoformat(),
            "tickets": (
                tickets_actuales + tickets_nuevos
            ),
        }

        mensaje = (
            f"{producto} activado y "
            f"{tickets_nuevos} ticket(s) agregado(s)"
        )

        return datos_usuario, mensaje

    if tipo == "tickets":
        cantidad_tickets = PAQUETES_TICKETS.get(
            producto
        )

        if cantidad_tickets is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "El paquete de tickets no está "
                    f"configurado: {producto}"
                ),
            )

        datos_usuario = {
            "tickets": (
                tickets_actuales
                + int(cantidad_tickets)
            ),
        }

        mensaje = (
            f"{cantidad_tickets} tickets "
            "agregados correctamente"
        )

        return datos_usuario, mensaje

    raise HTTPException(
        status_code=400,
        detail=(
            "El tipo de orden no es válido. "
            "Debe ser membresia o tickets"
        ),
    )


def revertir_marcado_orden(
    orden_id: int,
    estado_anterior: str,
    pagado_en_anterior: Optional[str],
) -> None:
    try:
        (
            supabase.table("ordenes")
            .update(
                {
                    "estado": estado_anterior,
                    "pagado_en": pagado_en_anterior,
                    "beneficios_aplicados": False,
                }
            )
            .eq("id", orden_id)
            .execute()
        )

    except Exception:
        pass


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
                orden_existente["creado_en"].replace(
                    "Z",
                    "+00:00",
                )
            )

            ahora = datetime.now(
                creado.tzinfo
            )

            if ahora - creado < timedelta(minutes=30):
                return {
                    "ok": True,
                    "mensaje": (
                        "Orden pendiente reutilizada"
                    ),
                    "reutilizada": True,
                    "orden": orden_existente,
                }

            (
                supabase.table("ordenes")
                .update({"estado": "expirada"})
                .eq("id", orden_existente["id"])
                .execute()
            )

        fecha = datetime.now(
            timezone.utc
        ).strftime("%Y%m%d%H%M%S")

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
            "beneficios_aplicados": False,
        }

        respuesta = (
            supabase.table("ordenes")
            .insert(datos)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=500,
                detail=(
                    "La orden no pudo ser registrada"
                ),
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
            detail=error.message,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@router.get("/listar")
def listar_ordenes(
    admin_usuario_id: int = Query(
        ...,
        description="ID del usuario administrador",
    ),
):
    try:
        validar_administrador(
            admin_usuario_id
        )

        respuesta_ordenes = (
            supabase.table("ordenes")
            .select("*")
            .order("creado_en", desc=True)
            .execute()
        )

        return {
            "ok": True,
            "total": len(
                respuesta_ordenes.data or []
            ),
            "ordenes": (
                respuesta_ordenes.data or []
            ),
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


@router.post("/{orden_id}/aprobar")
def aprobar_orden(
    orden_id: int,
    admin_usuario_id: int = Query(
        ...,
        description="ID del usuario administrador",
    ),
):
    try:
        validar_administrador(
            admin_usuario_id
        )

        orden = obtener_orden(
            orden_id
        )

        estado_actual = str(
            orden.get("estado", "")
        ).lower()

        beneficios_aplicados = bool(
            orden.get("beneficios_aplicados", False)
        )

        if beneficios_aplicados:
            return {
                "ok": True,
                "mensaje": (
                    "La orden ya fue aprobada y sus "
                    "beneficios ya fueron aplicados"
                ),
                "orden": orden,
            }

        if estado_actual == "cancelada":
            raise HTTPException(
                status_code=400,
                detail=(
                    "No se puede aprobar una "
                    "orden cancelada"
                ),
            )

        if estado_actual == "expirada":
            raise HTTPException(
                status_code=400,
                detail=(
                    "No se puede aprobar una "
                    "orden expirada"
                ),
            )

        if estado_actual not in {
            "pendiente",
            "pagada",
            "aprobada",
        }:
            raise HTTPException(
                status_code=400,
                detail=(
                    "El estado actual de la orden "
                    "no permite aprobarla"
                ),
            )

        usuario_id = orden.get(
            "usuario_id"
        )

        if usuario_id is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "La orden no tiene un usuario "
                    "asociado"
                ),
            )

        usuario = obtener_usuario(
            int(usuario_id)
        )

        datos_usuario, mensaje_beneficio = (
            calcular_actualizacion_usuario(
                orden,
                usuario,
            )
        )

        ahora = datetime.now(
            timezone.utc
        ).isoformat()

        estado_anterior = str(
            orden.get("estado", "pendiente")
        )

        pagado_en_anterior = orden.get(
            "pagado_en"
        )

        respuesta_marcado = (
            supabase.table("ordenes")
            .update(
                {
                    "estado": "pagada",
                    "pagado_en": (
                        pagado_en_anterior or ahora
                    ),
                    "beneficios_aplicados": True,
                }
            )
            .eq("id", orden_id)
            .eq("beneficios_aplicados", False)
            .execute()
        )

        if not respuesta_marcado.data:
            orden_actualizada = obtener_orden(
                orden_id
            )

            if orden_actualizada.get(
                "beneficios_aplicados"
            ):
                return {
                    "ok": True,
                    "mensaje": (
                        "La orden ya fue procesada "
                        "anteriormente"
                    ),
                    "orden": orden_actualizada,
                }

            raise HTTPException(
                status_code=409,
                detail=(
                    "La orden está siendo procesada "
                    "o ya fue modificada"
                ),
            )

        try:
            respuesta_usuario = (
                supabase.table("usuarios")
                .update(datos_usuario)
                .eq("id", int(usuario_id))
                .execute()
            )

            if not respuesta_usuario.data:
                revertir_marcado_orden(
                    orden_id,
                    estado_anterior,
                    pagado_en_anterior,
                )

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "No fue posible actualizar "
                        "los beneficios del usuario"
                    ),
                )

        except Exception:
            revertir_marcado_orden(
                orden_id,
                estado_anterior,
                pagado_en_anterior,
            )
            raise

        orden_actualizada = obtener_orden(
            orden_id
        )

        return {
            "ok": True,
            "mensaje": (
                "Orden aprobada correctamente. "
                f"{mensaje_beneficio}"
            ),
            "orden": orden_actualizada,
            "usuario": respuesta_usuario.data[0],
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


@router.post("/{orden_id}/cancelar")
def cancelar_orden(
    orden_id: int,
    admin_usuario_id: int = Query(
        ...,
        description="ID del usuario administrador",
    ),
):
    try:
        validar_administrador(
            admin_usuario_id
        )

        orden = obtener_orden(
            orden_id
        )

        estado_actual = str(
            orden.get("estado", "")
        ).lower()

        beneficios_aplicados = bool(
            orden.get("beneficios_aplicados", False)
        )

        if estado_actual == "cancelada":
            return {
                "ok": True,
                "mensaje": (
                    "La orden ya se encuentra "
                    "cancelada"
                ),
                "orden": orden,
            }

        if beneficios_aplicados:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No se puede cancelar una orden "
                    "cuyos beneficios ya fueron "
                    "aplicados"
                ),
            )

        if estado_actual in {
            "pagada",
            "aprobada",
        }:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No se puede cancelar una orden "
                    "que ya fue pagada"
                ),
            )

        if estado_actual == "expirada":
            raise HTTPException(
                status_code=400,
                detail=(
                    "La orden ya se encuentra "
                    "expirada"
                ),
            )

        respuesta = (
            supabase.table("ordenes")
            .update({"estado": "cancelada"})
            .eq("id", orden_id)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=500,
                detail=(
                    "No fue posible cancelar "
                    "la orden"
                ),
            )

        return {
            "ok": True,
            "mensaje": (
                "Orden cancelada correctamente"
            ),
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