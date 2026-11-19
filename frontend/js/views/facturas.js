import { api } from "../api.js";
import { toast, openModal, closeModal, handleError, canWrite, refreshCurrentView } from "../app.js";
import { openScanner, iScan } from "../scanner.js";

const WRITE_ROLES = ["ADMINISTRADOR", "FARMACEUTA"];
const ADMIN_ROLES = ["ADMINISTRADOR"];

let cache = [];
let tab = "TODAS";

export async function renderFacturas(root) {
  root.innerHTML = `
    <div class="panel">
      <div class="panel-head">
        <h2>Facturación</h2>
        <div class="actions">
          ${canWrite(WRITE_ROLES) ? `
            <button class="btn btn-ghost" id="btn-factura-entrada">+ Factura de entrada</button>
            <button class="btn btn-primary" id="btn-factura-salida">+ Factura de salida</button>
          ` : ""}
        </div>
      </div>
      <div class="toolbar">
        <span class="chip active" data-t="TODAS">Todas</span>
        <span class="chip" data-t="ENTRADA">Entrada (compras)</span>
        <span class="chip" data-t="SALIDA">Salida (ventas)</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>N.º factura</th><th>Tipo</th><th>Fecha</th><th>Total</th><th>Estado</th><th></th></tr></thead>
          <tbody id="fact-rows"><tr><td colspan="6" class="loading-state">Cargando…</td></tr></tbody>
        </table>
      </div>
    </div>
  `;

  root.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", () => {
      root.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      tab = chip.dataset.t;
      paint(root);
    });
  });

  if (canWrite(WRITE_ROLES)) {
    root.querySelector("#btn-factura-entrada").addEventListener("click", () => openEntradaForm());
    root.querySelector("#btn-factura-salida").addEventListener("click", () => openSalidaForm());
  }

  try {
    const data = await api.listarFacturas();
    cache = Array.isArray(data) ? data : [];
    paint(root);
  } catch (err) {
    handleError(err);
    root.querySelector("#fact-rows").innerHTML = `<tr><td colspan="6" class="empty-state">No se pudo cargar la facturación.</td></tr>`;
  }
}

function formatCOP(v) {
  if (v === undefined || v === null) return "—";
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(v);
}

function paint(root) {
  const body = root.querySelector("#fact-rows");
  const filtered = cache.filter(f => tab === "TODAS" || f.tipo === tab);
  if (!filtered.length) {
    body.innerHTML = `<tr><td colspan="6" class="empty-state">No hay facturas registradas.</td></tr>`;
    return;
  }
  body.innerHTML = filtered.map(f => {
    const esEntrada = f.tipo === "ENTRADA";
    const anulada = f.estado === "ANULADA";
    const fecha = f.fecha ? new Date(f.fecha).toLocaleString("es-CO") : "—";
    return `
      <tr>
        <td><strong>${f.numero_factura}</strong></td>
        <td><span class="badge ${esEntrada ? "badge-ok" : "badge-warn"}">${esEntrada ? "Entrada" : "Salida"}</span></td>
        <td>${fecha}</td>
        <td>${formatCOP(f.total)}</td>
        <td><span class="badge ${anulada ? "badge-danger" : "badge-ok"}">${f.estado}</span></td>
        <td>
          <div class="row-actions">
            ${canWrite(ADMIN_ROLES) && !anulada ? `<button class="btn btn-danger btn-sm" data-anular="${f.id_factura}">Anular</button>` : ""}
          </div>
        </td>
      </tr>`;
  }).join("");

  body.querySelectorAll("[data-anular]").forEach(btn => {
    btn.addEventListener("click", () => confirmAnular(btn.dataset.anular));
  });
}

function confirmAnular(id) {
  openModal(`
    <h3>Anular factura</h3>
    <p style="font-size:13.5px;color:var(--muted);">Esto revierte el efecto de la factura sobre el inventario (devuelve o descuenta las cantidades correspondientes) y queda registrado como un movimiento de ajuste.</p>
    <div class="modal-actions">
      <button type="button" class="btn btn-ghost" id="an-cancel">Cancelar</button>
      <button type="button" class="btn btn-danger" id="an-confirm">Anular factura</button>
    </div>
  `, {
    onMount: (box) => {
      box.querySelector("#an-cancel").addEventListener("click", closeModal);
      box.querySelector("#an-confirm").addEventListener("click", async () => {
        try {
          await api.anularFactura(id);
          toast("Factura anulada.", "success");
          closeModal();
          refreshCurrentView();
        } catch (err) { handleError(err); }
      });
    }
  });
}

// ---------------------------------------------------------------
// Factura de ENTRADA (compra): crea/alimenta lotes por cada renglón
// ---------------------------------------------------------------
async function openEntradaForm() {
  let medicamentos = [], proveedores = [];
  try {
    [medicamentos, proveedores] = await Promise.all([api.listarMedicamentos(), api.listarProveedores()]);
  } catch (err) { handleError(err); }
  medicamentos = Array.isArray(medicamentos) ? medicamentos : [];
  proveedores = Array.isArray(proveedores) ? proveedores : [];

  const today = new Date().toISOString().slice(0, 10);
  let rows = [{ id_medicamento: "", numero_lote: "", cantidad: "", precio_unitario: "", fecha_ingreso: today, fecha_vencimiento: "" }];

  const medOptions = medicamentos.map(m => `<option value="${m.id_medicamento}">${m.nombre}</option>`).join("");

  function rowsHtml() {
    return rows.map((r, i) => `
      <div data-row="${i}" style="border:1px solid var(--border);border-radius:10px;padding:12px;margin-bottom:10px;">
        <div class="form-grid" style="margin-bottom:10px;">
          <div class="field full">
            <label>Medicamento</label>
            <select data-f="id_medicamento" required>
              <option value="" disabled ${!r.id_medicamento ? "selected" : ""}>Selecciona…</option>
              ${medOptions}
            </select>
          </div>
          <div class="field">
            <label>Número de lote</label>
            <input data-f="numero_lote" required value="${r.numero_lote}" placeholder="LT-2026-0001">
          </div>
          <div class="field">
            <label>Cantidad</label>
            <input data-f="cantidad" type="number" min="1" required value="${r.cantidad}">
          </div>
          <div class="field">
            <label>Precio unit.</label>
            <input data-f="precio_unitario" type="number" min="0" required value="${r.precio_unitario}">
          </div>
          <div class="field">
            <label>Fecha ingreso</label>
            <input data-f="fecha_ingreso" type="date" required value="${r.fecha_ingreso}">
          </div>
          <div class="field">
            <label>Fecha vencimiento</label>
            <input data-f="fecha_vencimiento" type="date" required value="${r.fecha_vencimiento}">
          </div>
        </div>
        <button type="button" class="btn btn-ghost btn-sm" data-remove="${i}" ${rows.length === 1 ? "disabled" : ""}>✕ Quitar producto</button>
      </div>
    `).join("");
  }

  openModal(`
    <h3>Factura de entrada (compra)</h3>
    <form id="fact-form">
      <div class="form-grid" style="margin-bottom:12px;">
        <div class="field">
          <label>N.º de factura</label>
          <input name="numero_factura" required placeholder="FC-2026-001">
        </div>
        <div class="field">
          <label>Proveedor</label>
          <select name="id_proveedor" required>
            <option value="" disabled selected>Selecciona un proveedor…</option>
            ${proveedores.map(p => `<option value="${p.id_proveedor}">${p.nombre}</option>`).join("")}
          </select>
        </div>
      </div>
      <div id="fact-rows-box">${rowsHtml()}</div>
      <button type="button" class="btn btn-ghost btn-sm" id="fact-add-row">+ Agregar producto</button>
      <div class="modal-actions">
        <button type="button" class="btn btn-ghost" id="fact-cancel">Cancelar</button>
        <button type="submit" class="btn btn-primary">Guardar factura</button>
      </div>
    </form>
  `, {
    onMount: (box) => {
      const rowsBox = box.querySelector("#fact-rows-box");

      function syncRowsFromDom() {
        rowsBox.querySelectorAll("[data-row]").forEach((el, i) => {
          rows[i] = {
            id_medicamento: el.querySelector('[data-f="id_medicamento"]').value,
            numero_lote: el.querySelector('[data-f="numero_lote"]').value,
            cantidad: el.querySelector('[data-f="cantidad"]').value,
            precio_unitario: el.querySelector('[data-f="precio_unitario"]').value,
            fecha_ingreso: el.querySelector('[data-f="fecha_ingreso"]').value,
            fecha_vencimiento: el.querySelector('[data-f="fecha_vencimiento"]').value,
          };
        });
      }
      function wireRowEvents() {
        rowsBox.querySelectorAll("[data-remove]").forEach(btn => {
          btn.addEventListener("click", () => {
            syncRowsFromDom();
            rows.splice(Number(btn.dataset.remove), 1);
            rowsBox.innerHTML = rowsHtml();
            wireRowEvents();
          });
        });
      }
      wireRowEvents();

      box.querySelector("#fact-add-row").addEventListener("click", () => {
        syncRowsFromDom();
        rows.push({ id_medicamento: "", numero_lote: "", cantidad: "", precio_unitario: "", fecha_ingreso: today, fecha_vencimiento: "" });
        rowsBox.innerHTML = rowsHtml();
        wireRowEvents();
      });

      box.querySelector("#fact-cancel").addEventListener("click", closeModal);

      box.querySelector("#fact-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        syncRowsFromDom();
        const fd = new FormData(e.target);
        const payload = {
          id_proveedor: Number(fd.get("id_proveedor")),
          numero_factura: fd.get("numero_factura"),
          detalles: rows.map(r => ({
            id_medicamento: Number(r.id_medicamento),
            numero_lote: r.numero_lote,
            cantidad: Number(r.cantidad),
            precio_unitario: Number(r.precio_unitario),
            fecha_ingreso: r.fecha_ingreso,
            fecha_vencimiento: r.fecha_vencimiento,
          })),
        };
        try {
          await api.crearFacturaEntrada(payload);
          toast("Factura de entrada registrada.", "success");
          closeModal();
          refreshCurrentView();
        } catch (err) { handleError(err); }
      });
    }
  });
}

// ---------------------------------------------------------------
// Factura de SALIDA (venta): descuenta lotes existentes
// ---------------------------------------------------------------
async function openSalidaForm() {
  let lotes = [], medicamentos = [];
  try {
    [lotes, medicamentos] = await Promise.all([api.listarLotes(), api.listarMedicamentos()]);
  } catch (err) { handleError(err); }
  lotes = (Array.isArray(lotes) ? lotes : []).filter(l => (l.cantidad_disponible ?? 0) > 0);
  medicamentos = Array.isArray(medicamentos) ? medicamentos : (medicamentos?.items || []);

  let rows = [{ id_lote: "", cantidad: "", precio_unitario: "" }];
  const loteOptions = lotes.map(l =>
    `<option value="${l.id_lote}">${l.numero_lote} — ${l.medicamento_nombre || ""} (disp. ${l.cantidad_disponible})</option>`
  ).join("");

  function rowsHtml() {
    return rows.map((r, i) => `
      <div class="form-grid" data-row="${i}" style="grid-template-columns: 2fr 1fr 1fr auto; align-items:end; margin-bottom:10px;">
        <div class="field">
          <label>Lote</label>
          <select data-f="id_lote" required>
            <option value="" disabled ${!r.id_lote ? "selected" : ""}>Selecciona…</option>
            ${loteOptions}
          </select>
        </div>
        <div class="field">
          <label>Cantidad</label>
          <input data-f="cantidad" type="number" min="1" required value="${r.cantidad}">
        </div>
        <div class="field">
          <label>Precio unit. <span style="font-weight:400;color:var(--muted);">(opcional)</span></label>
          <input data-f="precio_unitario" type="number" min="0" value="${r.precio_unitario}" placeholder="Precio del catálogo">
        </div>
        <button type="button" class="btn btn-ghost btn-sm" data-remove="${i}" ${rows.length === 1 ? "disabled" : ""}>✕</button>
      </div>
    `).join("");
  }

  openModal(`
    <h3>Factura de salida (venta)</h3>
    <form id="fact-form">
      <div class="field full" style="margin-bottom:12px;">
        <label>N.º de factura</label>
        <input name="numero_factura" required placeholder="FV-2026-001">
      </div>
      <div id="fact-rows-box">${rowsHtml()}</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;">
        <button type="button" class="btn btn-ghost btn-sm" id="fact-add-row">+ Agregar producto</button>
        <button type="button" class="btn btn-ghost btn-sm" id="fact-scan-producto">${iScan()} Escanear producto</button>
      </div>
      <p style="font-size:12px;color:var(--muted);margin-top:8px;">Si dejas el precio unitario en blanco, se usa el precio actual del medicamento en el catálogo. Al escanear un producto, se selecciona automáticamente el lote con existencias más próximo a vencer.</p>
      <div class="modal-actions">
        <button type="button" class="btn btn-ghost" id="fact-cancel">Cancelar</button>
        <button type="submit" class="btn btn-primary">Guardar factura</button>
      </div>
    </form>
  `, {
    onMount: (box) => {
      const rowsBox = box.querySelector("#fact-rows-box");

      function syncRowsFromDom() {
        rowsBox.querySelectorAll("[data-row]").forEach((el, i) => {
          rows[i] = {
            id_lote: el.querySelector('[data-f="id_lote"]').value,
            cantidad: el.querySelector('[data-f="cantidad"]').value,
            precio_unitario: el.querySelector('[data-f="precio_unitario"]').value,
          };
        });
      }
      function wireRowEvents() {
        rowsBox.querySelectorAll("[data-remove]").forEach(btn => {
          btn.addEventListener("click", () => {
            syncRowsFromDom();
            rows.splice(Number(btn.dataset.remove), 1);
            rowsBox.innerHTML = rowsHtml();
            wireRowEvents();
          });
        });
      }
      wireRowEvents();

      box.querySelector("#fact-add-row").addEventListener("click", () => {
        syncRowsFromDom();
        rows.push({ id_lote: "", cantidad: "", precio_unitario: "" });
        rowsBox.innerHTML = rowsHtml();
        wireRowEvents();
      });

      box.querySelector("#fact-scan-producto").addEventListener("click", () => {
        openScanner({
          title: "Escanear producto",
          hint: "Escanea el código de barras del medicamento; se elegirá automáticamente el lote con existencias más próximo a vencer (FEFO).",
          onDetected: (code) => {
            const med = medicamentos.find(m => (m.codigo_barras || "").toLowerCase() === code.toLowerCase());
            if (!med) { toast("No se encontró un medicamento con ese código de barras.", "error"); return; }
            const candidatos = lotes
              .filter(l => l.id_medicamento === med.id_medicamento)
              .slice()
              .sort((a, b) => new Date(a.fecha_vencimiento) - new Date(b.fecha_vencimiento));
            if (!candidatos.length) { toast(`"${med.nombre}" no tiene lotes con existencias disponibles.`, "error"); return; }
            const elegido = candidatos[0];
            syncRowsFromDom();
            let idx = rows.findIndex(r => !r.id_lote);
            if (idx === -1) { rows.push({ id_lote: "", cantidad: "", precio_unitario: "" }); idx = rows.length - 1; }
            rows[idx].id_lote = String(elegido.id_lote);
            if (!rows[idx].cantidad) rows[idx].cantidad = "1";
            rowsBox.innerHTML = rowsHtml();
            wireRowEvents();
            toast(`Lote seleccionado: ${elegido.numero_lote} — ${med.nombre}`, "success");
          },
        });
      });

      box.querySelector("#fact-cancel").addEventListener("click", closeModal);

      box.querySelector("#fact-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        syncRowsFromDom();
        const fd = new FormData(e.target);
        const payload = {
          numero_factura: fd.get("numero_factura"),
          detalles: rows.map(r => ({
            id_lote: Number(r.id_lote),
            cantidad: Number(r.cantidad),
            ...(r.precio_unitario ? { precio_unitario: Number(r.precio_unitario) } : {}),
          })),
        };
        try {
          await api.crearFacturaSalida(payload);
          toast("Factura de salida registrada.", "success");
          closeModal();
          refreshCurrentView();
        } catch (err) { handleError(err); }
      });
    }
  });
}
