import sys
from tkinter import Tk, ttk

import base_datos
from base_datos import inicializar_base_datos
from vista_login import LoginApp


def main():
    # python main.py --prueba  -> usa la base de prueba con datos falsos
    if "--prueba" in sys.argv:
        import datos_prueba
        
        if not datos_prueba.RUTA_PRUEBA.exists():
            datos_prueba.generar()
        base_datos.RUTA_BASE_DATOS = datos_prueba.RUTA_PRUEBA

    inicializar_base_datos()
    
    root = Tk()
    
    estilo_global = ttk.Style()
    if 'clam' in estilo_global.theme_names():
        estilo_global.theme_use('clam')
        
    LoginApp(root)
    root.mainloop()
    estilo_global = ttk.Style()
    if 'clam' in estilo_global.theme_names():
        estilo_global.theme_use('clam')
        
    LoginApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
