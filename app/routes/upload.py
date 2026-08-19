from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from postgrest.exceptions import APIError

from app.database.supabase import supabase


router = APIRouter(
    prefix="/upload",
    tags=["Subida de archivos"],
)

TAMANO_MAXIMO = 5 * 1024 * 1024

TIPOS_PERMITIDOS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

BUCKETS_PERMITIDOS = {
    "premios",
    "comprobantes",
    "aliados",
}


@router.post("/imagen")
async def subir_imagen(
    bucket: str = Form(...),
    carpeta: str = Form("general"),
    archivo: UploadFile = File(...),
):
    if bucket not in BUCKETS_PERMITIDOS:
        raise HTTPException(
            status_code=400,
            detail="El bucket indicado no está permitido.",
        )

    if archivo.content_type not in TIPOS_PERMITIDOS:
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten imágenes JPG, PNG o WEBP.",
        )

    contenido = await archivo.read()

    if not contenido:
        raise HTTPException(
            status_code=400,
            detail="El archivo está vacío.",
        )

    if len(contenido) > TAMANO_MAXIMO:
        raise HTTPException(
            status_code=400,
            detail="La imagen no puede superar los 5 MB.",
        )

    extension = TIPOS_PERMITIDOS[archivo.content_type]

    carpeta_limpia = (
        carpeta.strip()
        .replace("..", "")
        .replace("/", "-")
        .replace("\\", "-")
        or "general"
    )

    nombre_archivo = (
        f"{carpeta_limpia}/"
        f"{uuid4().hex}{extension}"
    )

    try:
        supabase.storage.from_(bucket).upload(
            path=nombre_archivo,
            file=contenido,
            file_options={
                "content-type": archivo.content_type,
                "cache-control": "3600",
                "upsert": "false",
            },
        )

        url_publica = (
            supabase.storage
            .from_(bucket)
            .get_public_url(nombre_archivo)
        )

        return {
            "ok": True,
            "mensaje": "Imagen subida correctamente",
            "bucket": bucket,
            "ruta": nombre_archivo,
            "url": url_publica,
        }

    except APIError as error:
        raise HTTPException(
            status_code=500,
            detail=error.message,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    finally:
        await archivo.close()