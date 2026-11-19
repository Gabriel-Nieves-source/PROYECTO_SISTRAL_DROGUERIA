// ============================================================
// SITRAL — lector de códigos QR y de barras con la cámara del
// dispositivo (computador o celular).
//
// Usa la librería html5-qrcode (cargada como script global en
// index.html, variable Html5Qrcode). Si la cámara no está disponible
// —sin permisos, sin cámara, navegador no compatible o sin
// conexión para descargar la librería— el lector no se detiene
// ahí: siempre queda habilitado un campo para digitar el código
// manualmente, de modo que la función nunca deja a la persona sin
// una forma de continuar.
// ============================================================
import { openModal, closeModal, toast } from "./app.js";

let activeScanner = null;

async function stopActiveScanner() {
  if (!activeScanner) return;
  try { await activeScanner.stop(); } catch (_) { /* ya estaba detenida */ }
  try { activeScanner.clear(); } catch (_) { /* nada que limpiar */ }
  activeScanner = null;
}

/**
 * Abre el lector de códigos QR/barras en un modal.
 * @param {Object} opts
 * @param {string} [opts.title] Título del modal.
 * @param {string} [opts.hint] Texto de ayuda bajo el título.
 * @param {(code: string) => void} opts.onDetected Se invoca con el texto leído
 *        (por cámara o digitado manualmente).
 */
export function openScanner({
  title = "Escanear código",
  hint = "Apunta la cámara al código de barras o QR. Si no tienes cámara disponible, puedes escribir el código manualmente.",
  onDetected,
} = {}) {
  const readerId = "qr-reader-" + Date.now();

  openModal(`
    <h3>${title}</h3>
    <p style="font-size:13px;color:var(--muted);margin-bottom:12px;">${hint}</p>
    <div id="${readerId}" style="width:100%;border-radius:10px;overflow:hidden;background:#11161c;min-height:220px;display:flex;align-items:center;justify-content:center;"></div>
    <p id="scan-status" style="font-size:12.5px;color:var(--muted);margin:10px 0 0;">Iniciando cámara…</p>
    <div class="field full" style="margin-top:12px;">
      <label>O ingresa el código manualmente</label>
      <input id="scan-manual" type="text" placeholder="Código de barras o contenido del QR" autocomplete="off">
    </div>
    <div class="modal-actions">
      <button type="button" class="btn btn-ghost" id="scan-cancel">Cancelar</button>
      <button type="button" class="btn btn-primary" id="scan-manual-btn">Usar este código</button>
    </div>
  `, {
    onMount: (box) => {
      const statusEl = box.querySelector("#scan-status");
      const manualInput = box.querySelector("#scan-manual");
      const backdrop = document.getElementById("modal-backdrop");

      // Si el modal se cierra por otra vía (clic fuera, tecla Esc),
      // igual se debe liberar la cámara.
      const observer = new MutationObserver(() => {
        if (backdrop.hidden) { stopActiveScanner(); observer.disconnect(); }
      });
      observer.observe(backdrop, { attributes: true, attributeFilter: ["hidden"] });

      const finish = async (code) => {
        observer.disconnect();
        await stopActiveScanner();
        closeModal();
        onDetected?.(String(code).trim());
      };

      box.querySelector("#scan-cancel").addEventListener("click", async () => {
        observer.disconnect();
        await stopActiveScanner();
        closeModal();
      });
      box.querySelector("#scan-manual-btn").addEventListener("click", () => {
        const val = manualInput.value.trim();
        if (!val) { toast("Escribe o escanea un código.", "error"); return; }
        finish(val);
      });
      manualInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") { e.preventDefault(); box.querySelector("#scan-manual-btn").click(); }
      });

      if (typeof Html5Qrcode === "undefined") {
        statusEl.textContent = "No se pudo cargar el lector de cámara (sin conexión a internet). Usa el campo manual.";
        return;
      }
      if (!navigator.mediaDevices?.getUserMedia) {
        statusEl.textContent = "Este navegador no permite acceder a la cámara desde aquí. Usa el campo manual.";
        return;
      }

      activeScanner = new Html5Qrcode(readerId, /* verbose= */ false);
      activeScanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 230, height: 230 } },
        (decodedText) => finish(decodedText),
        () => { /* intento de lectura sin éxito en este cuadro: se sigue intentando */ }
      ).then(() => {
        statusEl.textContent = "Cámara activa: enfoca el código de barras o QR.";
      }).catch((err) => {
        console.error("No se pudo iniciar la cámara:", err);
        statusEl.textContent = "No se pudo acceder a la cámara (permiso denegado o sin cámara disponible). Usa el campo manual.";
      });
    },
  });
}

export function iScan() {
  return `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 8V5a1 1 0 011-1h3M20 8V5a1 1 0 00-1-1h-3M4 16v3a1 1 0 001 1h3M20 16v3a1 1 0 01-1 1h-3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M4 12h16" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>`;
}
