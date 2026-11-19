from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.factura import Factura
from app.models.detalle_factura import DetalleFactura
from app.models.lote import Lote
from app.models.medicamento import Medicamento
from app.models.proveedor import Proveedor
from app.models.movimiento_inventario import MovimientoInventario
from app.schemas.factura import (
    FacturaEntradaCrear,
    FacturaSalidaCrear,
    FacturaRespuesta
)
from app.security import obtener_usuario_actual, verificar_administrador
from app.domain.inventario import descontar_stock, estado_tras_salida


router = APIRouter(
    prefix="/facturas",
    tags=["Facturación"]
)


@router.get(
    "/",
    response_model=List[FacturaRespuesta]
)
def listar_facturas(
    tipo: Optional[str] = None,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):

    consulta = db.query(Factura)

    if tipo is not None:

        consulta = consulta.filter(Factura.tipo == tipo.upper())

    return consulta.order_by(Factura.fecha.desc()).all()


@router.get(
    "/{id_factura}",
    response_model=FacturaRespuesta
)
def obtener_factura(
    id_factura: int,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):

    factura = db.query(Factura).filter(
        Factura.id_factura == id_factura
    ).first()

    if not factura:

        raise HTTPException(
            status_code=404,
            detail="Factura no encontrada"
        )

    return factura


@router.post(
    "/entrada",
    response_model=FacturaRespuesta,
    status_code=201
)
def registrar_factura_entrada(
    datos: FacturaEntradaCrear,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):
    """
    RQF006 - Registro de facturas de compra (entrada). Por cada
    detalle se busca el lote (medicamento + número de lote); si ya
    existe se incrementa su cantidad, si no existe se crea. Cada
    movimiento queda registrado en movimiento_inventario.
    """

    proveedor = db.query(Proveedor).filter(
        Proveedor.id_proveedor == datos.id_proveedor
    ).first()

    if not proveedor:

        raise HTTPException(
            status_code=404,
            detail="El proveedor indicado no existe"
        )

    factura = Factura(
        id_usuario=int(usuario_actual["sub"]),
        id_proveedor=datos.id_proveedor,
        numero_factura=datos.numero_factura,
        tipo="ENTRADA",
        total=0,
        estado="ACTIVA"
    )

    db.add(factura)
    db.flush()

    total = 0

    for item in datos.detalles:

        medicamento = db.query(Medicamento).filter(
            Medicamento.id_medicamento == item.id_medicamento
        ).first()

        if not medicamento:

            db.rollback()

            raise HTTPException(
                status_code=404,
                detail=f"El medicamento {item.id_medicamento} no existe"
            )

        if item.fecha_vencimiento < item.fecha_ingreso:

            db.rollback()

            raise HTTPException(
                status_code=400,
                detail="La fecha de vencimiento no puede ser anterior a la de ingreso"
            )

        lote = db.query(Lote).filter(
            Lote.id_medicamento == item.id_medicamento,
            Lote.numero_lote == item.numero_lote
        ).first()

        if lote:

            lote.cantidad_inicial += item.cantidad
            lote.cantidad_disponible += item.cantidad

        else:

            lote = Lote(
                id_medicamento=item.id_medicamento,
                id_proveedor=datos.id_proveedor,
                numero_lote=item.numero_lote,
                cantidad_inicial=item.cantidad,
                cantidad_disponible=item.cantidad,
                fecha_ingreso=item.fecha_ingreso,
                fecha_vencimiento=item.fecha_vencimiento,
                estado="VIGENTE"
            )

            db.add(lote)

        db.flush()

        subtotal = item.cantidad * item.precio_unitario

        detalle = DetalleFactura(
            id_factura=factura.id_factura,
            id_medicamento=item.id_medicamento,
            id_lote=lote.id_lote,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario,
            subtotal=subtotal
        )

        db.add(detalle)

        movimiento = MovimientoInventario(
            id_lote=lote.id_lote,
            id_usuario=int(usuario_actual["sub"]),
            id_factura=factura.id_factura,
            tipo_movimiento="ENTRADA",
            cantidad=item.cantidad,
            descripcion=f"Entrada por factura {datos.numero_factura}"
        )

        db.add(movimiento)

        total += subtotal

    factura.total = total

    db.commit()
    db.refresh(factura)

    return factura


@router.post(
    "/salida",
    response_model=FacturaRespuesta,
    status_code=201
)
def registrar_factura_salida(
    datos: FacturaSalidaCrear,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):
    """
    RQF007 - Registro de facturas de venta (salida). Descuenta
    automáticamente las cantidades vendidas del lote indicado y valida
    que exista inventario suficiente antes de confirmar la venta.
    """

    factura = Factura(
        id_usuario=int(usuario_actual["sub"]),
        numero_factura=datos.numero_factura,
        tipo="SALIDA",
        total=0,
        estado="ACTIVA"
    )

    db.add(factura)
    db.flush()

    total = 0

    for item in datos.detalles:

        lote = db.query(Lote).filter(
            Lote.id_lote == item.id_lote
        ).first()

        if not lote:

            db.rollback()

            raise HTTPException(
                status_code=404,
                detail=f"El lote {item.id_lote} no existe"
            )

        try:

            nuevo_disponible = descontar_stock(lote.cantidad_disponible, item.cantidad)

        except ValueError as error:

            db.rollback()

            raise HTTPException(
                status_code=400,
                detail=f"Lote {lote.numero_lote}: {error}"
            ) from None

        precio_unitario = item.precio_unitario

        if precio_unitario is None:

            precio_unitario = lote.medicamento.precio if lote.medicamento else 0

        lote.cantidad_disponible = nuevo_disponible

        lote.estado = estado_tras_salida(nuevo_disponible, lote.estado)

        subtotal = item.cantidad * precio_unitario

        detalle = DetalleFactura(
            id_factura=factura.id_factura,
            id_medicamento=lote.id_medicamento,
            id_lote=lote.id_lote,
            cantidad=item.cantidad,
            precio_unitario=precio_unitario,
            subtotal=subtotal
        )

        db.add(detalle)

        movimiento = MovimientoInventario(
            id_lote=lote.id_lote,
            id_usuario=int(usuario_actual["sub"]),
            id_factura=factura.id_factura,
            tipo_movimiento="SALIDA",
            cantidad=item.cantidad,
            descripcion=f"Salida por factura {datos.numero_factura}"
        )

        db.add(movimiento)

        total += subtotal

    factura.total = total

    db.commit()
    db.refresh(factura)

    return factura


@router.patch(
    "/{id_factura}/anular",
    response_model=FacturaRespuesta
)
def anular_factura(
    id_factura: int,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(verificar_administrador)
):
    """
    Solo el Administrador puede anular una factura. Revierte el efecto
    de la factura sobre el inventario y deja constancia del ajuste en
    movimiento_inventario.
    """

    factura = db.query(Factura).filter(
        Factura.id_factura == id_factura
    ).first()

    if not factura:

        raise HTTPException(
            status_code=404,
            detail="Factura no encontrada"
        )

    if factura.estado == "ANULADA":

        raise HTTPException(
            status_code=400,
            detail="La factura ya se encuentra anulada"
        )

    for detalle in factura.detalles:

        lote = detalle.lote

        if factura.tipo == "SALIDA":

            lote.cantidad_disponible += detalle.cantidad

            if lote.estado == "AGOTADO":

                lote.estado = "VIGENTE"

        else:

            # Guía 8 - bug corregido: antes se restaba sin validar y el stock
            # podía quedar negativo si parte del lote ya se había vendido.
            try:

                lote.cantidad_disponible = descontar_stock(
                    lote.cantidad_disponible, detalle.cantidad
                )

            except ValueError:

                db.rollback()

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"No se puede anular: del lote {lote.numero_lote} ya salieron "
                        "unidades y el inventario quedaría negativo"
                    )
                ) from None

            lote.cantidad_inicial -= detalle.cantidad

        movimiento = MovimientoInventario(
            id_lote=lote.id_lote,
            id_usuario=int(usuario_actual["sub"]),
            id_factura=factura.id_factura,
            tipo_movimiento="AJUSTE",
            cantidad=detalle.cantidad,
            descripcion=(
                f"Reversión por anulación de factura {factura.numero_factura}"
            )
        )

        db.add(movimiento)

    factura.estado = "ANULADA"

    db.commit()
    db.refresh(factura)

    return factura
