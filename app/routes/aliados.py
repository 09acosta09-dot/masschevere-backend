from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

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


@router.get("/listar")
def listar_aliados():
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


@router.post("/crear")
def crear_aliado(datos: AliadoCrear):
    try:
        if not datos.nombre.strip():
            raise HTTPException(
                status_code=400,
                detail="El nombre del aliado es obligatorio.",
            )

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

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@router.put("/{aliado_id}/editar")
def editar_aliado(
    aliado_id: int,
    datos: AliadoEditar,
):
    try:
        cambios = datos.model_dump(
            exclude_none=True
        )

        if not cambios:
            raise HTTPException(
                status_code=400,
                detail="No hay cambios para guardar.",
            )

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


@router.patch("/{aliado_id}/estado")
def cambiar_estado(
    aliado_id: int,
    estado: str,
):
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


@router.delete("/{aliado_id}")
def eliminar_aliado(aliado_id: int):
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