"""
Aplicación Principal - Pío Pío Baena
Sistema de Gestión Avícola - Versión CustomTkinter
"""
import customtkinter as ctk
from data.database import db
from tkinter import messagebox
import matplotlib.pyplot as plt
from utils import config as util
from data.models import StockRepository

APP_VERSION = "2.1.1"

#self.parent.winfo_toplevel().actualizar_alertas() llamada de actualización de alertas desde un módulo
# Configurar tema y apariencia

ctk.set_default_color_theme("utils/theme.json")  # "blue", "green", "dark-blue"
ctk.set_appearance_mode("light")# "dark" o "light"

class GranjaApp(ctk.CTk):
    """Aplicación principal de gestión avícola"""
    
    def __init__(self):
        super().__init__()
        self.state("zoomed")
        # Configuración de la ventana principal
        self.title("Pío Pío Baena - Sistema de Gestión Avícola")
        self.geometry("1400x800")
        # Centrar ventana en la pantalla
        #self.center_window()
        
        # Configurar grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Variables
        self.current_module = None
        
        # Crear interfaz
        self.create_sidebar()
        self.create_main_container()
        
        # Cargar módulo de producción por defecto
        self.show_produccion()
        self.actualizar_alertas()
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
     
    def create_sidebar(self):
        """Crea la barra lateral de navegación"""

        self.sidebar_frame = ctk.CTkFrame(
            self,
            width=240,
            corner_radius=0,
            fg_color=util.CARD
        )
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)

        # ================= HEADER =================
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="🐔 Pío Pío Baena",
            font=util.font_section(),
            text_color=util.TEXT_MAIN
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(25, 5))

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Sistema de Gestión",
            font=util.font_label()
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # ================= BOTONES =================
        def create_nav_button(text, command):
            return ctk.CTkButton(
                self.sidebar_frame,
                text=text,
                command=command,
                font=util.font_input(),
                height=45,
                fg_color=util.PRIMARY,
                hover_color=util.PRIMARY_HOVER,
                corner_radius=10
            )

        self.btn_produccion = create_nav_button("📊 Producción", self.show_produccion)
        self.btn_produccion.grid(row=2, column=0, padx=20, pady=8, sticky="ew")

        self.btn_stock = create_nav_button("📦 Stock", self.show_stock)
        self.btn_stock.grid(row=3, column=0, padx=20, pady=8, sticky="ew")

        self.btn_ventas = create_nav_button("🚚 Ventas", self.show_ventas)
        self.btn_ventas.grid(row=4, column=0, padx=20, pady=8, sticky="ew")

        self.btn_insumos = create_nav_button("💰 Insumos", self.show_insumos_pagos)
        self.btn_insumos.grid(row=5, column=0, padx=20, pady=8, sticky="ew")

        self.btn_reportes = create_nav_button("📈 Reportes", self.show_reportes)
        self.btn_reportes.grid(row=6, column=0, padx=20, pady=8, sticky="ew")
        
        self.btn_explorador = create_nav_button("🔎 Explorador DB",self.show_explorador_db)
        self.btn_explorador.grid(row=7, column=0, padx=20, pady=8, sticky="ew")
        
        # ================= VERSIÓN =================
        self.version_label = ctk.CTkLabel(
            self.sidebar_frame,
            text=f"Versión {APP_VERSION}",
            font=util.font_label(),
            text_color="gray50"
        )
        self.version_label.grid(row=8, column=0, padx=20, pady=(10, 5))
        
        # ================= TEMA =================
        self.appearance_mode_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Tema",
            font=util.font_label()
        )
        self.appearance_mode_label.grid(row=9, column=0, padx=20, pady=(15, 5))

        self.appearance_mode_menu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["Claro", "Oscuro", "Sistema"],
            command=self.change_appearance_mode,
            font=util.font_label()
        )
        self.appearance_mode_menu.grid(row=10, column=0, padx=20, pady=(0, 20))
        self.appearance_mode_menu.set("Claro")
    
    def create_main_container(self):
        """Contenedor principal"""

        self.main_container = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=util.BACKGROUND
        )

        self.main_container.grid(
            row=0,
            column=1,
            padx=20,
            pady=20,
            sticky="nsew"
        )

        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        

        # =====================================================
        # TARJETA GLOBAL DE ALERTAS
        # =====================================================

        self.alert_frame = ctk.CTkFrame(
            self.main_container,
            fg_color="#ffe5e5",
            corner_radius=10
        )

        self.alert_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0,10)
        )

        self.alert_label = ctk.CTkLabel(
            self.alert_frame,
            text="Sin alertas",
            justify="left",
            wraplength=1000,
            text_color="#c0392b",
            font=util.font_label()
        )

        self.alert_label.pack(
            padx=15,
            pady=10,
            anchor="w"
        )
        self.alert_frame.grid_remove()

        # =====================================================
        # CONTENEDOR DE LOS MÓDULOS
        # =====================================================

        self.module_container = ctk.CTkFrame(
            self.main_container,
            fg_color="transparent"
        )

        self.module_container.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        self.module_container.grid_rowconfigure(0, weight=1)
        self.module_container.grid_columnconfigure(0, weight=1)
    
    def clear_main_container(self):
        
        # 🔥 1. Cerrar gráficos activos
        plt.close('all')

        # 🔥 2. Destruir módulo actual si tiene lógica propia
        if self.current_module and hasattr(self.current_module, "destroy"):
            try:
                self.current_module.destroy()
            except:
                pass

        # 🔥 3. Limpiar widgets visuales
        for widget in self.module_container.winfo_children():
            widget.destroy()

        # 🔥 4. Resetear referencia
        self.current_module = None
        
    def actualizar_alertas(self):
        """Actualiza la tarjeta global de alertas."""

        try:
            
            stock_repo = StockRepository(db)
            stock_insumos = stock_repo.obtener_stock_insumos()

            criticos = []
            bajos = []

            for item in stock_insumos:

                actual = float(item["cantidad_actual"])
                minimo = float(item["stock_minimo"])

                if minimo <= 0:
                    continue

                if actual <= minimo:

                    criticos.append(
                        f"🔴 {item['nombre']}: {actual} {item['unidad']} (mín. {minimo})"
                    )

                elif actual <= minimo * 1.30:

                    bajos.append(
                        f"🟡 {item['nombre']}: {actual} {item['unidad']} (mín. {minimo})"
                    )

            texto = ""

            if criticos:
                texto += "🔴 ALERTA DE INVENTARIO\n\n"
                texto += "\n".join(criticos)

            if bajos:

                if texto:
                    texto += "\n\n"

                texto += "🟡 Próximos al stock mínimo\n\n"
                texto += "\n".join(bajos)

            # ============================================
            # Mostrar u ocultar la tarjeta
            # ============================================

            if texto:

                self.alert_label.configure(text=texto)

                self.alert_frame.grid()

            else:

                self.alert_frame.grid_remove()
        except Exception as e:
            self.alert_label.configure(
                text=f"Error al actualizar alertas: {str(e)}"
            )
            self.alert_frame.grid()
        
    def change_appearance_mode(self, new_mode: str):
        """Cambia el tema de la aplicación"""
        mode_map = {
            "Claro": "light",
            "Oscuro": "dark",
            "Sistema": "system"
        }
        ctk.set_appearance_mode(mode_map.get(new_mode, "light"))
    
    def show_produccion(self):
        """Muestra el módulo de producción"""
        self.clear_main_container()
        self.highlight_button(self.btn_produccion)
        
        # Importar y crear módulo de producción
        try:
            from modules.produccion_tk import ProduccionModule
            self.current_module = ProduccionModule(self.module_container)
        except ImportError as e:
            self.show_module_placeholder("Producción", "produccion_tk.py", str(e))
    
    def show_stock(self):
        """Muestra el módulo de stock"""
        self.clear_main_container()
        self.highlight_button(self.btn_stock)
        
        try:
            from modules.stock_tk import StockModule
            self.current_module = StockModule(self.module_container)
        except ImportError as e:
            self.show_module_placeholder("Stock", "stock_tk.py", str(e))
    
    def show_ventas(self):
        """Muestra el módulo de ventas"""
        self.clear_main_container()
        self.highlight_button(self.btn_ventas)
        
        try:
            from modules.ventas_tk import VentasModule
            self.current_module = VentasModule(self.module_container)
        except ImportError as e:
            self.show_module_placeholder("Ventas", "ventas_tk.py", str(e))
    
    def show_insumos_pagos(self):
        """Muestra el módulo de insumos y pagos"""
        self.clear_main_container()
        self.highlight_button(self.btn_insumos)
        
        try:
            from modules.insumos_pagos_tk import InsumosPagosModule
            self.current_module = InsumosPagosModule(self.module_container)
        except ImportError as e:
            self.show_module_placeholder("Insumos y Pagos", "insumos_pagos_tk.py", str(e))
    
    def show_reportes(self):
        """Muestra el módulo de reportes"""
        self.clear_main_container()
        self.highlight_button(self.btn_reportes)
        
        try:
            from modules.reportes_tk import ReportesModule
            self.current_module = ReportesModule(self.module_container)
        except ImportError as e:
            self.show_module_placeholder("Reportes", "reportes_tk.py", str(e))
            
    def show_explorador_db(self):
        self.clear_main_container()
        self.highlight_button(self.btn_explorador)

        try:
            from modules.explorador_db_tk import ExploradorDBModule
            self.current_module = ExploradorDBModule(self.module_container)
        except ImportError as e:
            self.show_module_placeholder(
                "Explorador DB",
                "explorador_db_tk.py",
                str(e)
            )
    
    def highlight_button(self, button):
        """Resalta el botón activo"""

        for btn in [
            self.btn_produccion,
            self.btn_stock,
            self.btn_ventas,
            self.btn_insumos,
            self.btn_reportes,
            self.btn_explorador
        ]:
            btn.configure(fg_color=util.SECUNDARY)

        button.configure(fg_color=util.PRIMARY)
    
    def show_module_placeholder(self, module_name: str, file_name: str, error: str):
        """Muestra un placeholder cuando el módulo no está disponible"""
        placeholder = ctk.CTkFrame(self.main_container)
        placeholder.pack(fill="both", expand=True, padx=20, pady=20)
        
        label = ctk.CTkLabel(
            placeholder,
            text=f"Módulo '{module_name}' en desarrollo",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        label.pack(pady=(100, 20))
        
        info_label = ctk.CTkLabel(
            placeholder,
            text=f"El archivo 'modules/{file_name}' aún no está creado",
            font=ctk.CTkFont(size=14)
        )
        info_label.pack(pady=10)
        
        if error:
            error_label = ctk.CTkLabel(
                placeholder,
                text=f"Error: {error}",
                font=ctk.CTkFont(size=12),
                text_color="red"
            )
            error_label.pack(pady=10)
    
    def on_closing(self):
        if messagebox.askokcancel("Salir", "¿Desea cerrar la aplicación?"):
            try:
                import matplotlib.pyplot as plt
                plt.close('all')  # 🔥 cerrar todos los gráficos
            except:
                pass

            self.quit()     # 🔥 detiene el mainloop correctamente
            self.destroy()  # 🔥 luego destruye la ventana


def main():
    """Función principal"""
    app = GranjaApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
