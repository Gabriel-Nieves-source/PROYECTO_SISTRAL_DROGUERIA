from pydantic import BaseModel


class DashboardKPIs(BaseModel):

    total_medicamentos: int
    unidades_disponibles: int
    lotes_proximos_vencer: int
    lotes_vencidos: int
    proveedores_activos: int
