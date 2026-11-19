import { api } from "../api.js";
import { handleError } from "../app.js";

export async function renderDashboard(root) {
  let kpis = null, lotes = [], alertas = [];
  try {
    [kpis, lotes, alertas] = await Promise.all([
      api.obtenerKpis(),
      api.listarLotes().catch(() => []),
      api.listarAlertas({ estado: "PENDIENTE" }).catch(() => []),
    ]);
  } catch (err) {
    handleError(err);
  }

  lotes = Array.isArray(lotes) ? lotes : [];
  alertas = Array.isArray(alertas) ? alertas : [];
  kpis = kpis || {};

  root.innerHTML = `
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Medicamentos activos</div>
        <div class="kpi-value">${kpis.total_medicamentos ?? "—"}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Unidades disponibles</div>
        <div class="kpi-value">${kpis.unidades_disponibles ?? "—"}</div>
      </div>
      <div class="kpi-card warn">
        <div class="kpi-label">Lotes próximos a vencer</div>
        <div class="kpi-value">${kpis.lotes_proximos_vencer ?? "—"}</div>
      </div>
      <div class="kpi-card danger">
        <div class="kpi-label">Lotes vencidos</div>
        <div class="kpi-value">${kpis.lotes_vencidos ?? "—"}</div>
      </div>
    </div>

    <div class="kpi-grid" style="grid-template-columns:1fr;">
      <div class="kpi-card">
        <div class="kpi-label">Proveedores activos</div>
        <div class="kpi-value">${kpis.proveedores_activos ?? "—"}</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head">
        <h2>Alertas pendientes</h2>
        <span class="badge badge-danger">${alertas.length} pendiente${alertas.length === 1 ? "" : "s"}</span>
      </div>
      <div id="dash-alertas"></div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>Lotes próximos a vencer</h2></div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Lote</th><th>Medicamento</th><th>Disponible</th><th>Vence en</th><th>Estado</th></tr></thead>
          <tbody id="dash-lotes"></tbody>
        </table>
      </div>
    </div>
  `;

  const alertasBox = root.querySelector("#dash-alertas");
  if (!alertas.length) {
    alertasBox.innerHTML = `<div class="empty-state">No hay alertas pendientes en este momento.</div>`;
  } else {
    alertasBox.innerHTML = alertas.slice(0, 6).map(a => {
      const urgente = a.tipo === "VENCIDO" || (typeof a.dias_restantes === "number" && a.dias_restantes <= 7);
      return `
        <div class="list-card">
          <div class="stripe ${urgente ? "danger" : "warn"}"></div>
          <div style="flex:1">${a.mensaje}</div>
        </div>`;
    }).join("");
  }

  const lotesBody = root.querySelector("#dash-lotes");
  const criticos = lotes
    .filter(l => typeof l.dias_para_vencer === "number")
    .sort((a, b) => a.dias_para_vencer - b.dias_para_vencer)
    .slice(0, 8);
  if (!criticos.length) {
    lotesBody.innerHTML = `<tr><td colspan="5" class="empty-state">Sin lotes registrados todavía.</td></tr>`;
  } else {
    const badgeClass = { VIGENTE: "badge-ok", PROXIMO_VENCER: "badge-warn", VENCIDO: "badge-danger", AGOTADO: "badge-muted" };
    lotesBody.innerHTML = criticos.map(l => `
      <tr>
        <td>${l.numero_lote}</td>
        <td>${l.medicamento_nombre || "—"}</td>
        <td>${l.cantidad_disponible ?? "—"}</td>
        <td>${l.dias_para_vencer} días</td>
        <td><span class="badge ${badgeClass[l.estado] || "badge-muted"}">${(l.estado || "").replace("_", " ")}</span></td>
      </tr>`).join("");
  }
}
