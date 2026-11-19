// ============================================================
// SITRAL — shell de la aplicación: enrutamiento, sesión, UI común
// ============================================================
import { api, getApiBase, setApiBase, getSession, setSession, clearSession, ApiError } from "./api.js";

import { renderDashboard } from "./views/dashboard.js";
import { renderMedicamentos } from "./views/medicamentos.js";
import { renderProveedores } from "./views/proveedores.js";
import { renderLotes } from "./views/lotes.js";
import { renderFacturas } from "./views/facturas.js";
import { renderAlertas } from "./views/alertas.js";
import { renderUsuarios } from "./views/usuarios.js";

// ---------- navegación (icono SVG, etiqueta, vista, roles permitidos) ----------
const NAV = [
  { id: "dashboard", label: "Dashboard", view: renderDashboard, roles: ["ADMINISTRADOR"], icon: iHome() },
  { id: "lotes", label: "Lotes", view: renderLotes, roles: ["ADMINISTRADOR", "FARMACEUTA"], icon: iBox() },
  { id: "medicamentos", label: "Medicamentos", view: renderMedicamentos, roles: ["ADMINISTRADOR", "FARMACEUTA"], icon: iPill() },
  { id: "proveedores", label: "Proveedores", view: renderProveedores, roles: ["ADMINISTRADOR", "FARMACEUTA"], icon: iTruck() },
  { id: "facturas", label: "Facturación", view: renderFacturas, roles: ["ADMINISTRADOR", "FARMACEUTA"], icon: iReceipt() },
  { id: "alertas", label: "Alertas", view: renderAlertas, roles: ["ADMINISTRADOR", "FARMACEUTA"], icon: iBell() },
  { id: "usuarios", label: "Usuarios", view: renderUsuarios, roles: ["ADMINISTRADOR"], icon: iUsers() },
];

function iHome(){ return `<svg width="17" height="17" viewBox="0 0 24 24" fill="none"><path d="M4 11.5L12 4l8 7.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M6 10v9h12v-9" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>`; }
function iBox(){ return `<svg width="17" height="17" viewBox="0 0 24 24" fill="none"><path d="M3 8l9-5 9 5-9 5-9-5z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M3 8v8l9 5 9-5V8" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M12 13v8" stroke="currentColor" stroke-width="1.8"/></svg>`; }
function iPill(){ return `<svg width="17" height="17" viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="18" height="18" rx="5" stroke="currentColor" stroke-width="1.8"/><path d="M8 8l8 8M8 8v8h8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>`; }
function iTruck(){ return `<svg width="17" height="17" viewBox="0 0 24 24" fill="none"><path d="M3 7h11v9H3V7z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M14 10h4l3 3v3h-7v-6z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><circle cx="7" cy="17" r="1.6" stroke="currentColor" stroke-width="1.6"/><circle cx="17.5" cy="17" r="1.6" stroke="currentColor" stroke-width="1.6"/></svg>`; }
function iReceipt(){ return `<svg width="17" height="17" viewBox="0 0 24 24" fill="none"><path d="M6 3h12v18l-3-2-3 2-3-2-3 2V3z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M9 8h6M9 12h6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>`; }
function iBell(){ return `<svg width="17" height="17" viewBox="0 0 24 24" fill="none"><path d="M6 10a6 6 0 1112 0c0 4 1.5 5.5 1.5 5.5H4.5S6 14 6 10z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M9.5 18a2.5 2.5 0 005 0" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>`; }
function iUsers(){ return `<svg width="17" height="17" viewBox="0 0 24 24" fill="none"><circle cx="9" cy="8" r="3.2" stroke="currentColor" stroke-width="1.8"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="17.5" cy="9" r="2.4" stroke="currentColor" stroke-width="1.6"/><path d="M15.8 14.2c2.6.4 4.2 2.4 4.2 5.8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>`; }

// ---------- utilidades de UI globales ----------
export function toast(message, type = "default") {
  const stack = document.getElementById("toast-stack");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  stack.appendChild(el);
  setTimeout(() => el.remove(), 3800);
}

export function openModal(html, { onMount } = {}) {
  const backdrop = document.getElementById("modal-backdrop");
  const box = document.getElementById("modal-box");
  box.innerHTML = html;
  backdrop.hidden = false;
  if (onMount) onMount(box);
  const clickClose = (e) => { if (e.target === backdrop) closeModal(); };
  const escClose = (e) => { if (e.key === "Escape") closeModal(); };
  backdrop.addEventListener("click", clickClose, { once: true });
  document.addEventListener("keydown", escClose, { once: true });
}
export function closeModal() {
  document.getElementById("modal-backdrop").hidden = true;
  document.getElementById("modal-box").innerHTML = "";
}

export function handleError(err) {
  if (err instanceof ApiError) {
    toast(err.message, "error");
    if (err.status === 401) { logout(); }
  } else {
    toast("Ocurrió un error inesperado.", "error");
    console.error(err);
  }
}

export function currentRole() {
  const s = getSession();
  return s ? s.rol : null;
}
export function canWrite(moduleRoles) {
  const role = currentRole();
  return moduleRoles.includes(role);
}

// ---------- estado de ruta ----------
let activeId = null;

function setActiveView(id) {
  const item = NAV.find(n => n.id === id) || NAV[0];
  activeId = item.id;
  document.getElementById("page-title").textContent = item.label;

  document.querySelectorAll(".nav-item").forEach(el => el.classList.toggle("active", el.dataset.id === item.id));
  document.querySelectorAll(".bottom-item").forEach(el => el.classList.toggle("active", el.dataset.id === item.id));

  const root = document.getElementById("view-root");
  root.innerHTML = `<div class="loading-state">Cargando…</div>`;
  Promise.resolve(item.view(root)).catch(handleError);

  closeSidebar();
  location.hash = `#${item.id}`;
}

function navItemsForRole() {
  const role = currentRole();
  return NAV.filter(n => n.roles.includes(role));
}

function renderNav() {
  const items = navItemsForRole();
  const sideNav = document.getElementById("sidebar-nav");
  sideNav.innerHTML = items.map(n => `
    <button class="nav-item" data-id="${n.id}">${n.icon}<span>${n.label}</span></button>
  `).join("");
  sideNav.querySelectorAll(".nav-item").forEach(btn => {
    btn.addEventListener("click", () => setActiveView(btn.dataset.id));
  });

  // bottom nav: máximo 4 accesos directos + el resto queda accesible desde el sidebar en escritorio
  const bottom = document.getElementById("bottom-nav");
  const quick = items.slice(0, 4);
  bottom.innerHTML = quick.map(n => `
    <button class="bottom-item" data-id="${n.id}">${n.icon}<span>${n.label}</span></button>
  `).join("");
  bottom.querySelectorAll(".bottom-item").forEach(btn => {
    btn.addEventListener("click", () => setActiveView(btn.dataset.id));
  });
}

function closeSidebar() {
  document.getElementById("sidebar").classList.remove("open");
  document.getElementById("sidebar-scrim").classList.remove("open");
}

// ---------- sesión / login ----------
function showApp(session) {
  document.getElementById("login-screen").hidden = true;
  document.getElementById("app-shell").hidden = false;

  document.getElementById("user-name").textContent = session.nombre || session.usuario;
  document.getElementById("user-role").textContent = session.rol;
  const initials = (session.nombre || session.usuario || "??").split(" ").map(w => w[0]).slice(0, 2).join("").toUpperCase();
  document.getElementById("user-avatar").textContent = initials;

  renderNav();
  const items = navItemsForRole();
  setActiveView(items[0]?.id);
  void checkConnection(); // promesa ignorada a propósito: solo actualiza el indicador
}

function showLogin() {
  document.getElementById("login-screen").hidden = false;
  document.getElementById("app-shell").hidden = true;
}

function logout() {
  clearSession();
  showLogin();
}

async function checkConnection() {
  const ok = await api.ping();
  document.getElementById("conn-dot").className = `dot ${ok ? "ok" : "err"}`;
  document.getElementById("conn-text").textContent = ok
    ? "Conectado a la API"
    : "Sin conexión con la API";
}

// ---------- init ----------
function init() {
  document.getElementById("f-apibase").value = getApiBase();

  document.getElementById("save-apibase").addEventListener("click", () => {
    const val = document.getElementById("f-apibase").value.trim();
    if (val) { setApiBase(val); toast("Dirección guardada.", "success"); }
  });

  document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const usuario = document.getElementById("f-usuario").value.trim();
    const clave = document.getElementById("f-clave").value;
    const errBox = document.getElementById("login-error");
    const submitBtn = document.getElementById("login-submit");
    errBox.hidden = true;
    submitBtn.disabled = true;
    submitBtn.textContent = "Ingresando…";
    try {
      const resp = await api.login(usuario, clave);
      const session = {
        usuario: resp.usuario || usuario,
        nombre: resp.nombre || resp.nombre_completo || usuario,
        rol: resp.rol,
      };
      setSession(resp.access_token, session);
      showApp(session);
    } catch (err) {
      errBox.textContent = err instanceof ApiError ? err.message : "No se pudo iniciar sesión.";
      errBox.hidden = false;
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Ingresar";
    }
  });

  document.getElementById("logout-btn").addEventListener("click", logout);
  document.getElementById("menu-toggle").addEventListener("click", () => {
    document.getElementById("sidebar").classList.toggle("open");
    document.getElementById("sidebar-scrim").classList.toggle("open");
  });
  document.getElementById("sidebar-scrim").addEventListener("click", closeSidebar);

  const existing = getSession();
  if (existing) { showApp(existing); } else { showLogin(); }
}

document.addEventListener("DOMContentLoaded", init);

// se exponen para que las vistas puedan re-renderizar la actual tras una acción
export function refreshCurrentView() { if (activeId) setActiveView(activeId); }
