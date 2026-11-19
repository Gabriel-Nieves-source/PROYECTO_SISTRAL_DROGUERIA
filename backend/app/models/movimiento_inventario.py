from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class MovimientoInventario(Base):

    __tablename__ = "movimiento_inventario"

    id_movimiento = Column(
        Integer,
        primary_key=True,
        index=True
    )

    id_lote = Column(
        Integer,
        ForeignKey("lote.id_lote"),
        nullable=False
    )

    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id_usuario"),
        nullable=False
    )

    id_factura = Column(
        Integer,
        ForeignKey("factura.id_factura"),
        nullable=True
    )

    tipo_movimiento = Column(
        String(20),
        nullable=False
    )

    cantidad = Column(
        Integer,
        nullable=False
    )

    fecha = Column(
        DateTime,
        default=datetime.now
    )

    descripcion = Column(
        String(255)
    )

    lote = relationship(
        "Lote"
    )

    usuario = relationship(
        "Usuario"
    )

    factura = relationship(
        "Factura"
    )
