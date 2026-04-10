"""
Módulo de Reportes - CustomTkinter
Dashboard ejecutivo, análisis detallados, alertas y exportación de reportes
"""
from utils import config as util
from tkcalendar import DateEntry
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date, timedelta
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd
import io
import sys
sys.path.append('..')

from data.database import db
from data.models import (ReportesRepository, ProduccionRepository, StockRepository,
                         PedidosRepository, InsumosRepository, PreciosRepository)


class ReportesModule:

    def __init__(self, parent):
        self.parent = parent
        self.reportes_repo = ReportesRepository(db)
        self.produccion_repo = ProduccionRepository(db)
        self.stock_repo = StockRepository(db)
        self.pedidos_repo = PedidosRepository(db)
        self.insumos_repo = InsumosRepository(db)
        self.precios_repo = PreciosRepository(db)
        self.categorias_huevos = ['C', 'B', 'A', 'AA', 'AAA', 'Jumbo']
        self.categorias_db = ['tipo_c', 'tipo_b', 'tipo_a', 'tipo_aa', 'tipo_aaa', 'tipo_jumbo']

        self.create_ui()

    # ================= UI =================

    def create_ui(self):
        # --- Alertas en la parte superior ---
        self.frame_alertas = ctk.CTkFrame(self.parent, corner_radius=10, fg_color="#fdecea")
        self.label_alertas = ctk.CTkLabel(
            self.frame_alertas, text="", font=util.font_label(),
            text_color="#c0392b", justify="left", wraplength=900)
        self.label_alertas.pack(padx=15, pady=8)
        self._mostrar_alertas()

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
        self.notebook.pack(fill="both", expand=True, padx=40, pady=(10, 10))

        self.notebook.add("📊 Dashboard")
        self.notebook.add("🥚 Producción")
        self.notebook.add("💰 Ventas")
        self.notebook.add("💵 Financiero")
        self.notebook.add("📄 Exportar")

        self.notebook._segmented_button.configure(font=util.font_label(), height=40)

        self.create_dashboard_tab()
        self.create_produccion_tab()
        self.create_ventas_tab()
        self.create_financiero_tab()
        self.create_exportar_tab()

    # ================= ALERTAS =================

    def _mostrar_alertas(self):
        try:
            alertas = self.stock_repo.obtener_alertas_stock()
            if alertas:
                textos = [
                    f"🔴 {a['nombre']} ({a['categoria']}): {a['cantidad_actual']} / mín {a['stock_minimo']} {a['unidad']}"
                    for a in alertas[:3]
                ]
                msg = f"⚠️ ALERTAS ACTIVAS ({len(alertas)}): " + "   |   ".join(textos)
                if len(alertas) > 3:
                    msg += f"   +{len(alertas) - 3} más"
                self.label_alertas.configure(text=msg)
                self.frame_alertas.pack(fill="x", padx=40, pady=(10, 0))
            else:
                self.frame_alertas.pack_forget()
        except:
            self.frame_alertas.pack_forget()

    # ================= SELECTOR DE PERÍODO (reutilizable) =================

    def _crear_selector_periodo(self, parent, prefix):
        """Crea el widget de selección de período y retorna una función get_fechas()."""
        card = ctk.CTkFrame(parent, corner_radius=12)
        card.pack(fill="x", pady=8)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=20, pady=12, fill="x")

        inner.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        ctk.CTkLabel(inner, text="Período", font=util.font_label()).grid(
            row=0, column=0, sticky="w", padx=5)

        preset_var = ctk.StringVar(value="Último mes")
        preset_combo = ttk.Combobox(
            inner, textvariable=preset_var, state="readonly", font=("Arial", 12),
            values=["Personalizado", "Última semana", "Último mes", "Último semestre", "Año actual"]
        )
        preset_combo.grid(row=0, column=1, padx=5, sticky="ew")

        ctk.CTkLabel(inner, text="Desde", font=util.font_label()).grid(
            row=0, column=2, padx=(15, 5), sticky="w")
        fecha_inicio_entry = DateEntry(inner, date_pattern='yyyy-mm-dd',
                                      font=("Arial", 12), width=12)
        fecha_inicio_entry.set_date(date.today() - timedelta(days=30))
        fecha_inicio_entry.grid(row=0, column=3, padx=5)

        ctk.CTkLabel(inner, text="Hasta", font=util.font_label()).grid(
            row=0, column=4, padx=(10, 5), sticky="w")
        fecha_fin_entry = DateEntry(inner, date_pattern='yyyy-mm-dd',
                                   font=("Arial", 12), width=12)
        fecha_fin_entry.set_date(date.today())
        fecha_fin_entry.grid(row=0, column=5, padx=5)

        def on_preset_change(event=None):
            hoy = date.today()
            preset = preset_var.get()
            if preset == "Última semana":
                fecha_inicio_entry.set_date(hoy - timedelta(days=7))
                fecha_fin_entry.set_date(hoy)
            elif preset == "Último mes":
                fecha_inicio_entry.set_date(hoy - timedelta(days=30))
                fecha_fin_entry.set_date(hoy)
            elif preset == "Último semestre":
                fecha_inicio_entry.set_date(hoy - timedelta(days=180))
                fecha_fin_entry.set_date(hoy)
            elif preset == "Año actual":
                fecha_inicio_entry.set_date(date(hoy.year, 1, 1))
                fecha_fin_entry.set_date(hoy)

        preset_combo.bind("<<ComboboxSelected>>", on_preset_change)
        on_preset_change()

        def get_fechas():
            fi = datetime.strptime(fecha_inicio_entry.get(), "%Y-%m-%d").date()
            ff = datetime.strptime(fecha_fin_entry.get(), "%Y-%m-%d").date()
            return fi, ff

        return get_fechas

    # ================= TAB: DASHBOARD =================

    def create_dashboard_tab(self):
        tab = self.notebook.tab("📊 Dashboard")
        main = ctk.CTkScrollableFrame(tab)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main, text="📊 Dashboard Ejecutivo",
                     font=util.font_title(), text_color=util.TEXT_MAIN).pack(anchor="w", pady=(0, 6))

        self.dashboard_get_fechas = self._crear_selector_periodo(main, "dashboard")

        # Checkbox comparar
        self.dashboard_comparar_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(main, text="Comparar con período anterior",
                        variable=self.dashboard_comparar_var,
                        font=util.font_label()).pack(anchor="w", pady=(4, 6))

        ctk.CTkButton(
            main, text="📊 Generar Dashboard",
            font=util.font_input(), height=40,
            fg_color=util.PRIMARY, hover_color=util.PRIMARY_HOVER,
            command=lambda: self._cargar_dashboard(main)
        ).pack(anchor="w", pady=(0, 8))

        # Contenedor dinámico
        self.frame_dashboard_content = ctk.CTkFrame(main, fg_color="transparent")
        self.frame_dashboard_content.pack(fill="x")

    def _cargar_dashboard(self, main):
        for w in self.frame_dashboard_content.winfo_children():
            w.destroy()

        try:
            fi, ff = self.dashboard_get_fechas()
        except:
            messagebox.showerror("Error", "Formato de fecha inválido")
            return

        comparar = self.dashboard_comparar_var.get()
        dias = (ff - fi).days
        fi_ant = fi - timedelta(days=dias + 1)
        ff_ant = fi - timedelta(days=1)

        try:
            balance = self.reportes_repo.obtener_balance_periodo(fi, ff)
            resumen = self.reportes_repo.obtener_resumen_produccion_ventas(fi, ff)
            balance_ant = self.reportes_repo.obtener_balance_periodo(fi_ant, ff_ant) if comparar else {}
            resumen_ant = self.reportes_repo.obtener_resumen_produccion_ventas(fi_ant, ff_ant) if comparar else {}

            ing = balance.get('total_ingresos', 0) or 0
            egr = balance.get('total_egresos', 0) or 0
            bal = balance.get('balance', 0) or 0
            prod = resumen.get('total_producido', 0) or 0
            vend = resumen.get('total_vendido', 0) or 0
            ing_ant = balance_ant.get('total_ingresos', 0) or 0
            egr_ant = balance_ant.get('total_egresos', 0) or 0
            bal_ant = balance_ant.get('balance', 0) or 0
            prod_ant = resumen_ant.get('total_producido', 0) or 0
            vend_ant = resumen_ant.get('total_vendido', 0) or 0

            def delta_pct(nuevo, viejo):
                if viejo > 0:
                    return f" ({(nuevo - viejo) / viejo * 100:+.1f}%)"
                return ""

            # --- KPIs financieros ---
            card_kpi = ctk.CTkFrame(self.frame_dashboard_content, corner_radius=12)
            card_kpi.pack(fill="x", pady=8)
            inner_kpi = ctk.CTkFrame(card_kpi, fg_color="transparent")
            inner_kpi.pack(padx=20, pady=15, fill="x")
            ctk.CTkLabel(inner_kpi, text="📈 Indicadores Clave",
                         font=util.font_section()).pack(anchor="w", pady=(0, 8))

            frame_kpi = ctk.CTkFrame(inner_kpi, fg_color="transparent")
            frame_kpi.pack(fill="x")
            kpis = [
                ("💰 Ingresos", f"${ing:,.0f}", delta_pct(ing, ing_ant)),
                ("💸 Egresos", f"${egr:,.0f}", delta_pct(egr, egr_ant)),
                ("📊 Balance Neto", f"${bal:,.0f}", delta_pct(bal, bal_ant)),
                ("💹 Margen", f"{ing and (bal/ing*100):.1f}%" if ing else "N/A", ""),
            ]
            for i, (titulo, valor, delta) in enumerate(kpis):
                frame_kpi.grid_columnconfigure(i, weight=1)
                lbl = ctk.CTkLabel(frame_kpi,
                                   text=f"{titulo}\n{valor}{delta}",
                                   font=util.font_section())
                lbl.grid(row=0, column=i, padx=10, pady=4)

            # --- KPIs producción/ventas ---
            card_pv = ctk.CTkFrame(self.frame_dashboard_content, corner_radius=12)
            card_pv.pack(fill="x", pady=8)
            inner_pv = ctk.CTkFrame(card_pv, fg_color="transparent")
            inner_pv.pack(padx=20, pady=15, fill="x")
            ctk.CTkLabel(inner_pv, text="🥚 Producción y Ventas",
                         font=util.font_section()).pack(anchor="w", pady=(0, 8))

            tasa = f"{vend/prod*100:.1f}%" if prod > 0 else "N/A"
            tasa_ant = f"{vend_ant/prod_ant*100:.1f}%" if prod_ant > 0 else ""

            frame_pv = ctk.CTkFrame(inner_pv, fg_color="transparent")
            frame_pv.pack(fill="x")
            pv_kpis = [
                ("🥚 Producidos", f"{prod:,}", delta_pct(prod, prod_ant)),
                ("📦 Vendidos", f"{vend:,}", delta_pct(vend, vend_ant)),
                ("📊 Tasa de Venta", tasa, ""),
            ]
            for i, (titulo, valor, delta) in enumerate(pv_kpis):
                frame_pv.grid_columnconfigure(i, weight=1)
                ctk.CTkLabel(frame_pv, text=f"{titulo}\n{valor}{delta}",
                             font=util.font_section()).grid(row=0, column=i, padx=10, pady=4)

            # --- Costos y eficiencia ---
            try:
                costo_huevo = self.reportes_repo.calcular_costo_produccion_por_huevo(fi, ff) or 0
                precio_prom = (ing / vend) if vend > 0 else 0
                ganancia_huevo = precio_prom - costo_huevo

                card_cost = ctk.CTkFrame(self.frame_dashboard_content, corner_radius=12)
                card_cost.pack(fill="x", pady=8)
                inner_cost = ctk.CTkFrame(card_cost, fg_color="transparent")
                inner_cost.pack(padx=20, pady=15, fill="x")
                ctk.CTkLabel(inner_cost, text="💵 Costos y Eficiencia",
                             font=util.font_section()).pack(anchor="w", pady=(0, 8))

                frame_cost = ctk.CTkFrame(inner_cost, fg_color="transparent")
                frame_cost.pack(fill="x")
                cost_kpis = [
                    ("💰 Costo/Huevo", f"${costo_huevo:.2f}"),
                    ("💲 Precio Prom./Huevo", f"${precio_prom:.2f}" if vend > 0 else "N/A"),
                    ("💹 Ganancia/Huevo", f"${ganancia_huevo:.2f}" if vend > 0 else "N/A"),
                ]
                for i, (titulo, valor) in enumerate(cost_kpis):
                    frame_cost.grid_columnconfigure(i, weight=1)
                    ctk.CTkLabel(frame_cost, text=f"{titulo}\n{valor}",
                                 font=util.font_section()).grid(row=0, column=i, padx=10, pady=4)
            except:
                pass

            # --- Gráficos de tendencias ---
            try:
                prod_diaria = self.reportes_repo.obtener_produccion_diaria_periodo(fi, ff)
                ventas_diarias = self.reportes_repo.obtener_ventas_diarias_periodo(fi, ff)

                if prod_diaria or ventas_diarias:
                    card_graf = ctk.CTkFrame(self.frame_dashboard_content, corner_radius=12)
                    card_graf.pack(fill="x", pady=8)
                    inner_graf = ctk.CTkFrame(card_graf, fg_color="transparent")
                    inner_graf.pack(padx=20, pady=15, fill="x")
                    ctk.CTkLabel(inner_graf, text="📈 Tendencias",
                                 font=util.font_section()).pack(anchor="w", pady=(0, 8))

                    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))

                    if prod_diaria:
                        df_p = pd.DataFrame(prod_diaria)
                        df_p['fecha'] = pd.to_datetime(df_p['fecha'])
                        axes[0].plot(df_p['fecha'], df_p['total'], marker='o', linewidth=2, color="#3498db")
                        axes[0].set_title("Producción Diaria", fontsize=10, weight='bold')
                        axes[0].set_ylabel("Huevos")
                        axes[0].tick_params(axis='x', rotation=30)
                        axes[0].grid(True, alpha=0.3)

                    if ventas_diarias:
                        df_v = pd.DataFrame(ventas_diarias)
                        df_v['fecha'] = pd.to_datetime(df_v['fecha'])
                        axes[1].plot(df_v['fecha'], df_v['total_ingresos'],
                                     marker='o', linewidth=2, color="#2ecc71")
                        axes[1].set_title("Ingresos Diarios", fontsize=10, weight='bold')
                        axes[1].set_ylabel("Ingresos ($)")
                        axes[1].tick_params(axis='x', rotation=30)
                        axes[1].grid(True, alpha=0.3)

                    fig.tight_layout()
                    canvas = FigureCanvasTkAgg(fig, master=inner_graf)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill="x")
                    plt.close(fig)
            except:
                pass

            # --- Stock actual ---
            try:
                stock_stats = self.reportes_repo.obtener_estadisticas_stock()
                if stock_stats:
                    total_stock = stock_stats.get('total_huevos', 0) or 0
                    card_stock = ctk.CTkFrame(self.frame_dashboard_content, corner_radius=12)
                    card_stock.pack(fill="x", pady=8)
                    inner_stock = ctk.CTkFrame(card_stock, fg_color="transparent")
                    inner_stock.pack(padx=20, pady=15, fill="x")
                    ctk.CTkLabel(inner_stock, text="📦 Estado del Stock",
                                 font=util.font_section()).pack(anchor="w", pady=(0, 8))

                    info_txt = f"🥚 Total en Stock: {total_stock:,} huevos"
                    if prod > 0 and (ff - fi).days > 0:
                        dias_stock = total_stock / (prod / ((ff - fi).days + 1))
                        info_txt += f"    |    📅 Días de Stock estimados: {dias_stock:.1f}"
                    ctk.CTkLabel(inner_stock, text=info_txt,
                                 font=util.font_label()).pack(anchor="w", pady=(0, 8))

                    stock_por_cat = {
                        cat: stock_stats.get(cat_db, 0) or 0
                        for cat, cat_db in zip(self.categorias_huevos, self.categorias_db)
                    }
                    stock_por_cat = {k: v for k, v in stock_por_cat.items() if v > 0}

                    if stock_por_cat:
                        fig2, ax = plt.subplots(figsize=(5, 3.5))
                        ax.pie(list(stock_por_cat.values()),
                               labels=list(stock_por_cat.keys()),
                               autopct='%1.1f%%', startangle=90)
                        ax.set_title("Distribución del Stock", fontsize=10, weight='bold')
                        fig2.tight_layout()
                        canvas2 = FigureCanvasTkAgg(fig2, master=inner_stock)
                        canvas2.draw()
                        canvas2.get_tk_widget().pack()
                        plt.close(fig2)
            except:
                pass

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar dashboard: {str(e)}")

    # ================= TAB: PRODUCCIÓN =================

    def create_produccion_tab(self):
        tab = self.notebook.tab("🥚 Producción")
        main = ctk.CTkScrollableFrame(tab)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main, text="🥚 Análisis de Producción",
                     font=util.font_title(), text_color=util.TEXT_MAIN).pack(anchor="w", pady=(0, 6))

        self.prod_get_fechas = self._crear_selector_periodo(main, "prod")

        ctk.CTkButton(
            main, text="📊 Generar Análisis",
            font=util.font_input(), height=40,
            fg_color=util.PRIMARY, hover_color=util.PRIMARY_HOVER,
            command=lambda: self._cargar_produccion(main)
        ).pack(anchor="w", pady=(0, 8))

        self.frame_prod_content = ctk.CTkFrame(main, fg_color="transparent")
        self.frame_prod_content.pack(fill="x")

    def _cargar_produccion(self, main):
        for w in self.frame_prod_content.winfo_children():
            w.destroy()

        try:
            fi, ff = self.prod_get_fechas()
        except:
            messagebox.showerror("Error", "Formato de fecha inválido")
            return

        try:
            prod_diaria = self.reportes_repo.obtener_produccion_diaria_periodo(fi, ff)
            total_prod = self.produccion_repo.obtener_total_produccion_periodo(fi, ff)

            if not prod_diaria:
                ctk.CTkLabel(self.frame_prod_content,
                             text="ℹ️ No hay datos de producción en el período",
                             font=util.font_label()).pack(pady=20)
                return

            df = pd.DataFrame(prod_diaria)
            df['fecha'] = pd.to_datetime(df['fecha'])

            # Métricas
            card_m = ctk.CTkFrame(self.frame_prod_content, corner_radius=12)
            card_m.pack(fill="x", pady=8)
            inner_m = ctk.CTkFrame(card_m, fg_color="transparent")
            inner_m.pack(padx=20, pady=15, fill="x")
            ctk.CTkLabel(inner_m, text="📊 Resumen de Producción",
                         font=util.font_section()).pack(anchor="w", pady=(0, 8))

            frame_m = ctk.CTkFrame(inner_m, fg_color="transparent")
            frame_m.pack(fill="x")
            metricas = [
                ("🥚 Total Producido", f"{df['total'].sum():,}"),
                ("📊 Promedio Diario", f"{df['total'].mean():.0f}"),
                ("🏆 Mejor Día", f"{df['total'].max():,}"),
                ("📉 Peor Día", f"{df['total'].min():,}"),
            ]
            for i, (titulo, valor) in enumerate(metricas):
                frame_m.grid_columnconfigure(i, weight=1)
                ctk.CTkLabel(frame_m, text=f"{titulo}\n{valor}",
                             font=util.font_section()).grid(row=0, column=i, padx=10, pady=4)

            # Gráficos principales
            card_g = ctk.CTkFrame(self.frame_prod_content, corner_radius=12)
            card_g.pack(fill="x", pady=8)
            inner_g = ctk.CTkFrame(card_g, fg_color="transparent")
            inner_g.pack(padx=20, pady=15, fill="x")

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

            ax1.fill_between(df['fecha'], df['total'], alpha=0.6, color="#3498db")
            ax1.plot(df['fecha'], df['total'], color="#2980b9", linewidth=1.5)
            ax1.set_title("Producción Total por Día", fontsize=10, weight='bold')
            ax1.set_ylabel("Huevos")
            ax1.tick_params(axis='x', rotation=30)
            ax1.grid(True, alpha=0.3)

            # Área apilada por categoría
            cats_cols = ['tipo_c', 'tipo_b', 'tipo_a', 'tipo_aa', 'tipo_aaa', 'tipo_jumbo']
            cats_labels = ['C', 'B', 'A', 'AA', 'AAA', 'Jumbo']
            colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6", "#1abc9c"]
            data_stack = [df[c].values for c in cats_cols if c in df.columns]
            labels_stack = [l for c, l in zip(cats_cols, cats_labels) if c in df.columns]
            if data_stack:
                ax2.stackplot(df['fecha'], data_stack, labels=labels_stack, colors=colors, alpha=0.8)
                ax2.set_title("Producción por Categoría", fontsize=10, weight='bold')
                ax2.legend(loc='upper left', fontsize=8)
                ax2.tick_params(axis='x', rotation=30)
                ax2.grid(True, alpha=0.3)

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=inner_g)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x")
            plt.close(fig)

            # Distribución por categoría
            card_dist = ctk.CTkFrame(self.frame_prod_content, corner_radius=12)
            card_dist.pack(fill="x", pady=8)
            inner_dist = ctk.CTkFrame(card_dist, fg_color="transparent")
            inner_dist.pack(padx=20, pady=15, fill="x")
            ctk.CTkLabel(inner_dist, text="📈 Distribución por Categoría",
                         font=util.font_section()).pack(anchor="w", pady=(0, 8))

            cats_data = {
                'C': total_prod.get('total_c', 0) or 0,
                'B': total_prod.get('total_b', 0) or 0,
                'A': total_prod.get('total_a', 0) or 0,
                'AA': total_prod.get('total_aa', 0) or 0,
                'AAA': total_prod.get('total_aaa', 0) or 0,
                'Jumbo': total_prod.get('total_jumbo', 0) or 0,
            }
            cats_data = {k: v for k, v in cats_data.items() if v > 0}

            frame_dist_row = ctk.CTkFrame(inner_dist, fg_color="transparent")
            frame_dist_row.pack(fill="x")

            if cats_data:
                frame_pie = ctk.CTkFrame(frame_dist_row, fg_color="transparent")
                frame_pie.pack(side="left", fill="both", expand=True, padx=(0, 8))

                fig2, ax = plt.subplots(figsize=(4.5, 3.5))
                ax.pie(list(cats_data.values()), labels=list(cats_data.keys()),
                       autopct='%1.1f%%', startangle=90)
                ax.set_title("Distribución Porcentual", fontsize=10, weight='bold')
                fig2.tight_layout()
                canvas2 = FigureCanvasTkAgg(fig2, master=frame_pie)
                canvas2.draw()
                canvas2.get_tk_widget().pack(fill="x")
                plt.close(fig2)

                frame_tabla = ctk.CTkFrame(frame_dist_row, fg_color="transparent")
                frame_tabla.pack(side="left", fill="both", expand=True, padx=(8, 0))

                total_sum = sum(cats_data.values())
                cols_d = ("Categoría", "Cantidad", "%")
                tree_d = ttk.Treeview(frame_tabla, columns=cols_d, show="headings", height=7)
                for col in cols_d:
                    tree_d.heading(col, text=col)
                    tree_d.column(col, anchor="center", width=120)
                for cat, cant in cats_data.items():
                    pct = cant / total_sum * 100 if total_sum > 0 else 0
                    tree_d.insert("", "end", values=(cat, f"{cant:,}", f"{pct:.1f}%"))
                tree_d.pack(fill="x")

            # Estadísticas avanzadas
            card_stats = ctk.CTkFrame(self.frame_prod_content, corner_radius=12)
            card_stats.pack(fill="x", pady=8)
            inner_stats = ctk.CTkFrame(card_stats, fg_color="transparent")
            inner_stats.pack(padx=20, pady=15, fill="x")
            ctk.CTkLabel(inner_stats, text="📉 Estadísticas Avanzadas",
                         font=util.font_section()).pack(anchor="w", pady=(0, 8))

            frame_stats = ctk.CTkFrame(inner_stats, fg_color="transparent")
            frame_stats.pack(fill="x")
            tend = "📈 Creciente" if len(df) > 1 and df['total'].iloc[-1] > df['total'].iloc[0] else "📉 Decreciente"
            stats_data = [
                ("Desv. Estándar", f"{df['total'].std():.1f}"),
                ("Coef. Variación", f"{df['total'].std() / df['total'].mean() * 100:.1f}%"),
                ("Mediana", f"{df['total'].median():.0f}"),
                ("Rango", f"{df['total'].max() - df['total'].min():,}"),
                ("Días Registrados", str(len(df))),
                ("Tendencia", tend),
            ]
            for i, (titulo, valor) in enumerate(stats_data):
                frame_stats.grid_columnconfigure(i, weight=1)
                ctk.CTkLabel(frame_stats, text=f"{titulo}\n{valor}",
                             font=util.font_label()).grid(row=0, column=i, padx=8, pady=4)

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar análisis de producción: {str(e)}")

    # ================= TAB: VENTAS =================

    def create_ventas_tab(self):
        tab = self.notebook.tab("💰 Ventas")
        main = ctk.CTkScrollableFrame(tab)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main, text="💰 Análisis de Ventas",
                     font=util.font_title(), text_color=util.TEXT_MAIN).pack(anchor="w", pady=(0, 6))

        self.ventas_get_fechas = self._crear_selector_periodo(main, "ventas")

        ctk.CTkButton(
            main, text="📊 Generar Análisis",
            font=util.font_input(), height=40,
            fg_color=util.PRIMARY, hover_color=util.PRIMARY_HOVER,
            command=lambda: self._cargar_ventas(main)
        ).pack(anchor="w", pady=(0, 8))

        self.frame_ventas_content = ctk.CTkFrame(main, fg_color="transparent")
        self.frame_ventas_content.pack(fill="x")

    def _cargar_ventas(self, main):
        for w in self.frame_ventas_content.winfo_children():
            w.destroy()

        try:
            fi, ff = self.ventas_get_fechas()
        except:
            messagebox.showerror("Error", "Formato de fecha inválido")
            return

        try:
            ventas_diarias = self.reportes_repo.obtener_ventas_diarias_periodo(fi, ff)
            top_clientes = self.reportes_repo.obtener_top_clientes(fi, ff, limit=10)
            ventas_cat = self.reportes_repo.obtener_ventas_por_categoria(fi, ff)
            historial = self.pedidos_repo.obtener_historial_ventas(fi, ff)

            if not historial:
                ctk.CTkLabel(self.frame_ventas_content,
                             text="ℹ️ No hay ventas en el período seleccionado",
                             font=util.font_label()).pack(pady=20)
                return

            df = pd.DataFrame(historial)

            # Métricas
            card_m = ctk.CTkFrame(self.frame_ventas_content, corner_radius=12)
            card_m.pack(fill="x", pady=8)
            inner_m = ctk.CTkFrame(card_m, fg_color="transparent")
            inner_m.pack(padx=20, pady=15, fill="x")
            ctk.CTkLabel(inner_m, text="📊 Resumen de Ventas",
                         font=util.font_section()).pack(anchor="w", pady=(0, 8))

            frame_m = ctk.CTkFrame(inner_m, fg_color="transparent")
            frame_m.pack(fill="x")
            metricas = [
                ("🛒 Total Ventas", f"{len(df):,}"),
                ("💰 Ingresos", f"${df['precio_total'].sum():,.0f}"),
                ("🎫 Ticket Promedio", f"${df['precio_total'].mean():,.0f}"),
                ("📦 Canastillas", f"{df['total_canastillas'].sum():,.0f}"),
            ]
            for i, (titulo, valor) in enumerate(metricas):
                frame_m.grid_columnconfigure(i, weight=1)
                ctk.CTkLabel(frame_m, text=f"{titulo}\n{valor}",
                             font=util.font_section()).grid(row=0, column=i, padx=10, pady=4)

            # Gráficos ventas diarias
            if ventas_diarias:
                card_g = ctk.CTkFrame(self.frame_ventas_content, corner_radius=12)
                card_g.pack(fill="x", pady=8)
                inner_g = ctk.CTkFrame(card_g, fg_color="transparent")
                inner_g.pack(padx=20, pady=15, fill="x")

                df_vd = pd.DataFrame(ventas_diarias)
                df_vd['fecha'] = pd.to_datetime(df_vd['fecha'])

                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.5))
                ax1.bar(df_vd['fecha'], df_vd['total_ingresos'], color="#2ecc71", alpha=0.8)
                ax1.set_title("Ingresos Diarios", fontsize=10, weight='bold')
                ax1.set_ylabel("Ingresos ($)")
                ax1.tick_params(axis='x', rotation=30)
                ax1.grid(True, alpha=0.3, axis='y')

                ax2.plot(df_vd['fecha'], df_vd['cantidad_ventas'],
                         marker='o', linewidth=2, color="#e67e22")
                ax2.set_title("Ventas por Día", fontsize=10, weight='bold')
                ax2.set_ylabel("Cantidad")
                ax2.tick_params(axis='x', rotation=30)
                ax2.grid(True, alpha=0.3)

                fig.tight_layout()
                canvas = FigureCanvasTkAgg(fig, master=inner_g)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="x")
                plt.close(fig)

            # Top clientes
            if top_clientes:
                card_top = ctk.CTkFrame(self.frame_ventas_content, corner_radius=12)
                card_top.pack(fill="x", pady=8)
                inner_top = ctk.CTkFrame(card_top, fg_color="transparent")
                inner_top.pack(padx=20, pady=15, fill="x")
                ctk.CTkLabel(inner_top, text="🏆 Top Clientes",
                             font=util.font_section()).pack(anchor="w", pady=(0, 8))

                df_top = pd.DataFrame(top_clientes)

                frame_top_row = ctk.CTkFrame(inner_top, fg_color="transparent")
                frame_top_row.pack(fill="x")

                frame_top_graf = ctk.CTkFrame(frame_top_row, fg_color="transparent")
                frame_top_graf.pack(side="left", fill="both", expand=True, padx=(0, 8))

                fig2, ax = plt.subplots(figsize=(5, 3.5))
                ax.barh(df_top['nombre'], df_top['total_comprado'], color="#9b59b6")
                ax.set_title("Top Clientes", fontsize=10, weight='bold')
                ax.set_xlabel("Total ($)")
                ax.grid(True, alpha=0.3, axis='x')
                fig2.tight_layout()
                canvas2 = FigureCanvasTkAgg(fig2, master=frame_top_graf)
                canvas2.draw()
                canvas2.get_tk_widget().pack(fill="x")
                plt.close(fig2)

                frame_top_tabla = ctk.CTkFrame(frame_top_row, fg_color="transparent")
                frame_top_tabla.pack(side="left", fill="both", expand=True, padx=(8, 0))

                cols_top = ("Cliente", "Compras", "Canastillas", "Total ($)")
                tree_top = ttk.Treeview(frame_top_tabla, columns=cols_top,
                                        show="headings", height=8)
                for col in cols_top:
                    tree_top.heading(col, text=col)
                    tree_top.column(col, anchor="center", width=110)
                for _, row in df_top.iterrows():
                    tree_top.insert("", "end", values=(
                        row.get('nombre'),
                        row.get('cantidad_compras'),
                        row.get('total_canastillas'),
                        f"${row.get('total_comprado', 0):,.0f}"
                    ))
                tree_top.pack(fill="x")

            # Ventas por categoría
            if ventas_cat:
                card_cat = ctk.CTkFrame(self.frame_ventas_content, corner_radius=12)
                card_cat.pack(fill="x", pady=8)
                inner_cat = ctk.CTkFrame(card_cat, fg_color="transparent")
                inner_cat.pack(padx=20, pady=15, fill="x")
                ctk.CTkLabel(inner_cat, text="📦 Ventas por Categoría",
                             font=util.font_section()).pack(anchor="w", pady=(0, 8))

                cats_v = {
                    'C': ventas_cat.get('total_c', 0) or 0,
                    'B': ventas_cat.get('total_b', 0) or 0,
                    'A': ventas_cat.get('total_a', 0) or 0,
                    'AA': ventas_cat.get('total_aa', 0) or 0,
                    'AAA': ventas_cat.get('total_aaa', 0) or 0,
                    'Jumbo': ventas_cat.get('total_jumbo', 0) or 0,
                }
                cats_v = {k: v for k, v in cats_v.items() if v > 0}

                frame_cat_row = ctk.CTkFrame(inner_cat, fg_color="transparent")
                frame_cat_row.pack(fill="x")

                if cats_v:
                    frame_cat_pie = ctk.CTkFrame(frame_cat_row, fg_color="transparent")
                    frame_cat_pie.pack(side="left", fill="both", expand=True, padx=(0, 8))
                    fig3, ax3 = plt.subplots(figsize=(4.5, 3.5))
                    ax3.pie(list(cats_v.values()), labels=list(cats_v.keys()),
                            autopct='%1.1f%%', startangle=90)
                    ax3.set_title("Distribución por Categoría", fontsize=10, weight='bold')
                    fig3.tight_layout()
                    canvas3 = FigureCanvasTkAgg(fig3, master=frame_cat_pie)
                    canvas3.draw()
                    canvas3.get_tk_widget().pack(fill="x")
                    plt.close(fig3)

                    frame_cat_tabla = ctk.CTkFrame(frame_cat_row, fg_color="transparent")
                    frame_cat_tabla.pack(side="left", fill="both", expand=True, padx=(8, 0))
                    total_v = sum(cats_v.values())
                    cols_cv = ("Categoría", "Canastillas", "Huevos", "%")
                    tree_cv = ttk.Treeview(frame_cat_tabla, columns=cols_cv,
                                           show="headings", height=7)
                    for col in cols_cv:
                        tree_cv.heading(col, text=col)
                        tree_cv.column(col, anchor="center", width=110)
                    for cat, cant in cats_v.items():
                        pct = cant / total_v * 100 if total_v > 0 else 0
                        tree_cv.insert("", "end", values=(
                            cat, f"{cant:,}", f"{cant * 30:,}", f"{pct:.1f}%"))
                    tree_cv.pack(fill="x")

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar análisis de ventas: {str(e)}")

    # ================= TAB: FINANCIERO =================

    def create_financiero_tab(self):
        tab = self.notebook.tab("💵 Financiero")
        main = ctk.CTkScrollableFrame(tab)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main, text="💵 Análisis Financiero",
                     font=util.font_title(), text_color=util.TEXT_MAIN).pack(anchor="w", pady=(0, 6))

        self.fin_get_fechas = self._crear_selector_periodo(main, "financiero")

        ctk.CTkButton(
            main, text="📊 Generar Análisis",
            font=util.font_input(), height=40,
            fg_color=util.PRIMARY, hover_color=util.PRIMARY_HOVER,
            command=lambda: self._cargar_financiero(main)
        ).pack(anchor="w", pady=(0, 8))

        self.frame_fin_content = ctk.CTkFrame(main, fg_color="transparent")
        self.frame_fin_content.pack(fill="x")

    def _cargar_financiero(self, main):
        for w in self.frame_fin_content.winfo_children():
            w.destroy()

        try:
            fi, ff = self.fin_get_fechas()
        except:
            messagebox.showerror("Error", "Formato de fecha inválido")
            return

        try:
            balance = self.reportes_repo.obtener_balance_periodo(fi, ff)
            movimientos_cat = self.reportes_repo.obtener_movimientos_por_categoria(fi, ff)

            ing = balance.get('total_ingresos', 0) or 0
            egr = balance.get('total_egresos', 0) or 0
            bal = balance.get('balance', 0) or 0
            dias = (ff - fi).days + 1

            # Estado de resultados
            card_er = ctk.CTkFrame(self.frame_fin_content, corner_radius=12)
            card_er.pack(fill="x", pady=8)
            inner_er = ctk.CTkFrame(card_er, fg_color="transparent")
            inner_er.pack(padx=20, pady=15, fill="x")
            ctk.CTkLabel(inner_er, text="📋 Estado de Resultados",
                         font=util.font_section()).pack(anchor="w", pady=(0, 8))

            frame_er = ctk.CTkFrame(inner_er, fg_color="transparent")
            frame_er.pack(fill="x")
            signo = "✅ Ganancia" if bal >= 0 else "⚠️ Pérdida"
            er_data = [
                ("💰 Ingresos", f"${ing:,.0f}"),
                ("💸 Egresos", f"${egr:,.0f}"),
                ("📊 Resultado", f"${bal:,.0f} — {signo}"),
            ]
            for i, (titulo, valor) in enumerate(er_data):
                frame_er.grid_columnconfigure(i, weight=1)
                ctk.CTkLabel(frame_er, text=f"{titulo}\n{valor}",
                             font=util.font_section()).grid(row=0, column=i, padx=10, pady=4)

            # Gráfico waterfall (barras acumuladas simuladas con matplotlib)
            card_wf = ctk.CTkFrame(self.frame_fin_content, corner_radius=12)
            card_wf.pack(fill="x", pady=8)
            inner_wf = ctk.CTkFrame(card_wf, fg_color="transparent")
            inner_wf.pack(padx=20, pady=15, fill="x")

            fig, ax = plt.subplots(figsize=(6, 3.5))
            categorias_wf = ["Ingresos", "Egresos", "Balance Neto"]
            valores_wf = [ing, -egr, bal]
            colores_wf = ["#2ecc71", "#e74c3c", "#3498db" if bal >= 0 else "#e74c3c"]
            bars = ax.bar(categorias_wf, valores_wf, color=colores_wf, edgecolor="white", width=0.5)
            for bar, val in zip(bars, valores_wf):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(abs(ing), 1) * 0.02,
                        f"${val:,.0f}", ha='center', va='bottom', fontsize=9)
            ax.axhline(0, color='gray', linewidth=0.8)
            ax.set_title("Flujo de Caja del Período", fontsize=10, weight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=inner_wf)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x")
            plt.close(fig)

            # Desglose de egresos
            if movimientos_cat:
                df_mov = pd.DataFrame(movimientos_cat)
                df_egr = df_mov[df_mov['tipo'] == 'egreso']

                if not df_egr.empty:
                    card_eg = ctk.CTkFrame(self.frame_fin_content, corner_radius=12)
                    card_eg.pack(fill="x", pady=8)
                    inner_eg = ctk.CTkFrame(card_eg, fg_color="transparent")
                    inner_eg.pack(padx=20, pady=15, fill="x")
                    ctk.CTkLabel(inner_eg, text="💸 Desglose de Egresos",
                                 font=util.font_section()).pack(anchor="w", pady=(0, 8))

                    frame_eg_row = ctk.CTkFrame(inner_eg, fg_color="transparent")
                    frame_eg_row.pack(fill="x")

                    frame_eg_pie = ctk.CTkFrame(frame_eg_row, fg_color="transparent")
                    frame_eg_pie.pack(side="left", fill="both", expand=True, padx=(0, 8))
                    fig2, ax2 = plt.subplots(figsize=(4.5, 3.5))
                    ax2.pie(df_egr['total'], labels=df_egr['categoria'],
                            autopct='%1.1f%%', startangle=90)
                    ax2.set_title("Distribución de Egresos", fontsize=10, weight='bold')
                    fig2.tight_layout()
                    canvas2 = FigureCanvasTkAgg(fig2, master=frame_eg_pie)
                    canvas2.draw()
                    canvas2.get_tk_widget().pack(fill="x")
                    plt.close(fig2)

                    frame_eg_tabla = ctk.CTkFrame(frame_eg_row, fg_color="transparent")
                    frame_eg_tabla.pack(side="left", fill="both", expand=True, padx=(8, 0))
                    total_eg = df_egr['total'].sum()
                    cols_eg = ("Categoría", "Movimientos", "Total", "%")
                    tree_eg = ttk.Treeview(frame_eg_tabla, columns=cols_eg,
                                           show="headings", height=6)
                    for col in cols_eg:
                        tree_eg.heading(col, text=col)
                        tree_eg.column(col, anchor="center", width=110)
                    for _, row in df_egr.iterrows():
                        pct = row['total'] / total_eg * 100 if total_eg > 0 else 0
                        tree_eg.insert("", "end", values=(
                            row['categoria'], row['cantidad_movimientos'],
                            f"${row['total']:,.0f}", f"{pct:.1f}%"))
                    tree_eg.pack(fill="x")

            # Ratios + Proyección
            card_rat = ctk.CTkFrame(self.frame_fin_content, corner_radius=12)
            card_rat.pack(fill="x", pady=8)
            inner_rat = ctk.CTkFrame(card_rat, fg_color="transparent")
            inner_rat.pack(padx=20, pady=15, fill="x")
            ctk.CTkLabel(inner_rat, text="📊 Ratios y Proyección (30 días)",
                         font=util.font_section()).pack(anchor="w", pady=(0, 8))

            factor = 30 / dias if dias > 0 else 1
            margen = bal / ing * 100 if ing > 0 else 0
            ratio_gastos = egr / ing * 100 if ing > 0 else 0
            roi = bal / egr * 100 if egr > 0 else 0
            ing_diario = ing / dias if dias > 0 else 0

            frame_rat = ctk.CTkFrame(inner_rat, fg_color="transparent")
            frame_rat.pack(fill="x")
            rat_data = [
                ("💹 Margen Bruto", f"{margen:.1f}%"),
                ("📉 Ratio Gastos", f"{ratio_gastos:.1f}%"),
                ("📈 ROI", f"{roi:.1f}%"),
                ("💰 Ingreso Diario", f"${ing_diario:,.0f}"),
                ("💰 Ing. Proyect.", f"${ing * factor:,.0f}"),
                ("💸 Egr. Proyect.", f"${egr * factor:,.0f}"),
                ("📊 Bal. Proyect.", f"${bal * factor:,.0f}"),
            ]
            for i, (titulo, valor) in enumerate(rat_data):
                frame_rat.grid_columnconfigure(i, weight=1)
                ctk.CTkLabel(frame_rat, text=f"{titulo}\n{valor}",
                             font=util.font_label()).grid(row=0, column=i, padx=6, pady=4)

            ctk.CTkLabel(inner_rat,
                         text=f"💡 Proyección basada en {dias} días de datos reales",
                         font=util.font_label(), text_color="gray").pack(anchor="w", pady=(8, 0))

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar análisis financiero: {str(e)}")

    # ================= TAB: EXPORTAR =================

    def create_exportar_tab(self):
        tab = self.notebook.tab("📄 Exportar")
        main = ctk.CTkScrollableFrame(tab)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main, text="📄 Exportar Reportes",
                     font=util.font_title(), text_color=util.TEXT_MAIN).pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(
            main,
            text="💡 Genera reportes completos en Excel para archivo o presentación",
            font=util.font_label(), text_color="gray"
        ).pack(anchor="w", pady=(0, 10))

        self.export_get_fechas = self._crear_selector_periodo(main, "export")

        # Checkboxes de contenido
        card_checks = ctk.CTkFrame(main, corner_radius=12)
        card_checks.pack(fill="x", pady=8)
        inner_checks = ctk.CTkFrame(card_checks, fg_color="transparent")
        inner_checks.pack(padx=20, pady=15, fill="x")
        ctk.CTkLabel(inner_checks, text="📋 Selecciona el contenido",
                     font=util.font_section()).pack(anchor="w", pady=(0, 8))

        frame_checks = ctk.CTkFrame(inner_checks, fg_color="transparent")
        frame_checks.pack(fill="x")

        self.check_kpis = ctk.BooleanVar(value=True)
        self.check_prod = ctk.BooleanVar(value=True)
        self.check_ventas = ctk.BooleanVar(value=True)
        self.check_fin = ctk.BooleanVar(value=True)
        self.check_tablas = ctk.BooleanVar(value=True)

        checks = [
            ("KPIs Principales", self.check_kpis),
            ("Análisis de Producción", self.check_prod),
            ("Análisis de Ventas", self.check_ventas),
            ("Análisis Financiero", self.check_fin),
            ("Tablas Detalladas", self.check_tablas),
        ]
        for i, (texto, var) in enumerate(checks):
            frame_checks.grid_columnconfigure(i, weight=1)
            ctk.CTkCheckBox(frame_checks, text=texto, variable=var,
                            font=util.font_label()).grid(row=0, column=i, padx=8, sticky="w")

        # Botón exportar Excel
        card_btn = ctk.CTkFrame(main, corner_radius=12)
        card_btn.pack(fill="x", pady=8)
        inner_btn = ctk.CTkFrame(card_btn, fg_color="transparent")
        inner_btn.pack(padx=20, pady=15, fill="x")

        ctk.CTkButton(
            inner_btn, text="📥 Exportar a Excel",
            height=48, font=util.font_input(),
            fg_color="#2ecc71", hover_color="#27ae60",
            command=self._exportar_excel
        ).pack(anchor="w")

        # Info PDF
        ctk.CTkLabel(
            inner_btn,
            text="📄 El reporte Excel incluye: Resumen ejecutivo · Producción diaria · Historial de ventas · Movimientos financieros",
            font=util.font_label(), text_color="gray", wraplength=700, justify="left"
        ).pack(anchor="w", pady=(10, 0))

    def _exportar_excel(self):
        try:
            fi, ff = self.export_get_fechas()
        except:
            messagebox.showerror("Error", "Formato de fecha inválido")
            return

        file = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            title="Guardar reporte Excel",
            initialfile=f"reporte_granja_{fi}_a_{ff}.xlsx"
        )
        if not file:
            return

        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:

                if self.check_kpis.get():
                    balance = self.reportes_repo.obtener_balance_periodo(fi, ff)
                    resumen = self.reportes_repo.obtener_resumen_produccion_ventas(fi, ff)
                    ing = balance.get('total_ingresos', 0) or 0
                    egr = balance.get('total_egresos', 0) or 0
                    bal = balance.get('balance', 0) or 0
                    prod = resumen.get('total_producido', 0) or 1
                    vend = resumen.get('total_vendido', 0) or 0

                    df_res = pd.DataFrame({
                        'Indicador': [
                            'Período', 'Total Ingresos', 'Total Egresos',
                            'Balance Neto', 'Margen (%)',
                            'Huevos Producidos', 'Huevos Vendidos', 'Tasa de Venta (%)'
                        ],
                        'Valor': [
                            f"{fi} a {ff}",
                            f"${ing:,.0f}", f"${egr:,.0f}", f"${bal:,.0f}",
                            f"{bal / ing * 100:.1f}%" if ing > 0 else "N/A",
                            f"{prod:,}", f"{vend:,}",
                            f"{vend / prod * 100:.1f}%" if prod > 0 else "N/A"
                        ]
                    })
                    df_res.to_excel(writer, sheet_name='Resumen', index=False)

                if self.check_prod.get() and self.check_tablas.get():
                    prod_data = self.reportes_repo.obtener_produccion_diaria_periodo(fi, ff)
                    if prod_data:
                        pd.DataFrame(prod_data).to_excel(writer, sheet_name='Producción', index=False)

                if self.check_ventas.get() and self.check_tablas.get():
                    ventas_data = self.pedidos_repo.obtener_historial_ventas(fi, ff)
                    if ventas_data:
                        pd.DataFrame(ventas_data).to_excel(writer, sheet_name='Ventas', index=False)

                if self.check_fin.get() and self.check_tablas.get():
                    movs = self.reportes_repo.obtener_todos_movimientos(fi, ff)
                    if movs:
                        pd.DataFrame(movs).to_excel(writer, sheet_name='Movimientos', index=False)

            output.seek(0)
            with open(file, 'wb') as f:
                f.write(output.read())

            messagebox.showinfo("Éxito", f"✅ Reporte Excel generado correctamente:\n{file}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar Excel: {str(e)}")


# ================= UTILS =================

def render_reportes(parent):
    module = ReportesModule(parent)
    return module
