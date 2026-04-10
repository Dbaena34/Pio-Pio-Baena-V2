import customtkinter as ctk
import tkinter as tk
from pathlib import Path


def load_custom_font():
    """"Carga la fuente exo2 desde la carpeta font"""
    try:
        font_path_regular=Path("fonts/Exo2-Regular.ttf")
        font_path_bold=Path("fonts/Exo2-Bold.ttf")
        
        #Registrar fuente en tkinter
        tk.font.Font(file=str(font_path_regular))
        tk.font.Font(file=str(font_path_bold))

        font_family= "Exo 2"
    except:
        font_family="Arial"
    return font_family

#Cargar Fuente
FONT_FAMILY=load_custom_font()

#Definicion global de fuentes
import customtkinter as ctk
import tkinter as tk
from pathlib import Path


def load_custom_font():
    try:
        font_path = Path("fonts/Exo2-Regular.ttf")
        tk.font.Font(file=str(font_path))
        return "Exo 2"
    except:
        return "Arial"


FONT_FAMILY = load_custom_font()


# 🔥 FUNCIONES en vez de variables
def font_title():
    return ctk.CTkFont(family=FONT_FAMILY, size=30, weight="bold")

def font_section():
    return ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold")

def font_label():
    return ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold")

def font_text():
    return ctk.CTkFont(family=FONT_FAMILY, size=14)

def font_input():
    return ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold")
        

PRIMARY="#52b788"
PRIMARY_HOVER="#40916c"

SECUNDARY="#2d6a4f"
DARK_GREEN="#1b4332"

BACKGROUND="#f1f8e9"
CARD="#ffffff"

TEXT_MAIN="#1b4332"
TEXT_LIGHT="#ffffff"
CARD_BG = "#ffffff"
TEXT_MUTED = "#6c757d"

BORDER="#2d6a4f"
SUCCESS="#2ecc71"
WARNING="#f39c12"
DANGER="#e74c3c"




PAGE_CONFIG = {
    'page_title': 'Granja Ponedoras',
    'page_icon': '🐔',
    'layout': 'wide'
}

CATEGORIAS_HUEVOS = ['C', 'B', 'A', 'AA', 'AAA', 'Jumbo']
CATEGORIAS_INSUMOS = ['Alimento', 'Medicamento', 'Mantenimiento', 'Otros']


