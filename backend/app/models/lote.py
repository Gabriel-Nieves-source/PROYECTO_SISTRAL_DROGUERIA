from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Lote(Base):

    __tablename__ = "lote"

    id_lote = Column(
        Integer,
        primary_key=True,
        index=True
    )

    id_medicamento = Column(
        Integer,
        ForeignKey("medicamento.id_medicamento"),
        nullable=False
    )

    id_proveedor = Column(
        Integer,
        ForeignKey("proveedor.id_proveedor"),
        nullable=False
    )

    numero_lote = Column(
        String(100),
        nullable=False
    )

    cantidad_inicial = Column(
        Integer,
        nullable=False
    )

    cantidad_disponible = Column(
        Integer,
        nullable=False
    )

    fecha_ingreso = Column(
        Date,
        nullable=False
    )

    fecha_vencimiento = Column(
        Date,
        nullable=False
    )

    estado = Column(
        String(20),
        nullable=False,
        default="VIGENTE"
    )

    medicamento = relationship(
        "Medicamento"
    )

    proveedor = relationship(
        "Proveedor"
    )
