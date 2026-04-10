# Pío Pío Baena V2 🐔

**Pío Pío Baena V2** es la evolución del sistema de gestión avícola original, migrando de un entorno web (Streamlit) a una aplicación de escritorio nativa construida con **CustomTkinter**. Esta versión prioriza la fluidez de la interfaz, el manejo de datos local y una experiencia de usuario más cercana a un software de gestión profesional.

## 🔄 Evolución V2
- **Motor Gráfico:** Cambio a `customtkinter` para una interfaz moderna y personalizable.
- **Gestión de Módulos:** Arquitectura modular que permite cargar Producción, Stock, Ventas e Insumos de forma independiente.
- **Visualización:** Integración directa de `matplotlib` para reportes dinámicos dentro de la aplicación.
- **Temas:** Soporte nativo para modo claro y oscuro.

## 🛠️ Stack Técnico
- **GUI:** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- **Lenguaje:** Python 3.x
- **Gráficos:** Matplotlib
- **Utilidades:** Configuración modular mediante `utils/config.py`

## 📂 Estructura del Software
- `app.py`: Punto de entrada principal y lógica de navegación.
- `modules/`: Contiene la lógica individual de cada sección (Producción, Stock, etc.).
- `utils/`: Configuraciones de tema (JSON), fuentes y estilos globales.
- `assets/`: Iconos y recursos visuales del sistema.

## 🚀 Instalación
1. Clona este repositorio:
   ```bash
   git clone [https://github.com/tu-usuario/Pio-Pio-Baena-V2.git](https://github.com/tu-usuario/Pio-Pio-Baena-V2.git)