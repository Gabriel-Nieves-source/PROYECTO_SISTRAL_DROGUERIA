# SITRAL — Sistema completo (backend + frontend + base de datos)

[![CI SITRAL](https://github.com/Gabriel-Nieves-source/PROYECTO_SISTRAL_DROGUERIA/actions/workflows/ci.yml/badge.svg)](https://github.com/Gabriel-Nieves-source/PROYECTO_SISTRAL_DROGUERIA/actions/workflows/ci.yml)
[![CodeQL](https://github.com/Gabriel-Nieves-source/PROYECTO_SISTRAL_DROGUERIA/actions/workflows/codeql.yml/badge.svg)](https://github.com/Gabriel-Nieves-source/PROYECTO_SISTRAL_DROGUERIA/actions/workflows/codeql.yml)
[![Quality Gate](https://sonarcloud.io/api/project_badges/measure?project=Gabriel-Nieves-source_PROYECTO_SISTRAL_DROGUERIA&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Gabriel-Nieves-source_PROYECTO_SISTRAL_DROGUERIA)
[![Mutation Score](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Gabriel-Nieves-source/PROYECTO_SISTRAL_DROGUERIA/badges/mutation.json)](https://github.com/Gabriel-Nieves-source/PROYECTO_SISTRAL_DROGUERIA/actions/workflows/ci.yml)

Sistema de Trazabilidad y Control por Lotes para Droguerías. Este paquete
trae las tres partes juntas, listas para montar en tu computador:

```
SITRAL_sistema_completo/
├── backend/        → API en FastAPI (Python)
├── frontend/        → aplicación web (HTML/CSS/JS puro, con lector de QR y código de barras)
├── database/        → script SQL para crear la base de datos
├── iniciar_windows.bat
└── iniciar_mac_linux.sh
```

## 0. Requisitos previos

- **Python 3.10 o superior** instalado.
- **MySQL** instalado y corriendo (puede ser MySQL Server, XAMPP, WAMP, etc.).

## 1. Crear la base de datos

1. Abre tu cliente de MySQL (consola, MySQL Workbench, phpMyAdmin, etc.).
2. Crea la base de datos:
   ```sql
   CREATE DATABASE SITRAL;
   ```
3. Importa el script incluido:
   ```bash
   mysql -u root -p SITRAL < database/SITRAL.sql
   ```
   (con phpMyAdmin: entra a la base `SITRAL` → pestaña **Importar** → selecciona `database/SITRAL.sql`).

4. Configura el archivo `backend/.env` (desde la Guía 8 las claves ya **no** van en el código):
   ```bash
   cd backend
   copy .env.example .env          # Mac/Linux: cp .env.example .env
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
   Abre `backend/.env` y:
   - pega la clave generada en `SITRAL_JWT_SECRET=`
   - en `SITRAL_DATABASE_URL` pon tu usuario y contraseña de MySQL
     (si la contraseña tiene `@`, escríbelo como `%40`; ej. `12345@` → `12345%40`)
   - si vas a usarlo desde el celular, agrega `http://TU_IP:5500` en `SITRAL_CORS_ORIGINS`

## 2. Instalar y arrancar el backend (la API)

```bash
cd backend
pip install -r requirements.txt
python actualizar_passwords.py       # deja las contraseñas de prueba listas para iniciar sesión
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verifica que quedó funcionando abriendo `http://127.0.0.1:8000/docs` en el navegador.

**Déjala corriendo** (no cierres esa terminal) y sigue con el siguiente paso en otra terminal.

## 3. Arrancar el frontend (la página web)

```bash
cd frontend
python -m http.server 5500
```

Abre en el navegador: `http://127.0.0.1:5500`

## 4. Iniciar sesión

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin123` | Administrador |
| `farmaceuta` | `farm123` | Farmaceuta |

(Estas quedan activas después de ejecutar `actualizar_passwords.py` en el paso 2.)

## 5. Usarlo desde el celular (para probar el lector de QR/código de barras)

1. Conecta el celular a la **misma red Wi-Fi** que el computador.
2. En el computador averigua tu IP local:
   - Windows: `ipconfig` (busca "Dirección IPv4", algo como `192.168.1.25`)
   - Mac/Linux: `ifconfig` o `ip a`
3. En el celular abre el navegador y entra a `http://TU_IP:5500`.
4. En la pantalla de ingreso, despliega **"Dirección del servidor"** y escribe
   `http://TU_IP:8000` (la IP del computador — `127.0.0.1` en el celular
   apuntaría al propio celular, no sirve).
5. Inicia sesión normalmente. La primera vez que uses el botón de escanear
   (en Medicamentos, Lotes o Facturación), el navegador pedirá permiso de
   cámara — acéptalo.

   > Nota: algunos navegadores de celular exigen una conexión seguara
   > (HTTPS) para permitir la cámara al entrar por IP. Si la cámara no se
   > activa, la aplicación sigue funcionando: siempre queda el campo para
   > escribir el código manualmente.

## Atajos incluidos

Para no escribir los comandos cada vez, este paquete trae dos scripts que
abren el backend y el frontend automáticamente, cada uno en su propia
ventana:

- **Windows**: doble clic en `iniciar_windows.bat`
- **Mac/Linux**: en una terminal, dentro de esta carpeta, ejecuta
  `bash iniciar_mac_linux.sh`

(La primera vez sigue siendo necesario hacer los pasos 1 y 2 —crear la base
de datos, instalar dependencias y actualizar las contraseñas— una sola vez;
los scripts solo automatizan el arranque de los dos servidores.)

## Guía 8: calidad DevSecOps y seguridad

| Qué | Dónde |
|---|---|
| Pruebas automatizadas (70) con SQLite, sin MySQL | `backend/tests/` → `cd backend && pytest --cov` |
| Mutation Testing (mutmut, 46 mutantes, 100 %) | `backend/pyproject.toml`, `backend/app/domain/inventario.py` |
| Pipeline CI/CD (pruebas, SonarCloud, mutmut con umbral del 50 %) | `.github/workflows/ci.yml` |
| CodeQL y Dependabot | `.github/workflows/codeql.yml`, `.github/dependabot.yml` |
| Configuración segura (`.env`) | `backend/app/config.py`, `backend/.env.example` |
| JWT con iss/aud y rol leído de la BD | `backend/app/security.py` |
| Bloqueo tras 5 intentos fallidos de login | `backend/app/rate_limit.py` |
| Cabeceras de seguridad HTTP | `backend/app/middleware/security_headers.py` |

**Secreto necesario en GitHub** (Settings → Secrets and variables → Actions): `SONAR_TOKEN`.

## Documentación adicional

- `backend/DOCUMENTACION_API.md`: documentación completa de todos los
  endpoints de la API.
- `frontend/README.md`: detalles del frontend (estructura de archivos,
  permisos por rol, cómo ajustar rutas si cambia algo en el backend).
