"""Configuración de SITRAL leída desde variables de entorno (archivo backend/.env).

Guía 8 - OWASP API8:2023 (Security Misconfiguration): antes la clave JWT y la
contraseña de MySQL estaban escritas en el código fuente. Ahora se leen del
entorno y el archivo .env NO se sube al repositorio.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _bool(nombre: str, defecto: bool) -> bool:
    return os.getenv(nombre, str(defecto)).strip().lower() in {"1", "true", "si", "yes"}


def _lista(nombre: str, defecto: str) -> list[str]:
    return [x.strip() for x in os.getenv(nombre, defecto).split(",") if x.strip()]


JWT_SECRET = os.getenv("SITRAL_JWT_SECRET", "")
if len(JWT_SECRET) < 32:
    raise RuntimeError(
        "Falta SITRAL_JWT_SECRET (mínimo 32 caracteres) en backend/.env. "
        "Copie backend/.env.example como backend/.env y genere una clave con: "
        "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
    )

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("SITRAL_JWT_EXPIRE_MINUTES", "60"))
JWT_ISSUER = "sitral-api"
JWT_AUDIENCE = "sitral-web"

DATABASE_URL = os.getenv("SITRAL_DATABASE_URL", "")
if not DATABASE_URL:
    # SonarCloud (regla de seguridad, Bloqueador): antes había un valor por defecto
    # con MySQL sin contraseña. Ahora la conexión debe configurarse explícitamente.
    raise RuntimeError(
        "Falta SITRAL_DATABASE_URL en backend/.env "
        "(ejemplo: mysql+pymysql://usuario:contraseña@localhost/SITRAL)"
    )
SQL_ECHO = _bool("SITRAL_SQL_ECHO", False)

CORS_ORIGINS = _lista("SITRAL_CORS_ORIGINS", "http://127.0.0.1:5500,http://localhost:5500")
DEBUG = _bool("SITRAL_DEBUG", True)

LOGIN_MAX_INTENTOS = int(os.getenv("SITRAL_LOGIN_MAX_INTENTOS", "5"))
LOGIN_VENTANA_SEGUNDOS = int(os.getenv("SITRAL_LOGIN_VENTANA_SEGUNDOS", "300"))
