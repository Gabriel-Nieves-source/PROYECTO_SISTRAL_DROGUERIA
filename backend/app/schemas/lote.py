from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class LoteCrear(BaseModel):

    id_medicamento: int
    id_proveedor: int
    numero_lote: str
    cantidad_inicial: int = Field(gt=0)
    fecha_ingreso: date
    fecha_vencimiento: date


class LoteRespuesta(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id_lote: int
    id_medicamento: int
    id_proveedor: int
    numero_lote: str
    cantidad_inicial: int
    cantidad_disponible: int
    fecha_ingreso: date
    fecha_vencimiento: date
    estado: str


class LoteDetalleRespuesta(LoteRespuesta):

    medicamento_nombre: Optional[str] = None
    proveedor_nombre: Optional[str] = None
    dias_para_vencer: Optional[int] = None
