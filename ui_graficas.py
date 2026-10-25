import tkinter as tk
from datetime import date, timedelta

import ui_tema


# Gráficas sencillas dibujadas con Canvas (no requieren instalar nada).
# Se redibujan solas cuando cambia el tamaño de la ventana.

PALETA = list(ui_tema.PALETA_GRAFICAS)


def formato_dinero(valor):
    """$1,234 para ejes y etiquetas compactas."""
    if valor >= 1_000_000:
        return f"${valor / 1_000_000:.1f}M"
    if valor >= 10_000:
        return f"${valor / 1000:.0f}k"
    return f"${valor:,.0f}"


def recortar(texto, maximo):
    """Acorta un texto largo con puntos suspensivos."""
    return texto if len(texto) <= maximo else texto[:maximo - 1].rstrip() + "…"


def rellenar_dias(datos, desde, hasta):
    """
    Completa con 0 los días sin mermas para que la línea no "salte" fechas.
    `datos` es un diccionario {'AAAA-MM-DD': costo}. Devuelve [(date, costo)].
    """
    # Acepta fechas como texto 'AAAA-MM-DD' o como date
    if isinstance(desde, str):
        desde = date.fromisoformat(desde)
    if isinstance(hasta, str):
        hasta = date.fromisoformat(hasta)

    if desde is None:
        if not datos:
            return []
        desde = date.fromisoformat(min(datos))
    if hasta is None:
        hasta = date.today()

    resultado = []
    dia = desde
    while dia <= hasta:
        resultado.append((dia, datos.get(dia.isoformat(), 0.0)))
        dia += timedelta(days=1)
    return resultado


class GraficaBarras(tk.Canvas):
    """
    Barras horizontales: una fila por concepto.
    datos: lista de dicts con 'nombre', 'costo' y 'porcentaje'.
    """

    def __init__(self, d, padre, alto=240, max_filas=7):
        super().__init__(
            padre, bg=d.BLANCO, height=alto, highlightthickness=0
        )
        self.d = d
        self.datos = []
        self.filas = []   # (y_arriba, y_abajo, dato) para el tooltip
        self.max_filas = max_filas
        self.bind("<Configure>", lambda e: self.dibujar())
        self.bind("<Motion>", self.al_mover)
        self.bind("<Leave>", lambda e: self.delete("hover"))

    def mostrar(self, datos):
        self.datos = datos[:self.max_filas]
        self.dibujar()

    def al_mover(self, evento):
        self.delete("hover")
        for arriba, abajo, f in self.filas:
            if arriba <= evento.y <= abajo:
                break
        else:
            return

        d = self.d
        registros = f.get("registros")
        detalle = f"{registros} merma(s) · " if registros is not None else ""
        etiqueta = self.create_text(
            evento.x, max(18, evento.y - 20),
            text=f"{f['nombre']}\n{detalle}${f['costo']:,.2f} ({f['porcentaje']:.1f}%)",
            fill=d.BLANCO, font=ui_tema.fuente_texto(9, "bold"),
            anchor="w" if evento.x < self.winfo_width() - 190 else "e",
            tags="hover"
        )
        caja = self.bbox(etiqueta)
        fondo = self.create_rectangle(
            caja[0] - 6, caja[1] - 4, caja[2] + 6, caja[3] + 4,
            fill=d.VERDE_OSCURO, outline="", tags="hover"
        )
        self.tag_lower(fondo, etiqueta)

    def dibujar(self):
        self.delete("all")
        self.filas = []
        d = self.d
        ancho, alto = self.winfo_width(), self.winfo_height()
        if ancho < 50 or alto < 50:
            return

        if not self.datos:
            self.create_text(
                ancho / 2, alto / 2, text="Sin datos en este periodo.",
                fill=d.TEXTO_SECUNDARIO, font=ui_tema.fuente_texto(10)
            )
            return

        margen_der = 112           # espacio para "$1,234 · 28%"
        margen_izq = min(175, ancho * 0.4)
        margen_v = 10
        n = len(self.datos)
        alto_fila = (alto - 2 * margen_v) / n
        grosor = min(24, alto_fila * 0.58)
        maximo = max(f["costo"] for f in self.datos) or 1
        largo = max(20, ancho - margen_izq - margen_der)

        for i, f in enumerate(self.datos):
            y = margen_v + alto_fila * i + alto_fila / 2
            color = PALETA[i % len(PALETA)]
            self.filas.append((y - alto_fila / 2, y + alto_fila / 2, f))

            self.create_text(
                margen_izq - 10, y,
                text=recortar(f["nombre"], max(8, int((margen_izq - 16) / 7.6))),
                anchor="e", fill=d.TEXTO, font=ui_tema.fuente_texto(9)
            )

            # Fondo tenue de la barra para ver la escala completa
            self.create_rectangle(
                margen_izq, y - grosor / 2, margen_izq + largo, y + grosor / 2,
                fill=ui_tema.VERDE_SUAVE, outline=""
            )
            self.create_rectangle(
                margen_izq, y - grosor / 2,
                margen_izq + max(3, largo * f["costo"] / maximo),
                y + grosor / 2,
                fill=color, outline=""
            )

            self.create_text(
                margen_izq + largo + 8, y,
                text=f"{formato_dinero(f['costo'])} · {f['porcentaje']:.0f}%",
                anchor="w", fill=d.TEXTO, font=ui_tema.fuente_texto(9, "bold")
            )


class GraficaLinea(tk.Canvas):
    """
    Línea con área suave: costo por día.
    datos: lista de (date, costo). Al pasar el mouse muestra el valor del día.
    """

    def __init__(self, d, padre, alto=240):
        super().__init__(
            padre, bg=d.BLANCO, height=alto, highlightthickness=0
        )
        self.d = d
        self.datos = []
        self.puntos = []
        self.bind("<Configure>", lambda e: self.dibujar())
        self.bind("<Motion>", self.al_mover)
        self.bind("<Leave>", lambda e: self.delete("hover"))

    def mostrar(self, datos):
        self.datos = datos
        self.dibujar()

    def dibujar(self):
        self.delete("all")
        self.puntos = []
        d = self.d
        ancho, alto = self.winfo_width(), self.winfo_height()
        if ancho < 120 or alto < 80:
            return

        if not self.datos or not any(c for _, c in self.datos):
            self.create_text(
                ancho / 2, alto / 2, text="Sin datos en este periodo.",
                fill=d.TEXTO_SECUNDARIO, font=ui_tema.fuente_texto(10)
            )
            return

        izq, der, arriba, abajo = 52, 16, 14, 30
        area_w, area_h = ancho - izq - der, alto - arriba - abajo
        n = len(self.datos)
        maximo = max(c for _, c in self.datos)
        tope = self.redondear_tope(maximo)

        # Líneas guía y eje Y
        for i in range(5):
            valor = tope * i / 4
            y = arriba + area_h - area_h * i / 4
            self.create_line(izq, y, ancho - der, y, fill=ui_tema.BORDE)
            self.create_text(
                izq - 8, y, text=formato_dinero(valor), anchor="e",
                fill=d.TEXTO_SECUNDARIO, font=ui_tema.fuente_texto(8)
            )

        def coordenadas(i, costo):
            x = izq + (area_w * i / (n - 1) if n > 1 else area_w / 2)
            y = arriba + area_h - area_h * costo / tope
            return x, y

        puntos = [coordenadas(i, c) for i, (_, c) in enumerate(self.datos)]
        self.puntos = [
            (x, y, dia, costo)
            for (x, y), (dia, costo) in zip(puntos, self.datos)
        ]

        # Área bajo la línea y la línea
        base = arriba + area_h
        if n > 1:
            poligono = [puntos[0][0], base]
            for x, y in puntos:
                poligono += [x, y]
            poligono += [puntos[-1][0], base]
            self.create_polygon(poligono, fill=ui_tema.VERDE_SUAVE, outline="")
            linea = [c for p in puntos for c in p]
            self.create_line(
                *linea, fill=d.VERDE_CLARO, width=2.5,
                joinstyle="round", capstyle="round"
            )

        radio = 3 if n <= 31 else 0
        if radio:
            for x, y in puntos:
                self.create_oval(
                    x - radio, y - radio, x + radio, y + radio,
                    fill=d.BLANCO, outline=d.VERDE_CLARO, width=2
                )

        # Etiquetas del eje X (como máximo ~7)
        paso = max(1, round(n / 7))
        for i in range(0, n, paso):
            dia = self.datos[i][0]
            self.create_text(
                puntos[i][0], alto - 14, text=dia.strftime("%d/%m"),
                fill=d.TEXTO_SECUNDARIO, font=ui_tema.fuente_texto(8)
            )

    @staticmethod
    def redondear_tope(maximo):
        """Tope "bonito" para el eje Y (1, 2, 5 × potencia de 10)."""
        if maximo <= 0:
            return 1
        potencia = 10 ** (len(str(int(maximo))) - 1)
        for factor in (1, 2, 2.5, 5, 10):
            if maximo <= potencia * factor:
                return potencia * factor
        return maximo

    def al_mover(self, evento):
        self.delete("hover")
        if not self.puntos:
            return

        x, y, dia, costo = min(self.puntos, key=lambda p: abs(p[0] - evento.x))
        d = self.d
        self.create_line(
            x, 14, x, self.winfo_height() - 30,
            fill=d.TEXTO_SECUNDARIO, dash=(3, 3), tags="hover"
        )
        self.create_oval(
            x - 5, y - 5, x + 5, y + 5,
            fill=d.VERDE_CLARO, outline=d.BLANCO, width=2, tags="hover"
        )

        texto = f"{dia.strftime('%d/%m/%Y')}\n${costo:,.2f}"
        ancho = self.winfo_width()
        caja_x = x + 12 if x < ancho - 110 else x - 12
        ancla = "w" if x < ancho - 110 else "e"
        etiqueta = self.create_text(
            caja_x, max(30, y - 18), text=texto, anchor=ancla,
            fill=d.BLANCO, font=ui_tema.fuente_texto(9, "bold"), tags="hover"
        )
        caja = self.bbox(etiqueta)
        fondo = self.create_rectangle(
            caja[0] - 6, caja[1] - 4, caja[2] + 6, caja[3] + 4,
            fill=d.VERDE_OSCURO, outline="", tags="hover"
        )
        self.tag_lower(fondo, etiqueta)
