from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Usuario(Base):

    __tablename__ = "usuario"

    id_usuario = Column(
        Integer,
        primary_key=True,
        index=True
    )

    id_rol = Column(
        Integer,
        ForeignKey("rol.id_rol"),
        nullable=False
    )

    nombre = Column(
        String(100),
        nullable=False
    )

    apellido = Column(
        String(100)
    )

    usuario = Column(
        String(50),
        unique=True,
        nullable=False
    )

    password = Column(
        String(255),
        nullable=False
    )

    estado = Column(
        String(20),
        nullable=False,
        default="ACTIVO"
    )

    fecha_creacion = Column(
        DateTime,
        default=datetime.now
    )

    rol = relationship(
        "Rol"
    )