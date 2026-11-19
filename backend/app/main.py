import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import CORS_ORIGINS, DEBUG
from app.middleware.security_headers import SecurityHeadersMiddleware

from app.database import engine
from app.routers import auth
from app.routers import usuarios
from app.routers import proveedores
from app.routers import medicamentos
from app.routers import lotes
from app.routers import facturas
from app.routers import alertas
from app.routers import dashboard


app = FastAPI(

    title="SITRAL API",

    description="Sistema de Trazabilidad y Control por Lotes para Droguerías",

    version="1.1.0",

    # Guía 8 - OWASP API9: Swagger y el esquema OpenAPI solo en modo desarrollo
    docs_url="/docs" if DEBUG else None,
    redoc_url=None,
    openapi_url="/openapi.json" if DEBUG else None
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)

app.add_middleware(SecurityHeadersMiddleware)

# Guía 8 - OWASP API8: antes allow_origins=["*"] con credenciales.
# Ahora solo los orígenes de SITRAL_CORS_ORIGINS (backend/.env). Para usarlo desde
# el celular agregue ahí http://TU_IP:5500.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


app.include_router(
    auth.router
)

app.include_router(
    usuarios.router
)

app.include_router(
    proveedores.router
)

app.include_router(
    medicamentos.router
)

app.include_router(
    lotes.router
)

app.include_router(
    facturas.router
)

app.include_router(
    alertas.router
)

app.include_router(
    dashboard.router
)


@app.get("/")
def inicio():

    return {

        "success": True,

        "message": "API SITRAL funcionando correctamente"

    }


@app.get("/health")
def health():

    try:

        with engine.connect() as connection:

            connection.execute(
                text("SELECT 1")
            )

        return {

            "success": True,

            "api": "OK",

            "database": "OK"

        }

    except Exception:

        # Guía 8: ya no se devuelve el detalle del error (exponía el host y el
        # usuario de MySQL); queda solo en el log del servidor.
        logging.getLogger("sitral").exception("Fallo de conexión a la base de datos")

        return {

            "success": False,

            "api": "OK",

            "database": "ERROR"

        }