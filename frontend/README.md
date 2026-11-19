# SITRAL — Aplicación web (computador y celular)

Esta carpeta es el frontend de SITRAL: una aplicación web que funciona igual en
computador y en celular (es la misma página, adaptada con CSS responsivo), y que
se conecta a la API de FastAPI que ya tienes corriendo en tu proyecto
`SITRAL_API`. No necesita instalación, build ni frameworks: es HTML, CSS y
JavaScript puro, así que basta con abrirla en el navegador.

## 1. Requisitos

- Tu API de SITRAL corriendo localmente (`uvicorn app.main:app --reload`), tal
  como la has venido usando.
- Un servidor estático simple para servir esta carpeta (recomendado, en vez de
  abrir el `index.html` con doble clic, porque los módulos de JavaScript no
  funcionan bien con `file://`).

## 2. CORS

Ya no tienes que hacer nada aquí: la API (`app/main.py`) ya trae configurado
`CORSMiddleware`, así que el navegador puede llamarla desde otro origen
(otra pestaña/puerto) sin pasos adicionales.

## 3. Ejecutar la aplicación web

Desde esta carpeta (`sitral-web`), en una terminal aparte (con tu API ya
corriendo en otra):

```bash
python -m http.server 5500
```

Y abre en el navegador: `http://127.0.0.1:5500`

(Si no tienes Python a la mano en Windows, también funciona con la extensión
**Live Server** de VS Code: clic derecho sobre `index.html` → "Open with Live
Server".)

## 4. Iniciar sesión

Usa el mismo usuario y contraseña que ya tienes creados en tu base de datos
(los mismos con los que entras por Swagger UI). La aplicación guarda el token
en el navegador y lo reutiliza mientras no cierres sesión.

Si usas la base de datos original (`SITRAL.sql`) sin cambios, los usuarios ya
creados son:

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin123` | Administrador |
| `farmaceuta` | `farm123` | Farmaceuta |

Si tu API no corre en `http://127.0.0.1:8000` (por ejemplo, porque usas otro
puerto), despliega "Dirección del servidor" en la pantalla de inicio de
sesión y escribe la URL correcta antes de entrar.

## 5. Usarla desde el celular (misma red Wi-Fi)

1. Conecta el celular a la **misma red Wi-Fi** que el computador.
2. En el computador, averigua tu IP local (Windows: `ipconfig`, busca algo
   como `192.168.1.25`).
3. En el celular, abre el navegador y entra a
   `http://TU_IP:5500` (por ejemplo `http://192.168.1.25:5500`).
4. En "Dirección del servidor" de la pantalla de login, escribe
   `http://TU_IP:8000` (la IP del computador, no `127.0.0.1`, porque
   `127.0.0.1` en el celular apunta al propio celular).

Con eso la misma aplicación queda funcionando igual en pantalla grande
(computador, con menú lateral) y en pantalla de celular (con menú inferior),
sin tener que mantener dos proyectos distintos.

## 6. Si algún endpoint no coincide exactamente

El cliente de la API está centralizado en **un solo archivo**:
`js/api.js`. Ahí están declaradas todas las rutas (`/auth/login`,
`/medicamentos/`, `/lotes/`, `/facturas/entrada`, `/facturas/salida`,
`/alertas/generar`, `/dashboard/kpis`, etc.) exactamente como quedaron
documentadas en `Documentacion_API_SITRAL.docx`. Si alguna ruta o algún
nombre de campo cambió en tu backend, solo hay que ajustarlo en ese archivo;
el resto de la aplicación (vistas, formularios, tablas) no necesita tocarse.

## 7. Estructura de archivos

```
sitral-web/
├── index.html              # estructura de la página (login + shell de la app)
├── css/style.css           # estilos responsivos (escritorio y móvil)
└── js/
    ├── api.js               # único punto de contacto con la API FastAPI
    ├── app.js                # navegación, sesión, modales, notificaciones
    └── views/
        ├── dashboard.js      # KPIs y alertas (solo Administrador)
        ├── lotes.js          # registro y consulta de lotes
        ├── medicamentos.js   # catálogo de medicamentos
        ├── proveedores.js    # gestión de proveedores
        ├── facturas.js       # facturación de entrada y salida
        ├── alertas.js        # alertas de vencimiento y umbral
        └── usuarios.js       # gestión de usuarios (solo Administrador)
```

## 8. Permisos por rol (ya aplicados en la interfaz)

La interfaz oculta o deshabilita automáticamente lo que el rol que inició
sesión no puede hacer, siguiendo la misma matriz de permisos ya documentada
en el proyecto:

| Módulo | Consultar | Registrar | Modificar | Eliminar |
|---|---|---|---|---|
| Catálogo (medicamentos, proveedores) | Admin. y Farm. | Admin. y Farm. | Solo Admin. | Solo Admin. |
| Lotes | Admin. y Farm. | Admin. y Farm. | — | — |
| Facturación | Admin. y Farm. | Admin. y Farm. | — | Solo Admin. |
| Alertas | Admin. y Farm. | Admin. y Farm. | Solo Admin. (umbral) | — |
| Usuarios | Solo Admin. | Solo Admin. | Solo Admin. | Solo Admin. |
| Dashboard de KPIs | Solo Admin. | — | — | — |

Si el Farmaceuta intenta algo no permitido, de todas formas la API lo
rechazaría con 403; la interfaz simplemente evita mostrar botones que de
antemano sabemos que van a fallar.
