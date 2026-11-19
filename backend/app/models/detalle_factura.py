from sqlalchemy import Column, Integer, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class DetalleFactura(Base):

    __tablename__ = "detalle_factura"

    id_detalle = Column(
        Integer,
        primary_key=True,
        index=True
    )

    id_factura = Column(
        Integer,
        ForeignKey("factura.id_factura"),
        nullable=False
    )

    id_medicamento = Column(
        Integer,
        ForeignKey("medicamento.id_medicamento"),
        nullable=False
    )

    id_lote = Column(
        Integer,
        ForeignKey("lote.id_lote"),
        nullable=False
    )

    cantidad = Column(
        Integer,
        nullable=False
    )

    precio_unitario = Column(
        DECIMAL(12, 2),
        nullable=False
    )

    subtotal = Column(
        DECIMAL(14, 2),
        nullable=False
    )

    factura = relationship(
        "Factura",
        back_populates="detalles"
    )

    medicamento = relationship(
        "Medicamento"
    )

    lote = relationship(
        "Lote"
    )
