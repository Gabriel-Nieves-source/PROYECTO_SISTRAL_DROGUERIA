from pydantic import BaseModel, ConfigDict
from typing import Optional


class ProveedorCrear(BaseModel):

    nombre: str
    nit: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    direccion: Optional[str] = None


class ProveedorActualizar(BaseModel):

    nombre: Optional[str] = None
    nit: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    direccion: Optional[str] = None
    estado: Optional[str] = None


class ProveedorRespuesta(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id_proveedor: int
    nombre: str
    nit: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    direccion: Optional[str] = None
    estado: str
