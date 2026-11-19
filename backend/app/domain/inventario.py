"""Reglas de negocio de inventario y vencimiento de SITRAL.

Se extrajeron de los routers (lotes, alertas y facturas) a funciones puras para
poder probarlas con pruebas unitarias y con Mutation Testing (Guía 8).
"""
from datetime import date

VENCIDO = "VENCIDO"
PROXIMO_VENCER = "PROXIMO_VENCER"
VIGENTE = "VIGENTE"
AGOTADO = "AGOTADO"


def dias_para_vencer(fecha_vencimiento: date, hoy: date) -> int:
    """Días que faltan para el vencimiento (negativo si ya venció)."""
    return (fecha_vencimiento - hoy).days


def clasificar_vencimiento(fecha_vencimiento: date, hoy: date, umbral_dias: int) -> str:
    """VENCIDO si ya pasó la fecha, PROXIMO_VENCER si faltan <= umbral días, VIGENTE en otro caso."""
    dias = dias_para_vencer(fecha_vencimiento, hoy)
    if dias < 0:
        return VENCIDO
    if dias <= umbral_dias:
        return PROXIMO_VENCER
    return VIGENTE


def vence_dentro_de(fecha_vencimiento: date, hoy: date, dias: int) -> bool:
    """True si el lote no ha vencido y vence en los próximos `dias` días (filtro de inventario)."""
    return 0 <= dias_para_vencer(fecha_vencimiento, hoy) <= dias


def descontar_stock(disponible: int, cantidad: int) -> int:
    """Resta unidades de un lote. Nunca permite cantidades <= 0 ni dejar el stock negativo."""
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero")
    if cantidad > disponible:
        raise ValueError(f"Inventario insuficiente: disponible {disponible}, solicitado {cantidad}")
    return disponible - cantidad


def estado_tras_salida(disponible: int, estado_actual: str) -> str:
    """Un lote que queda en cero pasa a AGOTADO; si no, conserva su estado."""
    return AGOTADO if disponible == 0 else estado_actual
