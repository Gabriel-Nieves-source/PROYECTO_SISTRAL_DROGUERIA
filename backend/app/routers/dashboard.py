from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.dashboard import DashboardKPIs
from app.security import verificar_administrador


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get(
    "/kpis",
    response_model=DashboardKPIs
)
def obtener_kpis(
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(verificar_administrador)
):
    """
    RQF010 - Dashboard administrativo con KPIs de inventario. Reutiliza
    la vista vista_dashboard definida en el script SQL, que consolida
    total de medicamentos activos, unidades disponibles, lotes
    próximos a vencer, lotes vencidos y proveedores activos.
    """

    resultado = db.execute(
        text("SELECT * FROM vista_dashboard")
    ).mappings().first()

    if resultado is None:

        raise HTTPException(
            status_code=404,
            detail="No fue posible calcular los KPIs del dashboard"
        )

    return dict(resultado)
