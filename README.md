# YOGURTFRUT · Control de Mermas

Sistema de escritorio para registrar y analizar las mermas (pérdidas de producto) de la heladería Yogurth Frut. Está hecho en Python con Tkinter y usa SQLite como base de datos.

## Cómo correr el programa

Solo necesitas tener **Python 3.10 o superior**. No hay dependencias que instalar.

Abre una terminal **dentro de la carpeta del proyecto** (donde está `main.py`). El programa se puede abrir de dos formas:

| Modo | Comando | Base de datos | Para qué |
|---|---|---|---|
| **Normal** | `python main.py` | `mermas.db` | Uso real. Empieza vacía, solo con el usuario `admin`. |
| **Prueba** | `python main.py --prueba` | `mermas_prueba.db` | Probar el sistema con datos falsos ya cargados. |

### Modo normal

```bash
python main.py
```

Entra con `admin` / `admin`. Lo que captures se guarda en `mermas.db`.

### Modo prueba

```bash
python main.py --prueba
```

Entra con `admin` / `admin`. Trae productos, proveedores, empleados y varias semanas de compras y mermas. El título de la ventana dice **[BASE DE PRUEBA]** para que no la confundas con la normal. Lo que hagas aquí no afecta a `mermas.db`.

Para dejar la base de prueba como nueva (por ejemplo, si alguien la modificó):

```bash
python datos_prueba.py
```

> Si `python` no se reconoce, usa `py` en su lugar (por ejemplo `py main.py --prueba`).

## Usuario administrador

Si la base de datos no tiene usuarios, el programa crea el administrador inicial:

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin` | Administrador |

Desde el apartado **Usuarios** (solo visible para administradores) se pueden crear más usuarios, cambiar contraseñas y activar o desactivar cuentas. En **Usuarios → Mi cuenta** el administrador cambia su propio usuario y contraseña.

## Base de datos de prueba

- Se usa con `python main.py --prueba` y vive en el archivo `mermas_prueba.db`, separado de la base normal.
- Si no existe, se genera sola al abrir el programa en modo prueba. `python datos_prueba.py` la regenera desde cero, siempre con los mismos datos.
- Usuarios de la base de prueba: `admin`/`admin`, `gerente`/`gerente` y `empleado`/`empleado`.

## Base de datos

- La base de datos es el archivo `mermas.db`. Se crea sola la primera vez que corres el programa, con todas sus tablas y el usuario `admin`.
- **No se sube al repositorio** (está en `.gitignore`). Cada quien tiene la suya con sus propios datos de prueba.
- Para empezar desde cero, cierra el programa y borra `mermas.db`. Se volverá a crear al abrirlo.
- La estructura de las tablas está en `base_datos.py`. Si se agrega o cambia una tabla, se hace ahí.

## Estructura del proyecto

| Archivo | Contenido |
|---|---|
| `main.py` | Punto de entrada: inicializa la base y abre el login |
| `base_datos.py` | Conexión a SQLite y creación de las tablas |
| `vista_login.py` | Pantalla de inicio de sesión |
| `vista_dashboard.py` | Panel principal y menú lateral |
| `vista_productos.py` | Apartado **Productos**: alta, edición y desactivación |
| `vista_proveedores.py` | Apartado **Proveedores**: datos de quienes surten los insumos |
| `vista_compras.py` | Apartado **Compras**: pedidos a proveedores con su detalle; suben la existencia |
| `vista_mermas.py` | Apartado **Registrar merma**: producto, tipo, empleado, causa y costo; bajan la existencia |
| `vista_inventario.py` | Apartado **Inventario**: existencias actuales y movimientos por día |
| `vista_historial.py` | Apartado **Historial**: consulta de mermas con filtros |
| `vista_reportes.py` | Apartado **Reportes**: pérdidas por periodo, % de merma vs compras y exportación a CSV |
| `vista_empleados.py` | Apartado **Empleados**: personal que reporta las mermas |
| `vista_usuarios.py` | Apartado **Usuarios** (solo administradores) y **Mi cuenta** |
| `vista_catalogo.py` | Base común de los catálogos (Proveedores y Empleados) |
| `seguridad.py` | Cifrado y verificación de contraseñas |
| `datos_prueba.py` | Genera la base de prueba `mermas_prueba.db` con datos falsos |
| `ui_comunes.py` | Botones, tablas y tarjetas compartidas por los apartados |
| `asignar_rol.py` | Script para asignar el rol de Gerente a un usuario |
