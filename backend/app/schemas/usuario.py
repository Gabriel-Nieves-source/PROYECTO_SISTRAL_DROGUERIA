from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class UsuarioCrear(BaseModel):

    id_rol: int
    nombre: str
    apellido: Optional[str] = None
    usuario: str = Field(min_length=3, max_length=50)
    # Guía 8 - OWASP API2: contraseñas nuevas de mínimo 8 caracteres
    password: str = Field(min_length=8, max_length=128)


class UsuarioActualizar(BaseModel):

    id_rol: Optional[int] = None
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    usuario: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)


class UsuarioRespuesta(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id_usuario: int
    id_rol: int
    nombre: str
    apellido: Optional[str] = None
    usuario: str
    estado: str