from sqlalchemy import Column, Integer, String, DECIMAL

from app.database import Base


class Medicamento(Base):

    __tablename__ = "medicamento"

    id_medicamento = Column(
        Integer,
        primary_key=True,
        index=True
    )

    nombre = Column(
        String(150),
        nullable=False
    )

    presentacion = Column(
        String(100)
    )

    concentracion = Column(
        String(50)
    )

    codigo_barras = Column(
        String(100),
        unique=True,
        index=True
    )

    precio = Column(
        DECIMAL(12, 2),
        nullable=False,
        default=0
    )

    estado = Column(
        String(20),
        nullable=False,
        default="ACTIVO"
    )
