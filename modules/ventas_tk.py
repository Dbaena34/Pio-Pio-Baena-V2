"""
Módulo de Ventas - CustomTkinter
Gestiona pedidos, despachos y ventas de huevos por canastillas
"""
import sys
import traceback
import pandas as pd
import customtkinter as ctk
import matplotlib.pyplot as plt
from utils import config as util
from tkcalendar import DateEntry
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date, timedelta
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


sys.path.append('..')

from data.database import db
from data.models import PedidosRepository, ClientesRepository, PreciosRepository, StockRepository, InsumosRepository

class VentasModule:

    def __init__(self, parent):
        self.parent = parent
        self.pedidos_repo = PedidosRepository(db)
        self.clientes_repo = ClientesRepository(db)
        self.precios_repo = PreciosRepository(db)
        self.stock_repo = StockRepository(db)
        self.insumos_repo = InsumosRepository(db)
        self.categorias = ['C', 'B', 'A', 'AA', 'AAA', 'Jumbo']
        self.categorias_db = ['canastillas_c', 'canastillas_b', 'canastillas_a',
                              'canastillas_aa', 'canastillas_aaa', 'canastillas_jumbo']
        self.precios_db = ['precio_c', 'precio_b', 'precio_a', 'precio_aa', 'precio_aaa', 'precio_jumbo']
        self.HUEVOS_POR_CANASTILLA = 30

        # Estado interno (reemplaza st.session_state)
        self._clientes = []
        self._precios = {}
        self._stock_canastillas = {}
        self._pedidos_pendientes = []

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

        self.notebook.add("🛒 Crear Pedido")
        self.notebook.add("📦 Despachar")
        self.notebook.add("📊 Historial")
        self.notebook.add("👥 Clientes")

        self.notebook._segmented_button.configure(font=util.font_label(), height=40)

        self.create_pedido_tab()
        self.create_despachar_tab()
        self.create_historial_tab()
        self.create_clientes_tab()

    # ================= TAB: CREAR PEDIDO =================

    def create_pedido_tab(self):
        tab = self.notebook.tab("🛒 Crear Pedido")

        main = ctk.CTkScrollableFrame(tab)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main, text="🛒 Crear Nuevo Pedido",
                     font=util.font_title(), text_color=util.TEXT_MAIN).pack(anchor="w", pady=(0, 10))

        # --- CARD: DISPONIBILIDAD ---
        card_disp = ctk.CTkFrame(main, corner_radius=12)
        card_disp.pack(fill="x", pady=8)
        inner_disp = ctk.CTkFrame(card_disp, fg_color="transparent")
        inner_disp.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(inner_disp, text="📦 Disponibilidad de Canastillas",
                     font=util.font_section()).pack(anchor="w", pady=(0, 8))

        frame_disp = ctk.CTkFrame(inner_disp, fg_color="transparent")
        frame_disp.pack(fill="x")
        self.disp_labels = {}
        for i, cat in enumerate(self.categorias):
            frame_disp.grid_columnconfigure(i, weight=1)
            lbl = ctk.CTkLabel(frame_disp, text=f"{cat}\n--", font=util.font_label())
            lbl.grid(row=0, column=i, padx=8, pady=4)
            self.disp_labels[cat] = lbl

        # --- CARD: CLIENTE ---
        card_cli = ctk.CTkFrame(main, corner_radius=12)
        card_cli.pack(fill="x", pady=8)
        inner_cli = ctk.CTkFrame(card_cli, fg_color="transparent")
        inner_cli.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(inner_cli, text="👤 Cliente",
                     font=util.font_section()).pack(anchor="w", pady=(0, 8))

        frame_cli_row = ctk.CTkFrame(inner_cli, fg_color="transparent")
        frame_cli_row.pack(fill="x")
        frame_cli_row.grid_columnconfigure(0, weight=1)
        frame_cli_row.grid_columnconfigure(1, weight=0)

        self.pedido_cliente_var = ctk.StringVar(value="")
        self.pedido_cliente_combo = ttk.Combobox(
            frame_cli_row, textvariable=self.pedido_cliente_var,
            state="readonly", font=("Arial", 13)
        )
        self.pedido_cliente_combo.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.pedido_cliente_combo.bind("<<ComboboxSelected>>", lambda e: None)

        ctk.CTkButton(
            frame_cli_row, text="➕ Nuevo Cliente",
            font=util.font_input(), height=36,
            fg_color=util.PRIMARY, hover_color=util.PRIMARY_HOVER,
            command=self._toggle_form_nuevo_cliente
        ).grid(row=0, column=1)

        # Form nuevo cliente (oculto por defecto)
        self.frame_nuevo_cliente = ctk.CTkFrame(inner_cli, corner_radius=10)
        # No se hace pack hasta que el usuario lo abra

        inner_nc = ctk.CTkFrame(self.frame_nuevo_cliente, fg_color="transparent")
        inner_nc.pack(padx=15, pady=12, fill="x")

        ctk.CTkLabel(inner_nc, text="➕ Registrar Nuevo Cliente",
                     font=util.font_section()).pack(anchor="w", pady=(0, 6))

        frame_nc_row = ctk.CTkFrame(inner_nc, fg_color="transparent")
        frame_nc_row.pack(fill="x")
        frame_nc_row.grid_columnconfigure(0, weight=1)
        frame_nc_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame_nc_row, text="Nombre", font=util.font_text()).grid(
            row=0, column=0, sticky="w", padx=(0, 5))
        ctk.CTkLabel(frame_nc_row, text="Teléfono/Contacto", font=util.font_text()).grid(
            row=0, column=1, sticky="w", padx=(5, 0))

        self.nc_nombre_entry = ctk.CTkEntry(frame_nc_row, font=util.font_input(), height=36)
        self.nc_nombre_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=4)

        self.nc_contacto_entry = ctk.CTkEntry(frame_nc_row, font=util.font_input(), height=36)
        self.nc_contacto_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=4)

        frame_nc_btns = ctk.CTkFrame(inner_nc, fg_color="transparent")
        frame_nc_btns.pack(fill="x", pady=(4, 0))

        ctk.CTkButton(frame_nc_btns, text="💾 Guardar Cliente",
                      font=util.font_input(), height=36,
                      fg_color="#2ecc71", hover_color="#27ae60",
                      command=self._guardar_nuevo_cliente_pedido).pack(side="left", padx=(0, 8))

        ctk.CTkButton(frame_nc_btns, text="❌ Cancelar",
                      font=util.font_input(), height=36,
                      fg_color="#e74c3c", hover_color="#c0392b",
                      command=self._toggle_form_nuevo_cliente).pack(side="left")

        # --- CARD: FECHA/HORA ---
        card_dt = ctk.CTkFrame(main, corner_radius=12)
        card_dt.pack(fill="x", pady=8)
        inner_dt = ctk.CTkFrame(card_dt, fg_color="transparent")
        inner_dt.pack(padx=20, pady=15, fill="x")
        inner_dt.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(inner_dt, text="Fecha del pedido", font=util.font_label()).grid(
            row=0, column=0, padx=8, sticky="w")
        self.pedido_fecha = DateEntry(inner_dt, date_pattern='yyyy-mm-dd',
                                     font=("Arial", 13), width=14)
        self.pedido_fecha.set_date(date.today())
        self.pedido_fecha.grid(row=0, column=1, padx=8, sticky="w")

        ctk.CTkLabel(inner_dt, text="Hora del pedido", font=util.font_label()).grid(
            row=0, column=2, padx=8, sticky="w")
        self.pedido_hora_entry = ctk.CTkEntry(inner_dt, width=130, height=35,
                                              font=util.font_input(), justify="center")
        self.pedido_hora_entry.insert(0, datetime.now().strftime("%H:%M:%S"))
        self.pedido_hora_entry.grid(row=0, column=3, padx=8, sticky="ew")

        # --- CARD: CANASTILLAS ---
        card_cant = ctk.CTkFrame(main, corner_radius=12)
        card_cant.pack(fill="x", pady=8)
        inner_cant = ctk.CTkFrame(card_cant, fg_color="transparent")
        inner_cant.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(inner_cant, text="📝 Canastillas por categoría",
                     font=util.font_section()).pack(anchor="w", pady=(0, 8))

        grid_cant = ctk.CTkFrame(inner_cant, fg_color="transparent")
        grid_cant.pack()
        self.cant_entries = {}

        for i, cat in enumerate(self.categorias):
            grid_cant.grid_columnconfigure(i, weight=1)
            fc = ctk.CTkFrame(grid_cant, corner_radius=8)
            fc.grid(row=0, column=i, padx=6, sticky="nsew")
            ctk.CTkLabel(fc, text=f"Tipo {cat}", font=util.font_label()).pack(pady=(6, 0))
            e = ctk.CTkEntry(fc, height=40, justify="center", font=util.font_input())
            e.insert(0, "0")
            e.pack(pady=5, fill="x", padx=5)
            e.bind("<KeyRelease>", lambda ev: self._actualizar_resumen_pedido())
            self.cant_entries[cat] = e

        # --- CARD: RESUMEN ---
        card_res = ctk.CTkFrame(main, corner_radius=12)
        card_res.pack(fill="x", pady=8)
        inner_res = ctk.CTkFrame(card_res, fg_color="transparent")
        inner_res.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(inner_res, text="💰 Resumen del Pedido",
                     font=util.font_section()).pack(anchor="w", pady=(0, 8))

        frame_res_cols = ctk.CTkFrame(inner_res, fg_color="transparent")
        frame_res_cols.pack(fill="x")
        frame_res_cols.grid_columnconfigure(0, weight=1)
        frame_res_cols.grid_columnconfigure(1, weight=1)

        self.label_resumen_cantidades = ctk.CTkLabel(
            frame_res_cols, text="Sin cantidades aún", font=util.font_label(),
            justify="left")
        self.label_resumen_cantidades.grid(row=0, column=0, sticky="nw", padx=10)

        self.label_resumen_valores = ctk.CTkLabel(
            frame_res_cols, text="", font=util.font_label(), justify="left")
        self.label_resumen_valores.grid(row=0, column=1, sticky="nw", padx=10)

        # Ajuste de precio
        frame_ajuste = ctk.CTkFrame(inner_res, fg_color="transparent")
        frame_ajuste.pack(fill="x", pady=(10, 0))
        frame_ajuste.grid_columnconfigure(0, weight=1)
        frame_ajuste.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(frame_ajuste, text="Ajustar precio total (opcional)",
                     font=util.font_label()).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.precio_ajustado_entry = ctk.CTkEntry(
            frame_ajuste, height=38, justify="center", font=util.font_input(), width=180)
        self.precio_ajustado_entry.insert(0, "0")
        self.precio_ajustado_entry.grid(row=0, column=1)

        # Observaciones
        ctk.CTkLabel(inner_res, text="Observaciones (opcional)",
                     font=util.font_label()).pack(anchor="w", pady=(10, 4))
        self.pedido_obs_textbox = ctk.CTkTextbox(inner_res, height=70)
        self.pedido_obs_textbox.pack(fill="x")

        # Tipo de pedido
        ctk.CTkLabel(inner_res, text="¿Cómo procesar este pedido?",
                     font=util.font_label()).pack(anchor="w", pady=(10, 4))
        self.tipo_pedido_var = ctk.StringVar(value="pendiente")
        ctk.CTkSegmentedButton(
            inner_res,
            values=["pendiente", "despachar_ahora"],
            variable=self.tipo_pedido_var,
            font=util.font_label()
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkButton(
            inner_res, text="💾 Procesar Pedido",
            height=45, font=util.font_input(),
            fg_color="#2ecc71", hover_color="#27ae60",
            command=self._procesar_pedido
        ).pack(pady=(8, 0))

        # Carga inicial
        self._cargar_datos_pedido()

    def _cargar_datos_pedido(self):
        """Carga stock, precios y clientes para el formulario de pedido."""
        try:
            stock = self.stock_repo.obtener_stock_actual()
            self._precios = self.precios_repo.obtener_precio_actual() or {}
            cats_db_stock = ['tipo_c', 'tipo_b', 'tipo_a', 'tipo_aa', 'tipo_aaa', 'tipo_jumbo']
            for cat, cat_db in zip(self.categorias, cats_db_stock):
                huevos = stock.get(cat_db, 0) or 0
                self._stock_canastillas[cat] = huevos // self.HUEVOS_POR_CANASTILLA
                disp = self._stock_canastillas[cat]
                icono = "🟢" if disp > 5 else "🟡" if disp > 0 else "🔴"
                self.disp_labels[cat].configure(text=f"{icono} {cat}\n{disp} can.")
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando stock/precios: {str(e)}")

        self._cargar_clientes_combo(self.pedido_cliente_combo, self.pedido_cliente_var)

    def _cargar_clientes_combo(self, combo, var):
        """Carga la lista de clientes en un combo dado."""
        try:
            self._clientes = self.clientes_repo.obtener_clientes_activos() or []
            nombres = [c['nombre'] for c in self._clientes]
            combo['values'] = nombres
            if nombres:
                combo.set(nombres[0])
                var.set(nombres[0])
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando clientes: {str(e)}")

    def _get_cliente_id(self, nombre):
        """Devuelve el id del cliente por nombre."""
        for c in self._clientes:
            if c['nombre'] == nombre:
                return c['id']
        return None

    def _toggle_form_nuevo_cliente(self):
        if self.frame_nuevo_cliente.winfo_ismapped():
            self.frame_nuevo_cliente.pack_forget()
        else:
            self.frame_nuevo_cliente.pack(fill="x", pady=(8, 0))
            self.nc_nombre_entry.focus()

    def _guardar_nuevo_cliente_pedido(self):
        nombre = self.nc_nombre_entry.get().strip()
        contacto = self.nc_contacto_entry.get().strip()
        if not nombre:
            messagebox.showwarning("Advertencia", "Ingresa el nombre del cliente")
            return
        try:
            self.clientes_repo.crear_cliente(
                nombre=nombre,
                contacto=contacto if contacto else None
            )
            messagebox.showinfo("Éxito", f"✅ Cliente '{nombre}' creado exitosamente")
            self.frame_nuevo_cliente.pack_forget()
            self.nc_nombre_entry.delete(0, "end")
            self.nc_contacto_entry.delete(0, "end")
            self._cargar_clientes_combo(self.pedido_cliente_combo, self.pedido_cliente_var)
            # Seleccionar el recién creado
            self.pedido_cliente_combo.set(nombre)
            self.pedido_cliente_var.set(nombre)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _actualizar_resumen_pedido(self):
        try:
            cantidades = {cat: safe_int(self.cant_entries[cat].get()) for cat in self.categorias}
            total_can = sum(cantidades.values())

            if total_can == 0:
                self.label_resumen_cantidades.configure(text="Sin cantidades aún")
                self.label_resumen_valores.configure(text="")
                self.precio_ajustado_entry.delete(0, "end")
                self.precio_ajustado_entry.insert(0, "0")
                return

            lineas_cant = []
            lineas_val = []
            total_precio = 0

            for cat, precio_db in zip(self.categorias, self.precios_db):
                cant = cantidades[cat]
                if cant > 0:
                    huevos = cant * self.HUEVOS_POR_CANASTILLA
                    precio_can = (self._precios.get(precio_db, 0) or 0) * self.HUEVOS_POR_CANASTILLA
                    subtotal = cant * precio_can
                    total_precio += subtotal
                    lineas_cant.append(f"• {cat}: {cant} can. ({huevos} huevos)")
                    lineas_val.append(f"• {cat}: ${subtotal:,.0f}")

            lineas_cant.append(f"\nTotal: {total_can} can. ({total_can * self.HUEVOS_POR_CANASTILLA} huevos)")
            lineas_val.append(f"\nTotal: ${total_precio:,.0f}")

            self.label_resumen_cantidades.configure(text="\n".join(lineas_cant))
            self.label_resumen_valores.configure(text="\n".join(lineas_val))

            self.precio_ajustado_entry.delete(0, "end")
            self.precio_ajustado_entry.insert(0, str(int(total_precio)))
        except:
            pass

    def _procesar_pedido(self):
        nombre_cliente = self.pedido_cliente_var.get()
        cliente_id = self._get_cliente_id(nombre_cliente)
        if not cliente_id:
            messagebox.showwarning("Advertencia", "Selecciona un cliente")
            return

        cantidades = {cat: safe_int(self.cant_entries[cat].get()) for cat in self.categorias}
        total_can = sum(cantidades.values())
        if total_can == 0:
            messagebox.showwarning("Advertencia", "Agrega al menos una canastilla")
            return

        # Validar disponibilidad
        for cat in self.categorias:
            if cantidades[cat] > self._stock_canastillas.get(cat, 0):
                messagebox.showerror("Error",
                    f"No hay suficientes canastillas de tipo {cat}. "
                    f"Disponibles: {self._stock_canastillas.get(cat, 0)}")
                return

        try:
            fecha = datetime.strptime(self.pedido_fecha.get(), "%Y-%m-%d").date()
            hora = self.pedido_hora_entry.get()
            precio_total = safe_float(self.precio_ajustado_entry.get())
            obs = self.pedido_obs_textbox.get("1.0", "end-1c").strip()
            tipo = self.tipo_pedido_var.get()

            pedido_id = self.pedidos_repo.crear_pedido(
                cliente_id=cliente_id,
                fecha=fecha,
                hora=hora,
                canastillas_c=cantidades['C'],
                canastillas_b=cantidades['B'],
                canastillas_a=cantidades['A'],
                canastillas_aa=cantidades['AA'],
                canastillas_aaa=cantidades['AAA'],
                canastillas_jumbo=cantidades['Jumbo'],
                precio_total=precio_total,
                observaciones=obs if obs else None
            )

            if tipo == 'despachar_ahora':
                total_canastillas = sum(cantidades.values())
                
                pares_embalaje = self._preguntar_embalaje()
                
                # Canceló la operación
                if pares_embalaje is None:
                    return

                canastillas_embalaje = pares_embalaje * 2
                total_descontar = total_canastillas + canastillas_embalaje

                stock_info = self.insumos_repo.obtener_stock_canastillas()
                
                if stock_info['total'] < total_descontar:
                    messagebox.showerror(
                        "❌ Sin canastillas",
                        f"Stock disponible: {int(stock_info['total'])} canastillas\n"
                        f"Necesarias: {total_descontar}\n"
                        f"(Venta: {total_canastillas} + Embalaje: {canastillas_embalaje})"
                    )
                    return

                self.pedidos_repo.despachar_pedido(
                    pedido_id=pedido_id,
                    fecha=fecha,
                    hora=hora,
                    canastillas_c=cantidades['C'],
                    canastillas_b=cantidades['B'],
                    canastillas_a=cantidades['A'],
                    canastillas_aa=cantidades['AA'],
                    canastillas_aaa=cantidades['AAA'],
                    canastillas_jumbo=cantidades['Jumbo'],
                    observaciones="Despacho inmediato"
                )

                self.insumos_repo.descontar_canastillas(cantidad=total_descontar,motivo=(f"Despacho pedido #{pedido_id} "f"(Venta: {total_canastillas}, "f"Embalaje: {canastillas_embalaje})"))

                mensaje = (f"✅ Pedido #{pedido_id} creado y despachado exitosamente\n\n"f"📦 Canastillas vendidas: {total_canastillas}" )

                if canastillas_embalaje > 0:
                    mensaje += (
                        f"\n🧱 Embalaje: {pares_embalaje} par(es)"
                        f" ({canastillas_embalaje} canastillas)"
                    )

                mensaje += f"\n📉 Total descontado: {total_descontar} canastillas"

                messagebox.showinfo("Éxito", mensaje)
            else:
                messagebox.showinfo("Éxito",
                    f"✅ Pedido #{pedido_id} guardado como pendiente")

            # Limpiar formulario
            for e in self.cant_entries.values():
                e.delete(0, "end")
                e.insert(0, "0")
            self.pedido_obs_textbox.delete("1.0", "end")
            self.precio_ajustado_entry.delete(0, "end")
            self.precio_ajustado_entry.insert(0, "0")
            self.label_resumen_cantidades.configure(text="Sin cantidades aún")
            self.label_resumen_valores.configure(text="")
            self._cargar_datos_pedido()
            self.parent.winfo_toplevel().actualizar_alertas()

        

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Error", traceback.format_exc())

    def _preguntar_embalaje(self):
        """Pregunta si se desean agregar pares de canastillas de embalaje.
        Devuelve:
            None -> Canceló el proceso
            0    -> No agregar embalaje
            1..n -> Número de pares
        """

        resultado = {"pares": None}

        ventana = ctk.CTkToplevel(self.parent)
        ventana.title("Canastillas de embalaje")
        ventana.geometry("420x250")
        ventana.resizable(False, False)
        ventana.grab_set()

        ctk.CTkLabel(
            ventana,
            text="📦 Canastillas de embalaje",
            font=util.font_section()
        ).pack(pady=(20,10))

        ctk.CTkLabel(
            ventana,
            text="¿Desea agregar canastillas de embalaje?",
            font=util.font_label()
        ).pack()

        pares_var = ctk.IntVar(value=0)

        frame = ctk.CTkFrame(ventana, fg_color="transparent")
        frame.pack(pady=20)

        def disminuir():
            if pares_var.get() > 0:
                pares_var.set(pares_var.get()-1)
                lbl.configure(text=str(pares_var.get()))

        def aumentar():
            pares_var.set(pares_var.get()+1)
            lbl.configure(text=str(pares_var.get()))

        ctk.CTkButton(
            frame,
            text="-",
            width=40,
            command=disminuir
        ).pack(side="left", padx=10)

        lbl = ctk.CTkLabel(
            frame,
            text="0",
            width=60,
            font=util.font_title()
        )
        lbl.pack(side="left")

        ctk.CTkButton(
            frame,
            text="+",
            width=40,
            command=aumentar
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            ventana,
            text="Cada par corresponde a 2 canastillas.",
            font=util.font_text()
        ).pack()

        botones = ctk.CTkFrame(ventana, fg_color="transparent")
        botones.pack(pady=20)

        def aceptar():
            resultado["pares"] = pares_var.get()
            ventana.destroy()

        def cancelar():
            resultado["pares"] = None
            ventana.destroy()

        ctk.CTkButton(
            botones,
            text="Aceptar",
            command=aceptar,
            fg_color="#2ecc71"
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            botones,
            text="Cancelar",
            command=cancelar,
            fg_color="#e74c3c"
        ).pack(side="left", padx=8)

        ventana.wait_window()

        return resultado["pares"]

    # ================= TAB: DESPACHAR =================

    def create_despachar_tab(self):
        tab = self.notebook.tab("📦 Despachar")

        main = ctk.CTkScrollableFrame(tab)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main, text="📦 Despachar Pedidos Pendientes",
                     font=util.font_title(), text_color=util.TEXT_MAIN).pack(anchor="w", pady=(0, 10))

        ctk.CTkButton(
            main, text="🔄 Actualizar Lista",
            font=util.font_input(), height=38,
            fg_color=util.PRIMARY, hover_color=util.PRIMARY_HOVER,
            command=self._cargar_pedidos_pendientes
        ).pack(anchor="w", pady=(0, 10))

        self.label_pendientes_info = ctk.CTkLabel(
            main, text="", font=util.font_label()
        )
        self.label_pendientes_info.pack(anchor="w", pady=(0, 8))

        # Contenedor dinámico de tarjetas de pedidos
        self.frame_pedidos_container = ctk.CTkFrame(main, fg_color="transparent")
        self.frame_pedidos_container.pack(fill="x")

        self._cargar_pedidos_pendientes()

    def _cargar_pedidos_pendientes(self):
        # Limpiar contenedor
        for w in self.frame_pedidos_container.winfo_children():
            w.destroy()

        try:
            self._pedidos_pendientes = self.pedidos_repo.obtener_pedidos_pendientes() or []
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        if not self._pedidos_pendientes:
            self.label_pendientes_info.configure(text="✅ No hay pedidos pendientes")
            ctk.CTkLabel(
                self.frame_pedidos_container,
                text="💡 Crea un nuevo pedido en la pestaña 'Crear Pedido'",
                font=util.font_label()
            ).pack(pady=20)
            return

        self.label_pendientes_info.configure(
            text=f"📋 {len(self._pedidos_pendientes)} pedido(s) pendiente(s)"
        )

        for pedido in self._pedidos_pendientes:
            self._crear_card_pedido(pedido)

    def _crear_card_pedido(self, pedido):
        """Crea una card expandible para un pedido pendiente."""
        card = ctk.CTkFrame(self.frame_pedidos_container, corner_radius=12)
        card.pack(fill="x", pady=6)

        # Cabecera con info resumida
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(10, 5))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        titulo = (f"Pedido #{pedido['id']}  —  {pedido['cliente_nombre']}  —  "
                  f"{pedido['total_canastillas']} canastillas  —  "
                  f"${pedido['precio_total']:,.0f}")
        ctk.CTkLabel(header, text=titulo, font=util.font_section(),
                     anchor="w").grid(row=0, column=0, sticky="w")

        # Botón expandir/colapsar
        expand_var = ctk.BooleanVar(value=False)
        body_frame = ctk.CTkFrame(card, fg_color="transparent")

        def toggle_expand():
            if expand_var.get():
                body_frame.pack_forget()
                expand_var.set(False)
                btn_expand.configure(text="▼ Ver detalle")
            else:
                body_frame.pack(fill="x", padx=15, pady=(0, 10))
                expand_var.set(True)
                btn_expand.configure(text="▲ Ocultar")

        btn_expand = ctk.CTkButton(
            header, text="▼ Ver detalle", width=120,
            font=util.font_label(), height=30,
            fg_color="transparent", hover_color=util.CARD_BG,
            text_color=util.PRIMARY, border_width=1,
            command=toggle_expand
        )
        btn_expand.grid(row=0, column=1, padx=(8, 0))

        # Body (oculto por defecto)
        inner_body = ctk.CTkFrame(body_frame, fg_color="transparent")
        inner_body.pack(fill="x", pady=8)
        inner_body.grid_columnconfigure(0, weight=1)
        inner_body.grid_columnconfigure(1, weight=1)

        # Info cliente
        frame_info = ctk.CTkFrame(inner_body, fg_color="transparent")
        frame_info.grid(row=0, column=0, sticky="nw", padx=8)

        ctk.CTkLabel(frame_info, text="Información del Cliente",
                     font=util.font_section()).pack(anchor="w", pady=(0, 4))
        for txt in [
            f"👤 Nombre: {pedido['cliente_nombre']}",
            f"📞 Contacto: {pedido.get('cliente_contacto', 'N/A')}",
            f"📅 Fecha: {pedido['fecha']}",
            f"🕐 Hora: {pedido['hora']}",
        ]:
            ctk.CTkLabel(frame_info, text=txt, font=util.font_label(),
                         anchor="w").pack(anchor="w")
        if pedido.get('observaciones'):
            ctk.CTkLabel(frame_info, text=f"📝 Obs: {pedido['observaciones']}",
                         font=util.font_label(), anchor="w",
                         wraplength=280).pack(anchor="w")

        # Detalle canastillas
        frame_det = ctk.CTkFrame(inner_body, fg_color="transparent")
        frame_det.grid(row=0, column=1, sticky="nw", padx=8)

        ctk.CTkLabel(frame_det, text="Detalle del Pedido",
                     font=util.font_section()).pack(anchor="w", pady=(0, 4))
        for cat, cat_db in zip(self.categorias, self.categorias_db):
            cant = pedido.get(cat_db, 0)
            if cant > 0:
                huevos = cant * self.HUEVOS_POR_CANASTILLA
                ctk.CTkLabel(frame_det,
                             text=f"📦 {cat}: {cant} can. ({huevos} huevos)",
                             font=util.font_label()).pack(anchor="w")
        ctk.CTkLabel(frame_det, text=f"💰 Total: ${pedido['precio_total']:,.0f}",
                     font=util.font_section()).pack(anchor="w", pady=(6, 0))

        # Botones de acción
        frame_btns = ctk.CTkFrame(body_frame, fg_color="transparent")
        frame_btns.pack(fill="x", pady=(4, 0))

        ctk.CTkButton(
            frame_btns, text="✅ Despachar",
            font=util.font_input(), height=38,
            fg_color="#2ecc71", hover_color="#27ae60",
            command=lambda p=pedido: self._despachar_pedido(p)
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            frame_btns, text="✏️ Editar",
            font=util.font_input(), height=38,
            fg_color=util.PRIMARY, hover_color=util.PRIMARY_HOVER,
            command=lambda p=pedido, bf=body_frame, ev=expand_var, be=btn_expand: (
                self._mostrar_form_edicion(p, bf, ev, be)
            )
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            frame_btns, text="❌ Cancelar Pedido",
            font=util.font_input(), height=38,
            fg_color="#e74c3c", hover_color="#c0392b",
            command=lambda p=pedido: self._cancelar_pedido(p)
        ).pack(side="left")

    def _despachar_pedido(self, pedido):
        if not messagebox.askyesno("Confirmar",
                f"¿Despachar pedido #{pedido['id']} de {pedido['cliente_nombre']}?"):
            return
        try:
            total_canastillas = (
                pedido['canastillas_c'] + pedido['canastillas_b'] + pedido['canastillas_a'] +
                pedido['canastillas_aa'] + pedido['canastillas_aaa'] + pedido['canastillas_jumbo']
            )

            stock_info = self.insumos_repo.obtener_stock_canastillas()
            if stock_info['total'] < total_canastillas:
                messagebox.showerror(
                    "❌ Sin canastillas",
                    f"Stock disponible: {int(stock_info['total'])} canastillas\n"
                    f"Requeridas: {total_canastillas}\n\n"
                    "Registra una compra de canastillas en Insumos y Pagos."
                )
                return

            self.pedidos_repo.despachar_pedido(
                pedido_id=pedido['id'],
                fecha=date.today(),
                hora=datetime.now().strftime("%H:%M:%S"),
                canastillas_c=pedido['canastillas_c'],
                canastillas_b=pedido['canastillas_b'],
                canastillas_a=pedido['canastillas_a'],
                canastillas_aa=pedido['canastillas_aa'],
                canastillas_aaa=pedido['canastillas_aaa'],
                canastillas_jumbo=pedido['canastillas_jumbo'],
                observaciones="Despachado"
            )

            self.insumos_repo.descontar_canastillas(
                cantidad=total_canastillas,
                motivo=f"Despacho pedido #{pedido['id']}"
            )

            messagebox.showinfo("Éxito", f"✅ Pedido #{pedido['id']} despachado exitosamente")
            self._cargar_pedidos_pendientes()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _cancelar_pedido(self, pedido):
        if not messagebox.askyesno("Confirmar",
                f"¿Cancelar pedido #{pedido['id']}? Esta acción no se puede deshacer."):
            return
        try:
            self.pedidos_repo.cancelar_pedido(pedido['id'])
            messagebox.showinfo("Éxito", f"✅ Pedido #{pedido['id']} cancelado")
            self._cargar_pedidos_pendientes()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _mostrar_form_edicion(self, pedido, body_frame, expand_var, btn_expand):
        """Muestra el formulario de edición dentro del body de la card."""
        # Asegurar que el body esté visible
        if not expand_var.get():
            body_frame.pack(fill="x", padx=15, pady=(0, 10))
            expand_var.set(True)
            btn_expand.configure(text="▲ Ocultar")

        # Limpiar formularios de edición previos en esta card
        for w in body_frame.winfo_children():
            if getattr(w, '_es_form_edicion', False):
                w.destroy()

        form_edit = ctk.CTkFrame(body_frame, corner_radius=8)
        form_edit._es_form_edicion = True
        form_edit.pack(fill="x", pady=(8, 0))

        inner_edit = ctk.CTkFrame(form_edit, fg_color="transparent")
        inner_edit.pack(padx=15, pady=12, fill="x")

        ctk.CTkLabel(inner_edit, text="✏️ Editar Cantidades",
                     font=util.font_section()).pack(anchor="w", pady=(0, 6))

        grid_edit = ctk.CTkFrame(inner_edit, fg_color="transparent")
        grid_edit.pack()
        edit_entries = {}

        for i, (cat, cat_db) in enumerate(zip(self.categorias, self.categorias_db)):
            grid_edit.grid_columnconfigure(i, weight=1)
            fc = ctk.CTkFrame(grid_edit, corner_radius=8)
            fc.grid(row=0, column=i, padx=5, sticky="nsew")
            ctk.CTkLabel(fc, text=f"Tipo {cat}", font=util.font_label()).pack(pady=(5, 0))
            e = ctk.CTkEntry(fc, height=36, justify="center", font=util.font_input())
            e.insert(0, str(pedido.get(cat_db, 0)))
            e.pack(pady=4, fill="x", padx=4)
            edit_entries[cat] = e

        self.label_edit_resumen = ctk.CTkLabel(
            inner_edit, text="", font=util.font_label())
        self.label_edit_resumen.pack(anchor="w", pady=6)

        def actualizar_resumen_edit():
            try:
                precios = self.precios_repo.obtener_precio_actual() or {}
                total_can = sum(safe_int(edit_entries[cat].get()) for cat in self.categorias)
                total_precio = sum(
                    safe_int(edit_entries[cat].get()) *
                    (precios.get(precio_db, 0) or 0) * self.HUEVOS_POR_CANASTILLA
                    for cat, precio_db in zip(self.categorias, self.precios_db)
                )
                self.label_edit_resumen.configure(
                    text=f"📦 {total_can} canastillas — ${total_precio:,.0f}")
            except:
                pass

        for e in edit_entries.values():
            e.bind("<KeyRelease>", lambda ev: actualizar_resumen_edit())
        actualizar_resumen_edit()

        frame_edit_btns = ctk.CTkFrame(inner_edit, fg_color="transparent")
        frame_edit_btns.pack(fill="x", pady=(4, 0))

        def guardar_edicion():
            try:
                precios = self.precios_repo.obtener_precio_actual() or {}
                nuevas = {cat: safe_int(edit_entries[cat].get()) for cat in self.categorias}
                nuevo_precio = sum(
                    nuevas[cat] * (precios.get(precio_db, 0) or 0) * self.HUEVOS_POR_CANASTILLA
                    for cat, precio_db in zip(self.categorias, self.precios_db)
                )
                self.pedidos_repo.actualizar_pedido(
                    pedido_id=pedido['id'],
                    canastillas_c=nuevas['C'],
                    canastillas_b=nuevas['B'],
                    canastillas_a=nuevas['A'],
                    canastillas_aa=nuevas['AA'],
                    canastillas_aaa=nuevas['AAA'],
                    canastillas_jumbo=nuevas['Jumbo'],
                    precio_total=nuevo_precio
                )
                messagebox.showinfo("Éxito", "✅ Pedido actualizado")
                self._cargar_pedidos_pendientes()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        ctk.CTkButton(frame_edit_btns, text="💾 Guardar Cambios",
                      font=util.font_input(), height=36,
                      fg_color="#2ecc71", hover_color="#27ae60",
                      command=guardar_edicion).pack(side="left", padx=(0, 8))

        ctk.CTkButton(frame_edit_btns, text="❌ Cancelar Edición",
                      font=util.font_input(), height=36,
                      fg_color="#e74c3c", hover_color="#c0392b",
                      command=form_edit.destroy).pack(side="left")

    # ================= TAB: HISTORIAL =================

    def create_historial_tab(self):
        tab = self.notebook.tab("📊 Historial")

        main = ctk.CTkScrollableFrame(tab)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main, text="📊 Historial de Ventas",
                     font=util.font_title(), text_color=util.TEXT_MAIN).pack(anchor="w", pady=(0, 10))

        # Filtros
        card_filtros = ctk.CTkFrame(main, corner_radius=12)
        card_filtros.pack(fill="x", pady=8)
        filtros = ctk.CTkFrame(card_filtros, fg_color="transparent")
        filtros.pack(padx=20, pady=15, fill="x")
        filtros.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        ctk.CTkLabel(filtros, text="Desde", font=util.font_label()).grid(row=0, column=0, padx=5)
        self.hist_inicio = DateEntry(filtros, date_pattern='yyyy-mm-dd',
                                    font=("Arial", 13), width=12)
        self.hist_inicio.set_date(date.today() - timedelta(days=30))
        self.hist_inicio.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(filtros, text="Hasta", font=util.font_label()).grid(row=0, column=2, padx=5)
        self.hist_fin = DateEntry(filtros, date_pattern='yyyy-mm-dd',
                                  font=("Arial", 13), width=12)
        self.hist_fin.set_date(date.today())
        self.hist_fin.grid(row=0, column=3, padx=5)

        ctk.CTkButton(filtros, text="🔍 Buscar",
                      font=util.font_input(), height=38,
                      fg_color=util.PRIMARY, hover_color=util.PRIMARY_HOVER,
                      command=self._cargar_historial).grid(row=0, column=4, padx=10)

        # Métricas
        card_metrics = ctk.CTkFrame(main, corner_radius=12)
        card_metrics.pack(fill="x", pady=8)
        self.frame_hist_metrics = ctk.CTkFrame(card_metrics, fg_color="transparent")
        self.frame_hist_metrics.pack(padx=20, pady=15, fill="x")
        self.hist_metric_labels = []
        for _ in range(4):
            lbl = ctk.CTkLabel(self.frame_hist_metrics, text="--", font=util.font_section())
            lbl.pack(side="left", expand=True, padx=10)
            self.hist_metric_labels.append(lbl)

        # Gráficos
        card_graf = ctk.CTkFrame(main, corner_radius=12)
        card_graf.pack(fill="x", pady=8)
        inner_graf = ctk.CTkFrame(card_graf, fg_color="transparent")
        inner_graf.pack(padx=20, pady=15, fill="x")
        ctk.CTkLabel(inner_graf, text="📈 Análisis Visual",
                     font=util.font_section()).pack(anchor="w", pady=(0, 8))
        self.frame_hist_graficos = ctk.CTkFrame(inner_graf, fg_color="transparent")
        self.frame_hist_graficos.pack(fill="x")

        # Tabla
        card_tabla = ctk.CTkFrame(main, corner_radius=12)
        card_tabla.pack(fill="x", pady=8)
        inner_tabla = ctk.CTkFrame(card_tabla, fg_color="transparent")
        inner_tabla.pack(padx=20, pady=15, fill="x")
        ctk.CTkLabel(inner_tabla, text="📋 Detalle de Ventas",
                     font=util.font_section()).pack(anchor="w", pady=(0, 8))

        cols_hist = ("ID", "Fecha", "Cliente", "C", "B", "A", "AA", "AAA", "Jumbo",
                     "Total Can.", "Total $")
        self.tree_hist = ttk.Treeview(inner_tabla, columns=cols_hist,
                                      show="headings", height=10)
        for col in cols_hist:
            self.tree_hist.heading(col, text=col)
            self.tree_hist.column(col, anchor="center",
                                  width=70 if col not in ("Fecha", "Cliente", "Total $") else 110)
        self.tree_hist.pack(fill="x")

        ctk.CTkButton(
            inner_tabla, text="📥 Exportar CSV",
            font=util.font_input(), height=38,
            fg_color=util.PRIMARY, hover_color=util.PRIMARY_HOVER,
            command=self._exportar_historial
        ).pack(pady=(10, 0))

        self._cargar_historial()

    def _cargar_historial(self):
        for i in self.tree_hist.get_children():
            self.tree_hist.delete(i)
        for w in self.frame_hist_graficos.winfo_children():
            w.destroy()

        try:
            fi = datetime.strptime(self.hist_inicio.get(), "%Y-%m-%d").date()
            ff = datetime.strptime(self.hist_fin.get(), "%Y-%m-%d").date()
        except:
            messagebox.showerror("Error", "Formato de fecha inválido")
            return

        try:
            ventas = self.pedidos_repo.obtener_historial_ventas(fi, ff)
            if not ventas:
                for lbl in self.hist_metric_labels:
                    lbl.configure(text="--")
                return

            df = pd.DataFrame(ventas)

            # Métricas
            total_v = len(df)
            total_can = df['total_canastillas'].sum()
            total_huevos = total_can * self.HUEVOS_POR_CANASTILLA
            total_ing = df['precio_total'].sum()

            self.hist_metric_labels[0].configure(text=f"🧾 Ventas\n{total_v}")
            self.hist_metric_labels[1].configure(text=f"📦 Canastillas\n{total_can:,.0f}")
            self.hist_metric_labels[2].configure(text=f"🥚 Huevos\n{total_huevos:,.0f}")
            self.hist_metric_labels[3].configure(text=f"💰 Ingresos\n${total_ing:,.0f}")

            # Gráficos
            df['fecha'] = pd.to_datetime(df['fecha'])
            ventas_diarias = df.groupby('fecha')['precio_total'].sum().reset_index()
            top_clientes = (df.groupby('cliente_nombre')['precio_total']
                            .sum().sort_values(ascending=False).head(5))

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

            ax1.plot(ventas_diarias['fecha'], ventas_diarias['precio_total'],
                     marker='o', linewidth=2, color="#3498db")
            ax1.set_title("Ingresos por Día", fontsize=11, weight='bold')
            ax1.set_ylabel("Ingresos ($)")
            ax1.tick_params(axis='x', rotation=45)
            ax1.grid(True, alpha=0.3)

            ax2.barh(top_clientes.index, top_clientes.values, color="#2ecc71")
            ax2.set_title("Top 5 Clientes", fontsize=11, weight='bold')
            ax2.set_xlabel("Total Comprado ($)")
            ax2.grid(True, alpha=0.3, axis='x')

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=self.frame_hist_graficos)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x", pady=5)
            plt.close(fig)

            # Tabla
            for _, row in df.iterrows():
                self.tree_hist.insert("", "end", values=(
                    row.get('id'), row.get('fecha').date() if hasattr(row.get('fecha'), 'date') else row.get('fecha'),
                    row.get('cliente_nombre'),
                    row.get('canastillas_c', 0), row.get('canastillas_b', 0),
                    row.get('canastillas_a', 0), row.get('canastillas_aa', 0),
                    row.get('canastillas_aaa', 0), row.get('canastillas_jumbo', 0),
                    row.get('total_canastillas', 0),
                    f"${row.get('precio_total', 0):,.0f}"
                ))
            self._df_historial = df

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _exportar_historial(self):
        if not hasattr(self, '_df_historial') or self._df_historial is None:
            messagebox.showwarning("Advertencia", "No hay datos para exportar. Haz una búsqueda primero.")
            return

        file = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="Exportar historial de ventas"
        )
        if not file:
            return

        try:
            cols_export = ['id', 'fecha', 'cliente_nombre', 'canastillas_c', 'canastillas_b',
                           'canastillas_a', 'canastillas_aa', 'canastillas_aaa', 'canastillas_jumbo',
                           'total_canastillas', 'precio_total']
            df_exp = self._df_historial[[c for c in cols_export if c in self._df_historial.columns]].copy()
            df_exp.columns = ['ID', 'Fecha', 'Cliente', 'C', 'B', 'A', 'AA', 'AAA', 'Jumbo',
                              'Total Can.', 'Total $']
            df_exp.to_csv(file, index=False, encoding='utf-8')
            messagebox.showinfo("Exportado", "✅ CSV generado correctamente")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= TAB: CLIENTES =================

    def create_clientes_tab(self):
        tab = self.notebook.tab("👥 Clientes")

        main = ctk.CTkScrollableFrame(tab)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main, text="👥 Gestión de Clientes",
                     font=util.font_title(), text_color=util.TEXT_MAIN).pack(anchor="w", pady=(0, 10))

        ctk.CTkButton(
            main, text="🔄 Actualizar Lista",
            font=util.font_input(), height=38,
            fg_color=util.PRIMARY, hover_color=util.PRIMARY_HOVER,
            command=self._cargar_clientes_tabla
        ).pack(anchor="w", pady=(0, 8))

        self.label_total_clientes = ctk.CTkLabel(main, text="", font=util.font_label())
        self.label_total_clientes.pack(anchor="w", pady=(0, 6))

        # Tabla de clientes
        card_tabla = ctk.CTkFrame(main, corner_radius=12)
        card_tabla.pack(fill="x", pady=8)
        inner_tabla = ctk.CTkFrame(card_tabla, fg_color="transparent")
        inner_tabla.pack(padx=20, pady=15, fill="x")

        cols_cli = ("ID", "Nombre", "Contacto", "Fecha Registro")
        self.tree_clientes = ttk.Treeview(inner_tabla, columns=cols_cli,
                                          show="headings", height=8)
        for col in cols_cli:
            self.tree_clientes.heading(col, text=col)
            self.tree_clientes.column(col, anchor="center", width=160)
        self.tree_clientes.pack(fill="x")

        # Editar cliente
        card_edit = ctk.CTkFrame(main, corner_radius=12)
        card_edit.pack(fill="x", pady=8)
        inner_edit = ctk.CTkFrame(card_edit, fg_color="transparent")
        inner_edit.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(inner_edit, text="✏️ Editar Cliente",
                     font=util.font_section()).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(inner_edit, text="Selecciona el cliente",
                     font=util.font_text()).pack(anchor="w")

        self.edit_cli_var = ctk.StringVar(value="")
        self.edit_cli_combo = ttk.Combobox(
            inner_edit, textvariable=self.edit_cli_var,
            state="readonly", font=("Arial", 13)
        )
        self.edit_cli_combo.pack(fill="x", pady=4)
        self.edit_cli_combo.bind("<<ComboboxSelected>>", self._on_cliente_edit_selected)

        frame_edit_row = ctk.CTkFrame(inner_edit, fg_color="transparent")
        frame_edit_row.pack(fill="x", pady=4)
        frame_edit_row.grid_columnconfigure(0, weight=1)
        frame_edit_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame_edit_row, text="Nombre", font=util.font_text()).grid(
            row=0, column=0, sticky="w", padx=(0, 5))
        ctk.CTkLabel(frame_edit_row, text="Contacto", font=util.font_text()).grid(
            row=0, column=1, sticky="w", padx=(5, 0))

        self.edit_cli_nombre = ctk.CTkEntry(frame_edit_row, font=util.font_input(), height=36)
        self.edit_cli_nombre.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=4)

        self.edit_cli_contacto = ctk.CTkEntry(frame_edit_row, font=util.font_input(), height=36)
        self.edit_cli_contacto.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=4)

        frame_edit_btns = ctk.CTkFrame(inner_edit, fg_color="transparent")
        frame_edit_btns.pack(fill="x", pady=(4, 0))

        ctk.CTkButton(frame_edit_btns, text="💾 Guardar Cambios",
                      font=util.font_input(), height=38,
                      fg_color="#2ecc71", hover_color="#27ae60",
                      command=self._guardar_edicion_cliente).pack(side="left", padx=(0, 8))

        ctk.CTkButton(frame_edit_btns, text="🗑️ Desactivar Cliente",
                      font=util.font_input(), height=38,
                      fg_color="#e74c3c", hover_color="#c0392b",
                      command=self._desactivar_cliente).pack(side="left")

        # Agregar nuevo cliente
        card_nuevo = ctk.CTkFrame(main, corner_radius=12)
        card_nuevo.pack(fill="x", pady=8)
        inner_nuevo = ctk.CTkFrame(card_nuevo, fg_color="transparent")
        inner_nuevo.pack(padx=20, pady=15, fill="x")

        ctk.CTkLabel(inner_nuevo, text="➕ Agregar Nuevo Cliente",
                     font=util.font_section()).pack(anchor="w", pady=(0, 8))

        frame_nuevo_row = ctk.CTkFrame(inner_nuevo, fg_color="transparent")
        frame_nuevo_row.pack(fill="x")
        frame_nuevo_row.grid_columnconfigure(0, weight=1)
        frame_nuevo_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame_nuevo_row, text="Nombre", font=util.font_text()).grid(
            row=0, column=0, sticky="w", padx=(0, 5))
        ctk.CTkLabel(frame_nuevo_row, text="Contacto", font=util.font_text()).grid(
            row=0, column=1, sticky="w", padx=(5, 0))

        self.nuevo_cli_nombre = ctk.CTkEntry(frame_nuevo_row, font=util.font_input(), height=36)
        self.nuevo_cli_nombre.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=4)

        self.nuevo_cli_contacto = ctk.CTkEntry(frame_nuevo_row, font=util.font_input(), height=36)
        self.nuevo_cli_contacto.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=4)

        ctk.CTkButton(
            inner_nuevo, text="💾 Crear Cliente",
            height=42, font=util.font_input(),
            fg_color="#2ecc71", hover_color="#27ae60",
            command=self._crear_cliente
        ).pack(pady=(10, 0))

        self._cargar_clientes_tabla()

    def _cargar_clientes_tabla(self):
        for i in self.tree_clientes.get_children():
            self.tree_clientes.delete(i)

        try:
            clientes = self.clientes_repo.obtener_clientes_activos() or []
            self._clientes = clientes
            self.label_total_clientes.configure(
                text=f"👥 Total de clientes activos: {len(clientes)}")

            nombres = [c['nombre'] for c in clientes]
            self.edit_cli_combo['values'] = nombres
            if nombres:
                self.edit_cli_combo.set(nombres[0])
                self.edit_cli_var.set(nombres[0])
                self._on_cliente_edit_selected(None)

            for c in clientes:
                self.tree_clientes.insert("", "end", values=(
                    c.get('id'), c.get('nombre'),
                    c.get('contacto', ''), c.get('created_at', '')
                ))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_cliente_edit_selected(self, event):
        nombre = self.edit_cli_var.get()
        cliente = next((c for c in self._clientes if c['nombre'] == nombre), None)
        if cliente:
            self.edit_cli_nombre.delete(0, "end")
            self.edit_cli_nombre.insert(0, cliente.get('nombre', ''))
            self.edit_cli_contacto.delete(0, "end")
            self.edit_cli_contacto.insert(0, cliente.get('contacto', '') or '')

    def _guardar_edicion_cliente(self):
        nombre_sel = self.edit_cli_var.get()
        cliente = next((c for c in self._clientes if c['nombre'] == nombre_sel), None)
        if not cliente:
            messagebox.showwarning("Advertencia", "Selecciona un cliente")
            return
        nuevo_nombre = self.edit_cli_nombre.get().strip()
        nuevo_contacto = self.edit_cli_contacto.get().strip()
        if not nuevo_nombre:
            messagebox.showwarning("Advertencia", "El nombre es obligatorio")
            return
        try:
            self.clientes_repo.actualizar_cliente(
                cliente_id=cliente['id'],
                nombre=nuevo_nombre,
                contacto=nuevo_contacto if nuevo_contacto else None
            )
            messagebox.showinfo("Éxito", "✅ Cliente actualizado")
            self._cargar_clientes_tabla()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _desactivar_cliente(self):
        nombre_sel = self.edit_cli_var.get()
        cliente = next((c for c in self._clientes if c['nombre'] == nombre_sel), None)
        if not cliente:
            messagebox.showwarning("Advertencia", "Selecciona un cliente")
            return
        if not messagebox.askyesno("Confirmar",
                f"¿Desactivar al cliente '{cliente['nombre']}'?"):
            return
        try:
            self.clientes_repo.desactivar_cliente(cliente['id'])
            messagebox.showinfo("Éxito", "✅ Cliente desactivado")
            self._cargar_clientes_tabla()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _crear_cliente(self):
        nombre = self.nuevo_cli_nombre.get().strip()
        contacto = self.nuevo_cli_contacto.get().strip()
        if not nombre:
            messagebox.showwarning("Advertencia", "El nombre es obligatorio")
            return
        try:
            self.clientes_repo.crear_cliente(
                nombre=nombre,
                contacto=contacto if contacto else None
            )
            messagebox.showinfo("Éxito", f"✅ Cliente '{nombre}' creado")
            self.nuevo_cli_nombre.delete(0, "end")
            self.nuevo_cli_contacto.delete(0, "end")
            self._cargar_clientes_tabla()
            # Actualizar combo del tab de pedidos también
            self._cargar_clientes_combo(self.pedido_cliente_combo, self.pedido_cliente_var)
        except Exception as e:
            messagebox.showerror("Error", str(e))


# ================= UTILS =================

def safe_int(value):
    try:
        return int(float(value))
    except:
        return 0

def safe_float(value):
    try:
        return float(value)
    except:
        return 0.0


# Función principal para llamar desde app.py
def render_ventas(parent):
    module = VentasModule(parent)
    return module
