from fastapi import APIRouter, UploadFile, File, HTTPException

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


@router.post("/subir")
async def subir_comprobante(
    archivo: UploadFile = File(...)
):

    if not archivo.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten imágenes."
        )

    return {
        "ok": True,
        "nombre": archivo.filename,
        "tipo": archivo.content_type
    }