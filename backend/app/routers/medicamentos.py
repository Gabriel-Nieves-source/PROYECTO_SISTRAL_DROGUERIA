from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.medicamento import Medicamento
from app.schemas.medicamento import (
    MedicamentoCrear,
    MedicamentoActualizar,
    MedicamentoRespuesta
)
from app.security import obtener_usuario_actual, verificar_administrador


router = APIRouter(
    prefix="/medicamentos",
    tags=["Medicamentos"]
)


@router.get(
    "/",
    response_model=List[MedicamentoRespuesta]
)
def listar_medicamentos(
    nombre: Optional[str] = None,
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):

    consulta = db.query(Medicamento)

    if nombre is not None:

        consulta = consulta.filter(
            Medicamento.nombre.ilike(f"%{nombre}%")
        )

    if estado is not None:

        consulta = consulta.filter(Medicamento.estado == estado.upper())

    return consulta.all()


@router.get(
    "/codigo/{codigo_barras}",
    response_model=MedicamentoRespuesta
)
def obtener_medicamento_por_codigo(
    codigo_barras: str,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):
    """
    Consulta usada por el escáner de código de barras / QR de la app
    móvil (paso "Consultar medicamento" del diagrama de secuencia).
    """

    medicamento = db.query(Medicamento).filter(
        Medicamento.codigo_barras == codigo_barras
    ).first()

    if not medicamento:

        raise HTTPException(
            status_code=404,
            detail="No existe un medicamento con ese código"
        )

    return medicamento


@router.get(
    "/{id_medicamento}",
    response_model=MedicamentoRespuesta
)
def obtener_medicamento(
    id_medicamento: int,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):

    medicamento = db.query(Medicamento).filter(
        Medicamento.id_medicamento == id_medicamento
    ).first()

    if not medicamento:

        raise HTTPException(
            status_code=404,
            detail="Medicamento no encontrado"
        )

    return medicamento


@router.post(
    "/",
    response_model=MedicamentoRespuesta,
    status_code=201
)
def crear_medicamento(
    datos: MedicamentoCrear,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):
    """RQF004 - Administrador y Farmaceuta pueden registrar medicamentos."""

    if datos.codigo_barras:

        existente = db.query(Medicamento).filter(
            Medicamento.codigo_barras == datos.codigo_barras
        ).first()

        if existente:

            raise HTTPException(
                status_code=400,
                detail="Ya existe un medicamento con ese código de barras"
            )

    nuevo_medicamento = Medicamento(
        nombre=datos.nombre,
        presentacion=datos.presentacion,
        concentracion=datos.concentracion,
        codigo_barras=datos.codigo_barras,
        precio=datos.precio,
        estado="ACTIVO"
    )

    db.add(nuevo_medicamento)
    db.commit()
    db.refresh(nuevo_medicamento)

    return nuevo_medicamento


@router.put(
    "/{id_medicamento}",
    response_model=MedicamentoRespuesta
)
def actualizar_medicamento(
    id_medicamento: int,
    datos: MedicamentoActualizar,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(verificar_administrador)
):
    """RQF004 - Solo el Administrador puede modificar el catálogo."""

    medicamento = db.query(Medicamento).filter(
        Medicamento.id_medicamento == id_medicamento
    ).first()

    if not medicamento:

        raise HTTPException(
            status_code=404,
            detail="Medicamento no encontrado"
        )

    if datos.codigo_barras:

        existente = db.query(Medicamento).filter(
            Medicamento.codigo_barras == datos.codigo_barras,
            Medicamento.id_medicamento != id_medicamento
        ).first()

        if existente:

            raise HTTPException(
                status_code=400,
                detail="Ya existe un medicamento con ese código de barras"
            )

    datos_actualizados = datos.model_dump(exclude_unset=True)

    for campo, valor in datos_actualizados.items():

        setattr(medicamento, campo, valor)

    db.commit()
    db.refresh(medicamento)

    return medicamento


@router.delete(
    "/{id_medicamento}"
)
def eliminar_medicamento(
    id_medicamento: int,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(verificar_administrador)
):
    """
    RQF004 - Solo el Administrador puede eliminar. Se hace baja lógica
    (estado INACTIVO) porque el medicamento puede tener lotes asociados.
    """

    medicamento = db.query(Medicamento).filter(
        Medicamento.id_medicamento == id_medicamento
    ).first()

    if not medicamento:

        raise HTTPException(
            status_code=404,
            detail="Medicamento no encontrado"
        )

    medicamento.estado = "INACTIVO"

    db.commit()

    return {
        "success": True,
        "message": "Medicamento desactivado correctamente"
    }
