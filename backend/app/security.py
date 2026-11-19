"""Autenticación JWT y autorización por roles (RBAC) de SITRAL.

Cambios de la Guía 8 (OWASP API Security Top 10 2023):
- API2: la clave sale del entorno; el token lleva iss, aud e iat y se exigen al
  decodificarlo; el algoritmo está fijo (se rechaza "alg: none").
- API5: el rol y el estado se leen de la base de datos en cada petición, no del
  token. Si un administrador es degradado o desactivado, pierde acceso de inmediato.
"""
import logging
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import JWT_ALGORITHM, JWT_AUDIENCE, JWT_EXPIRE_MINUTES, JWT_ISSUER, JWT_SECRET
from app.database import get_db
from app.models.usuario import Usuario

log = logging.getLogger("sitral.security")

security = HTTPBearer(auto_error=False)

ROL_ADMIN = "ADMINISTRADOR"
ROL_FARMACEUTA = "FARMACEUTA"


def crear_token(data: dict, ahora: datetime | None = None) -> str:

    emitido = ahora or datetime.now(timezone.utc)

    datos = data.copy()
    datos.update({
        "iat": emitido,
        "exp": emitido + timedelta(minutes=JWT_EXPIRE_MINUTES),
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
    })

    return jwt.encode(datos, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decodificar_token(token: str) -> dict:

    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
        issuer=JWT_ISSUER,
        audience=JWT_AUDIENCE,
        options={"require": ["exp", "iat", "sub", "iss", "aud"]},
    )


def obtener_usuario_actual(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db)
) -> dict:

    if credentials is None:

        raise HTTPException(
            status_code=401,
            detail="No se envió el token de acceso",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:

        datos = decodificar_token(credentials.credentials)

    except jwt.ExpiredSignatureError:

        raise HTTPException(
            status_code=401,
            detail="El token ha expirado",
            headers={"WWW-Authenticate": "Bearer"}
        ) from None

    except jwt.InvalidTokenError as error:

        log.warning("Token rechazado: %s", type(error).__name__)

        raise HTTPException(
            status_code=401,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"}
        ) from None

    try:
        id_usuario = int(datos["sub"])
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Token inválido") from None

    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()

    if usuario is None or usuario.estado != "ACTIVO":

        raise HTTPException(
            status_code=401,
            detail="El usuario no existe o está inactivo",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Se devuelve el mismo formato de siempre (los routers usan usuario_actual["sub"]),
    # pero el rol viene de la base de datos y no de lo que diga el token.
    return {
        "sub": str(usuario.id_usuario),
        "usuario": usuario.usuario,
        "rol": usuario.rol.nombre,
    }


def requiere_roles(*roles: str):

    permitidos = set(roles)

    def verificador(usuario_actual: dict = Depends(obtener_usuario_actual)) -> dict:

        if usuario_actual["rol"] not in permitidos:

            log.warning(
                "Acceso denegado: usuario=%s rol=%s",
                usuario_actual["usuario"], usuario_actual["rol"]
            )

            raise HTTPException(
                status_code=403,
                detail="Tu rol no tiene permiso para realizar esta acción"
            )

        return usuario_actual

    return verificador


# Se conserva el nombre que ya usan los routers
verificar_administrador = requiere_roles(ROL_ADMIN)
