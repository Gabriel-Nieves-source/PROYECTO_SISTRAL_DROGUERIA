from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Factura(Base):

    __tablename__ = "factura"

    id_factura = Column(
        Integer,
        primary_key=True,
        index=True
    )

    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id_usuario"),
        nullable=False
    )

    id_proveedor = Column(
        Integer,
        ForeignKey("proveedor.id_proveedor"),
        nullable=True
    )

    numero_factura = Column(
        String(50),
        nullable=False
    )

    tipo = Column(
        String(10),
        nullable=False
    )

    fecha = Column(
        DateTime,
        default=datetime.now
    )

    total = Column(
        DECIMAL(14, 2),
        nullable=False,
        default=0
    )

    estado = Column(
        String(20),
        nullable=False,
        default="ACTIVA"
    )

    usuario = relationship(
        "Usuario"
    )

    proveedor = relationship(
        "Proveedor"
    )

    detalles = relationship(
        "DetalleFactura",
        back_populates="factura",
        cascade="all, delete-orphan"
    )
