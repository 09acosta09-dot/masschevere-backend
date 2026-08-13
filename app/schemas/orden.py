from pydantic import BaseModel


class OrdenCrear(BaseModel):
    producto: str
    metodo_pago: str