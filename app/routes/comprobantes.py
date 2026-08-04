from fastapi import APIRouter

router = APIRouter(
    prefix="/comprobantes",
    tags=["Comprobantes"]
)

@router.get("/test")
def test():
    return {
        "ok": True,
        "mensaje": "Ruta de comprobantes funcionando"
    }