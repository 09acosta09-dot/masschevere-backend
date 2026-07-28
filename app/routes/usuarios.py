import random

from passlib.context import CryptContext
from fastapi import APIRouter
from postgrest.exceptions import APIError

from app.database.supabase import supabase
from app.schemas.usuario import UsuarioCrear


router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
@router.post("/crear")
def crear_usuario(usuario: UsuarioCrear):
    codigo = "MC" + str(random.randint(100000, 999999))

    datos = {
        "nombres": usuario.nombres,
        "apellidos": "",
        "email": usuario.email,
        "celular": usuario.celular,
        "password": pwd_context.hash(usuario.password),
        "codigo_referido": codigo,
        "tickets": 1,
    }

    try:
        respuesta = supabase.table("usuarios").insert(datos).execute()

        return {
            "ok": True,
            "mensaje": "Usuario registrado correctamente",
            "codigo_referido": codigo,
            "usuario": respuesta.data,
        }

    except APIError as error:
        return {
            "ok": False,
            "mensaje": error.message,
        }