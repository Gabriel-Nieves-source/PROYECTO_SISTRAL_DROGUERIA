"""Reglas de inventario: pruebas unitarias (frontera) y de integración con los routers."""
from datetime import date, timedelta

import pytest

from app.domain.inventario import (
    AGOTADO, PROXIMO_VENCER, VENCIDO, VIGENTE,
    clasificar_vencimiento, descontar_stock, dias_para_vencer, estado_tras_salida, vence_dentro_de,
)
from tests.conftest import ADMIN, FARMACEUTA, auth, token_de

HOY = date(2026, 11, 18)


def test_constantes():
    assert (VENCIDO, PROXIMO_VENCER, VIGENTE, AGOTADO) == ("VENCIDO", "PROXIMO_VENCER", "VIGENTE", "AGOTADO")


@pytest.mark.parametrize("dias", [-5, 0, 7])
def test_dias_para_vencer(dias):
    assert dias_para_vencer(HOY + timedelta(days=dias), HOY) == dias


@pytest.mark.parametrize("dias, esperado", [
    (-1, VENCIDO), (0, PROXIMO_VENCER), (1, PROXIMO_VENCER),
    (30, PROXIMO_VENCER), (31, VIGENTE), (365, VIGENTE),
])
def test_clasificar_vencimiento_fronteras(dias, esperado):
    assert clasificar_vencimiento(HOY + timedelta(days=dias), HOY, 30) == esperado


@pytest.mark.parametrize("dias, esperado", [(-1, False), (0, True), (15, True), (16, False)])
def test_vence_dentro_de(dias, esperado):
    assert vence_dentro_de(HOY + timedelta(days=dias), HOY, 15) is esperado


def test_descontar_stock():
    assert descontar_stock(10, 3) == 7
    assert descontar_stock(5, 5) == 0
    assert descontar_stock(5, 1) == 4


def test_descontar_mas_del_disponible():
    with pytest.raises(ValueError) as exc:
        descontar_stock(5, 6)
    assert str(exc.value) == "Inventario insuficiente: disponible 5, solicitado 6"


@pytest.mark.parametrize("cantidad", [0, -2])
def test_descontar_cantidad_no_positiva(cantidad):
    with pytest.raises(ValueError) as exc:
        descontar_stock(5, cantidad)
    assert str(exc.value) == "La cantidad debe ser mayor que cero"


def test_estado_tras_salida():
    assert estado_tras_salida(0, VIGENTE) == AGOTADO
    assert estado_tras_salida(1, VIGENTE) == VIGENTE
    assert estado_tras_salida(3, PROXIMO_VENCER) == PROXIMO_VENCER


# ---------- Integración con la API ----------
def test_filtro_proximos_a_vencer(client):
    r = client.get("/lotes/?proximos_a_vencer=15", headers=auth(token_de(client, *FARMACEUTA)))
    assert [l["numero_lote"] for l in r.json()] == ["LOT-PROX"]
    assert r.json()[0]["dias_para_vencer"] == 10


def test_generar_alertas_clasifica_lotes(client):
    r = client.post("/alertas/generar", headers=auth(token_de(client, *ADMIN)))
    assert r.status_code in (200, 201), r.text
    estados = {l["numero_lote"]: l["estado"] for l in client.get("/lotes/", headers=auth(token_de(client, *ADMIN))).json()}
    assert estados == {"LOT-VIG": "VIGENTE", "LOT-PROX": "PROXIMO_VENCER", "LOT-VENC": "VENCIDO"}


def test_venta_descuenta_y_agota(client):
    t = token_de(client, *FARMACEUTA)
    r = client.post("/facturas/salida", headers=auth(t),
                    json={"numero_factura": "V-001", "detalles": [{"id_lote": 2, "cantidad": 10}]})
    assert r.status_code == 201, r.text
    lote = client.get("/lotes/2", headers=auth(t)).json()
    assert lote["cantidad_disponible"] == 0 and lote["estado"] == "AGOTADO"


def test_venta_sin_stock_suficiente(client):
    r = client.post("/facturas/salida", headers=auth(token_de(client, *FARMACEUTA)),
                    json={"numero_factura": "V-002", "detalles": [{"id_lote": 2, "cantidad": 11}]})
    assert r.status_code == 400
    assert "Inventario insuficiente" in r.json()["detail"]


def test_bug_anular_entrada_no_deja_stock_negativo(client):
    """Bug corregido: anular una compra cuyo lote ya se vendió dejaba el stock en negativo."""
    t_admin = token_de(client, *ADMIN)
    entrada = client.post("/facturas/entrada", headers=auth(t_admin), json={
        "id_proveedor": 1, "numero_factura": "C-100",
        "detalles": [{"id_medicamento": 1, "numero_lote": "LOT-NUEVO", "cantidad": 20, "precio_unitario": 1000,
                      "fecha_ingreso": str(date.today()), "fecha_vencimiento": str(date.today() + timedelta(days=300))}],
    })
    assert entrada.status_code == 201, entrada.text
    id_lote = entrada.json()["detalles"][0]["id_lote"]
    venta = client.post("/facturas/salida", headers=auth(t_admin),
                        json={"numero_factura": "V-100", "detalles": [{"id_lote": id_lote, "cantidad": 15}]})
    assert venta.status_code == 201

    r = client.patch(f"/facturas/{entrada.json()['id_factura']}/anular", headers=auth(t_admin))
    assert r.status_code == 400
    assert "inventario quedaría negativo" in r.json()["detail"]
    assert client.get(f"/lotes/{id_lote}", headers=auth(t_admin)).json()["cantidad_disponible"] == 5
