from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.lote import Lote
from app.models.medicamento import Medicamento
from app.models.proveedor import Proveedor
from app.models.movimiento_inventario import MovimientoInventario
from app.models.detalle_factura import DetalleFactura
from app.schemas.lote import LoteCrear, LoteDetalleRespuesta
from app.security import obtener_usuario_actual
from app.domain.inventario import dias_para_vencer, vence_dentro_de


router = APIRouter(
    prefix="/lotes",
    tags=["Lotes"]
)


def _lote_a_detalle(lote: Lote) -> dict:

    dias_restantes = dias_para_vencer(lote.fecha_vencimiento, date.today())

    return {
        "id_lote": lote.id_lote,
        "id_medicamento": lote.id_medicamento,
        "id_proveedor": lote.id_proveedor,
        "numero_lote": lote.numero_lote,
        "cantidad_inicial": lote.cantidad_inicial,
        "cantidad_disponible": lote.cantidad_disponible,
        "fecha_ingreso": lote.fecha_ingreso,
        "fecha_vencimiento": lote.fecha_vencimiento,
        "estado": lote.estado,
        "medicamento_nombre": lote.medicamento.nombre if lote.medicamento else None,
        "proveedor_nombre": lote.proveedor.nombre if lote.proveedor else None,
        "dias_para_vencer": dias_restantes
    }


@router.get(
    "/",
    response_model=List[LoteDetalleRespuesta]
)
def listar_lotes(
    medicamento: Optional[str] = None,
    numero_lote: Optional[str] = None,
    id_proveedor: Optional[int] = None,
    estado: Optional[str] = None,
    proximos_a_vencer: Optional[int] = Query(
        default=None,
        description="Filtra lotes que vencen en los próximos N días"
    ),
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):
    """
    RQF009 - Consulta de inventario. Permite filtrar por medicamento,
    número de lote, proveedor, estado y proximidad a la fecha de
    vencimiento.
    """

    consulta = db.query(Lote)

    if medicamento is not None:

        consulta = consulta.join(Medicamento).filter(
            Medicamento.nombre.ilike(f"%{medicamento}%")
        )

    if numero_lote is not None:

        consulta = consulta.filter(
            Lote.numero_lote.ilike(f"%{numero_lote}%")
        )

    if id_proveedor is not None:

        consulta = consulta.filter(Lote.id_proveedor == id_proveedor)

    if estado is not None:

        consulta = consulta.filter(Lote.estado == estado.upper())

    lotes = consulta.all()

    if proximos_a_vencer is not None:

        hoy = date.today()

        lotes = [
            lote for lote in lotes
            if vence_dentro_de(lote.fecha_vencimiento, hoy, proximos_a_vencer)
        ]

    return [_lote_a_detalle(lote) for lote in lotes]


@router.get(
    "/{id_lote}",
    response_model=LoteDetalleRespuesta
)
def obtener_lote(
    id_lote: int,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):

    lote = db.query(Lote).filter(Lote.id_lote == id_lote).first()

    if not lote:

        raise HTTPException(
            status_code=404,
            detail="Lote no encontrado"
        )

    return _lote_a_detalle(lote)


@router.get(
    "/{id_lote}/trazabilidad"
)
def trazabilidad_lote(
    id_lote: int,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):
    """
    RQF012 - Consulta de trazabilidad de lotes: historial completo de
    movimientos de inventario y facturas asociadas a un lote.
    """

    lote = db.query(Lote).filter(Lote.id_lote == id_lote).first()

    if not lote:

        raise HTTPException(
            status_code=404,
            detail="Lote no encontrado"
        )

    movimientos = db.query(MovimientoInventario).filter(
        MovimientoInventario.id_lote == id_lote
    ).order_by(MovimientoInventario.fecha).all()

    detalles_factura = db.query(DetalleFactura).filter(
        DetalleFactura.id_lote == id_lote
    ).all()

    return {
        "lote": _lote_a_detalle(lote),
        "movimientos": [
            {
                "id_movimiento": movimiento.id_movimiento,
                "tipo_movimiento": movimiento.tipo_movimiento,
                "cantidad": movimiento.cantidad,
                "fecha": movimiento.fecha,
                "descripcion": movimiento.descripcion,
                "id_factura": movimiento.id_factura
            }
            for movimiento in movimientos
        ],
        "facturas": [
            {
                "id_detalle": detalle.id_detalle,
                "id_factura": detalle.id_factura,
                "numero_factura": (
                    detalle.factura.numero_factura if detalle.factura else None
                ),
                "tipo_factura": (
                    detalle.factura.tipo if detalle.factura else None
                ),
                "cantidad": detalle.cantidad,
                "precio_unitario": detalle.precio_unitario,
                "subtotal": detalle.subtotal
            }
            for detalle in detalles_factura
        ]
    }


@router.post(
    "/",
    response_model=LoteDetalleRespuesta,
    status_code=201
)
def registrar_lote(
    datos: LoteCrear,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):
    """
    RQF005 - Registro de lotes mediante escaneo de código de barras o
    QR. El flujo esperado desde la app móvil es: escanear el código,
    consultar el medicamento con GET /medicamentos/codigo/{codigo} y
    luego enviar este formulario con los datos del lote (proveedor,
    número de lote, cantidad, fecha de ingreso y de vencimiento), tal
    como se muestra en el diagrama de secuencia del documento.
    """

    medicamento = db.query(Medicamento).filter(
        Medicamento.id_medicamento == datos.id_medicamento
    ).first()

    if not medicamento:

        raise HTTPException(
            status_code=404,
            detail="El medicamento indicado no existe"
        )

    proveedor = db.query(Proveedor).filter(
        Proveedor.id_proveedor == datos.id_proveedor
    ).first()

    if not proveedor:

        raise HTTPException(
            status_code=404,
            detail="El proveedor indicado no existe"
        )

    if datos.fecha_vencimiento < datos.fecha_ingreso:

        raise HTTPException(
            status_code=400,
            detail="La fecha de vencimiento no puede ser anterior a la de ingreso"
        )

    lote_existente = db.query(Lote).filter(
        Lote.id_medicamento == datos.id_medicamento,
        Lote.numero_lote == datos.numero_lote
    ).first()

    if lote_existente:

        raise HTTPException(
            status_code=400,
            detail="Ya existe un lote con ese número para este medicamento"
        )

    nuevo_lote = Lote(
        id_medicamento=datos.id_medicamento,
        id_proveedor=datos.id_proveedor,
        numero_lote=datos.numero_lote,
        cantidad_inicial=datos.cantidad_inicial,
        cantidad_disponible=datos.cantidad_inicial,
        fecha_ingreso=datos.fecha_ingreso,
        fecha_vencimiento=datos.fecha_vencimiento,
        estado="VIGENTE"
    )

    db.add(nuevo_lote)
    db.flush()

    movimiento = MovimientoInventario(
        id_lote=nuevo_lote.id_lote,
        id_usuario=int(usuario_actual["sub"]),
        tipo_movimiento="ENTRADA",
        cantidad=datos.cantidad_inicial,
        descripcion="Registro inicial de lote"
    )

    db.add(movimiento)
    db.commit()
    db.refresh(nuevo_lote)

    return _lote_a_detalle(nuevo_lote)
