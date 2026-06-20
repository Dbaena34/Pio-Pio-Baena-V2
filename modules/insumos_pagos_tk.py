"""
Módulo de Insumos y Pagos - CustomTkinter
Gestiona compras de insumos, pagos a trabajadores, configuración de precios y resumen financiero
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
from data.models import InsumosRepository, TrabajadoresRepository, PreciosRepository, ReportesRepository


class InsumosPagosModule:

    def __init__(self, parent):
        self.parent = parent
        self.insumos_repo = InsumosRepository(db)
        self.trabajadores_repo = TrabajadoresRepository(db)
        self.precios_repo = PreciosRepository(db)
        self.reportes_repo = ReportesRepository(db)
        self.categorias_huevos = ['C', 'B', 'A', 'AA', 'AAA', 'Jumbo']
        self.precios_db = ['precio_c', 'precio_b', 'precio_a', 'precio_aa', 'precio_aaa', 'precio_jumbo']

        self._trabajadores = []
        self._precios_actuales = {}
        self._df_historial_compras = None
        self._df_historial_pagos_gen = None

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

        self.notebook.add("🛒 Comprar Insumos")
        self.notebook.add("💵 Pagar Trabajadores")
        self.notebook.add("💲 Precios")
        self.notebook.add("📊 Resumen Financiero")

        self.notebook._segmented_button.configure(font=util.font_label(), height=40)

        self.create_comprar_tab()
        self.create_pagos_tab()
        self.create_precios_tab()
        self.create_resumen_tab()

    # ================= TAB: COMPRAR INSUMOS =================

    def create_comprar_tab(self):
        tab = self.notebook.tab("🛒 Comprar Insumos")
        main = ctk.CTkScrollableFrame(tab)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main, text="🛒 Registrar Compra de Insumos",
                     font=util.font_title(), text_color=util.TEXT_MAIN).pack(anchor="w", pady=(0, 10))

        # --- CARD: NUEVA COMPRA ---
        card = ctk.CTkFrame(main, corner_radius=12)
        card.pack(fill="x", pady=8)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(inner, text="📝 Nueva Compra",
                     font=util.font_section()).pack(anchor="w", pady=(0, 10))

        # Fila 1: fecha + proveedor
        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x", pady=4)
        row1.grid_columnconfigure(0, weight=1)
        row1.grid_columnconfigure(1, weight=2)

        ctk.CTkLabel(row1, text="Fecha de compra", font=util.font_label()).grid(
            row=0, column=0, sticky="w", padx=(0, 8))
        ctk.CTkLabel(row1, text="Proveedor (opcional)", font=util.font_label()).grid(
            row=0, column=1, sticky="w")

        self.compra_fecha = DateEntry(row1, date_pattern='yyyy-mm-dd',
                                     font=("Arial", 13), width=14)
        self.compra_fecha.set_date(date.today())
        self.compra_fecha.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)

        self.compra_proveedor = ctk.CTkEntry(row1, font=util.font_input(), height=36,
                                             placeholder_text="Nombre del proveedor")
        self.compra_proveedor.grid(row=1, column=1, sticky="ew", pady=4)

        # Fila 2: nombre + categoría
        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=4)
        row2.grid_columnconfigure(0, weight=1)
        row2.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row2, text="Nombre del insumo *", font=util.font_label()).grid(
            row=0, column=0, sticky="w", padx=(0, 8))
        ctk.CTkLabel(row2, text="Categoría *", font=util.font_label()).grid(
            row=0, column=1, sticky="w")


        self.compra_cat_var = ctk.StringVar(value="Alimento")
        self.compra_cat_combo = ttk.Combobox(
            row2, textvariable=self.compra_cat_var, state="readonly",
            font=("Arial", 13),
            values=['Alimento', 'Medicamento', 'Mantenimiento', 'Canastillas', 'Otros']
        )
        self.compra_cat_combo.grid(row=1, column=1, sticky="ew", pady=4)
        self.compra_cat_combo.bind("<<ComboboxSelected>>", lambda e: self._actualizar_opciones_nombre())
        
        self.compra_nombre = ttk.Combobox(row2, font=("Arial", 13))
        self.compra_nombre.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=4)
        self._actualizar_opciones_nombre()


        # Fila 3: cantidad + unidad
        row3 = ctk.CTkFrame(inner, fg_color="transparent")
        row3.pack(fill="x", pady=4)
        row3.grid_columnconfigure(0, weight=1)
        row3.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row3, text="Cantidad *", font=util.font_label()).grid(
            row=0, column=0, sticky="w", padx=(0, 8))
        ctk.CTkLabel(row3, text="Unidad *", font=util.font_label()).grid(
            row=0, column=1, sticky="w")

        self.compra_cantidad = ctk.CTkEntry(row3, font=util.font_input(), height=36,
                                            justify="center")
        self.compra_cantidad.insert(0, "0")
        self.compra_cantidad.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=4)
        self.compra_cantidad.bind("<KeyRelease>", lambda e: self._calcular_costo_total_compra())

        self.compra_unidad_var = ctk.StringVar(value="kg")
        self.compra_unidad_combo = ttk.Combobox(
            row3, textvariable=self.compra_unidad_var, state="readonly",
            font=("Arial", 13),
            values=['kg', 'bultos', 'litros', 'unidades']
        )
        self.compra_unidad_combo.grid(row=1, column=1, sticky="ew", pady=4)

        # Fila 4: costo unitario + costo total
        row4 = ctk.CTkFrame(inner, fg_color="transparent")
        row4.pack(fill="x", pady=4)
        row4.grid_columnconfigure(0, weight=1)
        row4.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row4, text="Costo unitario *", font=util.font_label()).grid(
            row=0, column=0, sticky="w", padx=(0, 8))
        ctk.CTkLabel(row4, text="Costo total *", font=util.font_label()).grid(
            row=0, column=1, sticky="w")

        self.compra_costo_unit = ctk.CTkEntry(row4, font=util.font_input(), height=36,
                                              justify="center")
        self.compra_costo_unit.insert(0, "0")
        self.compra_costo_unit.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=4)
        self.compra_costo_unit.bind("<KeyRelease>", lambda e: self._calcular_costo_total_compra())

        self.compra_costo_total = ctk.CTkEntry(row4, font=util.font_input(), height=36,
                                               justify="center")
        self.compra_costo_total.insert(0, "0")
        self.compra_costo_total.grid(row=1, column=1, sticky="ew", pady=4)

        # Resumen dinámico
        self.label_compra_resumen = ctk.CTkLabel(
            inner, text="", font=util.font_label(), text_color=util.PRIMARY)
        self.label_compra_resumen.pack(anchor="w", pady=(6, 0))

        ctk.CTkButton(
            inner, text="💾 Registrar Compra",
            height=44, font=util.font_input(),
            fg_color="#2ecc71", hover_color="#27ae60",
            command=self._registrar_compra
        ).pack(pady=(12, 0))

        # --- CARD: HISTORIAL DE COMPRAS ---
        card_hist = ctk.CTkFrame(main, corner_radius=12)
        card_hist.pack(fill="x", pady=8)
        inner_hist = ctk.CTkFrame(card_hist, fg_color="transparent")
        inner_hist.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(inner_hist, text="📋 Historial de Compras Recientes",
                     font=util.font_section()).pack(anchor="w", pady=(0, 8))

        frame_fechas = ctk.CTkFrame(inner_hist, fg_color="transparent")
        frame_fechas.pack(fill="x", pady=(0, 8))
        frame_fechas.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        ctk.CTkLabel(frame_fechas, text="Desde", font=util.font_label()).grid(row=0, column=0, padx=5)
        self.hist_compras_inicio = DateEntry(frame_fechas, date_pattern='yyyy-mm-dd',
                                            font=("Arial", 13), width=12)
        self.hist_compras_inicio.set_date(date.today() - timedelta(days=30))
        self.hist_compras_inicio.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(frame_fechas, text="Hasta", font=util.font_label()).grid(row=0, column=2, padx=5)
        self.hist_compras_fin = DateEntry(frame_fechas, date_pattern='yyyy-mm-dd',
                                         font=("Arial", 13), width=12)
        self.hist_compras_fin.set_date(date.today())
        self.hist_compras_fin.grid(row=0, column=3, padx=5)

        ctk.CTkButton(frame_fechas, text="🔍 Buscar",
                      font=util.font_input(), height=36,
                      fg_color=util.PRIMARY, hover_color=util.PRIMARY_HOVER,
                      command=self._cargar_historial_compras).grid(row=0, column=4, padx=8)

        # Métricas compras
        self.frame_compras_metrics = ctk.CTkFrame(inner_hist, fg_color="transparent")
        self.frame_compras_metrics.pack(fill="x", pady=(0, 8))
        self.compras_metric_labels = []
        for _ in range(3):
            lbl = ctk.CTkLabel(self.frame_compras_metrics, text="--", font=util.font_section())
            lbl.pack(side="left", expand=True, padx=10)
            self.compras_metric_labels.append(lbl)

        # Tabla historial compras
        cols_comp = ("Fecha", "Insumo", "Categoría", "Cantidad", "Unidad",
                     "Costo Unit.", "Costo Total", "Proveedor")
        self.tree_compras = ttk.Treeview(inner_hist, columns=cols_comp, show="headings", height=8)
        for col in cols_comp:
            self.tree_compras.heading(col, text=col)
            self.tree_compras.column(col, anchor="center",
                                     width=100 if col not in ("Insumo", "Proveedor") else 130)
        self.tree_compras.pack(fill="x")

        ctk.CTkButton(
            inner_hist, text="📥 Exportar CSV",
            font=util.font_input(), height=36,
            fg_color=util.PRIMARY, hover_color=util.PRIMARY_HOVER,
            command=self._exportar_compras
        ).pack(pady=(10, 0))

        self._cargar_historial_compras()

    def _actualizar_opciones_nombre(self):
        opciones_por_categoria = {
            'Alimento': ['Cuido'],
            'Canastillas': ['Canastillas'],
            'Medicamento': [],
            'Mantenimiento': [],
            'Otros': []
        }
        cat = self.compra_cat_var.get()
        opciones = opciones_por_categoria.get(cat, [])
        self.compra_nombre['values'] = opciones
        if opciones:
            self.compra_nombre.set(opciones[0])
        else:
            self.compra_nombre.set("")
    
    def _calcular_costo_total_compra(self):
        try:
            cant = safe_float(self.compra_cantidad.get())
            unit = safe_float(self.compra_costo_unit.get())
            total = cant * unit
            self.compra_costo_total.delete(0, "end")
            self.compra_costo_total.insert(0, f"{total:.2f}")
            unidad = self.compra_unidad_var.get()
            if total > 0 and cant > 0:
                self.label_compra_resumen.configure(
                    text=f"💰 Costo por {unidad}: ${total / cant:,.2f}   |   Total: ${total:,.2f}")
            else:
                self.label_compra_resumen.configure(text="")
        except:
            pass

    def _registrar_compra(self):
        nombre = self.compra_nombre.get().strip()
        cantidad = safe_float(self.compra_cantidad.get())
        costo_total = safe_float(self.compra_costo_total.get())
        costo_unit = safe_float(self.compra_costo_unit.get())

        if not nombre or cantidad <= 0 or costo_total <= 0:
            messagebox.showwarning("Advertencia", "Completa todos los campos obligatorios (*)")
            return

        try:
            fecha = datetime.strptime(self.compra_fecha.get(), "%Y-%m-%d").date()
            proveedor = self.compra_proveedor.get().strip()

            insumo_id = self.insumos_repo.registrar_compra_insumo(
                nombre=nombre,
                categoria=self.compra_cat_var.get(),
                cantidad=cantidad,
                unidad=self.compra_unidad_var.get(),
                costo_unitario=costo_unit,
                costo_total=costo_total,
                fecha_compra=fecha,
                proveedor=proveedor if proveedor else None
            )

            messagebox.showinfo("Éxito",
                f"✅ Compra registrada (ID: {insumo_id})\n"
                f"💰 Egreso: ${costo_total:,.2f}\n"
                f"📦 Stock actualizado: +{cantidad} {self.compra_unidad_var.get()}")

            # Limpiar formulario
            self.compra_nombre.delete(0, "end")
            self.compra_proveedor.delete(0, "end")
            self.compra_cantidad.delete(0, "end")
            self.compra_cantidad.insert(0, "0")
            self.compra_costo_unit.delete(0, "end")
            self.compra_costo_unit.insert(0, "0")
            self.compra_costo_total.delete(0, "end")
            self.compra_costo_total.insert(0, "0")
            self.label_compra_resumen.configure(text="")
            self._cargar_historial_compras()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _cargar_historial_compras(self):
        for i in self.tree_compras.get_children():
            self.tree_compras.delete(i)
        for lbl in self.compras_metric_labels:
            lbl.configure(text="--")

        try:
            fi = datetime.strptime(self.hist_compras_inicio.get(), "%Y-%m-%d").date()
            ff = datetime.strptime(self.hist_compras_fin.get(), "%Y-%m-%d").date()
            historial = self.insumos_repo.obtener_historial_compras(fi, ff)

            if not historial:
                return

            df = pd.DataFrame(historial)
            self._df_historial_compras = df

            total_gastado = df['costo_total'].sum()
            cat_top = df.groupby('categoria')['costo_total'].sum().idxmax() if not df.empty else "--"

            self.compras_metric_labels[0].configure(text=f"🧾 Compras\n{len(df)}")
            self.compras_metric_labels[1].configure(text=f"💰 Total Gastado\n${total_gastado:,.0f}")
            self.compras_metric_labels[2].configure(text=f"🏷️ Cat. Top\n{cat_top}")

            for _, row in df.iterrows():
                self.tree_compras.insert("", "end", values=(
                    row.get('fecha_compra'), row.get('nombre'), row.get('categoria'),
                    row.get('cantidad'), row.get('unidad'),
                    f"${row.get('costo_unitario', 0):,.2f}",
                    f"${row.get('costo_total', 0):,.0f}",
                    row.get('proveedor', '')
                ))

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _exportar_compras(self):
        if self._df_historial_compras is None or self._df_historial_compras.empty:
            messagebox.showwarning("Advertencia", "No hay datos. Haz una búsqueda primero.")
            return
        file = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")])
        if not file:
            return
        try:
            cols = ['fecha_compra', 'nombre', 'categoria', 'cantidad', 'unidad',
                    'costo_unitario', 'costo_total', 'proveedor']
            df_exp = self._df_historial_compras[
                [c for c in cols if c in self._df_historial_compras.columns]].copy()
            df_exp.columns = ['Fecha', 'Insumo', 'Categoría', 'Cantidad', 'Unidad',
                              'Costo Unit.', 'Costo Total', 'Proveedor']
            df_exp.to_csv(file, index=False, encoding='utf-8')
            messagebox.showinfo("Exportado", "✅ CSV generado correctamente")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= TAB: PAGAR TRABAJADORES =================

    def create_pagos_tab(self):
        tab = self.notebook.tab("💵 Pagar Trabajadores")
        main = ctk.CTkScrollableFrame(tab)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main, text="💵 Registrar Pago a Trabajadores",
                     font=util.font_title(), text_color=util.TEXT_MAIN).pack(anchor="w", pady=(0, 10))

        # --- CARD: NUEVO PAGO ---
        card_pago = ctk.CTkFrame(main, corner_radius=12)
        card_pago.pack(fill="x", pady=8)
        inner_pago = ctk.CTkFrame(card_pago, fg_color="transparent")
        inner_pago.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(inner_pago, text="💰 Nuevo Pago",
                     font=util.font_section()).pack(anchor="w", pady=(0, 8))

        # Selector trabajador + botón agregar
        frame_trab_row = ctk.CTkFrame(inner_pago, fg_color="transparent")
        frame_trab_row.pack(fill="x")
        frame_trab_row.grid_columnconfigure(0, weight=1)
        frame_trab_row.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(frame_trab_row, text="Seleccionar trabajador",
                     font=util.font_label()).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(frame_trab_row, text="", font=util.font_label()).grid(row=0, column=1)

        self.pago_trab_var = ctk.StringVar(value="")
        self.pago_trab_combo = ttk.Combobox(
            frame_trab_row, textvariable=self.pago_trab_var,
            state="readonly", font=("Arial", 13)
        )
        self.pago_trab_combo.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=4)
        self.pago_trab_combo.bind("<<ComboboxSelected>>", self._on_trabajador_selected)

        ctk.CTkButton(
            frame_trab_row, text="➕ Nuevo Trabajador",
            font=util.font_input(), height=36,
            fg_color=util.PRIMARY, hover_color=util.PRIMARY_HOVER,
            command=self._toggle_form_nuevo_trabajador
        ).grid(row=1, column=1)

        # Label info trabajador
        self.label_trabajador_info = ctk.CTkLabel(
            inner_pago, text="", font=util.font_label(), text_color=util.PRIMARY)
        self.label_trabajador_info.pack(anchor="w", pady=(4, 0))

        # Form nuevo trabajador (oculto)
        self.frame_nuevo_trabajador = ctk.CTkFrame(inner_pago, corner_radius=10)
        inner_nt = ctk.CTkFrame(self.frame_nuevo_trabajador, fg_color="transparent")
        inner_nt.pack(padx=15, pady=12, fill="x")

        ctk.CTkLabel(inner_nt, text="➕ Nuevo Trabajador",
                     font=util.font_section()).pack(anchor="w", pady=(0, 6))

        frame_nt_row = ctk.CTkFrame(inner_nt, fg_color="transparent")
        frame_nt_row.pack(fill="x")
        frame_nt_row.grid_columnconfigure(0, weight=1)
        frame_nt_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame_nt_row, text="Nombre", font=util.font_text()).grid(
            row=0, column=0, sticky="w", padx=(0, 5))
        ctk.CTkLabel(frame_nt_row, text="Cargo (opcional)", font=util.font_text()).grid(
            row=0, column=1, sticky="w", padx=(5, 0))

        self.nt_nombre = ctk.CTkEntry(frame_nt_row, font=util.font_input(), height=36)
        self.nt_nombre.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=4)

        self.nt_cargo = ctk.CTkEntry(frame_nt_row, font=util.font_input(), height=36)
        self.nt_cargo.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=4)

        frame_nt_btns = ctk.CTkFrame(inner_nt, fg_color="transparent")
        frame_nt_btns.pack(fill="x", pady=(4, 0))

        ctk.CTkButton(frame_nt_btns, text="💾 Guardar Trabajador",
                      font=util.font_input(), height=36,
                      fg_color="#2ecc71", hover_color="#27ae60",
                      command=self._guardar_nuevo_trabajador).pack(side="left", padx=(0, 8))
        ctk.CTkButton(frame_nt_btns, text="❌ Cancelar",
                      font=util.font_input(), height=36,
                      fg_color="#e74c3c", hover_color="#c0392b",
                      command=self._toggle_form_nuevo_trabajador).pack(side="left")

        # Fecha, hora, monto, concepto
        row_dt = ctk.CTkFrame(inner_pago, fg_color="transparent")
        row_dt.pack(fill="x", pady=(10, 4))
        row_dt.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(row_dt, text="Fecha del pago", font=util.font_label()).grid(
            row=0, column=0, sticky="w", padx=(0, 8))
        self.pago_fecha = DateEntry(row_dt, date_pattern='yyyy-mm-dd',
                                   font=("Arial", 13), width=14)
        self.pago_fecha.set_date(date.today())
        self.pago_fecha.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)

        ctk.CTkLabel(row_dt, text="Hora del pago", font=util.font_label()).grid(
            row=0, column=1, sticky="w", padx=(0, 8))
        self.pago_hora = ctk.CTkEntry(row_dt, width=130, height=35,
                                     font=util.font_input(), justify="center")
        self.pago_hora.insert(0, datetime.now().strftime("%H:%M:%S"))
        self.pago_hora.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=4)

        ctk.CTkLabel(row_dt, text="Monto a pagar *", font=util.font_label()).grid(
            row=0, column=2, sticky="w", padx=(0, 8))
        self.pago_monto = ctk.CTkEntry(row_dt, height=36, justify="center",
                                       font=util.font_input())
        self.pago_monto.insert(0, "0")
        self.pago_monto.grid(row=1, column=2, sticky="ew", padx=(0, 8), pady=4)

        ctk.CTkLabel(row_dt, text="Concepto", font=util.font_label()).grid(
            row=0, column=3, sticky="w")
        self.pago_concepto = ctk.CTkEntry(row_dt, font=util.font_input(), height=36,
                                          placeholder_text="Ej: Pago días 1-15...")
        self.pago_concepto.grid(row=1, column=3, sticky="ew", pady=4)

        ctk.CTkButton(
            inner_pago, text="💾 Registrar Pago",
            height=44, font=util.font_input(),
            fg_color="#2ecc71", hover_color="#27ae60",
            command=self._registrar_pago
        ).pack(pady=(12, 0))

        # --- CARD: HISTORIAL POR TRABAJADOR ---
        card_hist_trab = ctk.CTkFrame(main, corner_radius=12)
        card_hist_trab.pack(fill="x", pady=8)
        inner_ht = ctk.CTkFrame(card_hist_trab, fg_color="transparent")
        inner_ht.pack(padx=20, pady=15, fill="x")

        self.label_hist_trab_titulo = ctk.CTkLabel(
            inner_ht, text="📋 Historial de Pagos — Trabajador",
            font=util.font_section())
        self.label_hist_trab_titulo.pack(anchor="w", pady=(0, 8))

        frame_fechas_ht = ctk.CTkFrame(inner_ht, fg_color="transparent")
        frame_fechas_ht.pack(fill="x", pady=(0, 8))
        frame_fechas_ht.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        ctk.CTkLabel(frame_fechas_ht, text="Desde", font=util.font_label()).grid(row=0, column=0, padx=5)
        self.hist_trab_inicio = DateEntry(frame_fechas_ht, date_pattern='yyyy-mm-dd',
                                          font=("Arial", 13), width=12)
        self.hist_trab_inicio.set_date(date.today() - timedelta(days=30))
        self.hist_trab_inicio.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(frame_fechas_ht, text="Hasta", font=util.font_label()).grid(row=0, column=2, padx=5)
        self.hist_trab_fin = DateEntry(frame_fechas_ht, date_pattern='yyyy-mm-dd',
                                      font=("Arial", 13), width=12)
        self.hist_trab_fin.set_date(date.today())
        self.hist_trab_fin.grid(row=0, column=3, padx=5)

        ctk.CTkButton(frame_fechas_ht, text="🔍 Buscar",
                      font=util.font_input(), height=36,
                      fg_color=util.PRIMARY, hover_color=util.PRIMARY_HOVER,
                      command=self._cargar_hist_trabajador).grid(row=0, column=4, padx=8)

        self.frame_hist_trab_metrics = ctk.CTkFrame(inner_ht, fg_color="transparent")
        self.frame_hist_trab_metrics.pack(fill="x", pady=(0, 8))
        self.hist_trab_metric_labels = []
        for _ in range(3):
            lbl = ctk.CTkLabel(self.frame_hist_trab_metrics, text="--", font=util.font_section())
            lbl.pack(side="left", expand=True, padx=10)
            self.hist_trab_metric_labels.append(lbl)

        cols_ht = ("Fecha", "Hora", "Monto", "Concepto")
        self.tree_hist_trab = ttk.Treeview(inner_ht, columns=cols_ht, show="headings", height=6)
        for col in cols_ht:
            self.tree_hist_trab.heading(col, text=col)
            self.tree_hist_trab.column(col, anchor="center",
                                       width=100 if col != "Concepto" else 200)
        self.tree_hist_trab.pack(fill="x")

        # --- CARD: HISTORIAL GENERAL ---
        card_gen = ctk.CTkFrame(main, corner_radius=12)
        card_gen.pack(fill="x", pady=8)
        inner_gen = ctk.CTkFrame(card_gen, fg_color="transparent")
        inner_gen.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(inner_gen, text="📊 Historial General de Pagos",
                     font=util.font_section()).pack(anchor="w", pady=(0, 8))

        frame_fechas_gen = ctk.CTkFrame(inner_gen, fg_color="transparent")
        frame_fechas_gen.pack(fill="x", pady=(0, 8))
        frame_fechas_gen.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        ctk.CTkLabel(frame_fechas_gen, text="Desde", font=util.font_label()).grid(row=0, column=0, padx=5)
        self.hist_pagos_gen_inicio = DateEntry(frame_fechas_gen, date_pattern='yyyy-mm-dd',
                                              font=("Arial", 13), width=12)
        self.hist_pagos_gen_inicio.set_date(date.today() - timedelta(days=30))
        self.hist_pagos_gen_inicio.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(frame_fechas_gen, text="Hasta", font=util.font_label()).grid(row=0, column=2, padx=5)
        self.hist_pagos_gen_fin = DateEntry(frame_fechas_gen, date_pattern='yyyy-mm-dd',
                                           font=("Arial", 13), width=12)
        self.hist_pagos_gen_fin.set_date(date.today())
        self.hist_pagos_gen_fin.grid(row=0, column=3, padx=5)

        ctk.CTkButton(frame_fechas_gen, text="🔍 Buscar",
                      font=util.font_input(), height=36,
                      fg_color=util.PRIMARY, hover_color=util.PRIMARY_HOVER,
                      command=self._cargar_hist_pagos_general).grid(row=0, column=4, padx=8)

        self.frame_gen_metrics = ctk.CTkFrame(inner_gen, fg_color="transparent")
        self.frame_gen_metrics.pack(fill="x", pady=(0, 8))
        self.gen_metric_labels = []
        for _ in range(3):
            lbl = ctk.CTkLabel(self.frame_gen_metrics, text="--", font=util.font_section())
            lbl.pack(side="left", expand=True, padx=10)
            self.gen_metric_labels.append(lbl)

        self.frame_pagos_grafico = ctk.CTkFrame(inner_gen, fg_color="transparent")
        self.frame_pagos_grafico.pack(fill="x", pady=(0, 8))

        cols_gen = ("Fecha", "Trabajador", "Monto", "Concepto")
        self.tree_pagos_gen = ttk.Treeview(inner_gen, columns=cols_gen, show="headings", height=8)
        for col in cols_gen:
            self.tree_pagos_gen.heading(col, text=col)
            self.tree_pagos_gen.column(col, anchor="center",
                                       width=130 if col != "Concepto" else 200)
        self.tree_pagos_gen.pack(fill="x")

        ctk.CTkButton(
            inner_gen, text="📥 Exportar CSV",
            font=util.font_input(), height=36,
            fg_color=util.PRIMARY, hover_color=util.PRIMARY_HOVER,
            command=self._exportar_pagos
        ).pack(pady=(10, 0))

        self._cargar_trabajadores_combo()

    def _toggle_form_nuevo_trabajador(self):
        if self.frame_nuevo_trabajador.winfo_ismapped():
            self.frame_nuevo_trabajador.pack_forget()
        else:
            self.frame_nuevo_trabajador.pack(fill="x", pady=(8, 0))
            self.nt_nombre.focus()

    def _guardar_nuevo_trabajador(self):
        nombre = self.nt_nombre.get().strip()
        cargo = self.nt_cargo.get().strip()
        if not nombre:
            messagebox.showwarning("Advertencia", "Ingresa el nombre del trabajador")
            return
        try:
            self.trabajadores_repo.crear_trabajador(
                nombre=nombre,
                cargo=cargo if cargo else None
            )
            messagebox.showinfo("Éxito", f"✅ Trabajador '{nombre}' creado")
            self.frame_nuevo_trabajador.pack_forget()
            self.nt_nombre.delete(0, "end")
            self.nt_cargo.delete(0, "end")
            self._cargar_trabajadores_combo()
            self.pago_trab_combo.set(nombre)
            self.pago_trab_var.set(nombre)
            self._on_trabajador_selected(None)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _cargar_trabajadores_combo(self):
        try:
            self._trabajadores = self.trabajadores_repo.obtener_trabajadores_activos() or []
            nombres = [f"{t['nombre']} — {t.get('cargo', 'Sin cargo')}" for t in self._trabajadores]
            self.pago_trab_combo['values'] = nombres
            if nombres:
                self.pago_trab_combo.set(nombres[0])
                self.pago_trab_var.set(nombres[0])
                self._on_trabajador_selected(None)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_trabajador_selected(self, event):
        opcion = self.pago_trab_var.get()
        trab = self._get_trabajador_by_opcion(opcion)
        if trab:
            self.label_trabajador_info.configure(
                text=f"👤 {trab['nombre']} — {trab.get('cargo', 'Sin cargo')}")
            self.label_hist_trab_titulo.configure(
                text=f"📋 Historial de Pagos — {trab['nombre']}")

    def _get_trabajador_by_opcion(self, opcion):
        for t in self._trabajadores:
            label = f"{t['nombre']} — {t.get('cargo', 'Sin cargo')}"
            if label == opcion:
                return t
        return None

    def _registrar_pago(self):
        trab = self._get_trabajador_by_opcion(self.pago_trab_var.get())
        if not trab:
            messagebox.showwarning("Advertencia", "Selecciona un trabajador")
            return

        monto = safe_float(self.pago_monto.get())
        if monto <= 0:
            messagebox.showwarning("Advertencia", "Ingresa un monto mayor a 0")
            return

        try:
            fecha = datetime.strptime(self.pago_fecha.get(), "%Y-%m-%d").date()
            hora = self.pago_hora.get()
            concepto = self.pago_concepto.get().strip()

            pago_id = self.insumos_repo.registrar_pago_trabajador(
                trabajador_id=trab['id'],
                fecha=fecha,
                hora=hora,
                monto=monto,
                concepto=concepto if concepto else None
            )

            messagebox.showinfo("Éxito",
                f"✅ Pago registrado (ID: {pago_id})\n"
                f"💰 Egreso: ${monto:,.2f}")

            self.pago_monto.delete(0, "end")
            self.pago_monto.insert(0, "0")
            self.pago_concepto.delete(0, "end")
            self._cargar_hist_trabajador()
            self._cargar_hist_pagos_general()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _cargar_hist_trabajador(self):
        for i in self.tree_hist_trab.get_children():
            self.tree_hist_trab.delete(i)
        for lbl in self.hist_trab_metric_labels:
            lbl.configure(text="--")

        trab = self._get_trabajador_by_opcion(self.pago_trab_var.get())
        if not trab:
            return

        try:
            fi = datetime.strptime(self.hist_trab_inicio.get(), "%Y-%m-%d").date()
            ff = datetime.strptime(self.hist_trab_fin.get(), "%Y-%m-%d").date()
            pagos = self.insumos_repo.obtener_pagos_por_trabajador(trab['id'], fi, ff)

            if not pagos:
                return

            df = pd.DataFrame(pagos)
            total = df['monto'].sum()
            promedio = df['monto'].mean()

            self.hist_trab_metric_labels[0].configure(text=f"💳 Pagos\n{len(df)}")
            self.hist_trab_metric_labels[1].configure(text=f"💰 Total\n${total:,.0f}")
            self.hist_trab_metric_labels[2].configure(text=f"📊 Promedio\n${promedio:,.0f}")

            for _, row in df.iterrows():
                self.tree_hist_trab.insert("", "end", values=(
                    row.get('fecha'), row.get('hora'),
                    f"${row.get('monto', 0):,.0f}", row.get('concepto', '')
                ))

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _cargar_hist_pagos_general(self):
        for i in self.tree_pagos_gen.get_children():
            self.tree_pagos_gen.delete(i)
        for lbl in self.gen_metric_labels:
            lbl.configure(text="--")
        for w in self.frame_pagos_grafico.winfo_children():
            w.destroy()

        try:
            fi = datetime.strptime(self.hist_pagos_gen_inicio.get(), "%Y-%m-%d").date()
            ff = datetime.strptime(self.hist_pagos_gen_fin.get(), "%Y-%m-%d").date()
            historial = self.insumos_repo.obtener_historial_pagos(fi, ff)

            if not historial:
                return

            df = pd.DataFrame(historial)
            self._df_historial_pagos_gen = df

            total = df['monto'].sum()
            top = df.groupby('trabajador_nombre')['monto'].sum().idxmax()

            self.gen_metric_labels[0].configure(text=f"💳 Pagos\n{len(df)}")
            self.gen_metric_labels[1].configure(text=f"💰 Total\n${total:,.0f}")
            self.gen_metric_labels[2].configure(text=f"🏆 Top\n{top}")

            # Gráfico por trabajador
            pagos_por_trab = (df.groupby('trabajador_nombre')['monto']
                              .sum().sort_values(ascending=True))
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.barh(pagos_por_trab.index, pagos_por_trab.values, color="#9b59b6")
            ax.set_title("Total Pagado por Trabajador", fontsize=11, weight='bold')
            ax.set_xlabel("Total Pagado ($)")
            ax.grid(True, alpha=0.3, axis='x')
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=self.frame_pagos_grafico)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x", pady=5)
            plt.close(fig)

            for _, row in df.iterrows():
                self.tree_pagos_gen.insert("", "end", values=(
                    row.get('fecha'), row.get('trabajador_nombre'),
                    f"${row.get('monto', 0):,.0f}", row.get('concepto', '')
                ))

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _exportar_pagos(self):
        if self._df_historial_pagos_gen is None or self._df_historial_pagos_gen.empty:
            messagebox.showwarning("Advertencia", "No hay datos. Haz una búsqueda primero.")
            return
        file = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")])
        if not file:
            return
        try:
            cols = ['fecha', 'trabajador_nombre', 'monto', 'concepto']
            df_exp = self._df_historial_pagos_gen[
                [c for c in cols if c in self._df_historial_pagos_gen.columns]].copy()
            df_exp.columns = ['Fecha', 'Trabajador', 'Monto', 'Concepto']
            df_exp.to_csv(file, index=False, encoding='utf-8')
            messagebox.showinfo("Exportado", "✅ CSV generado correctamente")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= TAB: PRECIOS =================

    def create_precios_tab(self):
        tab = self.notebook.tab("💲 Precios")
        main = ctk.CTkScrollableFrame(tab)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main, text="💲 Configuración de Precios de Huevos",
                     font=util.font_title(), text_color=util.TEXT_MAIN).pack(anchor="w", pady=(0, 10))

        # --- CARD: PRECIOS ACTUALES ---
        card_act = ctk.CTkFrame(main, corner_radius=12)
        card_act.pack(fill="x", pady=8)
        inner_act = ctk.CTkFrame(card_act, fg_color="transparent")
        inner_act.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(inner_act, text="💰 Precios Actuales",
                     font=util.font_section()).pack(anchor="w", pady=(0, 4))

        self.label_vigencia_actual = ctk.CTkLabel(
            inner_act, text="", font=util.font_label(), text_color=util.PRIMARY)
        self.label_vigencia_actual.pack(anchor="w", pady=(0, 8))

        frame_precios_act = ctk.CTkFrame(inner_act, fg_color="transparent")
        frame_precios_act.pack(fill="x")
        self.precio_act_labels = {}
        for i, cat in enumerate(self.categorias_huevos):
            frame_precios_act.grid_columnconfigure(i, weight=1)
            lbl = ctk.CTkLabel(frame_precios_act, text=f"{cat}\n--\n--/can.", font=util.font_label())
            lbl.grid(row=0, column=i, padx=8, pady=4)
            self.precio_act_labels[cat] = lbl

        ctk.CTkButton(
            inner_act, text="🔄 Actualizar Vista",
            font=util.font_input(), height=34,
            fg_color=util.PRIMARY, hover_color=util.PRIMARY_HOVER,
            command=self._cargar_precios_actuales
        ).pack(pady=(10, 0))

        # --- CARD: ACTUALIZAR PRECIOS ---
        card_upd = ctk.CTkFrame(main, corner_radius=12)
        card_upd.pack(fill="x", pady=8)
        inner_upd = ctk.CTkFrame(card_upd, fg_color="transparent")
        inner_upd.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(inner_upd, text="✏️ Actualizar Precios",
                     font=util.font_section()).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            inner_upd,
            text="💡 Al actualizar se crea un nuevo registro y se desactiva el anterior automáticamente",
            font=util.font_label(), text_color="gray"
        ).pack(anchor="w", pady=(0, 8))

        # Fecha de vigencia
        frame_fv = ctk.CTkFrame(inner_upd, fg_color="transparent")
        frame_fv.pack(anchor="w", pady=(0, 8))
        ctk.CTkLabel(frame_fv, text="Fecha de vigencia", font=util.font_label()).pack(side="left", padx=(0, 8))
        self.precio_fecha_vigencia = DateEntry(frame_fv, date_pattern='yyyy-mm-dd',
                                               font=("Arial", 13), width=14)
        self.precio_fecha_vigencia.set_date(date.today())
        self.precio_fecha_vigencia.pack(side="left")

        ctk.CTkLabel(inner_upd, text="Nuevos precios por huevo:",
                     font=util.font_label()).pack(anchor="w", pady=(4, 6))

        # Grid de entries de precios
        grid_precios = ctk.CTkFrame(inner_upd, fg_color="transparent")
        grid_precios.pack()
        self.precio_entries = {}

        for i, cat in enumerate(self.categorias_huevos):
            grid_precios.grid_columnconfigure(i, weight=1)
            fc = ctk.CTkFrame(grid_precios, corner_radius=8)
            fc.grid(row=0, column=i, padx=6, sticky="nsew")
            ctk.CTkLabel(fc, text=f"💰 {cat}", font=util.font_label()).pack(pady=(6, 0))
            e = ctk.CTkEntry(fc, height=40, justify="center", font=util.font_input())
            e.insert(0, "0")
            e.pack(pady=5, fill="x", padx=5)
            e.bind("<KeyRelease>", lambda ev: self._actualizar_preview_canastillas())
            self.precio_entries[cat] = e

        # Preview precios por canastilla
        ctk.CTkLabel(inner_upd, text="Precios por canastilla (30 huevos):",
                     font=util.font_label()).pack(anchor="w", pady=(10, 4))

        frame_prev = ctk.CTkFrame(inner_upd, fg_color="transparent")
        frame_prev.pack(fill="x")
        self.precio_preview_labels = {}
        for i, cat in enumerate(self.categorias_huevos):
            frame_prev.grid_columnconfigure(i, weight=1)
            lbl = ctk.CTkLabel(frame_prev, text=f"{cat}: $0", font=util.font_label(),
                               text_color="#27ae60")
            lbl.grid(row=0, column=i, padx=8, pady=4)
            self.precio_preview_labels[cat] = lbl

        ctk.CTkButton(
            inner_upd, text="💾 Guardar Nuevos Precios",
            height=44, font=util.font_input(),
            fg_color="#2ecc71", hover_color="#27ae60",
            command=self._guardar_precios
        ).pack(pady=(14, 0))

        # --- CARD: HISTORIAL DE PRECIOS ---
        card_hist_p = ctk.CTkFrame(main, corner_radius=12)
        card_hist_p.pack(fill="x", pady=8)
        inner_hist_p = ctk.CTkFrame(card_hist_p, fg_color="transparent")
        inner_hist_p.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(inner_hist_p, text="📜 Historial de Precios",
                     font=util.font_section()).pack(anchor="w", pady=(0, 8))

        cols_hp = ("Fecha Vigencia", "C", "B", "A", "AA", "AAA", "Jumbo", "Activo")
        self.tree_hist_precios = ttk.Treeview(inner_hist_p, columns=cols_hp,
                                              show="headings", height=6)
        for col in cols_hp:
            self.tree_hist_precios.heading(col, text=col)
            self.tree_hist_precios.column(col, anchor="center", width=100)
        self.tree_hist_precios.pack(fill="x")

        self._cargar_precios_actuales()

    def _cargar_precios_actuales(self):
        try:
            precios = self.precios_repo.obtener_precio_actual()
            self._precios_actuales = precios or {}

            if precios:
                vigencia = precios.get('fecha_vigencia', 'N/A')
                self.label_vigencia_actual.configure(
                    text=f"📅 Vigente desde: {vigencia}")

                for cat, precio_db in zip(self.categorias_huevos, self.precios_db):
                    precio = precios.get(precio_db, 0) or 0
                    precio_can = precio * 30
                    self.precio_act_labels[cat].configure(
                        text=f"{cat}\n${precio:,.0f}/huevo\n${precio_can:,.0f}/can.")
                    # Precargar entries con valores actuales
                    self.precio_entries[cat].delete(0, "end")
                    self.precio_entries[cat].insert(0, str(int(precio)))
                self._actualizar_preview_canastillas()
            else:
                self.label_vigencia_actual.configure(text="⚠️ No hay precios configurados")

            # Historial
            self._cargar_historial_precios()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _actualizar_preview_canastillas(self):
        for cat in self.categorias_huevos:
            try:
                precio = safe_float(self.precio_entries[cat].get())
                self.precio_preview_labels[cat].configure(
                    text=f"{cat}: ${precio * 30:,.0f}")
            except:
                pass

    def _guardar_precios(self):
        nuevos = {cat: safe_float(self.precio_entries[cat].get())
                  for cat in self.categorias_huevos}

        if any(v <= 0 for v in nuevos.values()):
            messagebox.showwarning("Advertencia", "Todos los precios deben ser mayores a 0")
            return

        try:
            fecha = datetime.strptime(self.precio_fecha_vigencia.get(), "%Y-%m-%d").date()
            precio_id = self.precios_repo.crear_nuevo_precio(
                fecha_vigencia=fecha,
                precio_c=nuevos['C'],
                precio_b=nuevos['B'],
                precio_a=nuevos['A'],
                precio_aa=nuevos['AA'],
                precio_aaa=nuevos['AAA'],
                precio_jumbo=nuevos['Jumbo']
            )
            messagebox.showinfo("Éxito", f"✅ Precios actualizados exitosamente (ID: {precio_id})")
            self._cargar_precios_actuales()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _cargar_historial_precios(self):
        for i in self.tree_hist_precios.get_children():
            self.tree_hist_precios.delete(i)
        try:
            historial = self.precios_repo.obtener_historial_precios(limit=10)
            if not historial:
                return
            for row in historial:
                activo = '✅' if row.get('activo') == 1 else '❌'
                self.tree_hist_precios.insert("", "end", values=(
                    row.get('fecha_vigencia'),
                    f"${row.get('precio_c', 0):,.0f}",
                    f"${row.get('precio_b', 0):,.0f}",
                    f"${row.get('precio_a', 0):,.0f}",
                    f"${row.get('precio_aa', 0):,.0f}",
                    f"${row.get('precio_aaa', 0):,.0f}",
                    f"${row.get('precio_jumbo', 0):,.0f}",
                    activo
                ))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= TAB: RESUMEN FINANCIERO =================

    def create_resumen_tab(self):
        tab = self.notebook.tab("📊 Resumen Financiero")
        main = ctk.CTkScrollableFrame(tab)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main, text="📊 Resumen Financiero de Egresos",
                     font=util.font_title(), text_color=util.TEXT_MAIN).pack(anchor="w", pady=(0, 10))

        # Filtros
        card_filtros = ctk.CTkFrame(main, corner_radius=12)
        card_filtros.pack(fill="x", pady=8)
        filtros = ctk.CTkFrame(card_filtros, fg_color="transparent")
        filtros.pack(padx=20, pady=15, fill="x")
        filtros.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        ctk.CTkLabel(filtros, text="Desde", font=util.font_label()).grid(row=0, column=0, padx=5)
        self.resumen_inicio = DateEntry(filtros, date_pattern='yyyy-mm-dd',
                                       font=("Arial", 13), width=12)
        self.resumen_inicio.set_date(date.today() - timedelta(days=30))
        self.resumen_inicio.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(filtros, text="Hasta", font=util.font_label()).grid(row=0, column=2, padx=5)
        self.resumen_fin = DateEntry(filtros, date_pattern='yyyy-mm-dd',
                                    font=("Arial", 13), width=12)
        self.resumen_fin.set_date(date.today())
        self.resumen_fin.grid(row=0, column=3, padx=5)

        ctk.CTkButton(filtros, text="📊 Generar",
                      font=util.font_input(), height=38,
                      fg_color=util.PRIMARY, hover_color=util.PRIMARY_HOVER,
                      command=self._cargar_resumen_financiero).grid(row=0, column=4, padx=8)

        # Métricas principales
        card_metrics = ctk.CTkFrame(main, corner_radius=12)
        card_metrics.pack(fill="x", pady=8)
        self.frame_resumen_metrics = ctk.CTkFrame(card_metrics, fg_color="transparent")
        self.frame_resumen_metrics.pack(padx=20, pady=15, fill="x")
        self.resumen_metric_labels = []
        for _ in range(4):
            lbl = ctk.CTkLabel(self.frame_resumen_metrics, text="--", font=util.font_section())
            lbl.pack(side="left", expand=True, padx=10)
            self.resumen_metric_labels.append(lbl)

        # Gráficos egresos por categoría
        card_graf_egr = ctk.CTkFrame(main, corner_radius=12)
        card_graf_egr.pack(fill="x", pady=8)
        inner_graf_egr = ctk.CTkFrame(card_graf_egr, fg_color="transparent")
        inner_graf_egr.pack(padx=20, pady=15, fill="x")
        ctk.CTkLabel(inner_graf_egr, text="📊 Egresos por Categoría",
                     font=util.font_section()).pack(anchor="w", pady=(0, 8))
        self.frame_egr_graficos = ctk.CTkFrame(inner_graf_egr, fg_color="transparent")
        self.frame_egr_graficos.pack(fill="x")

        cols_egr = ("Categoría", "Cantidad", "Total")
        self.tree_egresos = ttk.Treeview(inner_graf_egr, columns=cols_egr,
                                         show="headings", height=5)
        for col in cols_egr:
            self.tree_egresos.heading(col, text=col)
            self.tree_egresos.column(col, anchor="center", width=180)
        self.tree_egresos.pack(fill="x", pady=(8, 0))

        # Compras por categoría
        card_compras_cat = ctk.CTkFrame(main, corner_radius=12)
        card_compras_cat.pack(fill="x", pady=8)
        inner_cc = ctk.CTkFrame(card_compras_cat, fg_color="transparent")
        inner_cc.pack(padx=20, pady=15, fill="x")
        ctk.CTkLabel(inner_cc, text="🛒 Compras de Insumos por Categoría",
                     font=util.font_section()).pack(anchor="w", pady=(0, 8))

        # Frame intermedio exclusivo para grid de 2 columnas
        row_cc = ctk.CTkFrame(inner_cc, fg_color="transparent")
        row_cc.pack(fill="x")
        row_cc.grid_columnconfigure(0, weight=1)
        row_cc.grid_columnconfigure(1, weight=1)

        frame_cc_tabla = ctk.CTkFrame(row_cc, fg_color="transparent")
        frame_cc_tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        cols_cc = ("Categoría", "Compras", "Total Gastado")
        self.tree_compras_cat = ttk.Treeview(frame_cc_tabla, columns=cols_cc,
                                             show="headings", height=6)
        for col in cols_cc:
            self.tree_compras_cat.heading(col, text=col)
            self.tree_compras_cat.column(col, anchor="center", width=140)
        self.tree_compras_cat.pack(fill="x")

        self.frame_cc_grafico = ctk.CTkFrame(row_cc, fg_color="transparent")
        self.frame_cc_grafico.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # Pagos trabajadores
        card_pag_trab = ctk.CTkFrame(main, corner_radius=12)
        card_pag_trab.pack(fill="x", pady=8)
        inner_pt = ctk.CTkFrame(card_pag_trab, fg_color="transparent")
        inner_pt.pack(padx=20, pady=15, fill="x")
        ctk.CTkLabel(inner_pt, text="💵 Pagos a Trabajadores",
                     font=util.font_section()).pack(anchor="w", pady=(0, 8))

        # Frame intermedio exclusivo para grid de 2 columnas
        row_pt = ctk.CTkFrame(inner_pt, fg_color="transparent")
        row_pt.pack(fill="x")
        row_pt.grid_columnconfigure(0, weight=1)
        row_pt.grid_columnconfigure(1, weight=1)

        frame_pt_tabla = ctk.CTkFrame(row_pt, fg_color="transparent")
        frame_pt_tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        cols_pt = ("Trabajador", "Total Pagado", "Cant. Pagos")
        self.tree_pagos_trab = ttk.Treeview(frame_pt_tabla, columns=cols_pt,
                                            show="headings", height=6)
        for col in cols_pt:
            self.tree_pagos_trab.heading(col, text=col)
            self.tree_pagos_trab.column(col, anchor="center", width=140)
        self.tree_pagos_trab.pack(fill="x")

        self.frame_pt_grafico = ctk.CTkFrame(row_pt, fg_color="transparent")
        self.frame_pt_grafico.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

    def _cargar_resumen_financiero(self):
        # Limpiar gráficos
        for w in self.frame_egr_graficos.winfo_children():
            w.destroy()
        for w in self.frame_cc_grafico.winfo_children():
            w.destroy()
        for w in self.frame_pt_grafico.winfo_children():
            w.destroy()
        for i in self.tree_egresos.get_children():
            self.tree_egresos.delete(i)
        for i in self.tree_compras_cat.get_children():
            self.tree_compras_cat.delete(i)
        for i in self.tree_pagos_trab.get_children():
            self.tree_pagos_trab.delete(i)

        try:
            fi = datetime.strptime(self.resumen_inicio.get(), "%Y-%m-%d").date()
            ff = datetime.strptime(self.resumen_fin.get(), "%Y-%m-%d").date()
        except:
            messagebox.showerror("Error", "Formato de fecha inválido")
            return

        try:
            balance = self.reportes_repo.obtener_balance_periodo(fi, ff)
            movimientos_cat = self.reportes_repo.obtener_movimientos_por_categoria(fi, ff)
            compras_cat = self.insumos_repo.obtener_compras_por_categoria(fi, ff)
            historial_pagos = self.insumos_repo.obtener_historial_pagos(fi, ff)

            # Métricas principales
            total_egr = balance.get('total_egresos', 0) or 0
            total_ing = balance.get('total_ingresos', 0) or 0
            balance_neto = balance.get('balance', 0) or 0
            margen = f"{(balance_neto / total_ing * 100):.1f}%" if total_ing > 0 else "N/A"

            self.resumen_metric_labels[0].configure(text=f"📉 Egresos\n${total_egr:,.0f}")
            self.resumen_metric_labels[1].configure(text=f"📈 Ingresos\n${total_ing:,.0f}")
            signo = "✅" if balance_neto >= 0 else "⚠️"
            self.resumen_metric_labels[2].configure(
                text=f"{signo} Balance\n${balance_neto:,.0f}")
            self.resumen_metric_labels[3].configure(text=f"📊 Margen\n{margen}")

            # Egresos por categoría
            if movimientos_cat:
                df_mov = pd.DataFrame(movimientos_cat)
                df_egr = df_mov[df_mov['tipo'] == 'egreso']

                if not df_egr.empty:
                    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.5))
                    ax1.bar(df_egr['categoria'], df_egr['total'],
                            color="#e74c3c", edgecolor="white")
                    ax1.set_title("Egresos por Categoría", fontsize=10, weight='bold')
                    ax1.set_ylabel("Total ($)")
                    ax1.tick_params(axis='x', rotation=30)
                    ax1.grid(True, alpha=0.3, axis='y')

                    ax2.pie(df_egr['total'], labels=df_egr['categoria'],
                            autopct='%1.1f%%', startangle=90)
                    ax2.set_title("Distribución (%)", fontsize=10, weight='bold')

                    fig.tight_layout()
                    canvas = FigureCanvasTkAgg(fig, master=self.frame_egr_graficos)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill="x", pady=5)
                    plt.close(fig)

                    for _, row in df_egr.iterrows():
                        self.tree_egresos.insert("", "end", values=(
                            row.get('categoria'),
                            row.get('cantidad_movimientos'),
                            f"${row.get('total', 0):,.0f}"
                        ))

            # Compras por categoría
            if compras_cat:
                df_cc = pd.DataFrame(compras_cat)
                for _, row in df_cc.iterrows():
                    self.tree_compras_cat.insert("", "end", values=(
                        row.get('categoria'),
                        row.get('cantidad_compras'),
                        f"${row.get('total_gastado', 0):,.0f}"
                    ))

                fig2, ax = plt.subplots(figsize=(4.5, 3.5))
                ax.pie(df_cc['total_gastado'], labels=df_cc['categoria'],
                       autopct='%1.1f%%', startangle=90)
                ax.set_title("Gastos en Insumos", fontsize=10, weight='bold')
                fig2.tight_layout()
                canvas2 = FigureCanvasTkAgg(fig2, master=self.frame_cc_grafico)
                canvas2.draw()
                canvas2.get_tk_widget().pack(fill="x", pady=5)
                plt.close(fig2)

            # Pagos trabajadores
            if historial_pagos:
                df_pt = pd.DataFrame(historial_pagos)
                resumen_pt = (df_pt.groupby('trabajador_nombre')['monto']
                              .agg(['sum', 'count']).reset_index())
                resumen_pt.columns = ['Trabajador', 'Total', 'Pagos']

                for _, row in resumen_pt.iterrows():
                    self.tree_pagos_trab.insert("", "end", values=(
                        row['Trabajador'],
                        f"${row['Total']:,.0f}",
                        row['Pagos']
                    ))

                fig3, ax3 = plt.subplots(figsize=(4.5, 3.5))
                ax3.bar(resumen_pt['Trabajador'], resumen_pt['Total'],
                        color="#9b59b6", edgecolor="white")
                ax3.set_title("Total Pagado por Trabajador", fontsize=10, weight='bold')
                ax3.set_ylabel("Total ($)")
                ax3.tick_params(axis='x', rotation=20)
                ax3.grid(True, alpha=0.3, axis='y')
                fig3.tight_layout()
                canvas3 = FigureCanvasTkAgg(fig3, master=self.frame_pt_grafico)
                canvas3.draw()
                canvas3.get_tk_widget().pack(fill="x", pady=5)
                plt.close(fig3)

        except Exception as e:
            messagebox.showerror("Error", str(e))


# ================= UTILS =================

def safe_float(value):
    try:
        return float(value)
    except:
        return 0.0


def render_insumos_pagos(parent):
    module = InsumosPagosModule(parent)
    return module
