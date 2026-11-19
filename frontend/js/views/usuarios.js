import { api } from "../api.js";
import { toast, openModal, closeModal, handleError, refreshCurrentView } from "../app.js";

// id_rol según los datos iniciales de SITRAL.sql: 1 = ADMINISTRADOR, 2 = FARMACEUTA.
const ROLES = [
  { id: 1, nombre: "Administrador" },
  { id: 2, nombre: "Farmaceuta" },
];
function nombreRol(id_rol) {
  return ROLES.find(r => r.id === Number(id_rol))?.nombre || `Rol #${id_rol}`;
}

let cache = [];

export async function renderUsuarios(root) {
  root.innerHTML = `
    <div class="panel">
      <div class="panel-head">
        <h2>Usuarios del sistema</h2>
        <div class="actions">
          <button class="btn btn-primary" id="btn-nuevo-user">+ Nuevo usuario</button>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Nombre</th><th>Usuario</th><th>Rol</th><th>Estado</th><th></th></tr></thead>
          <tbody id="user-rows"><tr><td colspan="5" class="loading-state">Cargando…</td></tr></tbody>
        </table>
      </div>
    </div>
  `;

  root.querySelector("#btn-nuevo-user").addEventListener("click", () => openForm());

  try {
    const data = await api.listarUsuarios();
    cache = Array.isArray(data) ? data : [];
    paint(root);
  } catch (err) {
    handleError(err);
    root.querySelector("#user-rows").innerHTML = `<tr><td colspan="5" class="empty-state">No se pudo cargar la lista de usuarios.</td></tr>`;
  }
}

function paint(root) {
  const body = root.querySelector("#user-rows");
  if (!cache.length) {
    body.innerHTML = `<tr><td colspan="5" class="empty-state">No hay usuarios registrados.</td></tr>`;
    return;
  }
  body.innerHTML = cache.map(u => `
    <tr>
      <td><strong>${u.nombre}${u.apellido ? " " + u.apellido : ""}</strong></td>
      <td>${u.usuario}</td>
      <td><span class="badge ${Number(u.id_rol) === 1 ? "badge-ok" : "badge-warn"}">${nombreRol(u.id_rol)}</span></td>
      <td><span class="badge ${u.estado === "INACTIVO" ? "badge-muted" : "badge-ok"}">${u.estado}</span></td>
      <td>
        <div class="row-actions">
          <button class="btn btn-ghost btn-sm" data-edit="${u.id_usuario}">Editar</button>
          <button class="btn ${u.estado === "INACTIVO" ? "btn-ghost" : "btn-danger"} btn-sm" data-toggle="${u.id_usuario}">
            ${u.estado === "INACTIVO" ? "Activar" : "Desactivar"}
          </button>
        </div>
      </td>
    </tr>
  `).join("");

  body.querySelectorAll("[data-edit]").forEach(btn => {
    btn.addEventListener("click", () => {
      const u = cache.find(x => String(x.id_usuario) === btn.dataset.edit);
      openForm(u);
    });
  });
  body.querySelectorAll("[data-toggle]").forEach(btn => {
    btn.addEventListener("click", () => confirmToggle(btn.dataset.toggle));
  });
}

function openForm(u = null) {
  const isEdit = !!u;
  openModal(`
    <h3>${isEdit ? "Editar usuario" : "Nuevo usuario"}</h3>
    <form id="user-form" class="form-grid">
      <div class="field">
        <label>Nombre</label>
        <input name="nombre" required value="${u?.nombre || ""}">
      </div>
      <div class="field">
        <label>Apellido</label>
        <input name="apellido" value="${u?.apellido || ""}">
      </div>
      <div class="field">
        <label>Usuario</label>
        <input name="usuario" required value="${u?.usuario || ""}">
      </div>
      <div class="field">
        <label>Rol</label>
        <select name="id_rol">
          ${ROLES.map(r => `<option value="${r.id}" ${u ? (Number(u.id_rol) === r.id ? "selected" : "") : (r.id === 2 ? "selected" : "")}>${r.nombre}</option>`).join("")}
        </select>
      </div>
      <div class="field full">
        <label>${isEdit ? "Nueva contraseña (déjalo en blanco para no cambiarla)" : "Contraseña inicial"}</label>
        <input name="password" type="password" ${isEdit ? "" : "required"} minlength="6">
      </div>
      <div class="modal-actions" style="grid-column:1/-1">
        <button type="button" class="btn btn-ghost" id="user-cancel">Cancelar</button>
        <button type="submit" class="btn btn-primary">${isEdit ? "Guardar cambios" : "Crear usuario"}</button>
      </div>
    </form>
  `, {
    onMount: (box) => {
      box.querySelector("#user-cancel").addEventListener("click", closeModal);
      box.querySelector("#user-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const password = fd.get("password");
        try {
          if (isEdit) {
            const payload = {
              nombre: fd.get("nombre"),
              apellido: fd.get("apellido") || null,
              usuario: fd.get("usuario"),
              id_rol: Number(fd.get("id_rol")),
            };
            if (password) payload.password = password;
            await api.actualizarUsuario(u.id_usuario, payload);
            toast("Usuario actualizado.", "success");
          } else {
            await api.crearUsuario({
              nombre: fd.get("nombre"),
              apellido: fd.get("apellido") || null,
              usuario: fd.get("usuario"),
              id_rol: Number(fd.get("id_rol")),
              password,
            });
            toast("Usuario creado.", "success");
          }
          closeModal();
          refreshCurrentView();
        } catch (err) { handleError(err); }
      });
    }
  });
}

function confirmToggle(id) {
  const u = cache.find(x => String(x.id_usuario) === String(id));
  const activar = u?.estado === "INACTIVO";
  openModal(`
    <h3>${activar ? "Activar" : "Desactivar"} usuario</h3>
    <p style="font-size:13.5px;color:var(--muted);">
      ${activar
        ? "El usuario podrá volver a iniciar sesión."
        : "El usuario no podrá iniciar sesión, pero su historial de operaciones se conserva."}
    </p>
    <div class="modal-actions">
      <button type="button" class="btn btn-ghost" id="tg-cancel">Cancelar</button>
      <button type="button" class="btn ${activar ? "btn-primary" : "btn-danger"}" id="tg-confirm">${activar ? "Activar" : "Desactivar"}</button>
    </div>
  `, {
    onMount: (box) => {
      box.querySelector("#tg-cancel").addEventListener("click", closeModal);
      box.querySelector("#tg-confirm").addEventListener("click", async () => {
        try {
          await api.cambiarEstadoUsuario(id);
          toast(`Usuario ${activar ? "activado" : "desactivado"}.`, "success");
          closeModal();
          refreshCurrentView();
        } catch (err) { handleError(err); }
      });
    }
  });
}
