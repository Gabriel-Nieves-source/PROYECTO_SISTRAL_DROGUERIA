import { api } from "../api.js";
import { toast, openModal, closeModal, handleError, canWrite, refreshCurrentView } from "../app.js";

const WRITE_ROLES = ["ADMINISTRADOR", "FARMACEUTA"];
const CONFIG_ROLES = ["ADMINISTRADOR"];

let cache = [];
let filtro = "PENDIENTE";

export async function renderAlertas(root) {
  root.innerHTML = `
    <div class="panel">
      <div class="panel-head">
        <h2>Alertas de vencimiento</h2>
        <div class="actions">
          ${canWrite(WRITE_ROLES) ? `<button class="btn btn-ghost" id="btn-generar">Generar alertas ahora</button>` : ""}
          ${canWrite(CONFIG_ROLES) ? `<button class="btn btn-primary" id="btn-umbral">Configurar umbral</button>` : ""}
        </div>
      </div>
      <div class="toolbar">
        <span class="chip active" data-f="PENDIENTE">Pendientes</span>
        <span class="chip" data-f="VISTA">Vistas</span>
        <span class="chip" data-f="ATENDIDA">Atendidas</span>
        <span class="chip" data-f="">Todas</span>
      </div>
      <div id="alertas-box"></div>
    </div>
  `;

  root.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", async () => {
      root.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      filtro = chip.dataset.f;
      await cargar(root);
    });
  });

  if (canWrite(WRITE_ROLES)) {
    root.querySelector("#btn-generar").addEventListener("click", async () => {
      try {
        const nuevas = await api.generarAlertas();
        toast(`Se evaluaron los lotes: ${nuevas.length} alerta(s) nueva(s) generada(s).`, "success");
        refreshCurrentView();
      } catch (err) { handleError(err); }
    });
  }
  if (canWrite(CONFIG_ROLES)) {
    root.querySelector("#btn-umbral").addEventListener("click", openUmbralForm);
  }

  await cargar(root);
}

async function cargar(root) {
  const box = root.querySelector("#alertas-box");
  box.innerHTML = `<div class="loading-state">Cargando…</div>`;
  try {
    const data = await api.listarAlertas(filtro ? { estado: filtro } : {});
    cache = Array.isArray(data) ? data : [];
    paint(box);
  } catch (err) {
    handleError(err);
    box.innerHTML = `<div class="empty-state">No se pudieron cargar las alertas.</div>`;
  }
}

function paint(box) {
  if (!cache.length) {
    box.innerHTML = `<div class="empty-state">No hay alertas en este estado. Usa "Generar alertas ahora" para evaluar los lotes próximos a vencer.</div>`;
    return;
  }
  box.innerHTML = cache.map(a => {
    const urgente = a.tipo === "VENCIDO" || (typeof a.dias_restantes === "number" && a.dias_restantes <= 7);
    const fecha = a.fecha_generacion ? new Date(a.fecha_generacion).toLocaleString("es-CO") : "—";
    return `
      <div class="list-card">
        <div class="stripe ${urgente ? "danger" : "warn"}"></div>
        <div style="flex:1">
          <div>${a.mensaje}</div>
          <div style="font-size:11.5px;color:var(--muted);margin-top:3px;">${fecha}</div>
        </div>
        <span class="badge ${urgente ? "badge-danger" : "badge-warn"}" style="margin-right:8px;">${a.estado}</span>
        ${a.estado !== "ATENDIDA" ? `<button class="btn btn-ghost btn-sm" data-atender="${a.id_alerta}">Marcar atendida</button>` : ""}
      </div>`;
  }).join("");

  box.querySelectorAll("[data-atender]").forEach(btn => {
    btn.addEventListener("click", async () => {
      try {
        await api.cambiarEstadoAlerta(btn.dataset.atender, "ATENDIDA");
        toast("Alerta marcada como atendida.", "success");
        refreshCurrentView();
      } catch (err) { handleError(err); }
    });
  });
}

async function openUmbralForm() {
  let actual = 30;
  try {
    const config = await api.obtenerConfiguracionAlertas();
    actual = config.dias_anticipacion ?? 30;
  } catch { /* si no hay configuración activa, se usa la línea base de 30 */ }

  openModal(`
    <h3>Configurar umbral de alertas</h3>
    <p style="font-size:13px;color:var(--muted);margin-bottom:14px;">Define con cuántos días de anticipación debe generarse una alerta de vencimiento (línea base: 30 días).</p>
    <form id="umbral-form" class="form-grid">
      <div class="field full">
        <label>Días de anticipación</label>
        <input name="dias_anticipacion" type="number" min="0" required value="${actual}">
      </div>
      <div class="modal-actions" style="grid-column:1/-1">
        <button type="button" class="btn btn-ghost" id="umbral-cancel">Cancelar</button>
        <button type="submit" class="btn btn-primary">Guardar</button>
      </div>
    </form>
  `, {
    onMount: (box) => {
      box.querySelector("#umbral-cancel").addEventListener("click", closeModal);
      box.querySelector("#umbral-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        try {
          await api.actualizarUmbral({ dias_anticipacion: Number(fd.get("dias_anticipacion")) });
          toast("Umbral actualizado.", "success");
          closeModal();
          refreshCurrentView();
        } catch (err) { handleError(err); }
      });
    }
  });
}
