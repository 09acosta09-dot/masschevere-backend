from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from postgrest.exceptions import APIError
from pydantic import BaseModel, Field

from app.database.supabase import supabase


router = APIRouter(
    prefix="/premios",
    tags=["Premios"],
)


class PremioCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    tickets_minimos: int = Field(default=1, ge=1)
    estado: str = "proximamente"


class PremioEditar(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    tickets_minimos: int = Field(default=1, ge=1)
    estado: str = "proximamente"
    ganador: Optional[str] = None


class PremioEstado(BaseModel):
    estado: str


ESTADOS_VALIDOS = {
    "proximamente",
    "activo",
    "pausado",
    "finalizado",
    "archivado",
}


def validar_administrador(admin_usuario_id: int) -> None:
    respuesta = (
        supabase.table("usuarios")
        .select("id,rol")
        .eq("id", admin_usuario_id)
        .limit(1)
        .execute()
    )

    if not respuesta.data:
        raise HTTPException(
            status_code=404,
            detail="Usuario administrador no encontrado",
        )

    rol = str(
        respuesta.data[0].get("rol", "")
    ).lower()

    if rol != "admin":
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para realizar esta acción",
        )


def validar_estado(estado: str) -> str:
    estado_normalizado = estado.strip().lower()

    if estado_normalizado not in ESTADOS_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Estado inválido. Usa: proximamente, activo, "
                "pausado, finalizado o archivado"
            ),
        )

    return estado_normalizado


@router.get("/listar")
def listar_premios(
    admin_usuario_id: int = Query(...),
):
    try:
        validar_administrador(admin_usuario_id)

        respuesta = (
            supabase.table("premios")
            .select("*")
            .neq("estado", "archivado")
            .order("creado_en", desc=True)
            .execute()
        )

        return {
            "ok": True,
            "total": len(respuesta.data or []),
            "premios": respuesta.data or [],
        }

    except HTTPException:
        raise

    except APIError as error:
        raise HTTPException(
            status_code=500,
            detail=error.message,
        )


@router.post("/crear")
def crear_premio(
    premio: PremioCrear,
    admin_usuario_id: int = Query(...),
):
    try:
        validar_administrador(admin_usuario_id)

        estado = validar_estado(premio.estado)

        if (
            premio.fecha_inicio
            and premio.fecha_fin
            and premio.fecha_fin < premio.fecha_inicio
        ):
            raise HTTPException(
                status_code=400,
                detail="La fecha final no puede ser anterior a la inicial",
            )

        datos = premio.model_dump(
            mode="json"
        )

        datos["estado"] = estado

        respuesta = (
            supabase.table("premios")
            .insert(datos)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=500,
                detail="No fue posible crear el premio",
            )

        return {
            "ok": True,
            "mensaje": "Premio creado correctamente",
            "premio": respuesta.data[0],
        }

    except HTTPException:
        raise

    except APIError as error:
        raise HTTPException(
            status_code=500,
            detail=error.message,
        )


@router.put("/{premio_id}/editar")
def editar_premio(
    premio_id: int,
    premio: PremioEditar,
    admin_usuario_id: int = Query(...),
):
    try:
        validar_administrador(admin_usuario_id)

        estado = validar_estado(premio.estado)

        if (
            premio.fecha_inicio
            and premio.fecha_fin
            and premio.fecha_fin < premio.fecha_inicio
        ):
            raise HTTPException(
                status_code=400,
                detail="La fecha final no puede ser anterior a la inicial",
            )

        datos = premio.model_dump(
            mode="json"
        )

        datos["estado"] = estado

        respuesta = (
            supabase.table("premios")
            .update(datos)
            .eq("id", premio_id)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=404,
                detail="Premio no encontrado",
            )

        return {
            "ok": True,
            "mensaje": "Premio actualizado correctamente",
            "premio": respuesta.data[0],
        }

    except HTTPException:
        raise

    except APIError as error:
        raise HTTPException(
            status_code=500,
            detail=error.message,
        )


@router.patch("/{premio_id}/estado")
def cambiar_estado_premio(
    premio_id: int,
    datos_estado: PremioEstado,
    admin_usuario_id: int = Query(...),
):
    try:
        validar_administrador(admin_usuario_id)

        estado = validar_estado(
            datos_estado.estado
        )

        respuesta = (
            supabase.table("premios")
            .update({"estado": estado})
            .eq("id", premio_id)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=404,
                detail="Premio no encontrado",
            )

        return {
            "ok": True,
            "mensaje": f"Premio cambiado a {estado}",
            "premio": respuesta.data[0],
        }

    except HTTPException:
        raise

    except APIError as error:
        raise HTTPException(
            status_code=500,
            detail=error.message,
        )


@router.patch("/{premio_id}/archivar")
def archivar_premio(
    premio_id: int,
    admin_usuario_id: int = Query(...),
):
    try:
        validar_administrador(admin_usuario_id)

        respuesta = (
            supabase.table("premios")
            .update({"estado": "archivado"})
            .eq("id", premio_id)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=404,
                detail="Premio no encontrado",
            )

        return {
            "ok": True,
            "mensaje": "Premio archivado correctamente",
            "premio": respuesta.data[0],
        }

    except HTTPException:
        raise

    except APIError as error:
        raise HTTPException(
            status_code=500,
            detail=error.message,
        )