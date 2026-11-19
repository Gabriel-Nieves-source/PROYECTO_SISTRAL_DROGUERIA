from sqlalchemy import Column, Integer, String

from app.database import Base


class Proveedor(Base):

    __tablename__ = "proveedor"

    id_proveedor = Column(
        Integer,
        primary_key=True,
        index=True
    )

    nombre = Column(
        String(150),
        nullable=False
    )

    nit = Column(
        String(30),
        unique=True
    )

    telefono = Column(
        String(30)
    )

    correo = Column(
        String(100)
    )

    direccion = Column(
        String(200)
    )

    estado = Column(
        String(20),
        nullable=False,
        default="ACTIVO"
    )
