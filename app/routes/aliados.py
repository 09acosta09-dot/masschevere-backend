from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database.supabase import supabase


router = APIRouter(
    prefix="/aliados",
    tags=["Aliados"],
)


class AliadoCrear(BaseModel):
    nombre: str
    categoria: Optional[str] = None
    beneficio: Optional[str] = None
    descripcion: Optional[str] = None
    logo_url: Optional[str] = None
    direccion: Optional[str] = None
    instagram: Optional[str] = None
    whatsapp: Optional[str] = None
    estado: str = "activo"


class AliadoEditar(BaseModel):
    nombre: Optional[str] = None
    categoria: Optional[str] = None
    beneficio: Optional[str] = None
    descripcion: Optional[str] = None
    logo_url: Optional[str] = None
    direccion: Optional[str] = None
    instagram: Optional[str] = None
    whatsapp: Optional[str] = None
    estado: Optional[str] = None


def validar_administrador(admin_usuario_id: int):
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
            detail="Administrador no encontrado.",
        )

    rol = str(
        respuesta.data[0].get("rol", "")
    ).lower()

    if rol != "admin":
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para realizar esta acción.",
        )


# =========================
# LISTADO PÚBLICO
# =========================

@router.get("/listar")
def listar_aliados():
    try:
        respuesta = (
            supabase.table("aliados")
            .select("*")
            .eq("estado", "activo")
            .order("id", desc=True)
            .execute()
        )

        return {
            "ok": True,
            "aliados": respuesta.data or [],
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# =========================
# LISTADO ADMIN
# =========================

@router.get("/admin/listar")
def listar_aliados_admin(
    admin_usuario_id: int = Query(...),
):
    validar_administrador(admin_usuario_id)

    try:
        respuesta = (
            supabase.table("aliados")
            .select("*")
            .order("id", desc=True)
            .execute()
        )

        return {
            "ok": True,
            "aliados": respuesta.data or [],
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# =========================
# CREAR
# =========================

@router.post("/crear")
def crear_aliado(
    datos: AliadoCrear,
    admin_usuario_id: int = Query(...),
):
    validar_administrador(admin_usuario_id)

    if not datos.nombre.strip():
        raise HTTPException(
            status_code=400,
            detail="El nombre del aliado es obligatorio.",
        )

    try:
        nuevo = datos.model_dump()

        nuevo["nombre"] = datos.nombre.strip()

        respuesta = (
            supabase.table("aliados")
            .insert(nuevo)
            .execute()
        )

        return {
            "ok": True,
            "mensaje": "Aliado creado correctamente",
            "aliado": respuesta.data[0],
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# =========================
# EDITAR
# =========================

@router.put("/{aliado_id}/editar")
def editar_aliado(
    aliado_id: int,
    datos: AliadoEditar,
    admin_usuario_id: int = Query(...),
):
    validar_administrador(admin_usuario_id)

    cambios = datos.model_dump(
        exclude_none=True
    )

    if not cambios:
        raise HTTPException(
            status_code=400,
            detail="No hay cambios para guardar.",
        )

    try:
        respuesta = (
            supabase.table("aliados")
            .update(cambios)
            .eq("id", aliado_id)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=404,
                detail="El aliado no existe.",
            )

        return {
            "ok": True,
            "mensaje": "Aliado actualizado correctamente",
            "aliado": respuesta.data[0],
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# =========================
# CAMBIAR ESTADO
# =========================

@router.patch("/{aliado_id}/estado")
def cambiar_estado(
    aliado_id: int,
    estado: str,
    admin_usuario_id: int = Query(...),
):
    validar_administrador(admin_usuario_id)

    estado = estado.lower().strip()

    if estado not in {"activo", "inactivo"}:
        raise HTTPException(
            status_code=400,
            detail="Estado no válido.",
        )

    try:
        respuesta = (
            supabase.table("aliados")
            .update({"estado": estado})
            .eq("id", aliado_id)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=404,
                detail="El aliado no existe.",
            )

        return {
            "ok": True,
            "mensaje": f"Aliado marcado como {estado}",
            "aliado": respuesta.data[0],
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# =========================
# ELIMINAR
# =========================

@router.delete("/{aliado_id}")
def eliminar_aliado(
    aliado_id: int,
    admin_usuario_id: int = Query(...),
):
    validar_administrador(admin_usuario_id)

    try:
        respuesta = (
            supabase.table("aliados")
            .delete()
            .eq("id", aliado_id)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=404,
                detail="El aliado no existe.",
            )

        return {
            "ok": True,
            "mensaje": "Aliado eliminado correctamente",
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )