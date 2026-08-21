from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.database.supabase import supabase


router = APIRouter(
    prefix="/verificacion",
    tags=["Verificación de membresía"],
)


@router.get("/{qr_token}")
def verificar_membresia(qr_token: UUID):
    try:
        respuesta = (
            supabase.table("usuarios")
            .select(
                "id,nombres,apellidos,plan,"
                "estado_plan,vence_plan,qr_token"
            )
            .eq("qr_token", str(qr_token))
            .limit(1)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=404,
                detail="Código de verificación no válido.",
            )

        usuario = respuesta.data[0]

        estado_plan = str(
            usuario.get("estado_plan") or ""
        ).upper()

        vence_plan = usuario.get("vence_plan")

        vigente_por_fecha = False

        if vence_plan:
            try:
                fecha_vencimiento = datetime.fromisoformat(
                    str(vence_plan).replace("Z", "+00:00")
                )

                if fecha_vencimiento.tzinfo is None:
                    fecha_vencimiento = fecha_vencimiento.replace(
                        tzinfo=timezone.utc
                    )

                vigente_por_fecha = (
                    fecha_vencimiento > datetime.now(timezone.utc)
                )

            except Exception:
                vigente_por_fecha = False

        membresia_activa = (
            estado_plan == "ACTIVO"
            and vigente_por_fecha
        )

        nombre_completo = " ".join(
            [
                str(usuario.get("nombres") or "").strip(),
                str(usuario.get("apellidos") or "").strip(),
            ]
        ).strip()

        return {
            "ok": True,
            "membresia_activa": membresia_activa,
            "estado": (
                "ACTIVA"
                if membresia_activa
                else "INACTIVA"
            ),
            "usuario": {
                "nombre": nombre_completo,
                "plan": usuario.get("plan"),
                "estado_plan": estado_plan,
                "vence_plan": vence_plan,
            },
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )