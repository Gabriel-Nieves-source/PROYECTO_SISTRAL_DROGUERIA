from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Alerta(Base):

    __tablename__ = "alerta"

    id_alerta = Column(
        Integer,
        primary_key=True,
        index=True
    )

    id_lote = Column(
        Integer,
        ForeignKey("lote.id_lote"),
        nullable=False
    )

    tipo = Column(
        String(50),
        nullable=False
    )

    mensaje = Column(
        String(255),
        nullable=False
    )

    dias_restantes = Column(
        Integer
    )

    fecha_generacion = Column(
        DateTime,
        default=datetime.now
    )

    estado = Column(
        String(20),
        nullable=False,
        default="PENDIENTE"
    )

    lote = relationship(
        "Lote"
    )
