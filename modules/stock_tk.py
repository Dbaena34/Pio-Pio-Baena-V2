"""
Módulo de Stock - CustomTkinter
Gestiona el stock de huevos e insumos, ajustes y movimientos
"""
from utils import config as util
from tkcalendar import DateEntry
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date, timedelta
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pandas as pd
import csv
import sys
sys.path.append('..')

from data.database import db
from data.models import StockRepository, InsumosRepository


class StockModule:

    def __init__(self, parent):
        self.parent = parent
        self.stock_repo = StockRepository(db)
        self.insumos_repo = InsumosRepository(db)
        self.categorias_huevos = ['C', 'B', 'A', 'AA', 'AAA', 'Jumbo']
        self.categorias_db = ['tipo_c', 'tipo_b', 'tipo_a', 'tipo_aa', 'tipo_aaa', 'tipo_jumbo']

        # Cache del DataFrame de insumos para reutilizar entre sub-secciones
        self._df_insumos = None

        self.create_ui()

    # ================= UI =================

    def create_ui(self):
        self.notebook = ctk.CTkTabview(
            self.parent,
            corner_radius=12,
            segmented_button_fg_color=util.CARD_BG,
            segmented_button_selected_color=util.PRIMARY,
            segmented_button_selected_hover_color=util.PRIMARY_HOVER,
            segmented_button_unselected_color="#e9ecef",
            text_color=util.TEXT_MAIN,
            fg_color="transparent"
        )
        self.notebook.pack(fill="both", expand=True, padx=40, pady=(20, 10))

        self.notebook.add("🥚 Huevos")
        self.notebook.add("🌾 Insumos")
        self.notebook.add("📋 Movimientos")

        self.notebook._segmented_button.configure(
            font=util.font_label(),
            height=40
        )

        self.create_huevos_tab()
        self.create_insumos_tab()
        self.create_movimientos_tab()

    # ================= TAB: HUEVOS =================

    def create_huevos_tab(self):
        tab = self.notebook.tab("🥚 Huevos")

        main = ctk.CTkScrollableFrame(tab)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # --- HEADER ---
        ctk.CTkLabel(
            main,
            text="🥚 Stock Actual de Huevos",
            font=util.font_title(),
            text_color=util.TEXT_MAIN
        ).pack(anchor="w", pady=(0, 10))

        # --- CARD: INVENTARIO ACTUAL ---
        card_inv = ctk.CTkFrame(main, corner_radius=12)
        card_inv.pack(fill="x", pady=10)

        inner_inv = ctk.CTkFrame(card_inv, fg_color="transparent")
        inner_inv.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(
            inner_inv,
            text="📊 Inventario Actual",
            font=util.font_section()
        ).pack(anchor="w", pady=(0, 10))

        # Fila de métricas por categoría
        frame_metrics = ctk.CTkFrame(inner_inv, fg_color="transparent")
        frame_metrics.pack(fill="x")

        self.metric_stock_labels = {}

        for i, (cat_db, cat) in enumerate(zip(self.categorias_db, self.categorias_huevos)):
            frame_metrics.grid_columnconfigure(i, weight=1)
            lbl = ctk.CTkLabel(
                frame_metrics,
                text=f"Tipo {cat}\n--",
                font=util.font_label()
            )
            lbl.grid(row=0, column=i, padx=10, pady=5)
            self.metric_stock_labels[cat_db] = lbl

        # Total + última actualización
        frame_total = ctk.CTkFrame(inner_inv, fg_color="transparent")
        frame_total.pack(fill="x", pady=(10, 0))
        frame_total.grid_columnconfigure(0, weight=1)
        frame_total.grid_columnconfigure(1, weight=2)

        self.label_total_stock = ctk.CTkLabel(
            frame_total,
            text="📦 TOTAL EN STOCK: --",
            font=util.font_section()
        )
        self.label_total_stock.grid(row=0, column=0, padx=10, sticky="w")

        self.label_ultima_actualizacion = ctk.CTkLabel(
            frame_total,
            text="🕐 Última actualización: --",
            font=util.font_label()
        )
        self.label_ultima_actualizacion.grid(row=0, column=1, padx=10, sticky="w")

        # Botón para recargar el inventario
        ctk.CTkButton(
            inner_inv,
            text="🔄 Actualizar Inventario",
            font=util.font_input(),
            height=36,
            fg_color=util.PRIMARY,
            hover_color=util.PRIMARY_HOVER,
            command=self.cargar_stock_huevos
        ).pack(pady=(12, 0))

        # --- CARD: GRÁFICOS ---
        card_graficos = ctk.CTkFrame(main, corner_radius=12)
        card_graficos.pack(fill="x", pady=10)

        inner_graf = ctk.CTkFrame(card_graficos, fg_color="transparent")
        inner_graf.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(
            inner_graf,
            text="📈 Distribución de Stock",
            font=util.font_section()
        ).pack(anchor="w", pady=(0, 8))

        self.frame_graficos_stock = ctk.CTkFrame(inner_graf, fg_color="transparent")
        self.frame_graficos_stock.pack(fill="x")

        # --- CARD: AJUSTE DE STOCK ---
        card_ajuste = ctk.CTkFrame(main, corner_radius=12)
        card_ajuste.pack(fill="x", pady=10)

        inner_ajuste = ctk.CTkFrame(card_ajuste, fg_color="transparent")
        inner_ajuste.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(
            inner_ajuste,
            text="⚙️ Ajustar Stock",
            font=util.font_section()
        ).pack(anchor="w", pady=(0, 8))

        # Tipo de ajuste (segmented button, más robusto que radio buttons)
        self.tipo_ajuste_var = ctk.StringVar(value="merma")

        ctk.CTkLabel(
            inner_ajuste,
            text="Tipo de ajuste",
            font=util.font_label()
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkSegmentedButton(
            inner_ajuste,
            values=["merma", "correccion"],
            variable=self.tipo_ajuste_var,
            font=util.font_label()
        ).pack(anchor="w", pady=(0, 10))

        # Inputs de cantidades por categoría
        ctk.CTkLabel(
            inner_ajuste,
            text="Cantidades:",
            font=util.font_label()
        ).pack(anchor="w", pady=(5, 5))

        grid_ajuste = ctk.CTkFrame(inner_ajuste, fg_color="transparent")
        grid_ajuste.pack()

        self.ajuste_entries = {}

        for i, cat in enumerate(self.categorias_huevos):
            grid_ajuste.grid_columnconfigure(i, weight=1)
            frame_cat = ctk.CTkFrame(grid_ajuste, corner_radius=8)
            frame_cat.grid(row=0, column=i, padx=6, sticky="nsew")

            ctk.CTkLabel(
                frame_cat,
                text=f"Tipo {cat}",
                font=util.font_label()
            ).pack(pady=(6, 0))

            entry = ctk.CTkEntry(
                frame_cat,
                height=40,
                justify="center",
                font=util.font_input()
            )
            entry.insert(0, "0")
            entry.pack(pady=5, fill="x", padx=5)
            self.ajuste_entries[cat] = entry

        # Motivo
        ctk.CTkLabel(
            inner_ajuste,
            text="Motivo del ajuste",
            font=util.font_label()
        ).pack(anchor="w", pady=(10, 4))

        self.motivo_ajuste_entry = ctk.CTkEntry(
            inner_ajuste,
            placeholder_text="Ej: Huevos rotos en transporte, Error de conteo...",
            font=util.font_text()
        )
        self.motivo_ajuste_entry.pack(fill="x")

        ctk.CTkButton(
            inner_ajuste,
            text="💾 Aplicar Ajuste",
            height=42,
            font=util.font_input(),
            fg_color="#e67e22",
            hover_color="#d35400",
            command=self.aplicar_ajuste_huevos
        ).pack(pady=(14, 0))

        # --- CARD: HISTORIAL DE AJUSTES ---
        card_hist = ctk.CTkFrame(main, corner_radius=12)
        card_hist.pack(fill="x", pady=10)

        inner_hist = ctk.CTkFrame(card_hist, fg_color="transparent")
        inner_hist.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(
            inner_hist,
            text="📜 Historial de Ajustes",
            font=util.font_section()
        ).pack(anchor="w", pady=(0, 8))

        frame_fechas_h = ctk.CTkFrame(inner_hist, fg_color="transparent")
        frame_fechas_h.pack(fill="x", pady=(0, 8))
        frame_fechas_h.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(frame_fechas_h, text="Desde", font=util.font_label()).grid(row=0, column=0, padx=5)

        self.hist_ajustes_inicio = DateEntry(
            frame_fechas_h, date_pattern='yyyy-mm-dd', font=("Arial", 14), width=12
        )
        self.hist_ajustes_inicio.set_date(date.today() - timedelta(days=30))
        self.hist_ajustes_inicio.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(frame_fechas_h, text="Hasta", font=util.font_label()).grid(row=0, column=2, padx=5)

        self.hist_ajustes_fin = DateEntry(
            frame_fechas_h, date_pattern='yyyy-mm-dd', font=("Arial", 14), width=12
        )
        self.hist_ajustes_fin.set_date(date.today())
        self.hist_ajustes_fin.grid(row=0, column=3, padx=5)

        ctk.CTkButton(
            inner_hist,
            text="🔍 Buscar Ajustes",
            font=util.font_input(),
            height=38,
            fg_color=util.PRIMARY,
            hover_color=util.PRIMARY_HOVER,
            command=self.cargar_historial_ajustes
        ).pack(pady=(0, 8))

        # Tabla de historial
        cols_hist = ("Fecha", "Hora", "Tipo", "C", "B", "A", "AA", "AAA", "Jumbo", "Total", "Motivo")
        self.tree_ajustes = ttk.Treeview(inner_hist, columns=cols_hist, show="headings", height=8)
        for col in cols_hist:
            self.tree_ajustes.heading(col, text=col)
            self.tree_ajustes.column(col, anchor="center", width=80 if col not in ("Fecha", "Motivo") else 100)
        self.tree_ajustes.pack(fill="x")

        # Carga inicial
        self.cargar_stock_huevos()

    def cargar_stock_huevos(self):
        try:
            stock = self.stock_repo.obtener_stock_actual()
            if not stock:
                messagebox.showwarning("Advertencia", "No se pudo obtener el stock actual")
                return

            total = 0
            for cat_db, cat in zip(self.categorias_db, self.categorias_huevos):
                cantidad = stock.get(cat_db, 0) or 0
                total += cantidad
                self.metric_stock_labels[cat_db].configure(text=f"Tipo {cat}\n{cantidad:,}")

            self.label_total_stock.configure(text=f"📦 TOTAL EN STOCK: {total:,} huevos")
            ultima = stock.get('updated_at', 'N/A')
            self.label_ultima_actualizacion.configure(text=f"🕐 Última actualización: {ultima}")

            # Gráficos
            self._generar_graficos_stock(stock)

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el stock: {str(e)}")

    def _generar_graficos_stock(self, stock):
        for widget in self.frame_graficos_stock.winfo_children():
            widget.destroy()

        datos = {cat: stock.get(cat_db, 0) or 0
                 for cat, cat_db in zip(self.categorias_huevos, self.categorias_db)}
        datos_filtrados = {k: v for k, v in datos.items() if v > 0}

        if not datos_filtrados:
            ctk.CTkLabel(
                self.frame_graficos_stock,
                text="ℹ️ Sin datos para graficar",
                font=util.font_label()
            ).pack()
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

        # Barras
        ax1.bar(list(datos_filtrados.keys()), list(datos_filtrados.values()),
                color="#3498db", edgecolor="white")
        ax1.set_title("Stock por Categoría", fontsize=11, weight='bold')
        ax1.set_ylabel("Cantidad")
        for i, (cat, val) in enumerate(datos_filtrados.items()):
            ax1.text(i, val + 0.5, str(val), ha='center', fontsize=9)
        ax1.grid(True, alpha=0.3, axis='y')

        # Pie
        ax2.pie(
            list(datos_filtrados.values()),
            labels=list(datos_filtrados.keys()),
            autopct='%1.1f%%',
            startangle=90
        )
        ax2.set_title("Distribución Porcentual", fontsize=11, weight='bold')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.frame_graficos_stock)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", pady=5)

    def aplicar_ajuste_huevos(self):
        tipo = self.tipo_ajuste_var.get()
        motivo = self.motivo_ajuste_entry.get().strip()

        try:
            ajustes = {cat: safe_int(self.ajuste_entries[cat].get()) for cat in self.categorias_huevos}
            total = sum(ajustes.values())

            if total == 0 and tipo != 'correccion':
                messagebox.showwarning("Advertencia", "Ingresa al menos un valor para ajustar")
                return

            if tipo == 'merma':
                ajustes_aplicar = {k: -v for k, v in ajustes.items()}
            else:
                ajustes_aplicar = ajustes

            self.stock_repo.registrar_ajuste_huevos(
                tipo_ajuste=tipo,
                tipo_c=ajustes_aplicar['C'],
                tipo_b=ajustes_aplicar['B'],
                tipo_a=ajustes_aplicar['A'],
                tipo_aa=ajustes_aplicar['AA'],
                tipo_aaa=ajustes_aplicar['AAA'],
                tipo_jumbo=ajustes_aplicar['Jumbo'],
                motivo=motivo if motivo else None
            )

            messagebox.showinfo("Éxito", "✅ Ajuste aplicado exitosamente")

            # Limpiar entradas
            for e in self.ajuste_entries.values():
                e.delete(0, "end")
                e.insert(0, "0")
            self.motivo_ajuste_entry.delete(0, "end")

            # Recargar inventario
            self.cargar_stock_huevos()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def cargar_historial_ajustes(self):
        for i in self.tree_ajustes.get_children():
            self.tree_ajustes.delete(i)

        try:
            fi = datetime.strptime(self.hist_ajustes_inicio.get(), "%Y-%m-%d").date()
            ff = datetime.strptime(self.hist_ajustes_fin.get(), "%Y-%m-%d").date()
        except:
            messagebox.showerror("Error", "Formato de fecha inválido (YYYY-MM-DD)")
            return

        try:
            historial = self.stock_repo.obtener_historial_ajustes_huevos(fi, ff)
            if not historial:
                messagebox.showinfo("Info", "No hay ajustes en el período seleccionado")
                return

            for r in historial:
                total = sum([
                    r.get('tipo_c', 0), r.get('tipo_b', 0), r.get('tipo_a', 0),
                    r.get('tipo_aa', 0), r.get('tipo_aaa', 0), r.get('tipo_jumbo', 0)
                ])
                self.tree_ajustes.insert("", "end", values=(
                    r.get("fecha"), r.get("hora"), r.get("tipo_ajuste"),
                    r.get('tipo_c', 0), r.get('tipo_b', 0), r.get('tipo_a', 0),
                    r.get('tipo_aa', 0), r.get('tipo_aaa', 0), r.get('tipo_jumbo', 0),
                    total, r.get("motivo", "")
                ))

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= TAB: INSUMOS =================

    def create_insumos_tab(self):
        tab = self.notebook.tab("🌾 Insumos")

        main = ctk.CTkScrollableFrame(tab)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # --- HEADER ---
        ctk.CTkLabel(
            main,
            text="🌾 Stock de Insumos",
            font=util.font_title(),
            text_color=util.TEXT_MAIN
        ).pack(anchor="w", pady=(0, 10))

        # --- CARD: ALERTAS ---
        self.card_alertas = ctk.CTkFrame(main, corner_radius=12, fg_color="#fdecea")
        # Se muestra solo si hay alertas (ver cargar_insumos)

        self.label_alertas = ctk.CTkLabel(
            self.card_alertas,
            text="",
            font=util.font_label(),
            text_color="#c0392b",
            justify="left",
            wraplength=600
        )
        self.label_alertas.pack(padx=15, pady=10)

        # --- CARD: INVENTARIO ---
        card_inv = ctk.CTkFrame(main, corner_radius=12)
        card_inv.pack(fill="x", pady=10)

        inner_inv = ctk.CTkFrame(card_inv, fg_color="transparent")
        inner_inv.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(
            inner_inv,
            text="📊 Inventario de Insumos",
            font=util.font_section()
        ).pack(anchor="w", pady=(0, 8))

        # Tabla de insumos
        cols_ins = ("Insumo", "Categoría", "Stock Actual", "Stock Mínimo", "Unidad")
        self.tree_insumos = ttk.Treeview(inner_inv, columns=cols_ins, show="headings", height=8)
        for col in cols_ins:
            self.tree_insumos.heading(col, text=col)
            self.tree_insumos.column(col, anchor="center", width=130)
        self.tree_insumos.pack(fill="x")

        ctk.CTkButton(
            inner_inv,
            text="🔄 Actualizar Insumos",
            font=util.font_input(),
            height=36,
            fg_color=util.PRIMARY,
            hover_color=util.PRIMARY_HOVER,
            command=self.cargar_insumos
        ).pack(pady=(10, 0))

        # --- CARD: GRÁFICO ---
        card_graf_ins = ctk.CTkFrame(main, corner_radius=12)
        card_graf_ins.pack(fill="x", pady=10)

        inner_graf_ins = ctk.CTkFrame(card_graf_ins, fg_color="transparent")
        inner_graf_ins.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(
            inner_graf_ins,
            text="📈 Stock por Categoría",
            font=util.font_section()
        ).pack(anchor="w", pady=(0, 8))

        self.frame_graficos_insumos = ctk.CTkFrame(inner_graf_ins, fg_color="transparent")
        self.frame_graficos_insumos.pack(fill="x")

        # --- CARD: GESTIÓN (SUB-TABS) ---
        card_gestion = ctk.CTkFrame(main, corner_radius=12)
        card_gestion.pack(fill="x", pady=10)

        inner_gest = ctk.CTkFrame(card_gestion, fg_color="transparent")
        inner_gest.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(
            inner_gest,
            text="⚙️ Gestión de Insumos",
            font=util.font_section()
        ).pack(anchor="w", pady=(0, 8))

        # Sub-tabs de gestión
        self.gestion_tabs = ctk.CTkTabview(
            inner_gest,
            corner_radius=10,
            fg_color="transparent"
        )
        self.gestion_tabs.pack(fill="x")
        self.gestion_tabs.add("📤 Consumo/Salida")
        self.gestion_tabs.add("✏️ Ajustar Stock")
        self.gestion_tabs.add("⚠️ Actualizar Mínimos")

        self._create_tab_consumo()
        self._create_tab_ajuste_insumo()
        self._create_tab_minimos()

        # Carga inicial
        self.cargar_insumos()

    def _create_tab_consumo(self):
        tab = self.gestion_tabs.tab("📤 Consumo/Salida")

        ctk.CTkLabel(
            tab, text="Registrar consumo o salida de insumo",
            font=util.font_label()
        ).pack(anchor="w", pady=(8, 4))

        # Selector de insumo
        ctk.CTkLabel(tab, text="Selecciona el insumo", font=util.font_text()).pack(anchor="w")

        self.consumo_insumo_var = ctk.StringVar(value="")
        self.consumo_insumo_combo = ttk.Combobox(
            tab,
            textvariable=self.consumo_insumo_var,
            state="readonly",
            font=("Arial", 13)
        )
        self.consumo_insumo_combo.bind("<<ComboboxSelected>>",
            lambda e: self._on_consumo_insumo_change(self.consumo_insumo_var.get()))
        self.consumo_insumo_combo.pack(fill="x", pady=4)

        # Info del insumo seleccionado
        self.label_consumo_info = ctk.CTkLabel(
            tab, text="", font=util.font_label(), text_color=util.PRIMARY
        )
        self.label_consumo_info.pack(anchor="w", pady=(2, 6))

        frame_consumo_row = ctk.CTkFrame(tab, fg_color="transparent")
        frame_consumo_row.pack(fill="x")
        frame_consumo_row.grid_columnconfigure(0, weight=1)
        frame_consumo_row.grid_columnconfigure(1, weight=2)

        ctk.CTkLabel(frame_consumo_row, text="Cantidad", font=util.font_text()).grid(
            row=0, column=0, padx=(0, 5), sticky="w"
        )
        ctk.CTkLabel(frame_consumo_row, text="Motivo", font=util.font_text()).grid(
            row=0, column=1, padx=(5, 0), sticky="w"
        )

        self.consumo_cantidad_entry = ctk.CTkEntry(
            frame_consumo_row, height=38, justify="center", font=util.font_input()
        )
        self.consumo_cantidad_entry.insert(0, "0")
        self.consumo_cantidad_entry.grid(row=1, column=0, padx=(0, 5), sticky="ew")

        self.consumo_motivo_entry = ctk.CTkEntry(
            frame_consumo_row,
            placeholder_text="Ej: Consumo diario, Mantenimiento...",
            font=util.font_text()
        )
        self.consumo_motivo_entry.grid(row=1, column=1, padx=(5, 0), sticky="ew")

        self.label_nuevo_stock_consumo = ctk.CTkLabel(
            tab, text="", font=util.font_label()
        )
        self.label_nuevo_stock_consumo.pack(anchor="w", pady=4)

        self.consumo_cantidad_entry.bind("<KeyRelease>", lambda e: self._calcular_nuevo_stock_consumo())

        ctk.CTkButton(
            tab,
            text="💾 Registrar Consumo",
            height=42,
            font=util.font_input(),
            fg_color="#2ecc71",
            hover_color="#27ae60",
            command=self.guardar_consumo_insumo
        ).pack(pady=(10, 5))

    def _create_tab_ajuste_insumo(self):
        tab = self.gestion_tabs.tab("✏️ Ajustar Stock")

        ctk.CTkLabel(
            tab, text="Ajustar stock manualmente",
            font=util.font_label()
        ).pack(anchor="w", pady=(8, 4))

        ctk.CTkLabel(tab, text="Selecciona el insumo", font=util.font_text()).pack(anchor="w")

        self.ajuste_ins_var = ctk.StringVar(value="")
        self.ajuste_ins_combo = ttk.Combobox(
            tab,
            textvariable=self.ajuste_ins_var,
            state="readonly",
            font=("Arial", 13)
        )
        self.ajuste_ins_combo.bind("<<ComboboxSelected>>",
            lambda e: self._on_ajuste_insumo_change(self.ajuste_ins_var.get()))
        self.ajuste_ins_combo.pack(fill="x", pady=4)

        self.label_ajuste_ins_info = ctk.CTkLabel(
            tab, text="", font=util.font_label(), text_color=util.PRIMARY
        )
        self.label_ajuste_ins_info.pack(anchor="w", pady=(2, 6))

        ctk.CTkLabel(tab, text="Nueva cantidad", font=util.font_text()).pack(anchor="w")

        self.ajuste_ins_cantidad_entry = ctk.CTkEntry(
            tab, height=38, justify="center", font=util.font_input()
        )
        self.ajuste_ins_cantidad_entry.insert(0, "0")
        self.ajuste_ins_cantidad_entry.pack(fill="x", pady=4)
        self.ajuste_ins_cantidad_entry.bind("<KeyRelease>", lambda e: self._calcular_diferencia_ajuste())

        self.label_diferencia_ajuste = ctk.CTkLabel(tab, text="", font=util.font_label())
        self.label_diferencia_ajuste.pack(anchor="w", pady=2)

        ctk.CTkLabel(tab, text="Motivo del ajuste", font=util.font_text()).pack(anchor="w")

        self.ajuste_ins_motivo_entry = ctk.CTkEntry(
            tab,
            placeholder_text="Ej: Corrección de inventario, Error de registro...",
            font=util.font_text()
        )
        self.ajuste_ins_motivo_entry.pack(fill="x", pady=4)

        ctk.CTkButton(
            tab,
            text="💾 Aplicar Ajuste",
            height=42,
            font=util.font_input(),
            fg_color="#e67e22",
            hover_color="#d35400",
            command=self.guardar_ajuste_insumo
        ).pack(pady=(10, 5))

    def _create_tab_minimos(self):
        tab = self.gestion_tabs.tab("⚠️ Actualizar Mínimos")

        ctk.CTkLabel(
            tab, text="Actualizar stocks mínimos",
            font=util.font_label()
        ).pack(anchor="w", pady=(8, 4))

        ctk.CTkLabel(tab, text="Selecciona el insumo", font=util.font_text()).pack(anchor="w")

        self.minimo_ins_var = ctk.StringVar(value="")
        self.minimo_ins_combo = ttk.Combobox(
            tab,
            textvariable=self.minimo_ins_var,
            state="readonly",
            font=("Arial", 13)
        )
        self.minimo_ins_combo.bind("<<ComboboxSelected>>",
            lambda e: self._on_minimo_insumo_change(self.minimo_ins_var.get()))
        self.minimo_ins_combo.pack(fill="x", pady=4)

        self.label_minimo_ins_info = ctk.CTkLabel(
            tab, text="", font=util.font_label(), text_color=util.PRIMARY
        )
        self.label_minimo_ins_info.pack(anchor="w", pady=(2, 6))

        ctk.CTkLabel(tab, text="Nuevo stock mínimo", font=util.font_text()).pack(anchor="w")

        self.minimo_ins_entry = ctk.CTkEntry(
            tab, height=38, justify="center", font=util.font_input()
        )
        self.minimo_ins_entry.insert(0, "0")
        self.minimo_ins_entry.pack(fill="x", pady=4)

        ctk.CTkButton(
            tab,
            text="💾 Actualizar Mínimo",
            height=42,
            font=util.font_input(),
            fg_color="#9b59b6",
            hover_color="#8e44ad",
            command=self.guardar_minimo_insumo
        ).pack(pady=(10, 5))

    def cargar_insumos(self):
        try:
            stock_insumos = self.stock_repo.obtener_stock_insumos()

            if not stock_insumos:
                messagebox.showinfo("Info", "No hay insumos registrados en el sistema")
                return

            self._df_insumos = pd.DataFrame(stock_insumos)
            df = self._df_insumos

            # Alertas de stock bajo
            alertas = [item for item in stock_insumos if item.get('alerta_stock', 0) == 1]
            if alertas:
                textos = [f"🔴 {a['nombre']} ({a['categoria']}): {a['cantidad_actual']} {a['unidad']} — Mín: {a['stock_minimo']}"
                          for a in alertas]
                self.label_alertas.configure(
                    text=f"⚠️ {len(alertas)} insumo(s) con stock bajo:\n" + "\n".join(textos)
                )
                self.card_alertas.pack(fill="x", pady=(0, 6), padx=20)
            else:
                self.card_alertas.pack_forget()

            # Llenar tabla
            for i in self.tree_insumos.get_children():
                self.tree_insumos.delete(i)

            for _, row in df.iterrows():
                self.tree_insumos.insert("", "end", values=(
                    row.get("nombre"),
                    row.get("categoria"),
                    row.get("cantidad_actual"),
                    row.get("stock_minimo"),
                    row.get("unidad")
                ))

            # Gráfico por categoría
            self._generar_grafico_insumos(df)

            # Actualizar combo boxes con los insumos
            opciones = [
                f"{row['nombre']} — Stock: {row['cantidad_actual']} {row['unidad']}"
                for _, row in df.iterrows()
            ]
            ids = df['insumo_id'].tolist()
            self._insumo_ids = ids
            self._insumo_opciones = opciones

            self.consumo_insumo_combo['values'] = opciones
            self.ajuste_ins_combo['values'] = opciones
            self.minimo_ins_combo['values'] = opciones

            if opciones:
                self.consumo_insumo_combo.set(opciones[0])
                self.ajuste_ins_combo.set(opciones[0])
                self.minimo_ins_combo.set(opciones[0])
                self._on_consumo_insumo_change(opciones[0])
                self._on_ajuste_insumo_change(opciones[0])
                self._on_minimo_insumo_change(opciones[0])

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar insumos: {str(e)}")

    def _generar_grafico_insumos(self, df):
        for widget in self.frame_graficos_insumos.winfo_children():
            widget.destroy()

        stock_cat = df.groupby('categoria')['cantidad_actual'].sum().reset_index()

        if stock_cat.empty:
            return

        fig, ax = plt.subplots(figsize=(8, 3.5))
        ax.bar(stock_cat['categoria'], stock_cat['cantidad_actual'], color="#52b788", edgecolor="white")
        ax.set_title("Stock Total por Categoría", fontsize=11, weight='bold')
        ax.set_ylabel("Cantidad")
        ax.grid(True, alpha=0.3, axis='y')
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.frame_graficos_insumos)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", pady=5)
        plt.close(fig)

    def _get_insumo_data(self, opcion_str):
        """Devuelve la fila del DataFrame correspondiente a la opción seleccionada en el combo."""
        if self._df_insumos is None or not hasattr(self, '_insumo_opciones'):
            return None
        try:
            idx = self._insumo_opciones.index(opcion_str)
            insumo_id = self._insumo_ids[idx]
            row = self._df_insumos[self._df_insumos['insumo_id'] == insumo_id]
            return row.iloc[0] if not row.empty else None
        except (ValueError, IndexError):
            return None

    def _on_consumo_insumo_change(self, opcion):
        data = self._get_insumo_data(opcion)
        if data is not None:
            self.label_consumo_info.configure(
                text=f"📦 Stock actual: {data['cantidad_actual']} {data['unidad']}"
            )
        self._calcular_nuevo_stock_consumo()

    def _calcular_nuevo_stock_consumo(self):
        data = self._get_insumo_data(self.consumo_insumo_var.get())
        if data is None:
            return
        try:
            cant = float(self.consumo_cantidad_entry.get() or 0)
            nuevo = data['cantidad_actual'] - cant
            self.label_nuevo_stock_consumo.configure(
                text=f"📊 Nuevo stock: {nuevo:.2f} {data['unidad']}"
            )
        except:
            pass

    def _on_ajuste_insumo_change(self, opcion):
        data = self._get_insumo_data(opcion)
        if data is not None:
            self.label_ajuste_ins_info.configure(
                text=f"📦 Stock actual: {data['cantidad_actual']} {data['unidad']}"
            )
            self.ajuste_ins_cantidad_entry.delete(0, "end")
            self.ajuste_ins_cantidad_entry.insert(0, str(data['cantidad_actual']))
        self._calcular_diferencia_ajuste()

    def _calcular_diferencia_ajuste(self):
        data = self._get_insumo_data(self.ajuste_ins_var.get())
        if data is None:
            return
        try:
            nueva = float(self.ajuste_ins_cantidad_entry.get() or 0)
            dif = nueva - data['cantidad_actual']
            flecha = "🔼" if dif > 0 else "🔽"
            self.label_diferencia_ajuste.configure(
                text=f"{flecha} Diferencia: {dif:+.2f} {data['unidad']}"
            )
        except:
            pass

    def _on_minimo_insumo_change(self, opcion):
        data = self._get_insumo_data(opcion)
        if data is not None:
            self.label_minimo_ins_info.configure(
                text=f"⚠️ Stock mínimo actual: {data['stock_minimo']} {data['unidad']}"
            )
            self.minimo_ins_entry.delete(0, "end")
            self.minimo_ins_entry.insert(0, str(data['stock_minimo']))

    def guardar_consumo_insumo(self):
        opcion = self.consumo_insumo_var.get()
        data = self._get_insumo_data(opcion)
        if data is None:
            messagebox.showwarning("Advertencia", "Selecciona un insumo")
            return

        try:
            cantidad = float(self.consumo_cantidad_entry.get() or 0)
            motivo = self.consumo_motivo_entry.get().strip()

            if cantidad <= 0:
                messagebox.showwarning("Advertencia", "Ingresa una cantidad mayor a 0")
                return
            if cantidad > data['cantidad_actual']:
                messagebox.showwarning("Advertencia", "La cantidad supera el stock disponible")
                return

            self.stock_repo.registrar_consumo_insumo(
                insumo_id=data['insumo_id'],
                cantidad=cantidad,
                motivo=motivo if motivo else None
            )

            messagebox.showinfo("Éxito", f"✅ Consumo registrado: {cantidad} {data['unidad']}")

            self.consumo_cantidad_entry.delete(0, "end")
            self.consumo_cantidad_entry.insert(0, "0")
            self.consumo_motivo_entry.delete(0, "end")
            self.cargar_insumos()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def guardar_ajuste_insumo(self):
        opcion = self.ajuste_ins_var.get()
        data = self._get_insumo_data(opcion)
        if data is None:
            messagebox.showwarning("Advertencia", "Selecciona un insumo")
            return

        try:
            nueva_cantidad = float(self.ajuste_ins_cantidad_entry.get() or 0)
            motivo = self.ajuste_ins_motivo_entry.get().strip()

            self.stock_repo.ajustar_stock_insumo(
                insumo_id=data['insumo_id'],
                nueva_cantidad=nueva_cantidad,
                motivo=motivo if motivo else "Ajuste manual"
            )

            messagebox.showinfo("Éxito", f"✅ Stock ajustado a {nueva_cantidad} {data['unidad']}")
            self.ajuste_ins_motivo_entry.delete(0, "end")
            self.cargar_insumos()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def guardar_minimo_insumo(self):
        opcion = self.minimo_ins_var.get()
        data = self._get_insumo_data(opcion)
        if data is None:
            messagebox.showwarning("Advertencia", "Selecciona un insumo")
            return

        try:
            nuevo_minimo = float(self.minimo_ins_entry.get() or 0)

            self.stock_repo.actualizar_stock_minimo(
                insumo_id=data['insumo_id'],
                stock_minimo=nuevo_minimo
            )

            messagebox.showinfo("Éxito", f"✅ Stock mínimo actualizado a {nuevo_minimo} {data['unidad']}")
            self.cargar_insumos()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= TAB: MOVIMIENTOS =================

    def create_movimientos_tab(self):
        tab = self.notebook.tab("📋 Movimientos")

        main = ctk.CTkScrollableFrame(tab)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # --- HEADER ---
        ctk.CTkLabel(
            main,
            text="📋 Historial de Movimientos",
            font=util.font_title(),
            text_color=util.TEXT_MAIN
        ).pack(anchor="w", pady=(0, 10))

        # --- CARD: FILTROS ---
        card_filtros = ctk.CTkFrame(main, corner_radius=12)
        card_filtros.pack(fill="x", pady=10)

        filtros = ctk.CTkFrame(card_filtros, fg_color="transparent")
        filtros.pack(padx=20, pady=15, fill="x")
        filtros.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        ctk.CTkLabel(filtros, text="Desde", font=util.font_label()).grid(row=0, column=0, padx=5)

        self.mov_fecha_inicio = DateEntry(
            filtros, date_pattern='yyyy-mm-dd', font=("Arial", 14), width=12
        )
        self.mov_fecha_inicio.set_date(date.today() - timedelta(days=30))
        self.mov_fecha_inicio.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(filtros, text="Hasta", font=util.font_label()).grid(row=0, column=2, padx=5)

        self.mov_fecha_fin = DateEntry(
            filtros, date_pattern='yyyy-mm-dd', font=("Arial", 14), width=12
        )
        self.mov_fecha_fin.set_date(date.today())
        self.mov_fecha_fin.grid(row=0, column=3, padx=5)

        ctk.CTkButton(
            filtros,
            text="🔍 Buscar",
            font=util.font_input(),
            height=40,
            fg_color=util.PRIMARY,
            hover_color=util.PRIMARY_HOVER,
            command=self.cargar_movimientos
        ).grid(row=0, column=4, padx=10)

        # --- SUB-TABS: ajustes huevos / movimientos insumos ---
        self.mov_tabs = ctk.CTkTabview(
            main,
            corner_radius=10,
            fg_color="transparent"
        )
        self.mov_tabs.pack(fill="both", expand=True, pady=10)
        self.mov_tabs.add("🥚 Ajustes de Huevos")
        self.mov_tabs.add("🌾 Movimientos de Insumos")

        # ---- Ajustes de Huevos ----
        tab_aj = self.mov_tabs.tab("🥚 Ajustes de Huevos")

        # Métricas
        self.frame_mov_metrics_aj = ctk.CTkFrame(tab_aj, fg_color="transparent")
        self.frame_mov_metrics_aj.pack(fill="x", pady=(8, 4))

        self.metric_aj_labels = []
        for _ in range(3):
            lbl = ctk.CTkLabel(self.frame_mov_metrics_aj, text="--", font=util.font_section())
            lbl.pack(side="left", expand=True, padx=10)
            self.metric_aj_labels.append(lbl)

        cols_aj = ("Fecha", "Hora", "Tipo", "C", "B", "A", "AA", "AAA", "Jumbo", "Total", "Motivo")
        self.tree_mov_ajustes = ttk.Treeview(tab_aj, columns=cols_aj, show="headings", height=10)
        for col in cols_aj:
            self.tree_mov_ajustes.heading(col, text=col)
            self.tree_mov_ajustes.column(col, anchor="center",
                                          width=80 if col not in ("Fecha", "Tipo", "Motivo") else 100)
        self.tree_mov_ajustes.pack(fill="x", padx=10, pady=8)

        # ---- Movimientos de Insumos ----
        tab_ins = self.mov_tabs.tab("🌾 Movimientos de Insumos")

        self.frame_mov_metrics_ins = ctk.CTkFrame(tab_ins, fg_color="transparent")
        self.frame_mov_metrics_ins.pack(fill="x", pady=(8, 4))

        self.metric_ins_labels = []
        for _ in range(2):
            lbl = ctk.CTkLabel(self.frame_mov_metrics_ins, text="--", font=util.font_section())
            lbl.pack(side="left", expand=True, padx=10)
            self.metric_ins_labels.append(lbl)

        cols_ins = ("Fecha", "Hora", "Insumo", "Categoría", "Tipo", "Cantidad", "Unidad", "Motivo")
        self.tree_mov_insumos = ttk.Treeview(tab_ins, columns=cols_ins, show="headings", height=10)
        for col in cols_ins:
            self.tree_mov_insumos.heading(col, text=col)
            self.tree_mov_insumos.column(col, anchor="center", width=100)
        self.tree_mov_insumos.pack(fill="x", padx=10, pady=8)

        # Botón exportar
        ctk.CTkButton(
            main,
            text="📥 Exportar Movimientos CSV",
            font=util.font_input(),
            height=40,
            fg_color=util.PRIMARY,
            hover_color=util.PRIMARY_HOVER,
            command=self.exportar_movimientos
        ).pack(pady=10)

    def cargar_movimientos(self):
        try:
            fi = datetime.strptime(self.mov_fecha_inicio.get(), "%Y-%m-%d").date()
            ff = datetime.strptime(self.mov_fecha_fin.get(), "%Y-%m-%d").date()
        except:
            messagebox.showerror("Error", "Formato de fecha inválido (YYYY-MM-DD)")
            return

        # -- Ajustes de huevos --
        for i in self.tree_mov_ajustes.get_children():
            self.tree_mov_ajustes.delete(i)

        try:
            data_aj = self.stock_repo.obtener_historial_ajustes_huevos(fi, ff)
            if data_aj:
                df_aj = pd.DataFrame(data_aj)
                df_aj['total'] = (
                    df_aj['tipo_c'] + df_aj['tipo_b'] + df_aj['tipo_a'] +
                    df_aj['tipo_aa'] + df_aj['tipo_aaa'] + df_aj['tipo_jumbo']
                )
                total_mermas = df_aj[df_aj['tipo_ajuste'] == 'merma']['total'].sum()
                total_corr = df_aj[df_aj['tipo_ajuste'] == 'correccion']['total'].sum()

                self.metric_aj_labels[0].configure(text=f"📋 Ajustes\n{len(df_aj)}")
                self.metric_aj_labels[1].configure(text=f"🔻 Mermas\n{abs(total_mermas):,}")
                self.metric_aj_labels[2].configure(text=f"✏️ Correcciones\n{total_corr:+,}")

                for r in data_aj:
                    total = sum([
                        r.get('tipo_c', 0), r.get('tipo_b', 0), r.get('tipo_a', 0),
                        r.get('tipo_aa', 0), r.get('tipo_aaa', 0), r.get('tipo_jumbo', 0)
                    ])
                    self.tree_mov_ajustes.insert("", "end", values=(
                        r.get("fecha"), r.get("hora"), r.get("tipo_ajuste"),
                        r.get('tipo_c', 0), r.get('tipo_b', 0), r.get('tipo_a', 0),
                        r.get('tipo_aa', 0), r.get('tipo_aaa', 0), r.get('tipo_jumbo', 0),
                        total, r.get("motivo", "")
                    ))
            else:
                for lbl in self.metric_aj_labels:
                    lbl.configure(text="--")
        except Exception as e:
            messagebox.showerror("Error", str(e))

        # -- Movimientos de insumos --
        for i in self.tree_mov_insumos.get_children():
            self.tree_mov_insumos.delete(i)

        try:
            data_ins = self.stock_repo.obtener_historial_movimientos_insumos(fi, ff)
            if data_ins:
                df_ins = pd.DataFrame(data_ins)
                total_salidas = df_ins[df_ins['tipo_movimiento'] == 'salida']['cantidad'].sum()

                self.metric_ins_labels[0].configure(text=f"📦 Movimientos\n{len(df_ins)}")
                self.metric_ins_labels[1].configure(text=f"📤 Salidas\n{total_salidas:.2f}")

                for r in data_ins:
                    self.tree_mov_insumos.insert("", "end", values=(
                        r.get("fecha"), r.get("hora"),
                        r.get("insumo_nombre"), r.get("categoria"),
                        r.get("tipo_movimiento"), r.get("cantidad"),
                        r.get("unidad"), r.get("motivo", "")
                    ))
            else:
                for lbl in self.metric_ins_labels:
                    lbl.configure(text="--")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def exportar_movimientos(self):
        try:
            fi = datetime.strptime(self.mov_fecha_inicio.get(), "%Y-%m-%d").date()
            ff = datetime.strptime(self.mov_fecha_fin.get(), "%Y-%m-%d").date()
        except:
            messagebox.showerror("Error", "Formato de fecha inválido")
            return

        file = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="Guardar movimientos"
        )
        if not file:
            return

        try:
            data_aj = self.stock_repo.obtener_historial_ajustes_huevos(fi, ff) or []
            data_ins = self.stock_repo.obtener_historial_movimientos_insumos(fi, ff) or []

            with open(file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                writer.writerow(["=== AJUSTES DE HUEVOS ==="])
                writer.writerow(["Fecha", "Hora", "Tipo", "C", "B", "A", "AA", "AAA", "Jumbo", "Total", "Motivo"])
                for r in data_aj:
                    total = sum([r.get('tipo_c', 0), r.get('tipo_b', 0), r.get('tipo_a', 0),
                                 r.get('tipo_aa', 0), r.get('tipo_aaa', 0), r.get('tipo_jumbo', 0)])
                    writer.writerow([
                        r.get("fecha"), r.get("hora"), r.get("tipo_ajuste"),
                        r.get('tipo_c', 0), r.get('tipo_b', 0), r.get('tipo_a', 0),
                        r.get('tipo_aa', 0), r.get('tipo_aaa', 0), r.get('tipo_jumbo', 0),
                        total, r.get("motivo", "")
                    ])

                writer.writerow([])
                writer.writerow(["=== MOVIMIENTOS DE INSUMOS ==="])
                writer.writerow(["Fecha", "Hora", "Insumo", "Categoría", "Tipo", "Cantidad", "Unidad", "Motivo"])
                for r in data_ins:
                    writer.writerow([
                        r.get("fecha"), r.get("hora"),
                        r.get("insumo_nombre"), r.get("categoria"),
                        r.get("tipo_movimiento"), r.get("cantidad"),
                        r.get("unidad"), r.get("motivo", "")
                    ])

            messagebox.showinfo("Exportado", "✅ CSV generado correctamente")

        except Exception as e:
            messagebox.showerror("Error", str(e))


# ================= UTILS =================

def safe_int(value):
    try:
        return int(value)
    except:
        return 0


# Función principal para llamar desde app.py
def render_stock(parent):
    """Función principal que se llama desde app.py"""
    module = StockModule(parent)
    return module
