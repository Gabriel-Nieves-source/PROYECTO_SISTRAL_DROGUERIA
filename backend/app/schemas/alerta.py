from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AlertaRespuesta(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id_alerta: int
    id_lote: int
    tipo: str
    mensaje: str
    dias_restantes: Optional[int] = None
    fecha_generacion: Optional[datetime] = None
    estado: str


class ConfiguracionAlertaRespuesta(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id_configuracion: int
    dias_anticipacion: int
    estado: str


class ConfiguracionAlertaActualizar(BaseModel):

    dias_anticipacion: int = Field(ge=0)
