from pydantic import BaseModel, EmailStr


class UsuarioCrear(BaseModel):
    nombres: str
    email: EmailStr
    celular: str
    password: str
    codigo_referido: str | None = None


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

class RecuperarPassword(BaseModel):
    email: EmailStr

class RestablecerPassword(BaseModel):
    email: EmailStr
    codigo: str
    nueva_password: str