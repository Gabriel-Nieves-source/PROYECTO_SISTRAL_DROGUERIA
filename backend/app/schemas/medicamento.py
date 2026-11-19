from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from decimal import Decimal


class MedicamentoCrear(BaseModel):

    nombre: str
    presentacion: Optional[str] = None
    concentracion: Optional[str] = None
    codigo_barras: Optional[str] = None
    precio: Decimal = Field(ge=0)


class MedicamentoActualizar(BaseModel):

    nombre: Optional[str] = None
    presentacion: Optional[str] = None
    concentracion: Optional[str] = None
    codigo_barras: Optional[str] = None
    precio: Optional[Decimal] = None
    estado: Optional[str] = None


class MedicamentoRespuesta(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id_medicamento: int
    nombre: str
    presentacion: Optional[str] = None
    concentracion: Optional[str] = None
    codigo_barras: Optional[str] = None
    precio: Decimal
    estado: str
