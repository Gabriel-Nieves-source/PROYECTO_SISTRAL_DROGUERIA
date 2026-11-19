"""Configuración de pruebas: base SQLite en memoria (no requiere MySQL)."""
import os

if len(os.environ.get("SITRAL_JWT_SECRET", "")) < 32:
    os.environ["SITRAL_JWT_SECRET"] = "clave-solo-para-pruebas-0123456789abcdef"
os.environ["SITRAL_DATABASE_URL"] = "sqlite://"
os.environ["SITRAL_DEBUG"] = "false"

from datetime import date, timedelta  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from pwdlib import PasswordHash  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.models  # noqa: E402,F401  (registra todos los modelos)
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    ConfiguracionAlerta, Lote, Medicamento, Proveedor, Rol, Usuario,
)
from app.routers.auth import limitador_login  # noqa: E402

ADMIN = ("admin", "Admin#2026seguro")
FARMACEUTA = ("farmaceuta", "Farm#2026seguro")
_hasher = PasswordHash.recommended()


@pytest.fixture()
def sesion():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with engine.begin() as con:  # equivalente en SQLite de la vista MySQL del script SITRAL.sql
        con.execute(text("""
            CREATE VIEW vista_dashboard AS SELECT
              (SELECT COUNT(*) FROM medicamento WHERE estado = 'ACTIVO') AS total_medicamentos,
              (SELECT COALESCE(SUM(cantidad_disponible), 0) FROM lote WHERE estado <> 'VENCIDO') AS unidades_disponibles,
              (SELECT COUNT(*) FROM lote l CROSS JOIN configuracion_alerta ca WHERE ca.estado = 'ACTIVA'
                 AND julianday(l.fecha_vencimiento) - julianday('now') BETWEEN 0 AND ca.dias_anticipacion) AS lotes_proximos_vencer,
              (SELECT COUNT(*) FROM lote WHERE fecha_vencimiento < date('now')) AS lotes_vencidos,
              (SELECT COUNT(*) FROM proveedor WHERE estado = 'ACTIVO') AS proveedores_activos
        """))
    Sesion = sessionmaker(bind=engine, autoflush=False)
    with Sesion() as db:
        db.add_all([Rol(id_rol=1, nombre="ADMINISTRADOR"), Rol(id_rol=2, nombre="FARMACEUTA")])
        db.add_all([
            Usuario(id_usuario=1, id_rol=1, nombre="Admin", usuario=ADMIN[0], password=_hasher.hash(ADMIN[1])),
            Usuario(id_usuario=2, id_rol=2, nombre="Carlos", usuario=FARMACEUTA[0], password=_hasher.hash(FARMACEUTA[1])),
            Usuario(id_usuario=3, id_rol=2, nombre="Inactivo", usuario="inactivo",
                    password=_hasher.hash("Inactivo#2026"), estado="INACTIVO"),
        ])
        db.add(ConfiguracionAlerta(dias_anticipacion=30))
        db.add(Proveedor(id_proveedor=1, nombre="Distribuidora Andina", nit="900123456"))
        db.add(Medicamento(id_medicamento=1, nombre="Acetaminofén 500 mg", codigo_barras="7702001023455", precio=1500))
        hoy = date.today()
        db.add_all([
            Lote(id_lote=1, id_medicamento=1, id_proveedor=1, numero_lote="LOT-VIG", cantidad_inicial=50,
                 cantidad_disponible=50, fecha_ingreso=hoy, fecha_vencimiento=hoy + timedelta(days=200), estado="VIGENTE"),
            Lote(id_lote=2, id_medicamento=1, id_proveedor=1, numero_lote="LOT-PROX", cantidad_inicial=10,
                 cantidad_disponible=10, fecha_ingreso=hoy, fecha_vencimiento=hoy + timedelta(days=10), estado="VIGENTE"),
            Lote(id_lote=3, id_medicamento=1, id_proveedor=1, numero_lote="LOT-VENC", cantidad_inicial=5,
                 cantidad_disponible=5, fecha_ingreso=hoy - timedelta(days=400), fecha_vencimiento=hoy - timedelta(days=1),
                 estado="VIGENTE"),
        ])
        db.commit()
    yield Sesion
    engine.dispose()


@pytest.fixture()
def client(sesion):
    def _get_db():
        with sesion() as db:
            yield db

    app.dependency_overrides[get_db] = _get_db
    limitador_login._fallos.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def token_de(client, usuario, password):
    r = client.post("/auth/login", json={"usuario": usuario, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}
