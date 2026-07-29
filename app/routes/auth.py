from fastapi import APIRouter, HTTPException
from pwdlib import PasswordHash

from app.database.supabase import supabase
from app.schemas.usuario import UsuarioLogin, RecuperarPassword

router = APIRouter(prefix="/auth", tags=["Autenticación"])
password_hash = PasswordHash.recommended()


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
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

    usuario = respuesta.data[0]

    try:
        password_valida = password_hash.verify(
            datos.password,
            usuario["password"]
        )
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Esta cuenta debe restablecer su contraseña"
        )

    if not password_valida:
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos"
        )

    return {
        "ok": True,
        "usuario_id": usuario["id"],
        "nombres": usuario["nombres"],
        "estado_plan": usuario["estado_plan"],
        "rol": usuario["rol"],
    }
import random
from datetime import datetime, timedelta, timezone


@router.post("/solicitar-recuperacion")
def solicitar_recuperacion(datos: RecuperarPassword):
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
            detail="No existe una cuenta con ese correo"
        )

    codigo = str(random.randint(100000, 999999))
    expiracion = datetime.now(timezone.utc) + timedelta(minutes=15)

    supabase.table("recuperacion_password").insert({
        "email": datos.email,
        "codigo": codigo,
        "usado": False,
        "fecha_expiracion": expiracion.isoformat()
    }).execute()

    return {
        "ok": True,
        "mensaje": "Código generado correctamente",
        "codigo": codigo
    }