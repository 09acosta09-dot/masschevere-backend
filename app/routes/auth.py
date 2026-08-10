import os
import random
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException
from pwdlib import PasswordHash

from app.database.supabase import supabase
from app.schemas.usuario import (
    UsuarioLogin,
    RecuperarPassword,
    RestablecerPassword,
)


router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"],
)

password_hash = PasswordHash.recommended()


def crear_access_token(
    usuario_id: int,
    rol: str,
) -> str:

    secret = os.getenv("JWT_SECRET")
    algorithm = os.getenv(
        "JWT_ALGORITHM",
        "HS256",
    )

    if not secret:
        raise HTTPException(
            status_code=500,
            detail="JWT_SECRET no está configurado.",
        )

    ahora = datetime.now(timezone.utc)

    payload = {
        "sub": str(usuario_id),
        "rol": rol,
        "iat": ahora,
        "exp": ahora + timedelta(hours=24),
    }

    return jwt.encode(
        payload,
        secret,
        algorithm=algorithm,
    )


@router.post("/login")
def login(datos: UsuarioLogin):

    respuesta = (
        supabase.table("usuarios")
        .select("*")
        .eq("email", datos.email)
        .limit(1)
        .execute()
    )

    if not respuesta.data:
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos",
        )

    usuario = respuesta.data[0]

    try:
        password_valida = password_hash.verify(
            datos.password,
            usuario["password"],
        )

    except Exception:
        raise HTTPException(
            status_code=401,
            detail=(
                "Esta cuenta debe restablecer "
                "su contraseña"
            ),
        )

    if not password_valida:
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos",
        )

    access_token = crear_access_token(
        usuario["id"],
        usuario.get("rol", "USUARIO"),
    )

    return {
        "ok": True,

        "access_token": access_token,
        "token_type": "bearer",

        "usuario": {
            "usuario_id": usuario["id"],
            "nombres": usuario["nombres"],
            "estado_plan": usuario["estado_plan"],
            "plan": usuario["plan"],
            "tickets": usuario["tickets"],
            "codigo_referido":
                usuario["codigo_referido"],
            "referido_por":
                usuario["referido_por"],
            "rol": usuario["rol"],
        },
    }


@router.post("/solicitar-recuperacion")
def solicitar_recuperacion(
    datos: RecuperarPassword,
):

    usuario = (
        supabase.table("usuarios")
        .select("id,email")
        .eq("email", datos.email)
        .limit(1)
        .execute()
    )

    if not usuario.data:
        raise HTTPException(
            status_code=404,
            detail=(
                "No existe una cuenta "
                "con ese correo"
            ),
        )

    codigo = str(
        random.randint(100000, 999999)
    )

    expiracion = (
        datetime.now(timezone.utc)
        + timedelta(minutes=15)
    )

    supabase.table(
        "recuperacion_password"
    ).insert({
        "email": datos.email,
        "codigo": codigo,
        "usado": False,
        "fecha_expiracion":
            expiracion.isoformat(),
    }).execute()

    return {
        "ok": True,
        "mensaje":
            "Código generado correctamente",
        "codigo": codigo,
    }


@router.post("/restablecer-password")
def restablecer_password(
    datos: RestablecerPassword,
):

    recuperacion = (
        supabase.table(
            "recuperacion_password"
        )
        .select("*")
        .eq("email", datos.email)
        .eq("codigo", datos.codigo)
        .eq("usado", False)
        .limit(1)
        .execute()
    )

    if not recuperacion.data:
        raise HTTPException(
            status_code=400,
            detail="Código inválido",
        )

    codigo = recuperacion.data[0]

    fecha_expiracion = datetime.fromisoformat(
        codigo["fecha_expiracion"]
    )

    if (
        fecha_expiracion
        < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=400,
            detail="El código ya expiró",
        )

    nueva_password = password_hash.hash(
        datos.nueva_password
    )

    (
        supabase.table("usuarios")
        .update({
            "password": nueva_password
        })
        .eq("email", datos.email)
        .execute()
    )

    (
        supabase.table(
            "recuperacion_password"
        )
        .update({
            "usado": True
        })
        .eq("id", codigo["id"])
        .execute()
    )

    return {
        "ok": True,
        "mensaje":
            "Contraseña actualizada correctamente",
    }