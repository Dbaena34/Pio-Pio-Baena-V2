import customtkinter as ctk
from tkinter import ttk, messagebox
from utils import config as util
from data.explorador_repository import ExploradorRepository


class ExploradorDBModule:

    def __init__(self, parent):

        self.parent = parent
        self.repo = ExploradorRepository()

        self.df = None
        self.tabla_actual = None
        self.botones_tablas = {}

        self.create_ui()

    # ==========================================================
    # UI
    # ==========================================================

    def create_ui(self):

        main = ctk.CTkFrame(self.parent)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            main,
            text="🔎 Explorador de Base de Datos",
            font=util.font_title()
        ).pack(anchor="w", pady=(0, 15))

        top = ctk.CTkFrame(main)
        top.pack(fill="both", expand=True)

        top.grid_columnconfigure(1, weight=1)
        top.grid_rowconfigure(0, weight=1)

        # ======================================================
        # PANEL IZQUIERDO
        # ======================================================

        left = ctk.CTkFrame(top, width=220)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 15))

        ctk.CTkLabel(
            left,
            text="Tablas",
            font=util.font_section()
        ).pack(pady=10)

        self.lista_tablas = ctk.CTkScrollableFrame(
            left,
            width=180,
            height=500
        )

        self.lista_tablas.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 10)
        )

        # ======================================================
        # PANEL DERECHO
        # ======================================================

        right = ctk.CTkFrame(top)
        right.grid(row=0, column=1, sticky="nsew")

        barra = ctk.CTkFrame(right)
        barra.pack(fill="x", padx=10, pady=10)

        barra.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            barra,
            text="Buscar"
        ).grid(row=0, column=0, padx=5)

        self.buscar = ctk.CTkEntry(barra)

        self.buscar.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=5
        )

        self.buscar.bind(
            "<KeyRelease>",
            lambda e: self.filtrar()
        )

        ctk.CTkButton(
            barra,
            text="🔄",
            width=40,
            command=self.refrescar_tabla
        ).grid(row=0, column=2, padx=5)

        self.label_registros = ctk.CTkLabel(
            barra,
            text="0 registros"
        )

        self.label_registros.grid(
            row=0,
            column=3,
            padx=10
        )

        self.info_tabla = ctk.CTkLabel(
            right,
            text="Seleccione una tabla",
            font=util.font_label(),
            anchor="w"
        )

        self.info_tabla.pack(
            fill="x",
            padx=10,
            pady=(0, 8)
        )

        # ======================================================
        # TREEVIEW
        # ======================================================

        frame_tree = ctk.CTkFrame(right)
        frame_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(frame_tree)

        vsb = ttk.Scrollbar(
            frame_tree,
            orient="vertical",
            command=self.tree.yview
        )

        hsb = ttk.Scrollbar(
            frame_tree,
            orient="horizontal",
            command=self.tree.xview
        )

        self.tree.configure(
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        self.tree.bind(
            "<Double-1>",
            self.ver_registro
        )

        self.cargar_tablas()

    # ==========================================================
    # TABLAS
    # ==========================================================

    def cargar_tablas(self):

        for tabla in self.repo.obtener_tablas():

            btn = ctk.CTkButton(
                self.lista_tablas,
                text=tabla,
                command=lambda t=tabla: self.cargar_tabla(t)
            )

            btn.pack(fill="x", pady=2)

            self.botones_tablas[tabla] = btn

    def cargar_tabla(self, tabla):

        self.tabla_actual = tabla

        self.df = self.repo.obtener_dataframe(tabla)

        self.info_tabla.configure(
            text=(
                f"📄 Tabla: {tabla}    |    "
                f"📊 Registros: {len(self.df)}    |    "
                f"🧩 Columnas: {len(self.df.columns)}"
            )
        )

        for boton in self.botones_tablas.values():
            boton.configure(fg_color=util.SECUNDARY)

        self.botones_tablas[tabla].configure(
            fg_color=util.PRIMARY
        )

        self.mostrar_dataframe(self.df)

    def refrescar_tabla(self):

        if self.tabla_actual:
            self.cargar_tabla(self.tabla_actual)

    # ==========================================================
    # TREEVIEW
    # ==========================================================

    def mostrar_dataframe(self, df):

        self.tree.delete(*self.tree.get_children())

        columnas = list(df.columns)

        self.tree["columns"] = columnas
        self.tree["show"] = "headings"

        for c in columnas:

            self.tree.heading(
                c,
                text=c
            )

            ancho = max(
                len(c),
                df[c].astype(str).str.len().max() if len(df) else 0
            )

            ancho = min(max(ancho * 8, 80), 250)

            self.tree.column(
                c,
                width=ancho,
                anchor="center"
            )

        for fila in df.itertuples(index=False):

            self.tree.insert(
                "",
                "end",
                values=list(fila)
            )

        self.label_registros.configure(
            text=f"{len(df)} registros"
        )

    # ==========================================================
    # FILTRO
    # ==========================================================

    def filtrar(self):

        if self.df is None:
            return

        texto = self.buscar.get().lower()

        if texto == "":

            self.mostrar_dataframe(self.df)
            return

        filtro = self.df.astype(str).apply(
            lambda x: x.str.lower().str.contains(texto)
        ).any(axis=1)

        self.mostrar_dataframe(
            self.df[filtro]
        )

    # ==========================================================
    # DETALLE DEL REGISTRO
    # ==========================================================

    def ver_registro(self, event):

        item = self.tree.focus()

        if not item:
            return

        valores = self.tree.item(item)["values"]

        texto = ""

        for columna, valor in zip(self.df.columns, valores):

            texto += f"{columna}: {valor}\n"

        messagebox.showinfo(
            "Registro",
            texto
        )