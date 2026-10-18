# YOGURTFRUT · Control de Mermas

Sistema de escritorio para registrar y analizar las mermas (pérdidas de producto) de la heladería Yogurth Frut. Está hecho en Python con Tkinter y usa SQLite como base de datos.

## Cómo correr el programa

Solo necesitas tener **Python 3.10 o superior**. No hay dependencias que instalar.

Abre una terminal **dentro de la carpeta del proyecto** (donde está `main.py`) y ejecuta:

```bash
python main.py
```

Si `python` no se reconoce, usa `py main.py`.

## Usuario de prueba

Al iniciar, el programa crea automáticamente un usuario para que todo el equipo pueda entrar:

| Usuario | Contraseña | Rol |
|---|---|---|
| `test` | `test` | Administrador |

## Base de datos

- La base de datos es el archivo `mermas.db`. Se crea sola la primera vez que corres el programa, con todas sus tablas y el usuario `test`.
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
| `vista_mermas.py` | Apartado **Registrar merma** |
| `vista_inventario.py` | Apartado **Inventario**: existencias y alertas de stock |
| `vista_historial.py` | Apartado **Historial**: consulta de mermas con filtros |
| `vista_reportes.py` | Apartado **Reportes**: pérdidas por periodo y exportación a CSV |
| `ui_comunes.py` | Botones, tablas y tarjetas compartidas por los apartados |
| `asignar_rol.py` | Script para asignar el rol de Gerente a un usuario |
