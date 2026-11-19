from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alerta import Alerta
from app.models.lote import Lote
from app.models.configuracion_alerta import ConfiguracionAlerta
from app.schemas.alerta import (
    AlertaRespuesta,
    ConfiguracionAlertaRespuesta,
    ConfiguracionAlertaActualizar
)
from app.security import obtener_usuario_actual, verificar_administrador
from app.domain.inventario import (
    PROXIMO_VENCER,
    VENCIDO,
    clasificar_vencimiento,
    dias_para_vencer,
)


router = APIRouter(
    prefix="/alertas",
    tags=["Alertas"]
)


@router.get(
    "/",
    response_model=List[AlertaRespuesta]
)
def listar_alertas(
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):

    consulta = db.query(Alerta)

    if estado is not None:

        consulta = consulta.filter(Alerta.estado == estado.upper())

    return consulta.order_by(Alerta.fecha_generacion.desc()).all()


@router.post(
    "/generar",
    response_model=List[AlertaRespuesta]
)
def generar_alertas(
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):
    """
    RQF008 - Corresponde al actor "Sistema (Job Diario)" del diagrama
    de casos de uso: evalúa las fechas de vencimiento de todos los
    lotes con inventario disponible contra el umbral configurado
    (configuracion_alerta.dias_anticipacion, línea base 30 días) y
    genera una alerta por cada lote que lo cumpla y no tenga ya una
    alerta pendiente/vista. Puede invocarse manualmente desde la app o
    programarse con un scheduler (cron) para que corra una vez al día.
    """

    configuracion = db.query(ConfiguracionAlerta).filter(
        ConfiguracionAlerta.estado == "ACTIVA"
    ).first()

    umbral = configuracion.dias_anticipacion if configuracion else 30

    hoy = date.today()

    lotes = db.query(Lote).filter(
        Lote.cantidad_disponible > 0
    ).all()

    alertas_generadas = []

    for lote in lotes:

        dias_restantes = dias_para_vencer(lote.fecha_vencimiento, hoy)

        nuevo_estado_lote = clasificar_vencimiento(lote.fecha_vencimiento, hoy, umbral)

        tipo_alerta = (
            nuevo_estado_lote
            if nuevo_estado_lote in (VENCIDO, PROXIMO_VENCER)
            else None
        )

        if lote.estado != nuevo_estado_lote:

            lote.estado = nuevo_estado_lote

        if tipo_alerta is None:

            continue

        alerta_existente = db.query(Alerta).filter(
            Alerta.id_lote == lote.id_lote,
            Alerta.tipo == tipo_alerta,
            Alerta.estado != "ATENDIDA"
        ).first()

        if alerta_existente:

            continue

        nombre_medicamento = (
            lote.medicamento.nombre if lote.medicamento else lote.id_medicamento
        )

        if tipo_alerta == "VENCIDO":

            mensaje = (
                f"El lote {lote.numero_lote} de {nombre_medicamento} "
                f"venció el {lote.fecha_vencimiento}."
            )

        else:

            mensaje = (
                f"El lote {lote.numero_lote} de {nombre_medicamento} "
                f"vence en {dias_restantes} día(s) ({lote.fecha_vencimiento})."
            )

        alerta = Alerta(
            id_lote=lote.id_lote,
            tipo=tipo_alerta,
            mensaje=mensaje,
            dias_restantes=dias_restantes,
            estado="PENDIENTE"
        )

        db.add(alerta)
        alertas_generadas.append(alerta)

    db.commit()

    for alerta in alertas_generadas:

        db.refresh(alerta)

    return alertas_generadas


@router.patch(
    "/{id_alerta}/estado",
    response_model=AlertaRespuesta
)
def cambiar_estado_alerta(
    id_alerta: int,
    nuevo_estado: str,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):
    """Permite marcar una alerta como VISTA o ATENDIDA."""

    if nuevo_estado.upper() not in ("PENDIENTE", "VISTA", "ATENDIDA"):

        raise HTTPException(
            status_code=400,
            detail="Estado inválido. Use PENDIENTE, VISTA o ATENDIDA"
        )

    alerta = db.query(Alerta).filter(
        Alerta.id_alerta == id_alerta
    ).first()

    if not alerta:

        raise HTTPException(
            status_code=404,
            detail="Alerta no encontrada"
        )

    alerta.estado = nuevo_estado.upper()

    db.commit()
    db.refresh(alerta)

    return alerta


@router.get(
    "/configuracion",
    response_model=ConfiguracionAlertaRespuesta
)
def obtener_configuracion(
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):

    configuracion = db.query(ConfiguracionAlerta).filter(
        ConfiguracionAlerta.estado == "ACTIVA"
    ).first()

    if not configuracion:

        raise HTTPException(
            status_code=404,
            detail="No hay una configuración de alertas activa"
        )

    return configuracion


@router.put(
    "/configuracion",
    response_model=ConfiguracionAlertaRespuesta
)
def actualizar_configuracion(
    datos: ConfiguracionAlertaActualizar,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(verificar_administrador)
):
    """
    RQF008 - El umbral (línea base 30 días) puede ser ajustado por el
    Administrador de acuerdo con las necesidades del negocio.
    """

    configuracion = db.query(ConfiguracionAlerta).filter(
        ConfiguracionAlerta.estado == "ACTIVA"
    ).first()

    if not configuracion:

        raise HTTPException(
            status_code=404,
            detail="No hay una configuración de alertas activa"
        )

    configuracion.dias_anticipacion = datos.dias_anticipacion

    db.commit()
    db.refresh(configuracion)

    return configuracion
