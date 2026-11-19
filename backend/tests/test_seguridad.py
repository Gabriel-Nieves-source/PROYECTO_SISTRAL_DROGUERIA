"""Pruebas de JWT, RBAC y controles OWASP sobre la API real de SITRAL."""
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app import config
from app.security import crear_token, decodificar_token
from tests.conftest import ADMIN, FARMACEUTA, auth, token_de


# ---------- Login ----------
def test_login_admin_ok(client):
    r = client.post("/auth/login", json={"usuario": ADMIN[0], "password": ADMIN[1]})
    assert r.status_code == 200
    body = r.json()
    assert body["rol"] == "ADMINISTRADOR" and body["token_type"] == "bearer"
    claims = decodificar_token(body["access_token"])
    assert claims["sub"] == "1" and claims["iss"] == "sitral-api" and claims["aud"] == "sitral-web"


def test_login_password_incorrecta(client):
    r = client.post("/auth/login", json={"usuario": ADMIN[0], "password": "incorrecta"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Usuario o contraseña incorrectos"


def test_login_usuario_inexistente_mismo_mensaje(client):
    r = client.post("/auth/login", json={"usuario": "nadie", "password": "loquesea"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Usuario o contraseña incorrectos"


def test_login_usuario_inactivo(client):
    r = client.post("/auth/login", json={"usuario": "inactivo", "password": "Inactivo#2026"})
    assert r.status_code == 403


def test_login_rechaza_campo_rol_extra(client):
    r = client.post("/auth/login", json={"usuario": FARMACEUTA[0], "password": FARMACEUTA[1], "rol": "ADMINISTRADOR"})
    assert r.status_code == 422


def test_login_rechaza_campos_muy_largos(client):
    r = client.post("/auth/login", json={"usuario": "a" * 51, "password": "x"})
    assert r.status_code == 422


def test_login_bloqueo_por_intentos(client):
    for _ in range(config.LOGIN_MAX_INTENTOS):
        assert client.post("/auth/login", json={"usuario": ADMIN[0], "password": "mala"}).status_code == 401
    r = client.post("/auth/login", json={"usuario": ADMIN[0], "password": ADMIN[1]})
    assert r.status_code == 429


def test_login_exitoso_reinicia_contador(client):
    for _ in range(config.LOGIN_MAX_INTENTOS - 1):
        client.post("/auth/login", json={"usuario": ADMIN[0], "password": "mala"})
    assert client.post("/auth/login", json={"usuario": ADMIN[0], "password": ADMIN[1]}).status_code == 200
    assert client.post("/auth/login", json={"usuario": ADMIN[0], "password": "mala"}).status_code == 401
    assert client.post("/auth/login", json={"usuario": ADMIN[0], "password": ADMIN[1]}).status_code == 200


# ---------- RBAC ----------
def test_admin_accede_a_dashboard(client):
    assert client.get("/dashboard/kpis", headers=auth(token_de(client, *ADMIN))).status_code == 200


def test_farmaceuta_no_accede_a_dashboard(client):
    r = client.get("/dashboard/kpis", headers=auth(token_de(client, *FARMACEUTA)))
    assert r.status_code == 403
    assert r.json()["detail"] == "Tu rol no tiene permiso para realizar esta acción"


def test_farmaceuta_no_gestiona_usuarios(client):
    assert client.get("/usuarios/", headers=auth(token_de(client, *FARMACEUTA))).status_code == 403


def test_admin_lista_usuarios_sin_password(client):
    r = client.get("/usuarios/", headers=auth(token_de(client, *ADMIN)))
    assert r.status_code == 200
    assert all("password" not in u for u in r.json())


def test_farmaceuta_consulta_lotes(client):
    r = client.get("/lotes/", headers=auth(token_de(client, *FARMACEUTA)))
    assert r.status_code == 200 and len(r.json()) == 3


def test_perfil_me(client):
    r = client.get("/auth/me", headers=auth(token_de(client, *FARMACEUTA)))
    assert r.status_code == 200
    assert r.json()["usuario"] == {"sub": "2", "usuario": "farmaceuta", "rol": "FARMACEUTA"}


def test_sin_token_401(client):
    r = client.get("/lotes/")
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"


def test_crear_usuario_exige_password_de_8(client):
    r = client.post("/usuarios/", headers=auth(token_de(client, *ADMIN)),
                    json={"id_rol": 2, "nombre": "Ana", "usuario": "ana", "password": "corta"})
    assert r.status_code == 422


# ---------- Tokens manipulados ----------
def test_token_alterado(client):
    t = token_de(client, *FARMACEUTA)
    assert client.get("/lotes/", headers=auth(t[:-3] + "abc")).status_code == 401


def test_token_expirado(client):
    t = crear_token({"sub": "1"}, ahora=datetime.now(timezone.utc) - timedelta(hours=3))
    r = client.get("/lotes/", headers=auth(t))
    assert r.status_code == 401 and r.json()["detail"] == "El token ha expirado"


def test_token_alg_none(client):
    t = jwt.encode({"sub": "1", "rol": "ADMINISTRADOR"}, key=None, algorithm="none")
    assert client.get("/dashboard/kpis", headers=auth(t)).status_code == 401


def test_token_firmado_con_otra_clave(client):
    ahora = datetime.now(timezone.utc)
    falso = jwt.encode({"sub": "1", "iat": ahora, "exp": ahora + timedelta(minutes=5),
                        "iss": "sitral-api", "aud": "sitral-web"},
                       "clave-del-atacante-0123456789abcdef", algorithm="HS256")
    assert client.get("/dashboard/kpis", headers=auth(falso)).status_code == 401


def test_token_sin_audiencia_correcta(client):
    ahora = datetime.now(timezone.utc)
    t = jwt.encode({"sub": "1", "iat": ahora, "exp": ahora + timedelta(minutes=5),
                    "iss": "sitral-api", "aud": "otra-app"}, config.JWT_SECRET, algorithm="HS256")
    assert client.get("/dashboard/kpis", headers=auth(t)).status_code == 401


def test_rol_falso_en_token_no_da_privilegios(client):
    # Token válido del farmaceuta (id 2) que dice ser ADMINISTRADOR: el rol se lee de la BD
    t = crear_token({"sub": "2", "rol": "ADMINISTRADOR"})
    assert client.get("/dashboard/kpis", headers=auth(t)).status_code == 403


def test_usuario_desactivado_pierde_acceso(client):
    t = crear_token({"sub": "3"})  # usuario inactivo
    assert client.get("/lotes/", headers=auth(t)).status_code == 401


@pytest.mark.parametrize("sub", ["abc", "999"])
def test_sub_invalido_o_inexistente(client, sub):
    assert client.get("/lotes/", headers=auth(crear_token({"sub": sub}))).status_code == 401


# ---------- Configuración segura ----------
def test_cabeceras_de_seguridad(client):
    r = client.get("/")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "max-age" in r.headers["strict-transport-security"]


def test_cors_solo_origenes_permitidos(client):
    ok = client.options("/lotes/", headers={"Origin": "http://127.0.0.1:5500", "Access-Control-Request-Method": "GET"})
    malo = client.options("/lotes/", headers={"Origin": "https://sitio-malicioso.com", "Access-Control-Request-Method": "GET"})
    assert ok.headers.get("access-control-allow-origin") == "http://127.0.0.1:5500"
    assert "access-control-allow-origin" not in malo.headers


def test_docs_deshabilitado_en_produccion(client):
    assert client.get("/docs").status_code == 404


def test_health_no_expone_detalle(client):
    r = client.get("/health")
    assert "detail" not in r.json()


def test_secreto_corto_es_rechazado(monkeypatch):
    import importlib
    monkeypatch.setenv("SITRAL_JWT_SECRET", "corta")
    with pytest.raises(RuntimeError, match="SITRAL_JWT_SECRET"):
        importlib.reload(config)
    monkeypatch.undo()
    importlib.reload(config)
