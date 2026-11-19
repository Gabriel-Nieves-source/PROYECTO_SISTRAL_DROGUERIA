from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):

    # Guía 8 - OWASP API3: se rechazan campos extra (p. ej. "rol") y se limitan longitudes
    model_config = ConfigDict(extra="forbid")

    usuario: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):

    success: bool
    message: str
    id_usuario: int
    usuario: str
    nombre: str
    rol: str
    access_token: str
    token_type: str