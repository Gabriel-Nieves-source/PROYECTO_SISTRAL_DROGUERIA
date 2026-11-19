from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from app.database import Base


class ConfiguracionAlerta(Base):

    __tablename__ = "configuracion_alerta"

    id_configuracion = Column(
        Integer,
        primary_key=True,
        index=True
    )

    dias_anticipacion = Column(
        Integer,
        nullable=False,
        default=30
    )

    fecha_actualizacion = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now
    )

    estado = Column(
        String(20),
        nullable=False,
        default="ACTIVA"
    )
