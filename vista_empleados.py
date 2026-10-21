from vista_catalogo import ModuloCatalogo


TURNOS = ["Matutino", "Vespertino", "Completo"]


class ModuloEmpleados(ModuloCatalogo):
    """Apartado Empleados: personal que registra o genera mermas."""

    TITULO = "Empleados"
    DESCRIPCION = "Administra el personal que reporta las mermas."
    TABLA = "empleados"
    NOMBRE_SINGULAR = "empleado"
    CAMPOS = [
        {"clave": "nombre", "etiqueta": "Nombre del empleado",
         "ancho": 260, "obligatorio": True},
        {"clave": "puesto", "etiqueta": "Puesto",
         "ancho": 200, "obligatorio": True},
        {"clave": "turno", "etiqueta": "Turno",
         "ancho": 140, "obligatorio": True, "opciones": TURNOS},
    ]
