import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, LoginResponse
from app.config import LOGIN_MAX_INTENTOS, LOGIN_VENTANA_SEGUNDOS
from app.rate_limit import LoginRateLimiter
from app.security import crear_token, obtener_usuario_actual

log = logging.getLogger("sitral.security")

# Guía 8 - OWASP API4: bloqueo temporal tras varios intentos fallidos
limitador_login = LoginRateLimiter(LOGIN_MAX_INTENTOS, LOGIN_VENTANA_SEGUNDOS)


router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"]
)


password_hash = PasswordHash.recommended()

# Hash ficticio: si el usuario no existe se verifica igual, para que el tiempo de
# respuesta no revele qué usuarios existen (OWASP API2)
_HASH_FICTICIO = password_hash.hash("usuario-inexistente-sitral")


@router.post(
    "/login",
    response_model=LoginResponse
)
def login(
    datos: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):

    ip = request.client.host if request.client else "desconocida"
    clave_limite = f"{ip}:{datos.usuario.lower()}"

    if limitador_login.bloqueado(clave_limite):

        log.warning("Login bloqueado por exceso de intentos ip=%s", ip)

        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos fallidos. Espera unos minutos e intenta de nuevo."
        )

    usuario = db.query(Usuario).filter(
        Usuario.usuario == datos.usuario
    ).first()

    hash_guardado = usuario.password if usuario else _HASH_FICTICIO

    try:
        password_valido = password_hash.verify(datos.password, hash_guardado)
    except Exception:
        password_valido = False  # hash mal formado en la base de datos

    if not usuario or not password_valido:

        limitador_login.registrar_fallo(clave_limite)
        log.warning("Login fallido ip=%s", ip)  # nunca se registra la contraseña

        raise HTTPException(
            status_code=401,
            detail="Usuario o contraseña incorrectos"
        )

    limitador_login.reiniciar(clave_limite)


    if usuario.estado != "ACTIVO":

        raise HTTPException(
            status_code=403,
            detail="El usuario está inactivo"
        )


    token = crear_token({

        "sub": str(usuario.id_usuario),

        "usuario": usuario.usuario,

        "rol": usuario.rol.nombre

    })


    return {

        "success": True,

        "message": "Inicio de sesión exitoso",

        "id_usuario": usuario.id_usuario,

        "usuario": usuario.usuario,

        "nombre": usuario.nombre,

        "rol": usuario.rol.nombre,

        "access_token": token,

        "token_type": "bearer"
    }


@router.get("/me")
def obtener_perfil(
    usuario_actual: dict = Depends(obtener_usuario_actual)
):

    return {

        "success": True,

        "message": "Token válido",

        "usuario": usuario_actual

    }