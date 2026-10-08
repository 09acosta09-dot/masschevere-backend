from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database.supabase import supabase


router = APIRouter(
    prefix="/productos",
    tags=["Productos"],
)


# =========================
# MODELOS
# =========================

class ProductoCrear(BaseModel):
    nombre: str
    categoria: str
    tipo: Optional[str] = None
    descripcion: Optional[str] = None
    caracteristicas: Optional[List[str]] = None
    imagen_url: Optional[str] = None
    instalacion_disponible: bool = False
    destacado: bool = False
    estado: str = "activo"


class ProductoEditar(BaseModel):
    nombre: Optional[str] = None
    categoria: Optional[str] = None
    tipo: Optional[str] = None
    descripcion: Optional[str] = None
    caracteristicas: Optional[List[str]] = None
    imagen_url: Optional[str] = None
    instalacion_disponible: Optional[bool] = None
    destacado: Optional[bool] = None
    estado: Optional[str] = None


# =========================
# VALIDACIONES
# =========================

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


def validar_estado(estado: str) -> str:
    estado = estado.lower().strip()

    if estado not in {"activo", "inactivo"}:
        raise HTTPException(
            status_code=400,
            detail="Estado no válido.",
        )

    return estado


def validar_categoria(categoria: str) -> str:
    categoria = categoria.strip()

    if not categoria:
        raise HTTPException(
            status_code=400,
            detail="La categoría del producto es obligatoria.",
        )

    return categoria


# =========================
# LISTADO PÚBLICO
# =========================

@router.get("/listar")
def listar_productos():
    try:
        respuesta = (
            supabase.table("productos")
            .select("*")
            .eq("estado", "activo")
            .order("id", desc=True)
            .execute()
        )

        return {
            "ok": True,
            "productos": respuesta.data or [],
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# =========================
# PRODUCTOS DESTACADOS
# =========================

@router.get("/destacados")
def listar_productos_destacados():
    try:
        respuesta = (
            supabase.table("productos")
            .select("*")
            .eq("estado", "activo")
            .eq("destacado", True)
            .order("id", desc=True)
            .execute()
        )

        return {
            "ok": True,
            "productos": respuesta.data or [],
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
def listar_productos_admin(
    admin_usuario_id: int = Query(...),
):
    validar_administrador(admin_usuario_id)

    try:
        respuesta = (
            supabase.table("productos")
            .select("*")
            .order("id", desc=True)
            .execute()
        )

        return {
            "ok": True,
            "productos": respuesta.data or [],
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
def crear_producto(
    datos: ProductoCrear,
    admin_usuario_id: int = Query(...),
):
    validar_administrador(admin_usuario_id)

    nombre = datos.nombre.strip()

    if not nombre:
        raise HTTPException(
            status_code=400,
            detail="El nombre del producto es obligatorio.",
        )

    categoria = validar_categoria(datos.categoria)
    estado = validar_estado(datos.estado)

    try:
        nuevo = datos.model_dump()

        nuevo["nombre"] = nombre
        nuevo["categoria"] = categoria
        nuevo["estado"] = estado

        respuesta = (
            supabase.table("productos")
            .insert(nuevo)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=500,
                detail="No se pudo crear el producto.",
            )

        return {
            "ok": True,
            "mensaje": "Producto creado correctamente",
            "producto": respuesta.data[0],
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# =========================
# EDITAR
# =========================

@router.put("/{producto_id}/editar")
def editar_producto(
    producto_id: int,
    datos: ProductoEditar,
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

    if "nombre" in cambios:
        cambios["nombre"] = str(
            cambios["nombre"]
        ).strip()

        if not cambios["nombre"]:
            raise HTTPException(
                status_code=400,
                detail="El nombre del producto es obligatorio.",
            )

    if "categoria" in cambios:
        cambios["categoria"] = validar_categoria(
            cambios["categoria"]
        )

    if "estado" in cambios:
        cambios["estado"] = validar_estado(
            cambios["estado"]
        )

    try:
        respuesta = (
            supabase.table("productos")
            .update(cambios)
            .eq("id", producto_id)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=404,
                detail="El producto no existe.",
            )

        return {
            "ok": True,
            "mensaje": "Producto actualizado correctamente",
            "producto": respuesta.data[0],
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

@router.patch("/{producto_id}/estado")
def cambiar_estado(
    producto_id: int,
    estado: str,
    admin_usuario_id: int = Query(...),
):
    validar_administrador(admin_usuario_id)

    estado = validar_estado(estado)

    try:
        respuesta = (
            supabase.table("productos")
            .update({"estado": estado})
            .eq("id", producto_id)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=404,
                detail="El producto no existe.",
            )

        return {
            "ok": True,
            "mensaje": f"Producto marcado como {estado}",
            "producto": respuesta.data[0],
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

@router.delete("/{producto_id}")
def eliminar_producto(
    producto_id: int,
    admin_usuario_id: int = Query(...),
):
    validar_administrador(admin_usuario_id)

    try:
        respuesta = (
            supabase.table("productos")
            .delete()
            .eq("id", producto_id)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=404,
                detail="El producto no existe.",
            )

        return {
            "ok": True,
            "mensaje": "Producto eliminado correctamente",
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )