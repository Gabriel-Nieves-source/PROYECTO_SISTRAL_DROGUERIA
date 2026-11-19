import { api } from "../api.js";
import { toast, openModal, closeModal, handleError, canWrite, refreshCurrentView } from "../app.js";

const WRITE_ROLES = ["ADMINISTRADOR", "FARMACEUTA"];
const EDIT_ROLES = ["ADMINISTRADOR"];

let cache = [];
let search = "";

export async function renderProveedores(root) {
  root.innerHTML = `
    <div class="panel">
      <div class="panel-head">
        <h2>Proveedores</h2>
        <div class="actions">
          ${canWrite(WRITE_ROLES) ? `<button class="btn btn-primary" id="btn-nuevo-prov">+ Nuevo proveedor</button>` : ""}
        </div>
      </div>
      <div class="toolbar">
        <div class="search-box">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><circle cx="11" cy="11" r="7" stroke="#9CA3AF" stroke-width="1.8"/><path d="M21 21l-4.3-4.3" stroke="#9CA3AF" stroke-width="1.8" stroke-linecap="round"/></svg>
          <input type="text" id="prov-search" placeholder="Buscar por nombre o NIT…">
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Nombre</th><th>NIT</th><th>Teléfono</th><th>Correo</th><th>Dirección</th><th>Estado</th><th></th></tr></thead>
          <tbody id="prov-rows"><tr><td colspan="7" class="loading-state">Cargando…</td></tr></tbody>
        </table>
      </div>
    </div>
  `;

  root.querySelector("#prov-search").addEventListener("input", (e) => {
    search = e.target.value.toLowerCase();
    paint(root);
  });
  if (canWrite(WRITE_ROLES)) {
    root.querySelector("#btn-nuevo-prov").addEventListener("click", () => openForm());
  }

  try {
    const data = await api.listarProveedores();
    cache = Array.isArray(data) ? data : (data?.items || []);
    paint(root);
  } catch (err) {
    handleError(err);
    root.querySelector("#prov-rows").innerHTML = `<tr><td colspan="6" class="empty-state">No se pudo cargar los proveedores.</td></tr>`;
  }
}

function paint(root) {
  const body = root.querySelector("#prov-rows");
  const filtered = cache.filter(p =>
    !search || (p.nombre || "").toLowerCase().includes(search) || (p.nit || "").toLowerCase().includes(search)
  );
  if (!filtered.length) {
    body.innerHTML = `<tr><td colspan="7" class="empty-state">No se encontraron proveedores.</td></tr>`;
    return;
  }
  body.innerHTML = filtered.map(p => `
    <tr>
      <td><strong>${p.nombre}</strong></td>
      <td>${p.nit || "—"}</td>
      <td>${p.telefono || "—"}</td>
      <td>${p.correo || "—"}</td>
      <td>${p.direccion || "—"}</td>
      <td><span class="badge ${p.estado === "INACTIVO" ? "badge-muted" : "badge-ok"}">${p.estado || "ACTIVO"}</span></td>
      <td>
        <div class="row-actions">
          ${canWrite(EDIT_ROLES) ? `
            <button class="btn btn-ghost btn-sm" data-edit="${p.id_proveedor}">Editar</button>
            <button class="btn btn-danger btn-sm" data-del="${p.id_proveedor}">Desactivar</button>
          ` : ""}
        </div>
      </td>
    </tr>
  `).join("");

  body.querySelectorAll("[data-edit]").forEach(btn => {
    btn.addEventListener("click", () => {
      const p = cache.find(x => String(x.id_proveedor) === btn.dataset.edit);
      openForm(p);
    });
  });
  body.querySelectorAll("[data-del]").forEach(btn => {
    btn.addEventListener("click", () => confirmDelete(btn.dataset.del));
  });
}

function openForm(p = null) {
  const isEdit = !!p;
  openModal(`
    <h3>${isEdit ? "Editar proveedor" : "Nuevo proveedor"}</h3>
    <form id="prov-form" class="form-grid">
      <div class="field full">
        <label>Nombre / razón social</label>
        <input name="nombre" required value="${p?.nombre || ""}">
      </div>
      <div class="field">
        <label>NIT</label>
        <input name="nit" required value="${p?.nit || ""}">
      </div>
      <div class="field">
        <label>Teléfono</label>
        <input name="telefono" value="${p?.telefono || ""}">
      </div>
      <div class="field">
        <label>Correo</label>
        <input name="correo" type="email" value="${p?.correo || ""}">
      </div>
      <div class="field full">
        <label>Dirección</label>
        <input name="direccion" value="${p?.direccion || ""}">
      </div>
      <div class="field">
        <label>Estado</label>
        <select name="estado">
          <option value="ACTIVO" ${!p || p.estado === "ACTIVO" ? "selected" : ""}>ACTIVO</option>
          <option value="INACTIVO" ${p?.estado === "INACTIVO" ? "selected" : ""}>INACTIVO</option>
        </select>
      </div>
      <div class="modal-actions" style="grid-column:1/-1">
        <button type="button" class="btn btn-ghost" id="prov-cancel">Cancelar</button>
        <button type="submit" class="btn btn-primary">${isEdit ? "Guardar cambios" : "Crear proveedor"}</button>
      </div>
    </form>
  `, {
    onMount: (box) => {
      box.querySelector("#prov-cancel").addEventListener("click", closeModal);
      box.querySelector("#prov-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const payload = {
          nombre: fd.get("nombre"),
          nit: fd.get("nit"),
          telefono: fd.get("telefono") || null,
          correo: fd.get("correo") || null,
          direccion: fd.get("direccion") || null,
          estado: fd.get("estado"),
        };
        try {
          if (isEdit) {
            await api.actualizarProveedor(p.id_proveedor, payload);
            toast("Proveedor actualizado.", "success");
          } else {
            await api.crearProveedor(payload);
            toast("Proveedor creado.", "success");
          }
          closeModal();
          refreshCurrentView();
        } catch (err) { handleError(err); }
      });
    }
  });
}

function confirmDelete(id) {
  openModal(`
    <h3>Desactivar proveedor</h3>
    <p style="font-size:13.5px;color:var(--muted);">Esta acción cambia su estado a INACTIVO; sus lotes y facturas históricas no se ven afectados.</p>
    <div class="modal-actions">
      <button type="button" class="btn btn-ghost" id="del-cancel">Cancelar</button>
      <button type="button" class="btn btn-danger" id="del-confirm">Desactivar</button>
    </div>
  `, {
    onMount: (box) => {
      box.querySelector("#del-cancel").addEventListener("click", closeModal);
      box.querySelector("#del-confirm").addEventListener("click", async () => {
        try {
          await api.eliminarProveedor(id);
          toast("Proveedor desactivado.", "success");
          closeModal();
          refreshCurrentView();
        } catch (err) { handleError(err); }
      });
    }
  });
}
