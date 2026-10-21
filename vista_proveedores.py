import re

from vista_catalogo import ModuloCatalogo


class ModuloProveedores(ModuloCatalogo):
    """Apartado Proveedores: datos de quienes surten los insumos."""

    TITULO = "Proveedores"
    DESCRIPCION = "Administra los proveedores que surten los insumos."
    TABLA = "proveedores"
    NOMBRE_SINGULAR = "proveedor"
    CAMPOS = [
        {"clave": "nombre", "etiqueta": "Nombre del proveedor",
         "ancho": 260, "obligatorio": True},
        {"clave": "telefono", "etiqueta": "Teléfono", "ancho": 160},
        {"clave": "correo", "etiqueta": "Correo", "ancho": 260},
    ]

    def validar(self, datos):
        telefono = datos["telefono"]
        if telefono and not re.fullmatch(r"[\d\s()+-]{7,20}", telefono):
            return "El teléfono solo puede tener números, espacios, ( ) + -."

        correo = datos["correo"]
        if correo and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo):
            return "El correo no tiene un formato válido."

        return None
