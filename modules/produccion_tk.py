"""
Módulo de Producción - CustomTkinter (VERSIÓN COMPLETA Y ALINEADA)
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
from data.models import ProduccionRepository, GallinasRepository, StockRepository

MAPEO_CATEGORIAS = {
    'C': 'tipo_c',
    'B': 'tipo_b',
    'A': 'tipo_a',
    'AA': 'tipo_aa',
    'AAA': 'tipo_aaa',
    'Jumbo': 'tipo_jumbo'
}

class ProduccionModule:

    def __init__(self, parent):
        self.parent = parent
        self.produccion_repo = ProduccionRepository(db)
        self.gallinas_repo = GallinasRepository(db)
        self.stock_repo = StockRepository(db)

        self.categorias = ['C', 'B', 'A', 'AA', 'AAA', 'Jumbo']
        self.entry_vars = {}

        self.create_ui()

    # ================= UI =================

    def safe_int(value):
        try:
            return int(value)
        except:
            return 0
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

        # 🔥 AÑADIR TABS
        self.notebook.add("📊 Registro")
        self.notebook.add("📋 Historial")
        self.notebook.add("📈 Análisis")

        # 🔥 MEJORAR TAMAÑO DE TEXTO (CLAVE)
        self.notebook._segmented_button.configure(
            font=util.font_label(),
            height=40
        )

        self.create_registro_tab()
        self.create_historial_tab()
        self.create_analisis_tab()

    # ================= REGISTRO =================

    def create_registro_tab(self):
        tab = self.notebook.tab("📊 Registro")

        main = ctk.CTkScrollableFrame(tab)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # ================= HEADER =================
        title = ctk.CTkLabel(
            main,
            text="📊 Registro de Producción",
            font=util.font_title(),
            text_color=util.TEXT_MAIN
        )
        title.pack(anchor="w", pady=(0, 10))

        # ================= CARD: FECHA =================
        card_dt = ctk.CTkFrame(main, corner_radius=12)
        card_dt.pack(fill="x", pady=10)

        inner_dt = ctk.CTkFrame(card_dt, fg_color="transparent")
        inner_dt.pack(padx=20, pady=15, fill="x")

        # 🔥 IMPORTANTE: usar SOLO grid dentro de inner_dt
        inner_dt.grid_columnconfigure(0, weight=0)
        inner_dt.grid_columnconfigure(1, weight=0)
        inner_dt.grid_columnconfigure(2, weight=0)
        inner_dt.grid_columnconfigure(3, weight=1)

        # FECHA LABEL
        ctk.CTkLabel(
            inner_dt,
            text="Fecha",
            font=util.font_label()
        ).grid(row=0, column=0, padx=10)

        # FECHA ENTRY
        self.fecha_entry = DateEntry(
            inner_dt,
            date_pattern='yyyy-mm-dd',
            font=("Arial", 14),
            width=14
        )
        self.fecha_entry.set_date(date.today())
        self.fecha_entry.grid(row=0, column=1, padx=10)

        # HORA LABEL
        ctk.CTkLabel(
            inner_dt,
            text="Hora",
            font=util.font_label()
        ).grid(row=0, column=2, padx=10)

        # HORA ENTRY
        self.hora_entry = ctk.CTkEntry(
            inner_dt,
            width=150,
            height=35,
            font=util.font_input(),
            justify="center"
        )
        self.hora_entry.insert(0, datetime.now().strftime("%H:%M:%S"))
        self.hora_entry.grid(row=0, column=3, padx=10, sticky="ew")

        # ================= CARD: PRODUCCIÓN =================
        card_prod = ctk.CTkFrame(main, corner_radius=12)
        card_prod.pack(fill="x", pady=10)

        inner_prod = ctk.CTkFrame(card_prod, fg_color="transparent")
        inner_prod.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(
            inner_prod,
            text="🥚 Producción por categoría",
            font=util.font_section()
        ).pack(anchor="w", pady=(0, 10))

        grid = ctk.CTkFrame(inner_prod, fg_color="transparent")
        grid.pack()

        self.entry_vars = {}

        for i in range(len(self.categorias)):
            grid.grid_columnconfigure(i, weight=1)

        for i, cat in enumerate(self.categorias):
            frame = ctk.CTkFrame(grid, corner_radius=8)
            frame.grid(row=0, column=i, padx=6, sticky="nsew")

            ctk.CTkLabel(
                frame,
                text=f"Tipo {cat}",
                font=util.font_label()
            ).pack(pady=(6, 0))

            entry = ctk.CTkEntry(
                frame,
                height=40,
                justify="center",
                font=util.font_input()
            )
            entry.insert(0, "0")
            entry.pack(pady=5, fill="x", padx=5)

            entry.bind("<KeyRelease>", lambda e, c=cat: self.calcular_total())
            self.entry_vars[cat] = entry

        self.total_label = ctk.CTkLabel(
            inner_prod,
            text="📦 Total: 0 huevos",
            font=util.font_section()
        )
        self.total_label.pack(pady=10)

        ctk.CTkLabel(
            inner_prod,
            text="🥚 Observaciones de la Producción",
            font=util.font_section()
        ).pack(anchor="w", pady=(10, 10))

        self.obs_textbox = ctk.CTkTextbox(inner_prod, height=80)
        self.obs_textbox.pack(fill="x")

        # ================= BOTÓN =================
        btn = ctk.CTkButton(
            main,
            text="💾 Guardar Producción",
            height=45,
            font=util.font_input(),
            fg_color="#2ecc71",
            hover_color="#27ae60",
            command=self.guardar_produccion
        )
        btn.pack(pady=25)

        # ================= CARD: INFERIOR =================
        card_bottom = ctk.CTkFrame(main, corner_radius=12)
        card_bottom.pack(fill="x", pady=10)

        inner_bottom = ctk.CTkFrame(card_bottom, fg_color="transparent")
        inner_bottom.pack(padx=20, pady=15, fill="x")

        inner_bottom.grid_columnconfigure(0, weight=1)
        inner_bottom.grid_columnconfigure(1, weight=1)
        
        # -------- GALLINAS --------
        frame_g = ctk.CTkFrame(inner_bottom, corner_radius=10)
        frame_g.grid(row=0, column=0, padx=10, sticky="nsew")

        ctk.CTkLabel(
            frame_g,
            text="🐔 Gallinas",
            font=util.font_section()
        ).pack(pady=10)

        self.label_poblacion_actual = ctk.CTkLabel(
            frame_g,
            text="🐔 Población actual: --",
            font=util.font_label()
        )
        self.label_poblacion_actual.pack(pady=5, anchor="w")

        # 🔥 LABEL RESTAURADO
        ctk.CTkLabel(
            frame_g,
            text="Cantidad total de gallinas",
            font=util.font_text()
        ).pack(pady=5)

        self.cant_gallinas_entry = ctk.CTkEntry(
            frame_g,
            height=40,
            justify="center",
            font=util.font_input()
        )
        self.cant_gallinas_entry.insert(0, "0")
        self.cant_gallinas_entry.pack(pady=5)

        # 🔥 LABEL RESTAURADO
        ctk.CTkLabel(
            frame_g,
            text="Descartes del día",
            font=util.font_text()
        ).pack(pady=5)

        self.descartes_entry = ctk.CTkEntry(
            frame_g,
            height=40,
            justify="center",
            font=util.font_input()
        )
        self.descartes_entry.insert(0, "0")
        self.descartes_entry.pack(pady=5)

        # 🔥 LABEL RESTAURADO
        ctk.CTkLabel(
            frame_g,
            text="Observaciones Población",
            font=util.font_label()
        ).pack(anchor="w", padx=10, pady=(10, 0))

        self.obs_gallinas_entry = ctk.CTkEntry(
            frame_g,
            placeholder_text="Observaciones",
            font=util.font_text()
        )
        self.obs_gallinas_entry.pack(pady=5, fill="x", padx=10)

        ctk.CTkButton(
            frame_g,
            text="💾 Guardar Población",
            font=util.font_input(),
            command=self.guardar_gallinas,
            fg_color="#52b788",
            hover_color="#2980b9"
        ).pack(pady=10)

        # -------- ALIMENTO --------
        frame_f = ctk.CTkFrame(inner_bottom, corner_radius=10)
        frame_f.grid(row=0, column=1, padx=10, sticky="nsew")

        ctk.CTkLabel(
            frame_f,
            text="🌾 Alimento",
            font=util.font_section()
        ).pack(pady=10)

        self.label_gallinas_consumo = ctk.CTkLabel(
            frame_f,
            text="🐔 Gallinas usadas: --",
            font=util.font_text()
        )
        self.label_gallinas_consumo.pack(pady=5)

        # 🔥 LABEL RESTAURADO
        ctk.CTkLabel(
            frame_f,
            text="Consumo por gallina (gramos)",
            font=util.font_text()
        ).pack(pady=5)

        self.consumo_gallina_entry = ctk.CTkEntry(
            frame_f,
            font=util.font_input()
        )
        self.consumo_gallina_entry.insert(0, "0")
        self.consumo_gallina_entry.pack(pady=5)

        self.consumo_gallina_entry.bind(
            "<KeyRelease>",
            lambda e: self.calcular_consumo()
        )

        self.consumo_total_label = ctk.CTkLabel(
            frame_f,
            text="Total: 0 g",
            font=util.font_label()
        )
        self.consumo_total_label.pack(pady=5)

        # 🔥 LABEL RESTAURADO
        ctk.CTkLabel(
            frame_f,
            text="Observaciones Alimento",
            font=util.font_label()
        ).pack(anchor="w", padx=10, pady=(10, 0))

        self.obs_alimento_entry = ctk.CTkEntry(
            frame_f,
            placeholder_text="Observaciones",
            font=util.font_text()
        )
        self.obs_alimento_entry.pack(pady=5, fill="x", padx=10)

        ctk.CTkButton(
            frame_f,
            text="💾 Guardar Consumo",
            font=util.font_input(),
            command=self.guardar_alimento,
            fg_color="#52b788",
            hover_color="#e67e22"
        ).pack(pady=10)
        self.cargar_poblacion_actual()

    # ================= GUARDAR =================

    def guardar_produccion(self):
        try:
            fecha = datetime.strptime(self.fecha_entry.get(), "%Y-%m-%d").date()
            hora = self.hora_entry.get()
            def safe_int(value):
                try:
                    return int(value)
                except:
                    return 0
            try:
                datetime.strptime(hora, "%H:%M:%S")
            except:
                messagebox.showerror("Error", "Formato de hora inválido (HH:MM:SS)")
                return

            cantidades = {cat: safe_int(self.entry_vars[cat].get()) for cat in self.categorias}
            total = sum(cantidades.values())

            if total == 0:
                messagebox.showwarning("Advertencia", "Debes ingresar al menos un huevo")
                return

            obs = self.obs_textbox.get("1.0", "end-1c").strip()

            datos = {
            MAPEO_CATEGORIAS[cat]: int(self.entry_vars[cat].get() or 0)for cat in self.categorias}

            prod_id = self.produccion_repo.registrar_produccion(fecha=fecha,
                                                                hora=hora,
                                                                observaciones=obs if obs else None,
                                                                **datos)

            stock = self.stock_repo.obtener_stock_actual()
            stock_msg = "\n".join([f"{k}: {v}" for k, v in stock.items()])

            messagebox.showinfo("Éxito", f"Producción registrada\nID: {prod_id}\n\nStock:\n{stock_msg}")

            self.limpiar_formulario()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def guardar_gallinas(self):
        try:
            fecha = datetime.strptime(self.fecha_entry.get(), "%Y-%m-%d").date()
            hora = self.hora_entry.get()

            cant_gallinas = int(self.cant_gallinas_entry.get() or 0)
            descartes = int(self.descartes_entry.get() or 0)
            obs = self.obs_gallinas_entry.get().strip()

            if cant_gallinas == 0:
                messagebox.showwarning("Advertencia", "Debes ingresar la cantidad de gallinas")
                return

            self.gallinas_repo.registrar_poblacion(
                fecha=fecha,
                hora=hora,
                cantidad_gallinas=cant_gallinas,
                descartes=descartes,
                observaciones=obs if obs else None
            )
            self.cargar_poblacion_actual()

            messagebox.showinfo("Éxito", f"Población registrada: {cant_gallinas} gallinas")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def guardar_alimento(self):
        try:
            fecha = datetime.strptime(self.fecha_entry.get(), "%Y-%m-%d").date()
            hora = self.hora_entry.get()

            consumo = float(self.consumo_gallina_entry.get() or 0)

            # 🔥 SIEMPRE BD
            poblacion_actual = self.gallinas_repo.obtener_poblacion_actual()
            gallinas = poblacion_actual.get('cantidad_gallinas', 0)

            obs = self.obs_alimento_entry.get().strip()

            if gallinas == 0:
                messagebox.showwarning("Advertencia", "No hay gallinas registradas")
                return

            if consumo == 0:
                messagebox.showwarning("Advertencia", "Ingresa el consumo por gallina")
                return

            self.gallinas_repo.registrar_consumo_alimento(
                fecha=fecha,
                hora=hora,
                consumo_por_gallina=consumo,
                cantidad_gallinas=gallinas,
                observaciones=obs if obs else None
            )

            total = consumo * gallinas

            messagebox.showinfo("Éxito", f"Consumo registrado: {total/1000:.2f} kg")

        except Exception as e:
            messagebox.showerror("Error", str(e))
        
    def cargar_poblacion_actual(self):
        try:
            poblacion_actual = self.gallinas_repo.obtener_poblacion_actual()
            cantidad = poblacion_actual.get('cantidad_gallinas', 0)

            # Actualizar campo
            self.cant_gallinas_entry.delete(0, "end")
            self.cant_gallinas_entry.insert(0, str(cantidad))

            # Mostrar info visual
            self.label_poblacion_actual.configure(
                text=f"🐔 Población actual: {cantidad} gallinas"
            )
            self.label_gallinas_consumo.configure(
                text=f"🐔 Gallinas usadas: {cantidad}"
            )

        except Exception as e:
            self.label_poblacion_actual.configure(
                text="🐔 Población actual: error"
            )
        
    def limpiar_formulario(self):
        for e in self.entry_vars.values():
            e.delete(0, "end")
            e.insert(0, "0")
    
    def calcular_total(self):
        try:
            total = sum(int(e.get() or 0) for e in self.entry_vars.values())
            self.total_label.configure(text=f"📦 Total: {total} huevos")
        except:
            pass

    def calcular_consumo(self):
        try:
            consumo = float(self.consumo_gallina_entry.get() or 0)

            # 🔥 SIEMPRE desde la BD
            poblacion_actual = self.gallinas_repo.obtener_poblacion_actual()
            gallinas = poblacion_actual.get('cantidad_gallinas', 0)

            total = consumo * gallinas

            self.consumo_total_label.configure(
                text=f"Total: {total:.0f} g ({total/1000:.2f} kg)"
            )

            # Mostrar también cuántas gallinas se usaron
            self.label_gallinas_consumo.configure(
                text=f"🐔 Gallinas usadas: {gallinas}"
            )

        except:
            pass
    

    # ================= HISTORIAL =================

    def create_historial_tab(self):
        tab = self.notebook.tab("📋 Historial")

        main = ctk.CTkScrollableFrame(tab)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # ================= HEADER =================
        ctk.CTkLabel(
            main,
            text="📋 Historial de Producción",
            font=util.font_title(),
            text_color=util.TEXT_MAIN
        ).pack(anchor="w", pady=(0, 10))

        # ================= CARD: FILTROS =================
        card_filtros = ctk.CTkFrame(main, corner_radius=12)
        card_filtros.pack(fill="x", pady=10)

        filtros = ctk.CTkFrame(card_filtros, fg_color="transparent")
        filtros.pack(padx=20, pady=15, fill="x")

        # 🔥 usamos grid (como en registro → consistencia)
        filtros.grid_columnconfigure((0,1,2,3,4), weight=1)

        # Fecha inicio
        ctk.CTkLabel(
            filtros,
            text="Desde",
            font=util.font_label()
        ).grid(row=0, column=0, padx=5)

        self.hist_fecha_inicio = DateEntry(
            filtros,
            date_pattern='yyyy-mm-dd',
            font=("Arial", 14),
            width=12
        )
        self.hist_fecha_inicio.set_date(date.today()-timedelta(days=30))
        self.hist_fecha_inicio.grid(row=0, column=1, padx=5)

        # Fecha fin
        ctk.CTkLabel(
            filtros,
            text="Hasta",
            font=util.font_label()
        ).grid(row=0, column=2, padx=5)

        self.hist_fecha_fin = DateEntry(
            filtros,
            date_pattern='yyyy-mm-dd',
            font=("Arial", 14),
            width=12
        )
        self.hist_fecha_fin.set_date(date.today())
        self.hist_fecha_fin.grid(row=0, column=3, padx=5)

        # Botón buscar
        btn = ctk.CTkButton(
            filtros,
            text="🔍 Buscar",
            font=util.font_input(),
            height=40,
            command=self.cargar_historial
        )
        btn.grid(row=0, column=4, padx=10)

        # ================= CARD: MÉTRICAS =================
        card_metrics = ctk.CTkFrame(main, corner_radius=12)
        card_metrics.pack(fill="x", pady=10)

        self.frame_metrics = ctk.CTkFrame(card_metrics, fg_color="transparent")
        self.frame_metrics.pack(padx=20, pady=15, fill="x")

        self.metric_labels = []

        for _ in range(4):
            lbl = ctk.CTkLabel(
                self.frame_metrics,
                text="--",
                font=util.font_section()
            )
            lbl.pack(side="left", expand=True, padx=10)
            self.metric_labels.append(lbl)

        # ================= CARD: TABLA =================
        card_table = ctk.CTkFrame(main, corner_radius=12)
        card_table.pack(fill="both", expand=True, pady=10)

        inner_table = ctk.CTkFrame(card_table, fg_color="transparent")
        inner_table.pack(padx=20, pady=15, fill="both", expand=True)

        columns = ("Fecha","Hora","C","B","A","AA","AAA","Jumbo","Total","Obs")

        self.tree = ttk.Treeview(inner_table, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")

        self.tree.pack(fill="both", expand=True)

        # ================= EXPORTAR =================
        btn_exp = ctk.CTkButton(
            main,
            text="📥 Exportar CSV",
            font=util.font_input(),
            height=40,
            fg_color=util.PRIMARY,
            hover_color=util.PRIMARY_HOVER,
            command=self.exportar_historial
        )
        btn_exp.pack(pady=15)

        self.cargar_historial()


    def cargar_historial(self):
        # limpiar tabla
        for i in self.tree.get_children():
            self.tree.delete(i)

        try:
            fi = datetime.strptime(self.hist_fecha_inicio.get(), "%Y-%m-%d").date()
            ff = datetime.strptime(self.hist_fecha_fin.get(), "%Y-%m-%d").date()
        except:
            messagebox.showerror("Error", "Formato de fecha inválido (YYYY-MM-DD)")
            return

        data = self.produccion_repo.obtener_produccion_por_fecha(fi, ff)

        if not data:
            messagebox.showinfo("Info", "No hay registros en el período")
            return

        totales = []

        for r in data:
            total = sum([
                r.get('tipo_c',0), r.get('tipo_b',0), r.get('tipo_a',0),
                r.get('tipo_aa',0), r.get('tipo_aaa',0), r.get('tipo_jumbo',0)
            ])

            totales.append(total)

            self.tree.insert("", "end", values=(
                r.get("fecha"),
                r.get("hora"),
                r.get('tipo_c',0),
                r.get('tipo_b',0),
                r.get('tipo_a',0),
                r.get('tipo_aa',0),
                r.get('tipo_aaa',0),
                r.get('tipo_jumbo',0),
                total,
                r.get("observaciones","")
            ))

        # -------- MÉTRICAS --------
        total_general = sum(totales)
        promedio = total_general / len(totales)
        mejor = max(totales)

        self.metric_labels[0].configure(text=f"📅 Días: {len(totales)}")
        self.metric_labels[1].configure(text=f"🥚 Total: {total_general}")
        self.metric_labels[2].configure(text=f"📊 Prom: {promedio:.0f}")
        self.metric_labels[3].configure(text=f"🏆 Mejor: {mejor}")

    def exportar_historial(self):
        try:
            fi = datetime.strptime(self.hist_fecha_inicio.get(), "%Y-%m-%d").date()
            ff = datetime.strptime(self.hist_fecha_fin.get(), "%Y-%m-%d").date()
        except:
            messagebox.showerror("Error", "Formato de fecha inválido")
            return

        data = self.produccion_repo.obtener_produccion_por_fecha(fi, ff)

        if not data:
            messagebox.showwarning("Advertencia", "No hay datos para exportar")
            return

        file = filedialog.asksaveasfilename(defaultextension=".csv")
        if not file:
            return

        with open(file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            writer.writerow([
                "Fecha","Hora","C","B","A","AA","AAA","Jumbo","Total","Observaciones"
            ])

            for r in data:
                total = sum([
                    r.get('tipo_c',0), r.get('tipo_b',0), r.get('tipo_a',0),
                    r.get('tipo_aa',0), r.get('tipo_aaa',0), r.get('tipo_jumbo',0)
                ])

                writer.writerow([
                    r.get("fecha"),
                    r.get("hora"),
                    r.get('tipo_c',0),
                    r.get('tipo_b',0),
                    r.get('tipo_a',0),
                    r.get('tipo_aa',0),
                    r.get('tipo_aaa',0),
                    r.get('tipo_jumbo',0),
                    total,
                    r.get("observaciones","")
                ])

        messagebox.showinfo("Exportado", "CSV generado correctamente")

    # ================= ANALISIS =================

    def create_analisis_tab(self):
        tab = self.notebook.tab("📈 Análisis")

        main = ctk.CTkFrame(tab)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # ================= HEADER =================
        ctk.CTkLabel(
            main,
            text="📊 Análisis de Producción",
            font=util.font_title(),
            text_color=util.TEXT_MAIN
        ).pack(anchor="w", pady=(0, 10))

        # ================= CARD: FILTROS =================
        card_filtros = ctk.CTkFrame(main, corner_radius=12)
        card_filtros.pack(fill="x", pady=10)

        filtros = ctk.CTkFrame(card_filtros, fg_color="transparent")
        filtros.pack(padx=20, pady=15)

        # --- Desde ---
        ctk.CTkLabel(
            filtros,
            text="Desde",
            font=util.font_label()
        ).grid(row=0, column=0, padx=10, pady=5)

        self.analisis_inicio = DateEntry(
            filtros,
            date_pattern='yyyy-mm-dd',
            font=("Arial", 14),
            width=12
        )
        self.analisis_inicio.set_date(date.today() - timedelta(days=30))
        self.analisis_inicio.grid(row=0, column=1, padx=10)

        # --- Hasta ---
        ctk.CTkLabel(
            filtros,
            text="Hasta",
            font=util.font_label()
        ).grid(row=0, column=2, padx=10, pady=5)

        self.analisis_fin = DateEntry(
            filtros,
            date_pattern='yyyy-mm-dd',
            font=("Arial", 14),
            width=12
        )
        self.analisis_fin.set_date(date.today())
        self.analisis_fin.grid(row=0, column=3, padx=10)

        # --- Botón ---
        ctk.CTkButton(
            filtros,
            text="📊 Generar",
            font=util.font_input(),
            height=40,
            fg_color=util.PRIMARY,
            hover_color=util.PRIMARY_HOVER,
            command=self.generar_graficos
        ).grid(row=0, column=4, padx=20)

        # ================= CARD: GRÁFICOS =================
        card_graficos = ctk.CTkFrame(main, corner_radius=12)
        card_graficos.pack(fill="both", expand=True, pady=10)

        self.frame_graficos = ctk.CTkScrollableFrame(card_graficos)
        self.frame_graficos.pack(fill="both", expand=True, padx=10, pady=10)

        # ================= CARD: MÉTRICAS =================
        card_stats = ctk.CTkFrame(main, corner_radius=12)
        card_stats.pack(fill="x", pady=10)

        self.frame_stats = ctk.CTkFrame(card_stats, fg_color="transparent")
        self.frame_stats.pack(padx=20, pady=15, fill="x")

        self.stats_labels = []

        for _ in range(6):
            lbl = ctk.CTkLabel(
                self.frame_stats,
                text="--",
                font=util.font_label()
            )
            lbl.pack(side="left", expand=True, padx=10)
            self.stats_labels.append(lbl)

        # 🔥 limpiar gráficos al entrar
        for widget in self.frame_graficos.winfo_children():
            widget.destroy()
        
    def generar_graficos(self):
        # limpiar gráficos anteriores
        for widget in self.frame_graficos.winfo_children():
            widget.destroy()

        try:
            fi = datetime.strptime(self.analisis_inicio.get(), "%Y-%m-%d").date()
            ff = datetime.strptime(self.analisis_fin.get(), "%Y-%m-%d").date()
        except:
            messagebox.showerror("Error", "Formato de fecha inválido")
            return

        data = self.produccion_repo.obtener_produccion_por_fecha(fi, ff)

        if not data:
            messagebox.showinfo("Info", "No hay datos suficientes")
            return

        df = pd.DataFrame(data)

        df['total'] = (
            df['tipo_c'] + df['tipo_b'] + df['tipo_a'] +
            df['tipo_aa'] + df['tipo_aaa'] + df['tipo_jumbo']
        )

        df['fecha'] = pd.to_datetime(df['fecha'])

        # ================= GRÁFICO 1 =================
        fig1 = plt.Figure(figsize=(8,4))
        ax1 = fig1.add_subplot(111)

        ax1.plot(df['fecha'], df['total'], marker='o', linewidth=2)

        # Línea de tendencia (promedio móvil)
        df['trend'] = df['total'].rolling(window=3, min_periods=1).mean()
        ax1.plot(df['fecha'], df['trend'], linestyle='--')

        ax1.set_title("Producción Total por Día", fontsize=12, weight='bold')
        ax1.set_xlabel("")
        ax1.set_ylabel("Huevos")

        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)

        canvas1 = FigureCanvasTkAgg(fig1, master=self.frame_graficos)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill="x", pady=10)
        plt.close(fig1)
        # ================= GRÁFICO 2 =================
        fig2 = plt.Figure(figsize=(8,4))
        ax2 = fig2.add_subplot(111)

        categorias = ['tipo_c','tipo_b','tipo_a','tipo_aa','tipo_aaa','tipo_jumbo']
        data_stack = [df[cat] for cat in categorias]

        labels = ['C','B','A','AA','AAA','Jumbo']

        ax2.stackplot(df['fecha'], data_stack, labels=labels)

        ax2.set_title("Producción por Categoría (Apilado)", fontsize=12, weight='bold')
        ax2.legend(loc='upper left')

        ax2.tick_params(axis='x', rotation=45)

        canvas2 = FigureCanvasTkAgg(fig2, master=self.frame_graficos)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill="x", pady=10)
        plt.close(fig2)
        # ================= GRÁFICO 3 =================
        total_periodo = self.produccion_repo.obtener_total_produccion_periodo(fi, ff)

        categorias = {
            'C': total_periodo.get('total_c',0) or 0,
            'B': total_periodo.get('total_b',0) or 0,
            'A': total_periodo.get('total_a',0) or 0,
            'AA': total_periodo.get('total_aa',0) or 0,
            'AAA': total_periodo.get('total_aaa',0) or 0,
            'Jumbo': total_periodo.get('total_jumbo',0) or 0
        }

        categorias = {k:v for k,v in categorias.items() if v > 0}

        if categorias:
            fig3 = plt.Figure(figsize=(5,5))
            ax3 = fig3.add_subplot(111)

            ax3.pie(
                categorias.values(),
                labels=categorias.keys(),
                autopct='%1.1f%%',
                startangle=90
            )

            ax3.set_title("Distribución por Categoría", fontsize=12, weight='bold')

            canvas3 = FigureCanvasTkAgg(fig3, master=self.frame_graficos)
            canvas3.draw()
            canvas3.get_tk_widget().pack(pady=10)
            plt.close(fig3)
        # ================= MÉTRICAS =================
        total = df['total'].sum()
        promedio = df['total'].mean()
        maximo = df['total'].max()
        minimo = df['total'].min()
        std = df['total'].std()
        dias = len(df)

        self.stats_labels[0].configure(text=f"🥚 Total\n{total}")
        self.stats_labels[1].configure(text=f"📊 Promedio\n{promedio:.0f}")
        self.stats_labels[2].configure(text=f"📈 Máximo\n{maximo}")
        self.stats_labels[3].configure(text=f"📉 Mínimo\n{minimo}")
        self.stats_labels[4].configure(text=f"📏 Desv\n{std:.1f}")
        self.stats_labels[5].configure(text=f"📅 Días\n{dias}")
    