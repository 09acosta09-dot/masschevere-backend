import os
import secrets
from datetime import datetime, timedelta, timezone

import httpx
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


def enviar_codigo_recuperacion(
    destinatario: str,
    codigo: str,
) -> None:

    api_key = os.getenv("RESEND_API_KEY")

    if not api_key:
        raise RuntimeError(
            "RESEND_API_KEY no está configurado."
        )

    remitente = os.getenv(
        "EMAIL_FROM",
        "privacidad@masschevere.com",
    )

    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="
        margin:0;
        padding:30px;
        background:#080808;
        font-family:Arial,sans-serif;
    ">

        <div style="
            max-width:600px;
            margin:auto;
            background:#111111;
            border:1px solid #FFC400;
            border-radius:20px;
            padding:35px;
            text-align:center;
        ">

            <h1 style="
                color:#FFC400;
                margin:0 0 25px;
            ">
                MASSCHEVERE
            </h1>

            <h2 style="
                color:#FFFFFF;
                margin-bottom:15px;
            ">
                Recuperación de contraseña
            </h2>

            <p style="
                color:#CCCCCC;
                line-height:1.7;
            ">
                Recibimos una solicitud para
                restablecer la contraseña de tu cuenta.
            </p>

            <p style="
                color:#CCCCCC;
            ">
                Tu código de recuperación es:
            </p>

            <div style="
                margin:25px auto;
                padding:18px;
                background:#1B1B1B;
                border-radius:14px;
                color:#FFC400;
                font-size:34px;
                font-weight:bold;
                letter-spacing:8px;
            ">
                {codigo}
            </div>

            <p style="
                color:#CCCCCC;
                line-height:1.7;
            ">
                Este código vence en
                <strong style="color:#FFFFFF;">
                    15 minutos
                </strong>.
            </p>

            <p style="
                color:#888888;
                font-size:13px;
                margin-top:30px;
            ">
                Si tú no solicitaste este cambio,
                puedes ignorar este mensaje.
            </p>

            <p style="
                color:#666666;
                font-size:12px;
                margin-top:25px;
            ">
                MassChevere.com
            </p>

        </div>

    </body>
    </html>
    """

    texto = f"""
MassChevere

Recibimos una solicitud para restablecer
la contraseña de tu cuenta.

Tu código de recuperación es:

{codigo}

Este código vence en 15 minutos.

Si tú no solicitaste este cambio,
puedes ignorar este mensaje.

MassChevere.com
"""

    respuesta = httpx.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization":
                f"Bearer {api_key}",
            "Content-Type":
                "application/json",
            "User-Agent":
                "MassChevere-Backend/1.0",
        },
        json={
            "from":
                f"MassChevere <{remitente}>",
            "to": [destinatario],
            "subject":
                "Código para recuperar tu cuenta MassChevere",
            "html": html,
            "text": texto,
        },
        timeout=20.0,
    )

    if not 200 <= respuesta.status_code < 300:

        try:
            detalle = respuesta.json()
        except Exception:
            detalle = respuesta.text

        raise RuntimeError(
            f"Resend respondió "
            f"{respuesta.status_code}: "
            f"{detalle}"
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
        usuario.get(
            "rol",
            "USUARIO",
        ),
    )

    return {
        "ok": True,
        "access_token": access_token,
        "token_type": "bearer",

        "usuario": {
            "usuario_id":
                usuario["id"],

            "nombres":
                usuario["nombres"],

            "estado_plan":
                usuario["estado_plan"],

            "plan":
                usuario["plan"],

            "tickets":
                usuario["tickets"],

            "codigo_referido":
                usuario["codigo_referido"],

            "referido_por":
                usuario["referido_por"],

            "rol":
                usuario["rol"],
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

    mensaje_generico = {
        "ok": True,
        "mensaje": (
            "Si el correo está registrado, "
            "recibirás un código de recuperación."
        ),
    }

    # No revelar si el correo existe.
    if not usuario.data:
        return mensaje_generico

    codigo = str(
        100000
        + secrets.randbelow(900000)
    )

    expiracion = (
        datetime.now(timezone.utc)
        + timedelta(minutes=15)
    )

    # Invalidar códigos anteriores.
    (
        supabase.table(
            "recuperacion_password"
        )
        .update({
            "usado": True
        })
        .eq(
            "email",
            datos.email,
        )
        .eq(
            "usado",
            False,
        )
        .execute()
    )

    respuesta_codigo = (
        supabase.table(
            "recuperacion_password"
        )
        .insert({
            "email":
                datos.email,

            "codigo":
                codigo,

            "usado":
                False,

            "fecha_expiracion":
                expiracion.isoformat(),
        })
        .execute()
    )

    if not respuesta_codigo.data:
        raise HTTPException(
            status_code=500,
            detail=(
                "No fue posible generar "
                "el código de recuperación."
            ),
        )

    try:
        enviar_codigo_recuperacion(
            datos.email,
            codigo,
        )

    except Exception as error:

        # El código queda inutilizado
        # si el correo no pudo enviarse.
        (
            supabase.table(
                "recuperacion_password"
            )
            .update({
                "usado": True
            })
            .eq(
                "id",
                respuesta_codigo.data[0]["id"],
            )
            .execute()
        )

        print(
            "Error enviando correo "
            "de recuperación:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "No fue posible enviar "
                "el correo de recuperación."
            ),
        )

    return mensaje_generico


@router.post("/restablecer-password")
def restablecer_password(
    datos: RestablecerPassword,
):

    recuperacion = (
        supabase.table(
            "recuperacion_password"
        )
        .select("*")
        .eq(
            "email",
            datos.email,
        )
        .eq(
            "codigo",
            datos.codigo,
        )
        .eq(
            "usado",
            False,
        )
        .order(
            "fecha_expiracion",
            desc=True,
        )
        .limit(1)
        .execute()
    )

    if not recuperacion.data:
        raise HTTPException(
            status_code=400,
            detail=(
                "Código inválido "
                "o ya utilizado."
            ),
        )

    codigo = recuperacion.data[0]

    fecha_expiracion = datetime.fromisoformat(
        str(
            codigo["fecha_expiracion"]
        ).replace(
            "Z",
            "+00:00",
        )
    )

    if (
        fecha_expiracion
        < datetime.now(timezone.utc)
    ):

        (
            supabase.table(
                "recuperacion_password"
            )
            .update({
                "usado": True
            })
            .eq(
                "id",
                codigo["id"],
            )
            .execute()
        )

        raise HTTPException(
            status_code=400,
            detail="El código ya expiró.",
        )

    nueva_password = password_hash.hash(
        datos.nueva_password
    )

    respuesta_usuario = (
        supabase.table("usuarios")
        .update({
            "password":
                nueva_password
        })
        .eq(
            "email",
            datos.email,
        )
        .execute()
    )

    if not respuesta_usuario.data:
        raise HTTPException(
            status_code=500,
            detail=(
                "No fue posible actualizar "
                "la contraseña."
            ),
        )

    (
        supabase.table(
            "recuperacion_password"
        )
        .update({
            "usado": True
        })
        .eq(
            "id",
            codigo["id"],
        )
        .execute()
    )

    return {
        "ok": True,
        "mensaje": (
            "Contraseña actualizada "
            "correctamente."
        ),
    }