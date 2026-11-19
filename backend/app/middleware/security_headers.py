"""Cabeceras de seguridad HTTP de la API (OWASP API8:2023)."""
from starlette.middleware.base import BaseHTTPMiddleware

CABECERAS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Cache-Control": "no-store",
}

# Swagger (/docs) carga JS y CSS desde jsDelivr y usa un script en línea
CSP_DOCS = (
    "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com; "
    "frame-ancestors 'none'"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):
        respuesta = await call_next(request)
        for nombre, valor in CABECERAS.items():
            respuesta.headers.setdefault(nombre, valor)
        if request.url.path.startswith("/docs"):
            respuesta.headers["Content-Security-Policy"] = CSP_DOCS
        if "server" in respuesta.headers:
            del respuesta.headers["server"]
        return respuesta
