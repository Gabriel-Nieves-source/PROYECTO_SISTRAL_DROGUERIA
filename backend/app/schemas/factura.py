from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DetalleEntradaItem(BaseModel):
    """Un renglón de una factura de compra: alimenta o crea un lote."""

    id_medicamento: int
    numero_lote: str
    cantidad: int = Field(gt=0)
    precio_unitario: Decimal = Field(ge=0)
    fecha_ingreso: date
    fecha_vencimiento: date


class FacturaEntradaCrear(BaseModel):

    id_proveedor: int
    numero_factura: str
    detalles: List[DetalleEntradaItem] = Field(min_length=1)


class DetalleSalidaItem(BaseModel):
    """Un renglón de una factura de venta: descuenta un lote existente."""

    id_lote: int
    cantidad: int = Field(gt=0)
    precio_unitario: Optional[Decimal] = None


class FacturaSalidaCrear(BaseModel):

    numero_factura: str
    detalles: List[DetalleSalidaItem] = Field(min_length=1)


class DetalleFacturaRespuesta(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id_detalle: int
    id_medicamento: int
    id_lote: int
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class FacturaRespuesta(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id_factura: int
    id_usuario: int
    id_proveedor: Optional[int] = None
    numero_factura: str
    tipo: str
    fecha: Optional[datetime] = None
    total: Decimal
    estado: str
    detalles: List[DetalleFacturaRespuesta] = []
