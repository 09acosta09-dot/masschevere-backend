from pydantic import BaseModel


class OrdenCrear(BaseModel):
    usuario_id: int
    producto: str
    tipo: str
    valor: int
    metodo_pago: str