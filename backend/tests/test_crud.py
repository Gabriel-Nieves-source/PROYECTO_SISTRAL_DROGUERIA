"""Pruebas de los módulos CRUD de SITRAL (medicamentos, proveedores, usuarios, lotes, facturas y alertas)."""
from datetime import date, timedelta

from tests.conftest import ADMIN, FARMACEUTA, auth, token_de


def _admin(client):
    return auth(token_de(client, *ADMIN))


def _farm(client):
    return auth(token_de(client, *FARMACEUTA))


# ---------- Medicamentos ----------
def test_medicamentos_flujo_completo(client):
    h = _admin(client)
    r = client.post("/medicamentos/", headers=h, json={"nombre": "Ibuprofeno 400 mg", "codigo_barras": "7700000000017", "precio": 2500})
    assert r.status_code == 201, r.text
    mid = r.json()["id_medicamento"]
    assert client.get(f"/medicamentos/{mid}", headers=h).json()["nombre"] == "Ibuprofeno 400 mg"
    assert client.get("/medicamentos/codigo/7700000000017", headers=h).status_code == 200
    assert client.put(f"/medicamentos/{mid}", headers=h, json={"precio": 3000}).status_code == 200
    assert len(client.get("/medicamentos/", headers=h).json()) >= 2
    assert client.delete(f"/medicamentos/{mid}", headers=h).status_code == 200


def test_medicamentos_errores(client):
    h = _admin(client)
    assert client.get("/medicamentos/999", headers=h).status_code == 404
    assert client.get("/medicamentos/codigo/000", headers=h).status_code == 404
    assert client.put("/medicamentos/999", headers=h, json={"precio": 1}).status_code == 404
    assert client.delete("/medicamentos/999", headers=h).status_code == 404
    dup = client.post("/medicamentos/", headers=h, json={"nombre": "Otro", "codigo_barras": "7702001023455", "precio": 1})
    assert dup.status_code == 400


def test_farmaceuta_no_edita_medicamentos(client):
    assert client.put("/medicamentos/1", headers=_farm(client), json={"precio": 1}).status_code == 403
    assert client.delete("/medicamentos/1", headers=_farm(client)).status_code == 403


# ---------- Proveedores ----------
def test_proveedores_flujo_completo(client):
    h = _admin(client)
    r = client.post("/proveedores/", headers=h, json={"nombre": "Drogas La Sabana", "nit": "800999111"})
    assert r.status_code == 201, r.text
    pid = r.json()["id_proveedor"]
    assert client.get(f"/proveedores/{pid}", headers=h).status_code == 200
    assert client.put(f"/proveedores/{pid}", headers=h, json={"telefono": "3001234567"}).status_code == 200
    assert len(client.get("/proveedores/", headers=h).json()) >= 2
    assert client.delete(f"/proveedores/{pid}", headers=h).status_code == 200


def test_proveedores_errores(client):
    h = _admin(client)
    assert client.get("/proveedores/999", headers=h).status_code == 404
    assert client.put("/proveedores/999", headers=h, json={"nombre": "x"}).status_code == 404
    assert client.delete("/proveedores/999", headers=h).status_code == 404
    assert client.post("/proveedores/", headers=h, json={"nombre": "Repetido", "nit": "900123456"}).status_code == 400


# ---------- Usuarios ----------
def test_usuarios_flujo_completo(client):
    h = _admin(client)
    r = client.post("/usuarios/", headers=h, json={"id_rol": 2, "nombre": "Ana", "usuario": "ana", "password": "AnaSegura#2026"})
    assert r.status_code == 201, r.text
    uid = r.json()["id_usuario"]
    assert "password" not in r.json()
    assert token_de(client, "ana", "AnaSegura#2026")
    assert client.get(f"/usuarios/{uid}", headers=h).status_code == 200
    assert client.put(f"/usuarios/{uid}", headers=h, json={"nombre": "Ana María", "password": "OtraClave#2026"}).status_code == 200
    assert client.patch(f"/usuarios/{uid}/estado", headers=h).status_code == 200
    assert client.post("/auth/login", json={"usuario": "ana", "password": "OtraClave#2026"}).status_code == 403
    assert client.delete(f"/usuarios/{uid}", headers=h).status_code in (200, 204)


def test_usuarios_errores(client):
    h = _admin(client)
    assert client.get("/usuarios/999", headers=h).status_code == 404
    assert client.put("/usuarios/999", headers=h, json={"nombre": "x"}).status_code == 404
    assert client.patch("/usuarios/999/estado", headers=h).status_code == 404
    assert client.delete("/usuarios/999", headers=h).status_code == 404
    dup = client.post("/usuarios/", headers=h, json={"id_rol": 2, "nombre": "X", "usuario": "admin", "password": "Duplicado#2026"})
    assert dup.status_code == 400


# ---------- Lotes ----------
def test_lotes_registro_y_consultas(client):
    h = _farm(client)
    hoy = date.today()
    r = client.post("/lotes/", headers=h, json={"id_medicamento": 1, "id_proveedor": 1, "numero_lote": "LOT-API-01",
                                                  "cantidad_inicial": 30, "fecha_ingreso": str(hoy),
                                                  "fecha_vencimiento": str(hoy + timedelta(days=90))})
    assert r.status_code == 201, r.text
    lid = r.json()["id_lote"]
    assert r.json()["cantidad_disponible"] == 30
    assert client.get(f"/lotes/{lid}/trazabilidad", headers=h).status_code == 200
    filtros = "?medicamento=Acetamin&numero_lote=LOT&id_proveedor=1&estado=vigente"
    assert client.get(f"/lotes/{filtros}", headers=h).status_code == 200


def test_lotes_errores(client):
    h = _farm(client)
    hoy = date.today()
    assert client.get("/lotes/999", headers=h).status_code == 404
    assert client.get("/lotes/999/trazabilidad", headers=h).status_code == 404
    malo = client.post("/lotes/", headers=h, json={"id_medicamento": 1, "id_proveedor": 1, "numero_lote": "LOT-MAL",
                                                     "cantidad_inicial": 5, "fecha_ingreso": str(hoy),
                                                     "fecha_vencimiento": str(hoy - timedelta(days=1))})
    assert malo.status_code == 400
    sin_med = client.post("/lotes/", headers=h, json={"id_medicamento": 999, "id_proveedor": 1, "numero_lote": "LOT-X",
                                                        "cantidad_inicial": 5, "fecha_ingreso": str(hoy),
                                                        "fecha_vencimiento": str(hoy + timedelta(days=10))})
    assert sin_med.status_code == 404


# ---------- Facturas ----------
def test_facturas_consulta_y_anulacion_de_venta(client):
    h = _admin(client)
    venta = client.post("/facturas/salida", headers=h,
                        json={"numero_factura": "V-200", "detalles": [{"id_lote": 1, "cantidad": 4}]})
    assert venta.status_code == 201
    fid = venta.json()["id_factura"]
    assert client.get("/facturas/", headers=h).status_code == 200
    assert client.get(f"/facturas/{fid}", headers=h).status_code == 200
    assert client.patch(f"/facturas/{fid}/anular", headers=h).status_code == 200
    assert client.get("/lotes/1", headers=h).json()["cantidad_disponible"] == 50
    assert client.patch(f"/facturas/{fid}/anular", headers=h).status_code == 400  # ya anulada


def test_facturas_errores(client):
    h = _admin(client)
    assert client.get("/facturas/999", headers=h).status_code == 404
    assert client.patch("/facturas/999/anular", headers=h).status_code == 404
    r = client.post("/facturas/salida", headers=h, json={"numero_factura": "V-300", "detalles": [{"id_lote": 999, "cantidad": 1}]})
    assert r.status_code == 404
    assert client.patch("/facturas/1/anular", headers=_farm(client)).status_code == 403


# ---------- Alertas ----------
def test_alertas_consulta_y_configuracion(client):
    h = _admin(client)
    client.post("/alertas/generar", headers=h)
    alertas = client.get("/alertas/", headers=h).json()
    assert {a["tipo"] for a in alertas} == {"VENCIDO", "PROXIMO_VENCER"}
    aid = alertas[0]["id_alerta"]
    assert client.patch(f"/alertas/{aid}/estado", headers=h).status_code in (200, 422)
    assert client.get("/alertas/configuracion", headers=h).json()["dias_anticipacion"] == 30
    assert client.put("/alertas/configuracion", headers=h, json={"dias_anticipacion": 60}).status_code == 200
    assert client.put("/alertas/configuracion", headers=_farm(client), json={"dias_anticipacion": 5}).status_code == 403
