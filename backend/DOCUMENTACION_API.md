# Documentación de la API — SITRAL

Sistema de Trazabilidad y Control por Lotes para Droguerías.
API construida en **FastAPI + SQLAlchemy + PyMySQL**, con autenticación
**JWT** (Bearer token) y contraseñas con hash mediante **pwdlib**.

Base URL local: `http://127.0.0.1:8000`
Documentación interactiva automática (Swagger): `http://127.0.0.1:8000/docs`

Todas las rutas, salvo `/`, `/health` y `/auth/login`, requieren el
encabezado:

```
Authorization: Bearer <access_token>
```

El token se obtiene en `POST /auth/login` y contiene el rol del
usuario (`ADMINISTRADOR` o `FARMACEUTA`). Los endpoints marcados
como **[Admin]** usan la dependencia `verificar_administrador` y
devuelven `403` si el usuario autenticado no tiene ese rol.

---

## 1. Módulo de Autenticación (`/auth`)

| Método | Ruta | Descripción | Roles |
|---|---|---|---|
| POST | `/auth/login` | Inicia sesión y devuelve el `access_token` (RQF001) | Público |
| GET | `/auth/me` | Devuelve los datos del token actual | Autenticado |

## 2. Módulo de Usuarios (`/usuarios`) — RQF002

| Método | Ruta | Descripción | Roles |
|---|---|---|---|
| GET | `/usuarios/` | Lista todos los usuarios | Admin |
| GET | `/usuarios/{id_usuario}` | Consulta un usuario | Admin |
| POST | `/usuarios/` | Crea un usuario | Admin |
| PUT | `/usuarios/{id_usuario}` | Actualiza un usuario | Admin |
| PATCH | `/usuarios/{id_usuario}/estado` | Activa/inactiva un usuario | Admin |
| DELETE | `/usuarios/{id_usuario}` | Elimina un usuario | Admin |

## 3. Módulo de Proveedores (`/proveedores`) — RQF003

| Método | Ruta | Descripción | Roles |
|---|---|---|---|
| GET | `/proveedores/` | Lista proveedores (filtro `estado`) | Admin, Farmaceuta |
| GET | `/proveedores/{id_proveedor}` | Consulta un proveedor | Admin, Farmaceuta |
| POST | `/proveedores/` | Registra un proveedor | Admin, Farmaceuta |
| PUT | `/proveedores/{id_proveedor}` | Modifica un proveedor | Admin |
| DELETE | `/proveedores/{id_proveedor}` | Baja lógica (`estado=INACTIVO`) | Admin |

## 4. Módulo de Medicamentos / Catálogo (`/medicamentos`) — RQF004

| Método | Ruta | Descripción | Roles |
|---|---|---|---|
| GET | `/medicamentos/` | Lista medicamentos (filtros `nombre`, `estado`) | Admin, Farmaceuta |
| GET | `/medicamentos/codigo/{codigo_barras}` | Busca por código de barras/QR (usado por el escáner) | Admin, Farmaceuta |
| GET | `/medicamentos/{id_medicamento}` | Consulta un medicamento | Admin, Farmaceuta |
| POST | `/medicamentos/` | Registra un medicamento | Admin, Farmaceuta |
| PUT | `/medicamentos/{id_medicamento}` | Modifica un medicamento | Admin |
| DELETE | `/medicamentos/{id_medicamento}` | Baja lógica | Admin |

## 5. Módulo de Lotes (`/lotes`) — RQF005, RQF009, RQF012

| Método | Ruta | Descripción | Roles |
|---|---|---|---|
| GET | `/lotes/` | Inventario, con filtros `medicamento`, `numero_lote`, `id_proveedor`, `estado`, `proximos_a_vencer` (días) | Admin, Farmaceuta |
| GET | `/lotes/{id_lote}` | Consulta un lote (incluye `dias_para_vencer`) | Admin, Farmaceuta |
| GET | `/lotes/{id_lote}/trazabilidad` | Historial completo: movimientos de inventario + facturas asociadas | Admin, Farmaceuta |
| POST | `/lotes/` | Registra el ingreso de un lote (flujo de escaneo QR/código de barras) | Admin, Farmaceuta |

Flujo esperado desde la app móvil (según el diagrama de secuencia del
documento): escanear código → `GET /medicamentos/codigo/{codigo}` →
mostrar datos del medicamento → `POST /lotes/` con proveedor, número
de lote, cantidad y fechas.

## 6. Módulo de Facturación (`/facturas`) — RQF006, RQF007

| Método | Ruta | Descripción | Roles |
|---|---|---|---|
| GET | `/facturas/` | Lista facturas (filtro `tipo=ENTRADA\|SALIDA`) | Admin, Farmaceuta |
| GET | `/facturas/{id_factura}` | Consulta una factura con su detalle | Admin, Farmaceuta |
| POST | `/facturas/entrada` | Registra una factura de compra; crea o incrementa el lote correspondiente | Admin, Farmaceuta |
| POST | `/facturas/salida` | Registra una factura de venta; descuenta el inventario del lote y valida existencias | Admin, Farmaceuta |
| PATCH | `/facturas/{id_factura}/anular` | Anula una factura y revierte su efecto en el inventario | Admin |

Cada factura de entrada/salida genera automáticamente sus
`movimiento_inventario` (tipo `ENTRADA`, `SALIDA` o `AJUSTE` al
anular).

## 7. Módulo de Alertas de Vencimiento (`/alertas`) — RQF008

| Método | Ruta | Descripción | Roles |
|---|---|---|---|
| GET | `/alertas/` | Lista alertas (filtro `estado`) | Admin, Farmaceuta |
| POST | `/alertas/generar` | Ejecuta la evaluación de vencimientos (rol "Sistema" del caso de uso); genera alertas para lotes vencidos o próximos a vencer según el umbral configurado | Admin, Farmaceuta |
| PATCH | `/alertas/{id_alerta}/estado?nuevo_estado=VISTA` | Marca una alerta como `VISTA` o `ATENDIDA` | Admin, Farmaceuta |
| GET | `/alertas/configuracion` | Consulta el umbral actual (línea base 30 días) | Admin, Farmaceuta |
| PUT | `/alertas/configuracion` | Ajusta el umbral de días de anticipación | Admin |

> Nota: `POST /alertas/generar` puede programarse con un scheduler
> (cron, tarea de Windows, etc.) para que corra una vez al día,
> simulando el actor "Sistema (Job Diario)" del diagrama de casos de
> uso; también puede llamarse manualmente desde la app.

## 8. Módulo de Dashboard / KPIs (`/dashboard`) — RQF010

| Método | Ruta | Descripción | Roles |
|---|---|---|---|
| GET | `/dashboard/kpis` | Total de medicamentos activos, unidades disponibles, lotes próximos a vencer, lotes vencidos y proveedores activos (usa la vista `vista_dashboard` del script SQL) | Admin |

---

## Pendiente / fuera de esta entrega

- **RQF011 (Migración de datos)**: no se implementó en este alcance;
  se sugiere un endpoint `POST /migracion/importar` que reciba un CSV
  y reutilice la lógica de `POST /medicamentos/` y `POST /lotes/`.
- Documentación formal en Swagger/OpenAPI (`/docs`) ya se genera
  automáticamente por FastAPI a partir de los `tags` y `response_model`
  de cada router.
