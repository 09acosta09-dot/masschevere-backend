from pydantic import BaseModel, EmailStr

class UsuarioCrear(BaseModel):
    nombres: str
    email: EmailStr
    celular: str
    password: str