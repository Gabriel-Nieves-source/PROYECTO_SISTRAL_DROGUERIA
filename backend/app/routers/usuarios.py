from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import (
    UsuarioCrear,
    UsuarioActualizar,
    UsuarioRespuesta
)
from app.security import verificar_administrador
from pwdlib import PasswordHash


router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)


password_hash = PasswordHash.recommended()


@router.get(
    "/",
    response_model=List[UsuarioRespuesta]
)
def listar_usuarios(
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(verificar_administrador)
):

    usuarios = db.query(Usuario).all()

    return usuarios


@router.get(
    "/{id_usuario}",
    response_model=UsuarioRespuesta
)
def obtener_usuario(
    id_usuario: int,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(verificar_administrador)
):

    usuario = db.query(Usuario).filter(
        Usuario.id_usuario == id_usuario
    ).first()

    if not usuario:

        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    return usuario


@router.post(
    "/",
    response_model=UsuarioRespuesta,
    status_code=201
)
def crear_usuario(
    datos: UsuarioCrear,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(verificar_administrador)
):

    usuario_existente = db.query(Usuario).filter(
        Usuario.usuario == datos.usuario
    ).first()

    if usuario_existente:

        raise HTTPException(
            status_code=400,
            detail="El nombre de usuario ya existe"
        )

    nuevo_usuario = Usuario(

        id_rol=datos.id_rol,

        nombre=datos.nombre,

        apellido=datos.apellido,

        usuario=datos.usuario,

        password=password_hash.hash(datos.password),

        estado="ACTIVO"
    )

    db.add(nuevo_usuario)

    db.commit()

    db.refresh(nuevo_usuario)

    return nuevo_usuario


@router.put(
    "/{id_usuario}",
    response_model=UsuarioRespuesta
)
def actualizar_usuario(
    id_usuario: int,
    datos: UsuarioActualizar,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(verificar_administrador)
):

    usuario = db.query(Usuario).filter(
        Usuario.id_usuario == id_usuario
    ).first()

    if not usuario:

        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    if datos.id_rol is not None:

        usuario.id_rol = datos.id_rol

    if datos.nombre is not None:

        usuario.nombre = datos.nombre

    if datos.apellido is not None:

        usuario.apellido = datos.apellido

    if datos.usuario is not None:

        usuario_existente = db.query(Usuario).filter(
            Usuario.usuario == datos.usuario,
            Usuario.id_usuario != id_usuario
        ).first()

        if usuario_existente:

            raise HTTPException(
                status_code=400,
                detail="El nombre de usuario ya existe"
            )

        usuario.usuario = datos.usuario

    if datos.password is not None:

        usuario.password = password_hash.hash(
            datos.password
        )

    db.commit()

    db.refresh(usuario)

    return usuario


@router.patch(
    "/{id_usuario}/estado",
    response_model=UsuarioRespuesta
)
def cambiar_estado_usuario(
    id_usuario: int,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(verificar_administrador)
):

    usuario = db.query(Usuario).filter(
        Usuario.id_usuario == id_usuario
    ).first()

    if not usuario:

        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    if usuario.estado == "ACTIVO":

        usuario.estado = "INACTIVO"

    else:

        usuario.estado = "ACTIVO"

    db.commit()

    db.refresh(usuario)

    return usuario


@router.delete(
    "/{id_usuario}"
)
def eliminar_usuario(
    id_usuario: int,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(verificar_administrador)
):

    usuario = db.query(Usuario).filter(
        Usuario.id_usuario == id_usuario
    ).first()

    if not usuario:

        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    if str(usuario.id_usuario) == usuario_actual.get("sub"):

        raise HTTPException(
            status_code=400,
            detail="No puedes eliminar tu propio usuario"
        )

    db.delete(usuario)

    try:

        db.commit()

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar el usuario porque tiene registros relacionados"
        )

    return {

        "success": True,

        "message": "Usuario eliminado correctamente"

    }