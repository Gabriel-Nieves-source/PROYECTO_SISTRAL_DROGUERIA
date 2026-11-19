# SITRAL – Sistema de Trazabilidad y Control por Lotes para Droguerías

<!-- Reemplace USUARIO/REPO y SU-ORGANIZACION_sitral por los valores reales -->
[![CI SITRAL](https://github.com/USUARIO/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/USUARIO/REPO/actions/workflows/ci.yml)
[![CodeQL](https://github.com/USUARIO/REPO/actions/workflows/codeql.yml/badge.svg)](https://github.com/USUARIO/REPO/actions/workflows/codeql.yml)
[![Quality Gate](https://sonarcloud.io/api/project_badges/measure?project=SU-ORGANIZACION_sitral&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=SU-ORGANIZACION_sitral)
[![Mutation Score](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/USUARIO/REPO/badges/mutation.json)](https://github.com/USUARIO/REPO/actions/workflows/ci.yml)

API en FastAPI con autenticación JWT, autorización por roles (RBAC: `ADMIN`, `USER`),
controles OWASP Top 10, Mutation Testing con mutmut y análisis con SonarCloud y CodeQL.

## Cómo ejecutar el programa (Windows)

Abra la carpeta del proyecto en VS Code y en la terminal (PowerShell) ejecute:

```powershell
# 1. Solo la primera vez: crear el entorno e instalar dependencias
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt

# 2. Solo la primera vez: crear el archivo .env
copy .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
#    -> pegue ese valor en SITRAL_JWT_SECRET= dentro de .env
#    -> para probar sin MySQL deje: SITRAL_DATABASE_URL=sqlite:///./sitral_dev.db
#    -> para ver /docs ponga: SITRAL_DEBUG=true

# 3. Solo la primera vez: crear usuarios y códigos de prueba
python -m scripts.crear_usuarios
python -m scripts.generar_codigos_prueba

# 4. Cada vez que quiera usar el programa
.venv\Scripts\activate
uvicorn app.main:app --reload
```

Luego abra en el navegador:

- **http://localhost:8000/scanner**: lector de QR y códigos de barras (cámara, imagen o lector USB).
- **http://localhost:8000/docs**: Swagger para probar los endpoints (solo con `SITRAL_DEBUG=true`).

Usuarios: `admin@sitral.co` / `AdminSegura#2026` (ADMIN) y `usuario@sitral.co` / `UserSegura#2026` (USER).
En Mac/Linux cambie `.venv\Scripts\activate` por `source .venv/bin/activate` y `copy` por `cp`.

## Lector de códigos QR y de barras

Lee **QR, Code128, EAN-13/EAN-8, UPC y DataMatrix**, incluido **GS1 DataMatrix**, el código de los medicamentos
que trae GTIN, lote y fecha de vencimiento. Cada código se clasifica así:

| Tipo | Ejemplo | Qué muestra |
|---|---|---|
| LOTE | `LOT-2026-001` | Código de lote de SITRAL |
| GS1 | `(01)07702001023455(17)270630(10)LOT-2026-003` | GTIN, lote, vencimiento y estado (VIGENTE / POR_VENCER / VENCIDO) |
| PRODUCTO | `7702001023455` | GTIN / EAN del producto |
| DESCONOCIDO | cualquier otro texto | El texto leído |

Formas de leer en http://localhost:8000/scanner:
1. **Cámara** del PC o del celular. La cámara solo funciona en `localhost` o con HTTPS.
2. **Subir imagen**: puede usar las imágenes de `codigos_prueba/`.
3. **Lector USB o Bluetooth**: funcionan como un teclado; haga clic en el campo de texto y escanee.

Endpoints: `POST /scanner/decodificar` (imagen, máx. 5 MB) y `POST /scanner/interpretar` (texto), ambos con token.

## Endpoints de prueba (Guía 8)

| Método | Ruta | Acceso | Respuesta esperada |
|---|---|---|---|
| POST | `/auth/login` | Público | 200 + token / 401 / 429 tras 5 intentos |
| GET | `/admin/dashboard` | Solo `ADMIN` | 200 admin · 403 user · 401 sin token |
| GET | `/users/me` | `USER` y `ADMIN` | 200 con perfil (sin hash) |

## Pruebas y calidad

```bash
pytest --cov --cov-report=term-missing      # 75 pruebas, ~96 % cobertura
mutmut run && mutmut export-cicd-stats      # 68 mutantes
python scripts/mutation_gate.py --min 50    # falla si el score < 50 %
```

## Secretos que debe crear en GitHub (Settings → Secrets and variables → Actions)

- `SONAR_TOKEN`: token de sonarcloud.io (My Account → Security).
- `SITRAL_JWT_SECRET_TEST`: cadena aleatoria de 32+ caracteres para las pruebas.

## Seguridad en GitHub (Settings → Code security)

Activar: Dependency graph, Dependabot alerts, Dependabot security updates,
Code scanning (CodeQL ya viene en `.github/workflows/codeql.yml`) y Secret scanning.
