from pydantic import BaseModel, EmailStr


class UsuarioCrear(BaseModel):
    nombres: str
    email: EmailStr
    celular: str
    password: str


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

class RecuperarPassword(BaseModel):
    email: EmailStr
