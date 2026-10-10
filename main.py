
from tkinter import Tk
from base_datos import inicializar_base_datos
from vista_login import LoginApp


def main():
    inicializar_base_datos()

    root = Tk()
    LoginApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
