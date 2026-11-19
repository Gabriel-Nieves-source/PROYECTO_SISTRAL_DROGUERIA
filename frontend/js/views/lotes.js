import { api } from "../api.js";
import { toast, openModal, closeModal, handleError, canWrite, refreshCurrentView } from "../app.js";
import { openScanner, iScan } from "../scanner.js";

const WRITE_ROLES = ["ADMINISTRADOR", "FARMACEUTA"];

let cache = [];
let search = "";
let filter = "TODOS";

export async function renderLotes(root) {
  root.innerHTML = `
    <div class="panel">
      <div class="panel-head">
        <h2>Lotes de medicamentos</h2>
        <div class="actions">
          ${canWrite(WRITE_ROLES) ? `<button class="btn btn-primary" id="btn-nuevo-lote">+ Registrar lote</button>` : ""}
        </div>
      </div>
      <div class="toolbar">
        <div class="search-box">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><circle cx="11" cy="11" r="7" stroke="#9CA3AF" stroke-width="1.8"/><path d="M21 21l-4.3-4.3" stroke="#9CA3AF" stroke-width="1.8" stroke-linecap="round"/></svg>
          <input type="text" id="lote-search" placeholder="Buscar por número de lote o medicamento…">
        </div>
        <span class="chip active" data-f="TODOS">Todos</span>
        <span class="chip" data-f="PROXIMO_VENCER">Próx. a vencer</span>
        <span class="chip" data-f="VENCIDO">Vencidos</span>
        <span class="chip" data-f="AGOTADO">Agotados</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Lote</th><th>Medicamento</th><th>Proveedor</th><th>Disponible</th><th>Vencimiento</th><th>Estado</th></tr></thead>
          <tbody id="lote-rows"><tr><td colspan="6" class="loading-state">Cargando…</td></tr></tbody>
        </table>
      </div>
    </div>
  `;

  root.querySelector("#lote-search").addEventListener("input", (e) => { search = e.target.value.toLowerCase(); paint(root); });
  root.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", () => {
      root.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      filter = chip.dataset.f;
      paint(root);
    });
  });
  if (canWrite(WRITE_ROLES)) {
    root.querySelector("#btn-nuevo-lote").addEventListener("click", () => openForm());
  }

  try {
    const data = await api.listarLotes();
    cache = Array.isArray(data) ? data : (data?.items || []);
    paint(root);
  } catch (err) {
    handleError(err);
    root.querySelector("#lote-rows").innerHTML = `<tr><td colspan="6" class="empty-state">No se pudo cargar el inventario de lotes.</td></tr>`;
  }
}

function deriveEstado(l) {
  if (l.estado) return l.estado;
  if ((l.cantidad_disponible ?? 0) <= 0) return "AGOTADO";
  if (typeof l.dias_para_vencer === "number") {
    if (l.dias_para_vencer <= 0) return "VENCIDO";
    if (l.dias_para_vencer <= 30) return "PROXIMO_VENCER";
  }
  return "VIGENTE";
}

function paint(root) {
  const body = root.querySelector("#lote-rows");
  const filtered = cache.filter(l => {
    const estado = deriveEstado(l);
    const matchesFilter = filter === "TODOS" || estado === filter;
    const text = `${l.numero_lote || ""} ${l.medicamento_nombre || ""}`.toLowerCase();
    return matchesFilter && (!search || text.includes(search));
  });
  if (!filtered.length) {
    body.innerHTML = `<tr><td colspan="6" class="empty-state">No se encontraron lotes con ese criterio.</td></tr>`;
    return;
  }
  const badgeClass = { VIGENTE: "badge-ok", PROXIMO_VENCER: "badge-warn", VENCIDO: "badge-danger", AGOTADO: "badge-muted" };
  body.innerHTML = filtered.map(l => {
    const estado = deriveEstado(l);
    return `
      <tr>
        <td><strong>${l.numero_lote || l.id_lote}</strong></td>
        <td>${l.medicamento_nombre || "—"}</td>
        <td>${l.proveedor_nombre || "—"}</td>
        <td>${l.cantidad_disponible ?? "—"}</td>
        <td>${l.fecha_vencimiento || "—"}</td>
        <td><span class="badge ${badgeClass[estado] || "badge-muted"}">${estado.replace("_", " ")}</span></td>
      </tr>`;
  }).join("");
}

async function openForm() {
  let medicamentos = [], proveedores = [];
  try {
    [medicamentos, proveedores] = await Promise.all([api.listarMedicamentos(), api.listarProveedores()]);
  } catch (err) { handleError(err); }
  medicamentos = Array.isArray(medicamentos) ? medicamentos : (medicamentos?.items || []);
  proveedores = Array.isArray(proveedores) ? proveedores : (proveedores?.items || []);

  const today = new Date().toISOString().slice(0, 10);

  openModal(`
    <h3>Registrar ingreso de lote</h3>
    <form id="lote-form" class="form-grid">
      <div class="field full">
        <label>Medicamento</label>
        <div class="field-with-scan">
          <select name="id_medicamento" id="lote-form-medicamento" required>
            <option value="" disabled selected>Selecciona un medicamento…</option>
            ${medicamentos.map(m => `<option value="${m.id_medicamento}">${m.nombre}${m.codigo_barras ? ` (${m.codigo_barras})` : ""}</option>`).join("")}
          </select>
          <button type="button" class="btn btn-ghost btn-sm" id="lote-form-scan" title="Escanear código de barras del medicamento">${iScan()}</button>
        </div>
      </div>
      <div class="field full">
        <label>Proveedor</label>
        <select name="id_proveedor" required>
          <option value="" disabled selected>Selecciona un proveedor…</option>
          ${proveedores.map(p => `<option value="${p.id_proveedor}">${p.nombre}</option>`).join("")}
        </select>
      </div>
      <div class="field">
        <label>Número de lote</label>
        <input name="numero_lote" required placeholder="LT-2026-0001">
      </div>
      <div class="field">
        <label>Cantidad</label>
        <input name="cantidad_inicial" type="number" min="1" required>
      </div>
      <div class="field">
        <label>Fecha de ingreso</label>
        <input name="fecha_ingreso" type="date" required value="${today}">
      </div>
      <div class="field">
        <label>Fecha de vencimiento</label>
        <input name="fecha_vencimiento" type="date" required>
      </div>
      <div class="modal-actions" style="grid-column:1/-1">
        <button type="button" class="btn btn-ghost" id="lote-cancel">Cancelar</button>
        <button type="submit" class="btn btn-primary">Guardar lote</button>
      </div>
    </form>
  `, {
    onMount: (box) => {
      box.querySelector("#lote-cancel").addEventListener("click", closeModal);
      box.querySelector("#lote-form-scan").addEventListener("click", () => {
        openScanner({
          title: "Escanear código de barras del medicamento",
          hint: "Escanea el código del empaque para seleccionar el medicamento automáticamente.",
          onDetected: (code) => {
            const match = medicamentos.find(m => (m.codigo_barras || "").toLowerCase() === code.toLowerCase());
            if (match) {
              box.querySelector("#lote-form-medicamento").value = String(match.id_medicamento);
              toast(`Medicamento seleccionado: ${match.nombre}`, "success");
            } else {
              toast("No se encontró ningún medicamento con ese código de barras.", "error");
            }
          },
        });
      });
      box.querySelector("#lote-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const payload = {
          id_medicamento: Number(fd.get("id_medicamento")),
          id_proveedor: Number(fd.get("id_proveedor")),
          numero_lote: fd.get("numero_lote"),
          cantidad_inicial: Number(fd.get("cantidad_inicial")),
          fecha_ingreso: fd.get("fecha_ingreso"),
          fecha_vencimiento: fd.get("fecha_vencimiento"),
        };
        try {
          await api.crearLote(payload);
          toast("Lote registrado correctamente.", "success");
          closeModal();
          refreshCurrentView();
        } catch (err) { handleError(err); }
      });
    }
  });
}
