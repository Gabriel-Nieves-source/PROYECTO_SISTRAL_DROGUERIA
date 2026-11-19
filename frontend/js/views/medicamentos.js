import { api } from "../api.js";
import { toast, openModal, closeModal, handleError, canWrite, refreshCurrentView } from "../app.js";
import { openScanner, iScan } from "../scanner.js";

const WRITE_ROLES = ["ADMINISTRADOR", "FARMACEUTA"]; // registrar
const EDIT_ROLES = ["ADMINISTRADOR"]; // modificar / eliminar

let cache = [];
let search = "";

export async function renderMedicamentos(root) {
  root.innerHTML = `
    <div class="panel">
      <div class="panel-head">
        <h2>Catálogo de medicamentos</h2>
        <div class="actions">
          ${canWrite(WRITE_ROLES) ? `<button class="btn btn-primary" id="btn-nuevo-med">+ Nuevo medicamento</button>` : ""}
        </div>
      </div>
      <div class="toolbar">
        <div class="search-box">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><circle cx="11" cy="11" r="7" stroke="#9CA3AF" stroke-width="1.8"/><path d="M21 21l-4.3-4.3" stroke="#9CA3AF" stroke-width="1.8" stroke-linecap="round"/></svg>
          <input type="text" id="med-search" placeholder="Buscar por nombre o código de barras…">
          <button type="button" class="scan-btn" id="med-scan-btn" title="Escanear código de barras">${iScan()}</button>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Nombre</th><th>Presentación</th><th>Concentración</th><th>Código de barras</th><th>Precio</th><th>Estado</th><th></th></tr></thead>
          <tbody id="med-rows"><tr><td colspan="7" class="loading-state">Cargando…</td></tr></tbody>
        </table>
      </div>
    </div>
  `;

  root.querySelector("#med-search").addEventListener("input", (e) => {
    search = e.target.value.toLowerCase();
    paint(root);
  });
  root.querySelector("#med-scan-btn").addEventListener("click", () => {
    openScanner({
      title: "Escanear código de barras",
      hint: "Apunta la cámara al código de barras del medicamento para buscarlo en el catálogo.",
      onDetected: (code) => {
        root.querySelector("#med-search").value = code;
        search = code.toLowerCase();
        paint(root);
        const found = cache.find(m => (m.codigo_barras || "").toLowerCase() === search);
        toast(
          found ? `Medicamento encontrado: ${found.nombre}` : "No hay ningún medicamento en el catálogo con ese código.",
          found ? "success" : "default"
        );
      },
    });
  });
  if (canWrite(WRITE_ROLES)) {
    root.querySelector("#btn-nuevo-med").addEventListener("click", () => openForm());
  }

  try {
    const data = await api.listarMedicamentos();
    cache = Array.isArray(data) ? data : (data?.items || []);
    paint(root);
  } catch (err) {
    handleError(err);
    root.querySelector("#med-rows").innerHTML = `<tr><td colspan="6" class="empty-state">No se pudo cargar el catálogo.</td></tr>`;
  }
}

function paint(root) {
  const body = root.querySelector("#med-rows");
  const filtered = cache.filter(m =>
    !search || (m.nombre || "").toLowerCase().includes(search) || (m.codigo_barras || "").toLowerCase().includes(search)
  );
  if (!filtered.length) {
    body.innerHTML = `<tr><td colspan="7" class="empty-state">No se encontraron medicamentos.</td></tr>`;
    return;
  }
  body.innerHTML = filtered.map(m => `
    <tr>
      <td><strong>${m.nombre}</strong></td>
      <td>${m.presentacion || "—"}</td>
      <td>${m.concentracion || "—"}</td>
      <td>${m.codigo_barras || "—"}</td>
      <td>${formatCOP(m.precio)}</td>
      <td><span class="badge ${m.estado === "INACTIVO" ? "badge-muted" : "badge-ok"}">${m.estado || "ACTIVO"}</span></td>
      <td>
        <div class="row-actions">
          ${canWrite(EDIT_ROLES) ? `
            <button class="btn btn-ghost btn-sm" data-edit="${m.id_medicamento}">Editar</button>
            <button class="btn btn-danger btn-sm" data-del="${m.id_medicamento}">Desactivar</button>
          ` : ""}
        </div>
      </td>
    </tr>
  `).join("");

  body.querySelectorAll("[data-edit]").forEach(btn => {
    btn.addEventListener("click", () => {
      const m = cache.find(x => String(x.id_medicamento) === btn.dataset.edit);
      openForm(m);
    });
  });
  body.querySelectorAll("[data-del]").forEach(btn => {
    btn.addEventListener("click", () => confirmDelete(btn.dataset.del));
  });
}

function formatCOP(v) {
  if (v === undefined || v === null) return "—";
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(v);
}

function openForm(m = null) {
  const isEdit = !!m;
  openModal(`
    <h3>${isEdit ? "Editar medicamento" : "Nuevo medicamento"}</h3>
    <form id="med-form" class="form-grid">
      <div class="field full">
        <label>Nombre</label>
        <input name="nombre" required value="${m?.nombre || ""}">
      </div>
      <div class="field">
        <label>Presentación</label>
        <input name="presentacion" value="${m?.presentacion || ""}">
      </div>
      <div class="field">
        <label>Concentración</label>
        <input name="concentracion" value="${m?.concentracion || ""}">
      </div>
      <div class="field">
        <label>Código de barras</label>
        <div class="field-with-scan">
          <input name="codigo_barras" id="med-form-codigo" value="${m?.codigo_barras || ""}">
          <button type="button" class="btn btn-ghost btn-sm" id="med-form-scan" title="Escanear código de barras">${iScan()}</button>
        </div>
      </div>
      <div class="field">
        <label>Precio (COP)</label>
        <input name="precio" type="number" min="0" step="1" required value="${m?.precio ?? ""}">
      </div>
      <div class="field">
        <label>Estado</label>
        <select name="estado">
          <option value="ACTIVO" ${!m || m.estado === "ACTIVO" ? "selected" : ""}>ACTIVO</option>
          <option value="INACTIVO" ${m?.estado === "INACTIVO" ? "selected" : ""}>INACTIVO</option>
        </select>
      </div>
      <div class="modal-actions full" style="grid-column:1/-1">
        <button type="button" class="btn btn-ghost" id="med-cancel">Cancelar</button>
        <button type="submit" class="btn btn-primary">${isEdit ? "Guardar cambios" : "Crear medicamento"}</button>
      </div>
    </form>
  `, {
    onMount: (box) => {
      box.querySelector("#med-cancel").addEventListener("click", closeModal);
      box.querySelector("#med-form-scan").addEventListener("click", () => {
        openScanner({
          title: "Escanear código de barras",
          hint: "Apunta la cámara al código de barras del empaque del medicamento.",
          onDetected: (code) => { box.querySelector("#med-form-codigo").value = code; },
        });
      });
      box.querySelector("#med-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const payload = {
          nombre: fd.get("nombre"),
          presentacion: fd.get("presentacion") || null,
          concentracion: fd.get("concentracion") || null,
          codigo_barras: fd.get("codigo_barras") || null,
          precio: Number(fd.get("precio")),
          estado: fd.get("estado"),
        };
        try {
          if (isEdit) {
            await api.actualizarMedicamento(m.id_medicamento, payload);
            toast("Medicamento actualizado.", "success");
          } else {
            await api.crearMedicamento(payload);
            toast("Medicamento creado.", "success");
          }
          closeModal();
          refreshCurrentView();
        } catch (err) {
          handleError(err);
        }
      });
    }
  });
}

function confirmDelete(id) {
  openModal(`
    <h3>Desactivar medicamento</h3>
    <p style="font-size:13.5px;color:var(--muted);">Esta acción cambia su estado a INACTIVO; no se elimina físicamente, para preservar la trazabilidad de sus lotes y facturas.</p>
    <div class="modal-actions">
      <button type="button" class="btn btn-ghost" id="del-cancel">Cancelar</button>
      <button type="button" class="btn btn-danger" id="del-confirm">Desactivar</button>
    </div>
  `, {
    onMount: (box) => {
      box.querySelector("#del-cancel").addEventListener("click", closeModal);
      box.querySelector("#del-confirm").addEventListener("click", async () => {
        try {
          await api.eliminarMedicamento(id);
          toast("Medicamento desactivado.", "success");
          closeModal();
          refreshCurrentView();
        } catch (err) { handleError(err); }
      });
    }
  });
}
