from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.proveedor import Proveedor
from app.schemas.proveedor import (
    ProveedorCrear,
    ProveedorActualizar,
    ProveedorRespuesta
)
from app.security import obtener_usuario_actual, verificar_administrador


router = APIRouter(
    prefix="/proveedores",
    tags=["Proveedores"]
)


@router.get(
    "/",
    response_model=List[ProveedorRespuesta]
)
def listar_proveedores(
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):

    consulta = db.query(Proveedor)

    if estado is not None:

        consulta = consulta.filter(Proveedor.estado == estado.upper())

    return consulta.all()


@router.get(
    "/{id_proveedor}",
    response_model=ProveedorRespuesta
)
def obtener_proveedor(
    id_proveedor: int,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):

    proveedor = db.query(Proveedor).filter(
        Proveedor.id_proveedor == id_proveedor
    ).first()

    if not proveedor:

        raise HTTPException(
            status_code=404,
            detail="Proveedor no encontrado"
        )

    return proveedor


@router.post(
    "/",
    response_model=ProveedorRespuesta,
    status_code=201
)
def crear_proveedor(
    datos: ProveedorCrear,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):
    """RQF003 - Administrador y Farmaceuta pueden registrar proveedores."""

    if datos.nit:

        existente = db.query(Proveedor).filter(
            Proveedor.nit == datos.nit
        ).first()

        if existente:

            raise HTTPException(
                status_code=400,
                detail="Ya existe un proveedor con ese NIT"
            )

    nuevo_proveedor = Proveedor(
        nombre=datos.nombre,
        nit=datos.nit,
        telefono=datos.telefono,
        correo=datos.correo,
        direccion=datos.direccion,
        estado="ACTIVO"
    )

    db.add(nuevo_proveedor)
    db.commit()
    db.refresh(nuevo_proveedor)

    return nuevo_proveedor


@router.put(
    "/{id_proveedor}",
    response_model=ProveedorRespuesta
)
def actualizar_proveedor(
    id_proveedor: int,
    datos: ProveedorActualizar,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(verificar_administrador)
):
    """RQF003 - Solo el Administrador puede modificar proveedores."""

    proveedor = db.query(Proveedor).filter(
        Proveedor.id_proveedor == id_proveedor
    ).first()

    if not proveedor:

        raise HTTPException(
            status_code=404,
            detail="Proveedor no encontrado"
        )

    if datos.nit:

        existente = db.query(Proveedor).filter(
            Proveedor.nit == datos.nit,
            Proveedor.id_proveedor != id_proveedor
        ).first()

        if existente:

            raise HTTPException(
                status_code=400,
                detail="Ya existe un proveedor con ese NIT"
            )

    datos_actualizados = datos.model_dump(exclude_unset=True)

    for campo, valor in datos_actualizados.items():

        setattr(proveedor, campo, valor)

    db.commit()
    db.refresh(proveedor)

    return proveedor


@router.delete(
    "/{id_proveedor}"
)
def eliminar_proveedor(
    id_proveedor: int,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(verificar_administrador)
):
    """
    RQF003 - Solo el Administrador puede eliminar proveedores.
    Se hace una baja lógica (estado INACTIVO) porque el proveedor
    puede estar referenciado por lotes y facturas existentes.
    """

    proveedor = db.query(Proveedor).filter(
        Proveedor.id_proveedor == id_proveedor
    ).first()

    if not proveedor:

        raise HTTPException(
            status_code=404,
            detail="Proveedor no encontrado"
        )

    proveedor.estado = "INACTIVO"

    db.commit()

    return {
        "success": True,
        "message": "Proveedor desactivado correctamente"
    }
