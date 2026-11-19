// ============================================================
// SITRAL — cliente de la API (FastAPI)
// Centraliza la URL base, el token JWT y el manejo de errores.
// Los nombres de endpoints y campos están alineados exactamente
// con los routers/esquemas reales del proyecto SITRAL_API.
// ============================================================

const DEFAULT_BASE = "http://127.0.0.1:8000";

export function getApiBase() {
  return localStorage.getItem("sitral_api_base") || DEFAULT_BASE;
}
export function setApiBase(url) {
  // Quita las "/" finales sin expresión regular (SonarCloud: regex con backtracking)
  let limpia = url.trim();
  while (limpia.endsWith("/")) limpia = limpia.slice(0, -1);
  localStorage.setItem("sitral_api_base", limpia);
}
export function getToken() {
  return localStorage.getItem("sitral_token");
}
export function getSession() {
  const raw = localStorage.getItem("sitral_session");
  return raw ? JSON.parse(raw) : null;
}
export function setSession(token, usuario) {
  localStorage.setItem("sitral_token", token);
  localStorage.setItem("sitral_session", JSON.stringify(usuario));
}
export function clearSession() {
  localStorage.removeItem("sitral_token");
  localStorage.removeItem("sitral_session");
}

// Mensajes amigables por código HTTP (coherentes con la sección
// "Validaciones y manejo de errores" de la documentación del proyecto).
const HTTP_MESSAGES = {
  400: "La operación no se pudo completar: revisa los datos ingresados o una regla de negocio no se cumple (por ejemplo, stock insuficiente o un dato duplicado).",
  401: "La sesión no es válida o expiró. Por favor, inicia sesión de nuevo.",
  403: "Tu rol no tiene permiso para realizar esta acción.",
  404: "El registro solicitado no existe o ya fue desactivado.",
  422: "Alguno de los campos no tiene un formato válido. Revisa fechas, números y campos obligatorios.",
  500: "Ocurrió un error inesperado en el servidor.",
};

export class ApiError extends Error {
  constructor(status, detail) {
    super(detail || HTTP_MESSAGES[status] || `Error ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const t = getToken();
    if (t) headers["Authorization"] = `Bearer ${t}`;
  }

  let res;
  try {
    res = await fetch(`${getApiBase()}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (networkErr) {
    throw new ApiError(
      0,
      "No se pudo conectar con la API. Verifica que el servidor (uvicorn) esté corriendo, que CORS esté habilitado y que la dirección configurada sea correcta."
    );
  }

  if (res.status === 204) return null;

  let data = null;
  const text = await res.text();
  if (text) {
    try { data = JSON.parse(text); } catch { data = text; }
  }

  if (!res.ok) {
    // FastAPI/Pydantic puede devolver detail como string o como lista de errores 422
    let detail = null;
    if (data && typeof data.detail === "string") detail = data.detail;
    else if (data && Array.isArray(data.detail)) {
      detail = data.detail.map(d => d.msg || JSON.stringify(d)).join(" · ");
    }
    if (res.status === 401) { clearSession(); }
    throw new ApiError(res.status, detail || HTTP_MESSAGES[res.status]);
  }
  return data;
}

function qs(params = {}) {
  const parts = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== "")
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`);
  return parts.length ? `?${parts.join("&")}` : "";
}

export const api = {
  // --- salud / conexión ---
  async ping() {
    try {
      const res = await fetch(`${getApiBase()}/`, { method: "GET" });
      return res.ok;
    } catch { return false; }
  },

  // --- auth (POST /auth/login → {usuario, password}) ---
  login: (usuario, password) =>
    request("/auth/login", { method: "POST", auth: false, body: { usuario, password } }),

  // --- usuarios (solo Administrador) ---
  listarUsuarios: () => request("/usuarios/"),
  crearUsuario: (data) => request("/usuarios/", { method: "POST", body: data }),
  actualizarUsuario: (id, data) => request(`/usuarios/${id}`, { method: "PUT", body: data }),
  cambiarEstadoUsuario: (id) => request(`/usuarios/${id}/estado`, { method: "PATCH" }),

  // --- proveedores ---
  listarProveedores: (filtros) => request(`/proveedores/${qs(filtros)}`),
  crearProveedor: (data) => request("/proveedores/", { method: "POST", body: data }),
  actualizarProveedor: (id, data) => request(`/proveedores/${id}`, { method: "PUT", body: data }),
  eliminarProveedor: (id) => request(`/proveedores/${id}`, { method: "DELETE" }),

  // --- medicamentos ---
  listarMedicamentos: (filtros) => request(`/medicamentos/${qs(filtros)}`),
  obtenerMedicamentoPorCodigo: (codigo) => request(`/medicamentos/codigo/${encodeURIComponent(codigo)}`),
  crearMedicamento: (data) => request("/medicamentos/", { method: "POST", body: data }),
  actualizarMedicamento: (id, data) => request(`/medicamentos/${id}`, { method: "PUT", body: data }),
  eliminarMedicamento: (id) => request(`/medicamentos/${id}`, { method: "DELETE" }),

  // --- lotes ---
  listarLotes: (filtros) => request(`/lotes/${qs(filtros)}`),
  crearLote: (data) => request("/lotes/", { method: "POST", body: data }),
  trazabilidadLote: (id) => request(`/lotes/${id}/trazabilidad`),

  // --- facturas ---
  listarFacturas: (filtros) => request(`/facturas/${qs(filtros)}`),
  crearFacturaEntrada: (data) => request("/facturas/entrada", { method: "POST", body: data }),
  crearFacturaSalida: (data) => request("/facturas/salida", { method: "POST", body: data }),
  anularFactura: (id) => request(`/facturas/${id}/anular`, { method: "PATCH" }),

  // --- alertas ---
  listarAlertas: (filtros) => request(`/alertas/${qs(filtros)}`),
  generarAlertas: () => request("/alertas/generar", { method: "POST" }),
  cambiarEstadoAlerta: (id, nuevoEstado) =>
    request(`/alertas/${id}/estado${qs({ nuevo_estado: nuevoEstado })}`, { method: "PATCH" }),
  obtenerConfiguracionAlertas: () => request("/alertas/configuracion"),
  actualizarUmbral: (data) => request("/alertas/configuracion", { method: "PUT", body: data }),

  // --- dashboard (solo Administrador) ---
  obtenerKpis: () => request("/dashboard/kpis"),
};
