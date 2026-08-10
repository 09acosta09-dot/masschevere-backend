import random
from datetime import datetime, timezone

from fastapi import APIRouter
from postgrest.exceptions import APIError
from pwdlib import PasswordHash

from app.database.supabase import supabase
from app.schemas.usuario import UsuarioCrear


password_hash = PasswordHash.recommended()

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"],
)


@router.post("/crear")
def crear_usuario(usuario: UsuarioCrear):

    # Validar consentimiento legal
    if (
        not usuario.acepta_terminos
        or not usuario.acepta_tratamiento_datos
    ):
        return {
            "ok": False,
            "mensaje": (
                "Debes aceptar los Términos y Condiciones "
                "y autorizar el tratamiento de tus datos personales."
            ),
        }

    # Generar código de referido
    codigo = "MC" + str(
        random.randint(100000, 999999)
    )

    referido_por = None

    # Validar código de referido
    if usuario.codigo_referido:

        consulta = (
            supabase.table("usuarios")
            .select("id")
            .eq(
                "codigo_referido",
                usuario.codigo_referido
            )
            .execute()
        )

        if not consulta.data:
            return {
                "ok": False,
                "mensaje": (
                    "El código de referido no es válido."
                ),
            }

        referido_por = consulta.data[0]["id"]

    # Datos del nuevo usuario
    datos = {
        "nombres": usuario.nombres,
        "apellidos": "",
        "email": usuario.email,
        "celular": usuario.celular,
        "password": password_hash.hash(
            usuario.password
        ),
        "codigo_referido": codigo,
        "referido_por": referido_por,
        "tickets": 1,

        # Evidencia de consentimiento legal
        "acepta_terminos":
            usuario.acepta_terminos,

        "acepta_tratamiento_datos":
            usuario.acepta_tratamiento_datos,

        "fecha_aceptacion_legal":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "version_terminos":
            usuario.version_terminos,

        "version_politica_datos":
            usuario.version_politica_datos,
    }

    try:

        # Crear usuario
        respuesta = (
            supabase.table("usuarios")
            .insert(datos)
            .execute()
        )

        nuevo_usuario = respuesta.data[0]

        # Procesar referido
        if referido_por:

            usuario_referidor = (
                supabase.table("usuarios")
                .select("tickets")
                .eq("id", referido_por)
                .single()
                .execute()
            )

            tickets_actuales = (
                usuario_referidor.data["tickets"]
                or 0
            )

            supabase.table("usuarios").update({
                "tickets": tickets_actuales + 1
            }).eq(
                "id",
                referido_por
            ).execute()

            supabase.table("referidos").insert({
                "usuario_id": referido_por,
                "referido_id": nuevo_usuario["id"],
                "codigo_usado":
                    usuario.codigo_referido,
                "ticket_otorgado": True,
            }).execute()

        return {
            "ok": True,
            "mensaje":
                "Usuario registrado correctamente",
            "codigo_referido": codigo,
            "usuario": respuesta.data,
        }

    except APIError as error:

        return {
            "ok": False,
            "mensaje": error.message,
        }