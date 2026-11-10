# AgroQuiriquina — Backend (Django + DRF)

API REST para la gestión de inventario, ventas, finanzas, contactos y RRHH de AgroQuiriquina,
pensada para una app móvil Android que trabaja **offline** y sincroniza al recuperar conexión.

- **Python** 3.10+ (recomendado 3.11 o 3.12) · **Django** 5.0/5.1 · **DRF** 3.15
- **Auth:** JWT (SimpleJWT) con RBAC por rol: `ADMIN`, `VENDEDOR`, `SUPERVISOR`
- **BD:** SQLite por defecto (prototipo) · PostgreSQL opcional
- **Herencia Multi-table:** `Persona → Cliente / Proveedor / Trabajador` e `ItemBodega → ProductoVenta / InsumoAgricola`

---
Usuario	Contraseña
admin	Cambiar123!
gerente	Cambiar123!
vendedor1	Cambiar123!
vendedor2	Cambiar123!
supervisor1	Cambiar123!
supervisor2	Cambiar123!

## 1. Requisitos previos

| Herramienta | Verificar con | Descarga |
|---|---|---|
| Python 3.10+ | `python --version` (Windows) · `python3 --version` (Mac/Linux) | https://www.python.org/downloads/ |
| VS Code | — | https://code.visualstudio.com/ |
| Extensión *Python* de VS Code | — | se instala desde VS Code (ver paso 2) |

> **Windows:** al instalar Python marca la casilla **“Add python.exe to PATH”**.

---

## 2. Abrir el proyecto en VS Code

1. Descomprime `agroquiriquina.zip`.
2. VS Code → **File → Open Folder…** → selecciona la carpeta `agroquiriquina` (la que contiene `manage.py`).
3. VS Code te sugerirá instalar las extensiones recomendadas (Python, Pylance, Django, REST Client). Acepta.
4. Abre la terminal integrada: **Terminal → New Terminal** (`` Ctrl+` ``).

---

## 3. Instalación (paso a paso)

### 3.1 Crear y activar el entorno virtual

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
> Si PowerShell bloquea el script (“la ejecución de scripts está deshabilitada”), ejecuta una vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y repite la activación.
> Alternativa sin cambiar nada: usa **CMD** con `.venv\Scripts\activate.bat`.

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Verás `(.venv)` al inicio de la línea de la terminal. VS Code normalmente detecta el entorno solo; si no,
pulsa `Ctrl+Shift+P` → **Python: Select Interpreter** → elige el que dice `.venv`.

### 3.2 Instalar dependencias
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 Variables de entorno (opcional en desarrollo)
```bash
# Windows:      copy .env.example .env
# Mac / Linux:  cp .env.example .env
```
Sin `.env` el proyecto funciona igual con valores de desarrollo (SQLite, `DEBUG=True`).

### 3.4 Crear las tablas

> ⚠️ El proyecto **no incluye archivos de migración**: se generan en tu máquina con tu versión de Django.
> Es necesario hacerlo **antes** de `migrate` (el modelo de usuario es personalizado).

```bash
python manage.py makemigrations users inventory sales hr
python manage.py migrate
```

### 3.5 Cargar datos de ejemplo
```bash
python manage.py seed_demo
```
Crea usuarios de prueba para cada rol, productos, insumos, clientes, un proveedor y trabajadores.
El comando es **idempotente** (puedes repetirlo sin duplicar datos).

#### 👤 Usuarios de prueba

Clave de **todos** los usuarios: `Cambiar123!`

| Usuario | Rol | Qué sirve para probar |
|---|---|---|
| `admin` | Administrador (superusuario) | Todo, incluido el panel `/admin/`, nómina y finanzas |
| `gerente` | Administrador (no superusuario) | Rol `ADMIN` sin acceso a `/admin/`; mismo acceso a la API que `admin` |
| `vendedor1` | Vendedor (María González) | Clientes, ventas, pagos, despachos, catálogo y subida masiva de ventas |
| `vendedor2` | Vendedor (Pedro Soto) | Aislamiento: no ve las ventas de `vendedor1` |
| `supervisor1` | Supervisor de Terreno (Carlos Muñoz) | Trabajadores, desempeño diario, subida masiva de desempeños. Vinculado a un `Trabajador` |
| `supervisor2` | Supervisor de Terreno (Ana Rojas) | Igual que `supervisor1`, segunda cuenta |
| `inactivo` | Vendedor desactivado | El login debe devolver `401` |

Opciones del comando:
```bash
python manage.py seed_demo --password "OtraClave123"   # usar otra clave
python manage.py seed_demo --reset                      # restablecer clave/rol/estado si los usuarios ya existen
```

Matriz rápida de permisos (probada en `apps/users/tests.py`):

| Endpoint | admin / gerente | vendedor | supervisor |
|---|:---:|:---:|:---:|
| `clientes/` | ✅ | ✅ | ❌ 403 |
| `trabajadores/` | ✅ | ❌ 403 | ✅ |
| `finanzas/cuentas-por-cobrar/` | ✅ | ❌ 403 | ❌ 403 |
| `remuneraciones/` | ✅ | ❌ 403 | ❌ 403 |
| `usuarios/` | ✅ | ❌ 403 | ❌ 403 |

> ⚠️ Son credenciales **solo para el prototipo**. Antes de usar datos reales, cambia las claves o borra estos usuarios
> (`python manage.py shell` → `User.objects.filter(username__in=[...]).delete()`).

Si prefieres tu propio administrador: `python manage.py createsuperuser` (luego entra a `/admin/` y asígnale rol *Administrador*).

### 3.6 Levantar el servidor
```bash
python manage.py runserver
```
Abre:
- Health check: http://127.0.0.1:8000/api/v1/health/ → `{"status": "ok"}`
- Panel de administración: http://127.0.0.1:8000/admin/
- Para probar desde un celular/emulador en la misma red: `python manage.py runserver 0.0.0.0:8000`
  (en el emulador Android la PC es `http://10.0.2.2:8000`).

**Desde VS Code:** pestaña *Run and Debug* (`Ctrl+Shift+D`) → **Django: runserver** → ▶ (permite poner *breakpoints*).

### 3.7 Ejecutar los tests
```bash
python manage.py test
```
(o la configuración **Django: tests** del panel *Run and Debug*).

---

## 4. Aplicación web (prototipo)

Con el servidor corriendo, abre **http://127.0.0.1:8000/** e ingresa con cualquiera de los usuarios de la sección 3.5 (p. ej. `vendedor1`, `supervisor1` o `admin`; clave `Cambiar123!`).
Es una app web instalable (PWA) en `frontend/`, sin pasos de compilación: se edita `frontend/index.html` y se recarga.

| Rol | Menú que ve |
|---|---|
| Vendedor | Inicio · Ventas (nueva venta) · Clientes · Bodega |
| Supervisor | Inicio · Bodega (con calculadora de insumos por hectárea) · Terreno (registrar trabajo diario) |
| Administrador | Todo, más Finanzas (por cobrar y resumen del mes) y Nómina (calcular, aprobar y pagar) |

**Cómo funciona offline:** ventas, clientes nuevos y registros de terreno se guardan en el teléfono (`localStorage`) y se envían por lotes a
`/api/v1/sync/*/bulk/` cuando hay conexión (automático al reconectar, cada 60 s y con el botón 🔄). El catálogo se descarga al sincronizar.
Los registros con error se muestran en *Inicio* y se pueden descartar.

**Probarlo sin internet:** inicia sesión con conexión, abre las herramientas de desarrollo del navegador → *Network* → *Offline*, y crea una venta.
Verás “por enviar”. Al volver a *Online* se envía sola.

**Desde el celular:** `python manage.py runserver 0.0.0.0:8000` y abre `http://<IP-de-tu-PC>:8000/`. Instalar como app y abrir sin conexión
requiere **HTTPS** (o `localhost`); sin HTTPS funciona como página web normal con guardado local de datos.

**Limitaciones del prototipo:** el primer inicio de sesión necesita conexión; Finanzas y Nómina son solo en línea; no hay pantallas
para despachos ni abonos a deudas (la API sí los tiene); los datos locales no están cifrados.

---

## 5. Probar la API

### Con VS Code (recomendado)
Abre `api_examples.http` (extensión *REST Client*) y pulsa **Send Request** en cada bloque.

### Con curl
```bash
# 1) Obtener token
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"vendedor1","password":"Cambiar123!"}'

# 2) Usar el token
curl http://127.0.0.1:8000/api/v1/sync/catalogo/ -H "Authorization: Bearer <ACCESS_TOKEN>"
```
> En PowerShell usa `curl.exe` (no el alias `curl`) o prefiere el archivo `.http`.

### Endpoints principales (`/api/v1/`)

| Recurso | Endpoint | Roles (además de ADMIN) |
|---|---|---|
| Auth | `POST auth/token/` · `POST auth/token/refresh/` · `GET me/` | todos |
| Usuarios | `usuarios/` | solo ADMIN |
| Clientes | `clientes/` | VENDEDOR |
| Proveedores | `proveedores/` | lectura VENDEDOR |
| Trabajadores | `trabajadores/` | SUPERVISOR |
| Productos | `productos/` · `POST productos/<id>/movimiento/` | lectura VENDEDOR/SUPERVISOR; escribe ADMIN |
| Insumos | `insumos/` · `GET insumos/<id>/requerimiento/?hectareas=10` | lectura SUPERVISOR; escribe ADMIN |
| Movimientos de stock | `movimientos/` (solo lectura) | SUPERVISOR |
| Ventas | `ventas/` · `POST ventas/<id>/anular/` | VENDEDOR (ve solo las suyas) |
| Pagos / Despachos | `pagos/` · `despachos/` | VENDEDOR |
| Finanzas | `finanzas/cuentas-por-cobrar/` · `finanzas/rentabilidad/?desde=&hasta=` | solo ADMIN |
| Desempeño | `desempenos/` | SUPERVISOR |
| Remuneraciones | `remuneraciones/` · `POST …/<id>/calcular/ aprobar/ pagar/` | solo ADMIN |
| **Sync masivo** | `POST sync/ventas/bulk/` · `sync/desempenos/bulk/` · `sync/clientes/bulk/` | VENDEDOR / SUPERVISOR / VENDEDOR |
| **Sync catálogo** | `GET sync/catalogo/?updated_since=<ISO8601>` | según rol |

Todos los listados aceptan `?search=`, `?ordering=`, filtros por campo y paginación `?limit=&offset=`.

---

## 5. Cómo funciona la sincronización offline

1. **UUID desde el cliente:** la app Android genera el `id` (UUID v4) de cada venta/desempeño/cliente. Reenviar el mismo lote **nunca duplica**.
2. **Subida masiva** (`POST /sync/ventas/bulk/`): hasta **500** registros por lote, como lista JSON o `{"ventas": [...]}`.
   Cada ítem se procesa en su propia transacción; uno inválido no bloquea a los demás. Respuesta:
   ```json
   {
     "resumen": {"recibidos": 3, "creados": 2, "duplicados": 0, "errores": 1},
     "resultados": [
       {"index": 0, "id": "…", "status": "created"},
       {"index": 1, "id": "…", "status": "duplicate"},
       {"index": 2, "id": "…", "status": "error", "errors": {"detalles": ["…"]}}
     ],
     "server_time": "2026-01-15T14:02:11Z"
   }
   ```
   HTTP `200` si todo salió bien, `207` si hubo algún error. La app marca como sincronizados los `created` y `duplicate`.
3. **Stock:** al sincronizar una venta se descuenta stock y se registra un `MovimientoStock`. Si el stock no alcanza, la venta **no se rechaza**
   (ya ocurrió físicamente): se descuenta lo disponible y queda `requiere_revision = true` para que el administrador la revise
   (`GET /ventas/?requiere_revision=true`).
4. **Descarga incremental:** `GET /sync/catalogo/?updated_since=<server_time anterior>` entrega clientes/productos (o trabajadores) modificados,
   **incluidos los borrados lógicos** (`is_deleted: true`). Guarda el `server_time` de la respuesta para la siguiente llamada.
   Si pasas la fecha en la URL, codifica el `+` del huso horario como `%2B`.
5. **Borrado lógico:** `DELETE` marca `is_deleted=true`; no elimina filas.

---

## 6. Estructura del proyecto

```
agroquiriquina/
├── manage.py
├── requirements.txt
├── .env.example
├── api_examples.http          # peticiones de ejemplo (REST Client)
├── .vscode/                   # launch.json, settings.json, extensions.json
├── config/
│   ├── settings/ (base.py, dev.py, prod.py)
│   ├── urls.py · wsgi.py · asgi.py
└── apps/
    ├── core/        # SyncModel (UUID + sync), validador de RUT, permisos RBAC, utilidades
    ├── users/       # User (rol), Persona → Cliente/Proveedor/Trabajador, comando seed_demo
    ├── inventory/   # ItemBodega → ProductoVenta/InsumoAgricola, MovimientoStock, servicio de stock
    ├── sales/       # Venta, DetalleVenta, Pago, Despacho, finanzas (por cobrar, rentabilidad)
    ├── hr/          # Desempeno, Remuneracion (cálculo de nómina)
    └── sync/        # Endpoints de carga masiva y catálogo offline
```

---

## 7. PostgreSQL (opcional)

```bash
pip install "psycopg[binary]"
```
En `.env`:
```
DB_ENGINE=postgres
DB_NAME=agroquiriquina
DB_USER=postgres
DB_PASSWORD=tu_clave
DB_HOST=localhost
DB_PORT=5432
```
Crea la base (`createdb agroquiriquina`) y repite `makemigrations` (si cambiaste de motor, borra antes la carpeta de migraciones generadas
excepto `__init__.py`) y `migrate`.

## 8. Producción (resumen)

- `DJANGO_SETTINGS_MODULE=config.settings.prod`, con `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` definidos.
- `pip install gunicorn` y `gunicorn config.wsgi`, detrás de Nginx con HTTPS.
- `python manage.py collectstatic`.

## 9. Problemas frecuentes

| Síntoma | Solución |
|---|---|
| `ModuleNotFoundError: No module named 'django'` | El entorno virtual no está activo o faltó `pip install -r requirements.txt`. |
| `Dependency on app with no migrations: users` / `no such table: users_user` | Ejecuta `python manage.py makemigrations users inventory sales hr` **antes** de `migrate`. |
| `InconsistentMigrationHistory … admin.0001 … users.0001` | Borra `db.sqlite3` y las migraciones generadas (no `__init__.py`), y repite el paso 3.4. |
| PowerShell no deja activar el venv | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, o usa CMD. |
| VS Code subraya imports en rojo | `Ctrl+Shift+P` → *Python: Select Interpreter* → elige `.venv`. |
| `401 Unauthorized` | Falta `Authorization: Bearer <token>` o el token venció (usa `auth/token/refresh/`). |
| `403` en un endpoint | El rol del usuario no tiene permiso (ver tabla de endpoints). |
| Puerto 8000 ocupado | `python manage.py runserver 8001`. |

## 10. Siguientes pasos sugeridos
Resolución de conflictos de edición (no solo creación) en la sincronización, reportes de rentabilidad con costo de insumos y compras,
exportación de nómina a PDF/Excel, documentación OpenAPI (`drf-spectacular`) y despliegue con Docker.
