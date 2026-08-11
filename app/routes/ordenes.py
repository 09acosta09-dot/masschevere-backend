
Editar






esto es lo unico que va hecho sigamos con el menu


http://masschevere.online/wp-content/uploads/2026/07/MassOfmc-removebg-preview.png
esa es la url del logo edita el codigo para que aparezca por favor y bajalo un poco mas que quedó muy montado arriba

dom, 19 jul a las 11:38 p.m.





Estoy aqui dime que hacer o como hacemos para que tu hagas todo lo q me dijiste con botones animados y todo eso 



yo pegue el nuevo codigo que me dijiste y salio asi

el logo quedo hacia un lado como es para centrarlo


Editar


Editar


Se daño la sección 


Ahora quedó asi los botones de las redes me gustan pero se desacomodó esa parte

Las letras azules las quiero en el amarillo de la marca y aun falta el boton amarillo que estaba antes 


style.css
Archivo
este es el archivo

Editar


Editar





las lineas rojas son el espacio que quiero reducir 

El separador q tu dices es la linea amarilla q esta seleccionada y el espacio que esta marcado en rojo es otra cosa 


ves todo el espacio negro arriba y abajo del texto y el boton eso es lo q no me gusta mucho 



No Sofi aun esta amarillo y no me deja cambiar








Editar


Generame la misma imagen  pero usando este logo 

Editar


Editar


Editar



Arquitectura_Economica_v1_MassChevere(1).docx
Documento
Lee ese documento y basado en eso actua como la dueña del sitio y escribe el siguiente html pa el bloque que sigue 

Pero Sofi debemos poner la logica en el sitio web las paginas están creadas pero en este momento yo abro el sitio y no veo por donde iniciar sesión ... ahi esta la primera pantalla que aparece al entrar al sitio

Este es el menu que aparece activo 

donde creo el proyecto?

me sale esto 








masschevere-backend.zip
Archivo zip




No me deja editarlo directamente de ahi... Yo quiero que me ayudes a limpiar esos archivos y que queden los que realmente necesitamos porq esa carpeta comprimida no me deja modificar 










mié, 29 jul a las 11:42 a.m.












Listo quedo así porq no se porq razón cuando pego el codigo no queda identado como tu lo pones sino q me toca estar corriendo para que se acomode pero eso q esta como en naranja no quizo moverse a donde deberia ir


Pasted text.txt
Documento


Pasted text(1).txt
Documento

Esto es lo q veo




Pasted text(2).txt
Documento


Pasted text(3).txt
Documento


Sofi perdiste el contexto??

y estos son los valores para quienes quieran comprar mas tickets y tener mas oportunidades



esas son todas


Pasted text(4).txt
Documento

image(127).png
image(128).png









MassOfmc-removebg-preview.png
MassOfmc__1_-removebg-preview.png
La que dice masschevere quiero q sea la splash screen

Editar


Editar


Editar



Ya pero aparece doble






pero no veo desde donde voy a arrastrar el bloque




A no Sofi aparece así y me gusta pero no aparece "MENU FUNCIONANDO" Yo dije asi porq me funciona pero no porq aparece esa frase 





martes 1:03 p.m.

Pasted text(5).txt
Documento


Pasted text(6).txt
Documento

porq aparece ese error la x roja

Solo un detalle, ese espacio donde puse la raya roja no lo podemos eliminar?? queda mucho espacio 




jueves 1:11 p.m.

Puse lo del style pero no cambia se queda azul 


Pasted text(7).txt
Documento


Código pegado: py
Archivo

No, tranquilo 😄. La parte pesada ya la hicimos.

Las variables JWT_SECRET y JWT_ALGORITHM ya existen en Railway y sirven para todo el sistema. Tampoco necesitamos instalar nuevamente PyJWT.

Ahora simplemente reutilizamos el mismo JWT para proteger las funciones del administrador.

Sí habrá un nuevo deploy, porque modificaremos código del backend, pero será el normal:

git add .
git commit -m "Proteger acciones administrativas con JWT"
git push origin main
En resumen: no empezamos de cero. Ya construimos la cerradura y la llave; ahora simplemente vamos a poner esa misma cerradura en la puerta del administrador. 😄

Si seguimos, lo hacemos igual que hoy: un cambio a la vez y probamos antes de avanzar.


Ok dime la acción

Vamos. Primero protegemos listar órdenes, y después aprobar/cancelar.

Acción 1
En ordenes.py ya creamos esta función:

obtener_usuario_desde_token(...)
Justo debajo de esa función agrega esta nueva:

def obtener_admin_desde_token(
    authorization: str | None,
) -> int:

    usuario_id = obtener_usuario_desde_token(
        authorization
    )

    respuesta = (
        supabase.table("usuarios")
        .select("id,rol")
        .eq("id", usuario_id)
        .limit(1)
        .execute()
    )

    if not respuesta.data:
        raise HTTPException(
            status_code=401,
            detail="Usuario no encontrado",
        )

    usuario = respuesta.data[0]

    if str(
        usuario.get("rol", "")
    ).lower() != "admin":

        raise HTTPException(
            status_code=403,
            detail="No tienes permisos de administrador",
        )

    return usuario_id
Esto hace dos comprobaciones:

JWT válido → identifica usuario → comprueba en Supabase que realmente tenga rol admin.

Haz solo esto por ahora y dime listo. Luego conectamos esa protección a /ordenes/listar.



Código pegado: py(1)
Archivo
Te lo envio completo y tu me lo regresas corregido porq no se donde esta eso que me dices

Procesó durante 1m 22s
Sí. Ya te lo corregí completo para que no tengas que buscar dónde va cada parte.

Hice estos cambios:

eliminé la validación antigua por admin_usuario_id;

agregué validación de administrador usando el JWT;

protegí /ordenes/listar;

protegí /ordenes/{id}/aprobar;

protegí /ordenes/{id}/cancelar;

mantuve intacta la lógica que ya funcionaba para crear órdenes, aplicar membresías y tickets. El archivo original todavía validaba administración mediante un ID enviado por parámetro en esas rutas. 


Además, verifiqué que el archivo corregido no tenga errores de sintaxis.


Acción
Descarga el archivo.

Reemplaza todo el contenido de:

app/routes/ordenes.py
Guarda.

Todavía no hagas deploy. Cuando me digas listo, te doy el siguiente cambio en el panel Admin para que envíe el token JWT al listar, aprobar y cancelar órdenes.



Biblioteca
/
ordenes_corregido.py


import calendar
from datetime import datetime, timedelta, timezone
from typing import Optional

import os
import jwt

from fastapi import (
    APIRouter,
    HTTPException,
    Header,
)
from postgrest.exceptions import APIError

from app.database.supabase import supabase
from app.schemas.orden import OrdenCrear


router = APIRouter(prefix="/ordenes", tags=["Órdenes"])


PLANES_MEMBRESIA = {
    "Plan Mensual": {
        "meses": 1,
        "tickets": 1,
    },
    "Plan Trimestral": {
        "meses": 3,
        "tickets": 3,
    },
    "Plan Semestral": {
        "meses": 6,
        "tickets": 6,
    },
    "Plan Anual": {
        "meses": 12,
        "tickets": 12,
    },
}


PAQUETES_TICKETS = {
    "Paquete de 10 Tickets": 10,
    "Paquete de 25 Tickets": 25,
    "Paquete de 50 Tickets": 50,
    "Paquete de 100 Tickets": 100,
}


def obtener_orden(orden_id: int) -> dict:
    respuesta_orden = (
        supabase.table("ordenes")
        .select("*")
        .eq("id", orden_id)
        .limit(1)
        .execute()
    )

    if not respuesta_orden.data:
        raise HTTPException(
            status_code=404,
            detail="Orden no encontrada",
        )

    return respuesta_orden.data[0]


def obtener_usuario(usuario_id: int) -> dict:
    respuesta_usuario = (
        supabase.table("usuarios")
        .select(
            "id,plan,estado_plan,vence_plan,tickets"
        )
        .eq("id", usuario_id)
        .limit(1)
        .execute()
    )

    if not respuesta_usuario.data:
        raise HTTPException(
            status_code=404,
            detail="Usuario asociado a la orden no encontrado",
        )

    return respuesta_usuario.data[0]


def convertir_fecha(
    valor: Optional[str],
) -> Optional[datetime]:
    if not valor:
        return None

    try:
        fecha = datetime.fromisoformat(
            str(valor).replace("Z", "+00:00")
        )

        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)

        return fecha

    except (TypeError, ValueError):
        return None


def sumar_meses(
    fecha: datetime,
    cantidad_meses: int,
) -> datetime:
    mes_total = (
        fecha.month - 1 + cantidad_meses
    )

    nuevo_anio = (
        fecha.year + mes_total // 12
    )

    nuevo_mes = (
        mes_total % 12 + 1
    )

    ultimo_dia_mes = calendar.monthrange(
        nuevo_anio,
        nuevo_mes,
    )[1]

    nuevo_dia = min(
        fecha.day,
        ultimo_dia_mes,
    )

    return fecha.replace(
        year=nuevo_anio,
        month=nuevo_mes,
        day=nuevo_dia,
    )


def calcular_actualizacion_usuario(
    orden: dict,
    usuario: dict,
) -> tuple[dict, str]:
    producto = str(
        orden.get("producto", "")
    ).strip()

    tipo = str(
        orden.get("tipo", "")
    ).strip().lower()

    tickets_actuales = int(
        usuario.get("tickets") or 0
    )

    ahora = datetime.now(timezone.utc)

    if tipo == "membresia":
        configuracion = PLANES_MEMBRESIA.get(
            producto
        )

        if not configuracion:
            raise HTTPException(
                status_code=400,
                detail=(
                    "El producto de membresía no está "
                    f"configurado: {producto}"
                ),
            )

        meses = int(
            configuracion["meses"]
        )

        tickets_nuevos = int(
            configuracion["tickets"]
        )

        vencimiento_actual = convertir_fecha(
            usuario.get("vence_plan")
        )

        estado_plan_actual = str(
            usuario.get("estado_plan", "")
        ).upper()

        if (
            vencimiento_actual
            and vencimiento_actual > ahora
            and estado_plan_actual == "ACTIVO"
        ):
            fecha_inicio = vencimiento_actual
        else:
            fecha_inicio = ahora

        nuevo_vencimiento = sumar_meses(
            fecha_inicio,
            meses,
        )

        datos_usuario = {
            "plan": producto,
            "estado_plan": "ACTIVO",
            "vence_plan": nuevo_vencimiento.isoformat(),
            "tickets": (
                tickets_actuales + tickets_nuevos
            ),
        }

        mensaje = (
            f"{producto} activado y "
            f"{tickets_nuevos} ticket(s) agregado(s)"
        )

        return datos_usuario, mensaje

    if tipo == "tickets":
        cantidad_tickets = PAQUETES_TICKETS.get(
            producto
        )

        if cantidad_tickets is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "El paquete de tickets no está "
                    f"configurado: {producto}"
                ),
            )

        datos_usuario = {
            "tickets": (
                tickets_actuales
                + int(cantidad_tickets)
            ),
        }

        mensaje = (
            f"{cantidad_tickets} tickets "
            "agregados correctamente"
        )

        return datos_usuario, mensaje

    raise HTTPException(
        status_code=400,
        detail=(
            "El tipo de orden no es válido. "
            "Debe ser membresia o tickets"
        ),
    )


def revertir_marcado_orden(
    orden_id: int,
    estado_anterior: str,
    pagado_en_anterior: Optional[str],
) -> None:
    try:
        (
            supabase.table("ordenes")
            .update(
                {
                    "estado": estado_anterior,
                    "pagado_en": pagado_en_anterior,
                    "beneficios_aplicados": False,
                }
            )
            .eq("id", orden_id)
            .execute()
        )

    except Exception:
        pass

def obtener_usuario_desde_token(
    authorization: str | None,
) -> int:

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Debes iniciar sesión",
        )

    partes = authorization.split()

    if (
        len(partes) != 2
        or partes[0].lower() != "bearer"
    ):
        raise HTTPException(
            status_code=401,
            detail="Credencial de sesión inválida",
        )

    token = partes[1]

    secret = os.getenv("JWT_SECRET")
    algorithm = os.getenv(
        "JWT_ALGORITHM",
        "HS256",
    )

    if not secret:
        raise HTTPException(
            status_code=500,
            detail="JWT_SECRET no está configurado",
        )

    try:

        payload = jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
        )

        usuario_id = payload.get("sub")

        if not usuario_id:
            raise HTTPException(
                status_code=401,
                detail="Credencial de sesión inválida",
            )

        return int(usuario_id)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Tu sesión ha expirado",
        )

    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
    ):
        raise HTTPException(
            status_code=401,
            detail="Credencial de sesión inválida",
        )


def obtener_admin_desde_token(
    authorization: str | None,
) -> int:
    usuario_id = obtener_usuario_desde_token(
        authorization
    )

    respuesta = (
        supabase.table("usuarios")
        .select("id,rol")
        .eq("id", usuario_id)
        .limit(1)
        .execute()
    )

    if not respuesta.data:
        raise HTTPException(
            status_code=401,
            detail="Usuario no encontrado",
        )

    usuario = respuesta.data[0]

    if str(
        usuario.get("rol", "")
    ).lower() != "admin":
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos de administrador",
        )

    return usuario_id

@router.post("/crear")
def crear_orden(
    orden: OrdenCrear,
    authorization: str | None = Header(
        default=None
    ),
):
    usuario_id = obtener_usuario_desde_token(
        authorization
    )

    try:
        ordenes = (
            supabase.table("ordenes")
            .select("*")
            .eq("usuario_id", usuario_id)
            .eq("producto", orden.producto)
            .eq("estado", "pendiente")
            .order("creado_en", desc=True)
            .limit(1)
            .execute()
        )

        if ordenes.data:
            orden_existente = ordenes.data[0]

            creado = datetime.fromisoformat(
                orden_existente["creado_en"].replace(
                    "Z",
                    "+00:00",
                )
            )

            ahora = datetime.now(
                creado.tzinfo
            )

            if ahora - creado < timedelta(minutes=30):
                return {
                    "ok": True,
                    "mensaje": (
                        "Orden pendiente reutilizada"
                    ),
                    "reutilizada": True,
                    "orden": orden_existente,
                }

            (
                supabase.table("ordenes")
                .update({"estado": "expirada"})
                .eq("id", orden_existente["id"])
                .execute()
            )

        fecha = datetime.now(
            timezone.utc
        ).strftime("%Y%m%d%H%M%S")

        numero_orden = (
            f"MC-{fecha}-{usuario_id}"
        )

        datos = {
            "numero_orden": numero_orden,
            "usuario_id": usuario_id,
            "producto": orden.producto,
            "tipo": orden.tipo,
            "valor": orden.valor,
            "metodo_pago": orden.metodo_pago,
            "estado": "pendiente",
            "beneficios_aplicados": False,
        }

        respuesta = (
            supabase.table("ordenes")
            .insert(datos)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=500,
                detail=(
                    "La orden no pudo ser registrada"
                ),
            )

        return {
            "ok": True,
            "mensaje": "Orden creada correctamente",
            "reutilizada": False,
            "orden": respuesta.data[0],
        }

    except HTTPException:
        raise

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


@router.get("/listar")
def listar_ordenes(
    authorization: str | None = Header(
        default=None
    ),
):
    obtener_admin_desde_token(
        authorization
    )

    try:

        respuesta_ordenes = (
            supabase.table("ordenes")
            .select("*")
            .order("creado_en", desc=True)
            .execute()
        )

        return {
            "ok": True,
            "total": len(
                respuesta_ordenes.data or []
            ),
            "ordenes": (
                respuesta_ordenes.data or []
            ),
        }

    except HTTPException:
        raise

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


@router.post("/{orden_id}/aprobar")
def aprobar_orden(
    orden_id: int,
    authorization: str | None = Header(
        default=None
    ),
):
    obtener_admin_desde_token(
        authorization
    )

    try:

        orden = obtener_orden(
            orden_id
        )

        estado_actual = str(
            orden.get("estado", "")
        ).lower()

        beneficios_aplicados = bool(
            orden.get("beneficios_aplicados", False)
        )

        if beneficios_aplicados:
            return {
                "ok": True,
                "mensaje": (
                    "La orden ya fue aprobada y sus "
                    "beneficios ya fueron aplicados"
                ),
                "orden": orden,
            }

        if estado_actual == "cancelada":
            raise HTTPException(
                status_code=400,
                detail=(
                    "No se puede aprobar una "
                    "orden cancelada"
                ),
            )

        if estado_actual == "expirada":
            raise HTTPException(
                status_code=400,
                detail=(
                    "No se puede aprobar una "
                    "orden expirada"
                ),
            )

        if estado_actual not in {
            "pendiente",
            "pagada",
            "aprobada",
        }:
            raise HTTPException(
                status_code=400,
                detail=(
                    "El estado actual de la orden "
                    "no permite aprobarla"
                ),
            )

        usuario_id = orden.get(
            "usuario_id"
        )

        if usuario_id is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "La orden no tiene un usuario "
                    "asociado"
                ),
            )

        usuario = obtener_usuario(
            int(usuario_id)
        )

        datos_usuario, mensaje_beneficio = (
            calcular_actualizacion_usuario(
                orden,
                usuario,
            )
        )

        ahora = datetime.now(
            timezone.utc
        ).isoformat()

        estado_anterior = str(
            orden.get("estado", "pendiente")
        )

        pagado_en_anterior = orden.get(
            "pagado_en"
        )

        respuesta_marcado = (
            supabase.table("ordenes")
            .update(
                {
                    "estado": "pagada",
                    "pagado_en": (
                        pagado_en_anterior or ahora
                    ),
                    "beneficios_aplicados": True,
                }
            )
            .eq("id", orden_id)
            .eq("beneficios_aplicados", False)
            .execute()
        )

        if not respuesta_marcado.data:
            orden_actualizada = obtener_orden(
                orden_id
            )

            if orden_actualizada.get(
                "beneficios_aplicados"
            ):
                return {
                    "ok": True,
                    "mensaje": (
                        "La orden ya fue procesada "
                        "anteriormente"
                    ),
                    "orden": orden_actualizada,
                }

            raise HTTPException(
                status_code=409,
                detail=(
                    "La orden está siendo procesada "
                    "o ya fue modificada"
                ),
            )

        try:
            respuesta_usuario = (
                supabase.table("usuarios")
                .update(datos_usuario)
                .eq("id", int(usuario_id))
                .execute()
            )

            if not respuesta_usuario.data:
                revertir_marcado_orden(
                    orden_id,
                    estado_anterior,
                    pagado_en_anterior,
                )

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "No fue posible actualizar "
                        "los beneficios del usuario"
                    ),
                )

        except Exception:
            revertir_marcado_orden(
                orden_id,
                estado_anterior,
                pagado_en_anterior,
            )
            raise

        orden_actualizada = obtener_orden(
            orden_id
        )

        return {
            "ok": True,
            "mensaje": (
                "Orden aprobada correctamente. "
                f"{mensaje_beneficio}"
            ),
            "orden": orden_actualizada,
            "usuario": respuesta_usuario.data[0],
        }

    except HTTPException:
        raise

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


@router.post("/{orden_id}/cancelar")
def cancelar_orden(
    orden_id: int,
    authorization: str | None = Header(
        default=None
    ),
):
    obtener_admin_desde_token(
        authorization
    )

    try:

        orden = obtener_orden(
            orden_id
        )

        estado_actual = str(
            orden.get("estado", "")
        ).lower()

        beneficios_aplicados = bool(
            orden.get("beneficios_aplicados", False)
        )

        if estado_actual == "cancelada":
            return {
                "ok": True,
                "mensaje": (
                    "La orden ya se encuentra "
                    "cancelada"
                ),
                "orden": orden,
            }

        if beneficios_aplicados:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No se puede cancelar una orden "
                    "cuyos beneficios ya fueron "
                    "aplicados"
                ),
            )

        if estado_actual in {
            "pagada",
            "aprobada",
        }:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No se puede cancelar una orden "
                    "que ya fue pagada"
                ),
            )

        if estado_actual == "expirada":
            raise HTTPException(
                status_code=400,
                detail=(
                    "La orden ya se encuentra "
                    "expirada"
                ),
            )

        respuesta = (
            supabase.table("ordenes")
            .update({"estado": "cancelada"})
            .eq("id", orden_id)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=500,
                detail=(
                    "No fue posible cancelar "
                    "la orden"
                ),
            )

        return {
            "ok": True,
            "mensaje": (
                "Orden cancelada correctamente"
            ),
            "orden": respuesta.data[0],
        }

    except HTTPException:
        raise

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
Biblioteca
/
ordenes_corregido.py


import calendar
from datetime import datetime, timedelta, timezone
from typing import Optional

import os
import jwt

from fastapi import (
    APIRouter,
    HTTPException,
    Header,
)
from postgrest.exceptions import APIError

from app.database.supabase import supabase
from app.schemas.orden import OrdenCrear


router = APIRouter(prefix="/ordenes", tags=["Órdenes"])


PLANES_MEMBRESIA = {
    "Plan Mensual": {
        "meses": 1,
        "tickets": 1,
    },
    "Plan Trimestral": {
        "meses": 3,
        "tickets": 3,
    },
    "Plan Semestral": {
        "meses": 6,
        "tickets": 6,
    },
    "Plan Anual": {
        "meses": 12,
        "tickets": 12,
    },
}


PAQUETES_TICKETS = {
    "Paquete de 10 Tickets": 10,
    "Paquete de 25 Tickets": 25,
    "Paquete de 50 Tickets": 50,
    "Paquete de 100 Tickets": 100,
}


def obtener_orden(orden_id: int) -> dict:
    respuesta_orden = (
        supabase.table("ordenes")
        .select("*")
        .eq("id", orden_id)
        .limit(1)
        .execute()
    )

    if not respuesta_orden.data:
        raise HTTPException(
            status_code=404,
            detail="Orden no encontrada",
        )

    return respuesta_orden.data[0]


def obtener_usuario(usuario_id: int) -> dict:
    respuesta_usuario = (
        supabase.table("usuarios")
        .select(
            "id,plan,estado_plan,vence_plan,tickets"
        )
        .eq("id", usuario_id)
        .limit(1)
        .execute()
    )

    if not respuesta_usuario.data:
        raise HTTPException(
            status_code=404,
            detail="Usuario asociado a la orden no encontrado",
        )

    return respuesta_usuario.data[0]


def convertir_fecha(
    valor: Optional[str],
) -> Optional[datetime]:
    if not valor:
        return None

    try:
        fecha = datetime.fromisoformat(
            str(valor).replace("Z", "+00:00")
        )

        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)

        return fecha

    except (TypeError, ValueError):
        return None


def sumar_meses(
    fecha: datetime,
    cantidad_meses: int,
) -> datetime:
    mes_total = (
        fecha.month - 1 + cantidad_meses
    )

    nuevo_anio = (
        fecha.year + mes_total // 12
    )

    nuevo_mes = (
        mes_total % 12 + 1
    )

    ultimo_dia_mes = calendar.monthrange(
        nuevo_anio,
        nuevo_mes,
    )[1]

    nuevo_dia = min(
        fecha.day,
        ultimo_dia_mes,
    )

    return fecha.replace(
        year=nuevo_anio,
        month=nuevo_mes,
        day=nuevo_dia,
    )


def calcular_actualizacion_usuario(
    orden: dict,
    usuario: dict,
) -> tuple[dict, str]:
    producto = str(
        orden.get("producto", "")
    ).strip()

    tipo = str(
        orden.get("tipo", "")
    ).strip().lower()

    tickets_actuales = int(
        usuario.get("tickets") or 0
    )

    ahora = datetime.now(timezone.utc)

    if tipo == "membresia":
        configuracion = PLANES_MEMBRESIA.get(
            producto
        )

        if not configuracion:
            raise HTTPException(
                status_code=400,
                detail=(
                    "El producto de membresía no está "
                    f"configurado: {producto}"
                ),
            )

        meses = int(
            configuracion["meses"]
        )

        tickets_nuevos = int(
            configuracion["tickets"]
        )

        vencimiento_actual = convertir_fecha(
            usuario.get("vence_plan")
        )

        estado_plan_actual = str(
            usuario.get("estado_plan", "")
        ).upper()

        if (
            vencimiento_actual
            and vencimiento_actual > ahora
            and estado_plan_actual == "ACTIVO"
        ):
            fecha_inicio = vencimiento_actual
        else:
            fecha_inicio = ahora

        nuevo_vencimiento = sumar_meses(
            fecha_inicio,
            meses,
        )

        datos_usuario = {
            "plan": producto,
            "estado_plan": "ACTIVO",
            "vence_plan": nuevo_vencimiento.isoformat(),
            "tickets": (
                tickets_actuales + tickets_nuevos
            ),
        }

        mensaje = (
            f"{producto} activado y "
            f"{tickets_nuevos} ticket(s) agregado(s)"
        )

        return datos_usuario, mensaje

    if tipo == "tickets":
        cantidad_tickets = PAQUETES_TICKETS.get(
            producto
        )

        if cantidad_tickets is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "El paquete de tickets no está "
                    f"configurado: {producto}"
                ),
            )

        datos_usuario = {
            "tickets": (
                tickets_actuales
                + int(cantidad_tickets)
            ),
        }

        mensaje = (
            f"{cantidad_tickets} tickets "
            "agregados correctamente"
        )

        return datos_usuario, mensaje

    raise HTTPException(
        status_code=400,
        detail=(
            "El tipo de orden no es válido. "
            "Debe ser membresia o tickets"
        ),
    )


def revertir_marcado_orden(
    orden_id: int,
    estado_anterior: str,
    pagado_en_anterior: Optional[str],
) -> None:
    try:
        (
            supabase.table("ordenes")
            .update(
                {
                    "estado": estado_anterior,
                    "pagado_en": pagado_en_anterior,
                    "beneficios_aplicados": False,
                }
            )
            .eq("id", orden_id)
            .execute()
        )

    except Exception:
        pass

def obtener_usuario_desde_token(
    authorization: str | None,
) -> int:

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Debes iniciar sesión",
        )

    partes = authorization.split()

    if (
        len(partes) != 2
        or partes[0].lower() != "bearer"
    ):
        raise HTTPException(
            status_code=401,
            detail="Credencial de sesión inválida",
        )

    token = partes[1]

    secret = os.getenv("JWT_SECRET")
    algorithm = os.getenv(
        "JWT_ALGORITHM",
        "HS256",
    )

    if not secret:
        raise HTTPException(
            status_code=500,
            detail="JWT_SECRET no está configurado",
        )

    try:

        payload = jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
        )

        usuario_id = payload.get("sub")

        if not usuario_id:
            raise HTTPException(
                status_code=401,
                detail="Credencial de sesión inválida",
            )

        return int(usuario_id)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Tu sesión ha expirado",
        )

    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
    ):
        raise HTTPException(
            status_code=401,
            detail="Credencial de sesión inválida",
        )


def obtener_admin_desde_token(
    authorization: str | None,
) -> int:
    usuario_id = obtener_usuario_desde_token(
        authorization
    )

    respuesta = (
        supabase.table("usuarios")
        .select("id,rol")
        .eq("id", usuario_id)
        .limit(1)
        .execute()
    )

    if not respuesta.data:
        raise HTTPException(
            status_code=401,
            detail="Usuario no encontrado",
        )

    usuario = respuesta.data[0]

    if str(
        usuario.get("rol", "")
    ).lower() != "admin":
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos de administrador",
        )

    return usuario_id

@router.post("/crear")
def crear_orden(
    orden: OrdenCrear,
    authorization: str | None = Header(
        default=None
    ),
):
    usuario_id = obtener_usuario_desde_token(
        authorization
    )

    try:
        ordenes = (
            supabase.table("ordenes")
            .select("*")
            .eq("usuario_id", usuario_id)
            .eq("producto", orden.producto)
            .eq("estado", "pendiente")
            .order("creado_en", desc=True)
            .limit(1)
            .execute()
        )

        if ordenes.data:
            orden_existente = ordenes.data[0]

            creado = datetime.fromisoformat(
                orden_existente["creado_en"].replace(
                    "Z",
                    "+00:00",
                )
            )

            ahora = datetime.now(
                creado.tzinfo
            )

            if ahora - creado < timedelta(minutes=30):
                return {
                    "ok": True,
                    "mensaje": (
                        "Orden pendiente reutilizada"
                    ),
                    "reutilizada": True,
                    "orden": orden_existente,
                }

            (
                supabase.table("ordenes")
                .update({"estado": "expirada"})
                .eq("id", orden_existente["id"])
                .execute()
            )

        fecha = datetime.now(
            timezone.utc
        ).strftime("%Y%m%d%H%M%S")

        numero_orden = (
            f"MC-{fecha}-{usuario_id}"
        )

        datos = {
            "numero_orden": numero_orden,
            "usuario_id": usuario_id,
            "producto": orden.producto,
            "tipo": orden.tipo,
            "valor": orden.valor,
            "metodo_pago": orden.metodo_pago,
            "estado": "pendiente",
            "beneficios_aplicados": False,
        }

        respuesta = (
            supabase.table("ordenes")
            .insert(datos)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=500,
                detail=(
                    "La orden no pudo ser registrada"
                ),
            )

        return {
            "ok": True,
            "mensaje": "Orden creada correctamente",
            "reutilizada": False,
            "orden": respuesta.data[0],
        }

    except HTTPException:
        raise

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


@router.get("/listar")
def listar_ordenes(
    authorization: str | None = Header(
        default=None
    ),
):
    obtener_admin_desde_token(
        authorization
    )

    try:

        respuesta_ordenes = (
            supabase.table("ordenes")
            .select("*")
            .order("creado_en", desc=True)
            .execute()
        )

        return {
            "ok": True,
            "total": len(
                respuesta_ordenes.data or []
            ),
            "ordenes": (
                respuesta_ordenes.data or []
            ),
        }

    except HTTPException:
        raise

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


@router.post("/{orden_id}/aprobar")
def aprobar_orden(
    orden_id: int,
    authorization: str | None = Header(
        default=None
    ),
):
    obtener_admin_desde_token(
        authorization
    )

    try:

        orden = obtener_orden(
            orden_id
        )

        estado_actual = str(
            orden.get("estado", "")
        ).lower()

        beneficios_aplicados = bool(
            orden.get("beneficios_aplicados", False)
        )

        if beneficios_aplicados:
            return {
                "ok": True,
                "mensaje": (
                    "La orden ya fue aprobada y sus "
                    "beneficios ya fueron aplicados"
                ),
                "orden": orden,
            }

        if estado_actual == "cancelada":
            raise HTTPException(
                status_code=400,
                detail=(
                    "No se puede aprobar una "
                    "orden cancelada"
                ),
            )

        if estado_actual == "expirada":
            raise HTTPException(
                status_code=400,
                detail=(
                    "No se puede aprobar una "
                    "orden expirada"
                ),
            )

        if estado_actual not in {
            "pendiente",
            "pagada",
            "aprobada",
        }:
            raise HTTPException(
                status_code=400,
                detail=(
                    "El estado actual de la orden "
                    "no permite aprobarla"
                ),
            )

        usuario_id = orden.get(
            "usuario_id"
        )

        if usuario_id is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "La orden no tiene un usuario "
                    "asociado"
                ),
            )

        usuario = obtener_usuario(
            int(usuario_id)
        )

        datos_usuario, mensaje_beneficio = (
            calcular_actualizacion_usuario(
                orden,
                usuario,
            )
        )

        ahora = datetime.now(
            timezone.utc
        ).isoformat()

        estado_anterior = str(
            orden.get("estado", "pendiente")
        )

        pagado_en_anterior = orden.get(
            "pagado_en"
        )

        respuesta_marcado = (
            supabase.table("ordenes")
            .update(
                {
                    "estado": "pagada",
                    "pagado_en": (
                        pagado_en_anterior or ahora
                    ),
                    "beneficios_aplicados": True,
                }
            )
            .eq("id", orden_id)
            .eq("beneficios_aplicados", False)
            .execute()
        )

        if not respuesta_marcado.data:
            orden_actualizada = obtener_orden(
                orden_id
            )

            if orden_actualizada.get(
                "beneficios_aplicados"
            ):
                return {
                    "ok": True,
                    "mensaje": (
                        "La orden ya fue procesada "
                        "anteriormente"
                    ),
                    "orden": orden_actualizada,
                }

            raise HTTPException(
                status_code=409,
                detail=(
                    "La orden está siendo procesada "
                    "o ya fue modificada"
                ),
            )

        try:
            respuesta_usuario = (
                supabase.table("usuarios")
                .update(datos_usuario)
                .eq("id", int(usuario_id))
                .execute()
            )

            if not respuesta_usuario.data:
                revertir_marcado_orden(
                    orden_id,
                    estado_anterior,
                    pagado_en_anterior,
                )

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "No fue posible actualizar "
                        "los beneficios del usuario"
                    ),
                )

        except Exception:
            revertir_marcado_orden(
                orden_id,
                estado_anterior,
                pagado_en_anterior,
            )
            raise

        orden_actualizada = obtener_orden(
            orden_id
        )

        return {
            "ok": True,
            "mensaje": (
                "Orden aprobada correctamente. "
                f"{mensaje_beneficio}"
            ),
            "orden": orden_actualizada,
            "usuario": respuesta_usuario.data[0],
        }

    except HTTPException:
        raise

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


@router.post("/{orden_id}/cancelar")
def cancelar_orden(
    orden_id: int,
    authorization: str | None = Header(
        default=None
    ),
):
    obtener_admin_desde_token(
        authorization
    )

    try:

        orden = obtener_orden(
            orden_id
        )

        estado_actual = str(
            orden.get("estado", "")
        ).lower()

        beneficios_aplicados = bool(
            orden.get("beneficios_aplicados", False)
        )

        if estado_actual == "cancelada":
            return {
                "ok": True,
                "mensaje": (
                    "La orden ya se encuentra "
                    "cancelada"
                ),
                "orden": orden,
            }

        if beneficios_aplicados:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No se puede cancelar una orden "
                    "cuyos beneficios ya fueron "
                    "aplicados"
                ),
            )

        if estado_actual in {
            "pagada",
            "aprobada",
        }:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No se puede cancelar una orden "
                    "que ya fue pagada"
                ),
            )

        if estado_actual == "expirada":
            raise HTTPException(
                status_code=400,
                detail=(
                    "La orden ya se encuentra "
                    "expirada"
                ),
            )

        respuesta = (
            supabase.table("ordenes")
            .update({"estado": "cancelada"})
            .eq("id", orden_id)
            .execute()
        )

        if not respuesta.data:
            raise HTTPException(
                status_code=500,
                detail=(
                    "No fue posible cancelar "
                    "la orden"
                ),
            )

        return {
            "ok": True,
            "mensaje": (
                "Orden cancelada correctamente"
            ),
            "orden": respuesta.data[0],
        }

    except HTTPException:
        raise

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
