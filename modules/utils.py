# pages/utils.py
import os
import base64
import pandas as pd
from PIL import Image
import streamlit as st

# =========================
# 🧠 CACHEO DEL LOGO
# =========================
@st.cache_data
def load_logo(path: str):
    try:
        return Image.open(path)
    except FileNotFoundError:
        st.warning(f"⚠️ No se encontró el logo en {path}")
        return None

def show_logo(width: int = 120):
    """Muestra el logo desde el caché o la sesión."""
    if "logo" not in st.session_state:
        st.session_state.logo = load_logo("images/Logo.png")
    if st.session_state.logo:
        st.image(st.session_state.logo, width=width)


def load_font(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def set_custom_style():
    """Aplica el estilo agropecuario respetando la estructura original del usuario."""

    try:
        exo2_regular = load_font("fonts/Exo2-Regular.ttf")
        exo2_bold = load_font("fonts/Exo2-Bold.ttf")
    except Exception:
        exo2_regular = ""
        exo2_bold = ""

    st.markdown(f"""
        <style>
        @font-face {{
            font-family: 'Exo2';
            src: url(data:font/ttf;base64,{exo2_regular}) format('truetype');
            font-weight: normal;
        }}
        @font-face {{
            font-family: 'Exo2';
            src: url(data:font/ttf;base64,{exo2_bold}) format('truetype');
            font-weight: bold;
        }}

        /* ✅ Fuente global aplicada */
        html, body, [class*="st-"] {{
            font-family: 'Exo2', sans-serif !important;
        }}

        section.main * {{
            font-family: 'Exo2', sans-serif !important;
        }}

        /* 📏 Jerarquía tipográfica - Tonos Tierra/Verde */
        h1 {{ font-size: 3rem !important; letter-spacing: 1px; color: #1b4332 !important; }}
        h2 {{ font-size: 2.4rem !important; letter-spacing: 0.5px; color: #2d6a4f !important; }}
        h3 {{ font-size: 1.8rem !important; color: #40916c !important; }}
        h1, h2, h3 {{ font-weight: bold !important; }}

        /* 🎨 Fondo general (Gradiente Natural) */
        [data-testid="stAppViewContainer"] {{
            background: radial-gradient(circle at top, #f1f8e9 0%, #dcedc8 85%);
        }}

        /* 📊 Tablas */
        table {{
            width: 100%;
            border-collapse: collapse;
            border-radius: 8px;
            overflow: hidden;
            background-color: #ffffff !important;
            box-shadow: 0 0 12px rgba(0, 0, 0, 0.1);
        }}

        thead tr th {{
            background-color: #795548 !important; /* Marrón tierra */
            color: #ffffff !important;
            font-weight: bold !important;
            text-align: center !important;
            padding: 8px 10px !important;
        }}

        tbody tr:nth-child(even) {{ background-color: #f9fbe7 !important; }}

        td, th {{
            border: 0.5px solid #a5d6a7 !important;
            padding: 6px 10px !important;
            color: #000000 !important;
            text-align: center !important;
        }}

        /* ✍️ Texto general */
        p, label, span {{
            color: #1b4332 !important;
        }}

        /* 🧩 Campos de entrada (Inputs/Selects) - Forzado a Blanco/Negro */
        textarea, input, select, 
        div[data-baseweb="input"] input,
        div[data-baseweb="textarea"] textarea,
        div[data-baseweb="select"] > div {{
            background-color: #ffffff !important;
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            border-radius: 6px !important;
            border: 1px solid #2d6a4f !important;
        }}

        /* 🎮 Botones (Estilo Producción) */
        div[data-testid="stButton"] > button {{
            background: linear-gradient(90deg, #52b788 0%, #74c69d 100%);
            color: #000000 !important;
            border: 2px solid #2d6a4f;
            border-radius: 8px;
            font-weight: bold;
            transition: all 0.2s ease-in-out;
        }}

        div[data-testid="stButton"] > button:hover {{
            background: #ffffff !important;
            color: #1b4332 !important;
            border: 2px solid #52b788;
            transform: scale(1.02);
            box-shadow: 0 0 10px rgba(82, 183, 136, 0.5);
        }}

        /* ─────────────────────────────── */
        hr {{ border-color: #2d6a4f44 !important; }}
        
        /* Ajuste para que las pestañas (Tabs) se vean negras */
        button[data-baseweb="tab"] p {{
            color: #000000 !important;
        }}
        </style>
        """, unsafe_allow_html=True)
    
def set_custom_style_2():
    """Aplica el estilo agropecuario respetando la estructura original del usuario."""

    try:
        exo2_regular = load_font("fonts/Exo2-Regular.ttf")
        exo2_bold = load_font("fonts/Exo2-Bold.ttf")
    except Exception:
        exo2_regular = ""
        exo2_bold = ""

    st.markdown(f"""
        <style>
        @font-face {{
            font-family: 'Exo2';
            src: url(data:font/ttf;base64,{exo2_regular}) format('truetype');
            font-weight: normal;
        }}
        @font-face {{
            font-family: 'Exo2';
            src: url(data:font/ttf;base64,{exo2_bold}) format('truetype');
            font-weight: bold;
        }}

        /* ✅ Fuente global aplicada */
        html, body, [class*="st-"] {{
            font-family: 'Exo2', sans-serif !important;
        }}

        section.main * {{
            font-family: 'Exo2', sans-serif !important;
        }}

        /* 📏 Jerarquía tipográfica - Tonos Tierra/Verde */
        h1 {{ font-size: 3rem !important; letter-spacing: 1px; color: #1b4332 !important; }}
        h2 {{ font-size: 2.4rem !important; letter-spacing: 0.5px; color: #2d6a4f !important; }}
        h3 {{ font-size: 1.8rem !important; color: #40916c !important; }}
        h1, h2, h3 {{ font-weight: bold !important; }}

        /* 🎨 Fondo general (Gradiente Natural) */
        [data-testid="stAppViewContainer"] {{
            background: radial-gradient(circle at top, #f1f8e9 0%, #dcedc8 85%);
        }}
        
        /* 📊 Mejora de visibilidad para st.metric */
        [data-testid="stMetricValue"] {{
            color: #1b4332 !important;
            font-weight: bold !important;
        }}

        [data-testid="stMetricLabel"] p {{
            color: #2d6a4f !important;
            font-size: 1.1rem !important;
        }}

        /* 📋 Mejora de visibilidad para st.dataframe */
        div[data-testid="stDataFrame"] td {{
            color: #000000 !important;
        }}

        /* 🌑 Forzar texto negro en los selectores y números de entrada */
        div[data-baseweb="select"] span, 
        input[type="number"] {{
            color: #000000 !important;
        }}

        /* 🎨 Ajuste de contraste para los Tabs activos */
        button[data-baseweb="tab"][aria-selected="true"] p {{
            color: #2d6a4f !important;
            font-weight: bold !important;
        }}

        /* 📊 Tablas */
        table {{
            width: 100%;
            border-collapse: collapse;
            border-radius: 8px;
            overflow: hidden;
            background-color: #ffffff !important;
            box-shadow: 0 0 12px rgba(0, 0, 0, 0.1);
        }}

        thead tr th {{
            background-color: #795548 !important;
            color: #ffffff !important;
            font-weight: bold !important;
            text-align: center !important;
            padding: 8px 10px !important;
        }}

        tbody tr:nth-child(even) {{ background-color: #f9fbe7 !important; }}

        td, th {{
            border: 0.5px solid #a5d6a7 !important;
            padding: 6px 10px !important;
            color: #000000 !important;
            text-align: center !important;
        }}

        /* ✍️ Texto general */
        p, label, span {{
            color: #1b4332 !important;
        }}

        /* 🧩 Campos de entrada */
        textarea, input, select, 
        div[data-baseweb="input"] input,
        div[data-baseweb="textarea"] textarea,
        div[data-baseweb="select"] > div {{
            background-color: #ffffff !important;
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            border-radius: 6px !important;
            border: 1px solid #2d6a4f !important;
        }}

        /* 🎮 Botones */
        div[data-testid="stButton"] > button {{
            background: linear-gradient(90deg, #52b788 0%, #74c69d 100%);
            color: #000000 !important;
            border: 2px solid #2d6a4f;
            border-radius: 8px;
            font-weight: bold;
            transition: all 0.2s ease-in-out;
        }}

        div[data-testid="stButton"] > button:hover {{
            background: #ffffff !important;
            color: #1b4332 !important;
            border: 2px solid #52b788;
            transform: scale(1.02);
            box-shadow: 0 0 10px rgba(82, 183, 136, 0.5);
        }}

        hr {{ border-color: #2d6a4f44 !important; }}
        
        button[data-baseweb="tab"] p {{
            color: #000000 !important;
        }}
        </style>
        """, unsafe_allow_html=True)

def set_harvest_style():
    """Variante Tierra y Cosecha: Tonos cálidos y ocres."""
    try:
        exo2_regular = load_font("fonts/Exo2-Regular.ttf")
        exo2_bold = load_font("fonts/Exo2-Bold.ttf")
    except Exception:
        exo2_regular = ""
        exo2_bold = ""
    st.markdown(f"""
        <style>
         @font-face {{
            font-family: 'Exo2';
            src: url(data:font/ttf;base64,{exo2_regular}) format('truetype');
            font-weight: normal;
        }}
        @font-face {{
            font-family: 'Exo2';
            src: url(data:font/ttf;base64,{exo2_bold}) format('truetype');
            font-weight: bold;
        }}

        /* ✅ Fuente global aplicada */
        html, body, [class*="st-"] {{
            font-family: 'Exo2', sans-serif !important;
        }}

        section.main * {{
            font-family: 'Exo2', sans-serif !important;
        }}

        /* 📏 Jerarquía tipográfica - Tonos Tierra/Verde */
        h1 {{ font-size: 3rem !important; letter-spacing: 1px; color: #1b4332 !important; }}
        h2 {{ font-size: 2.4rem !important; letter-spacing: 0.5px; color: #2d6a4f !important; }}
        h3 {{ font-size: 1.8rem !important; color: #40916c !important; }}
        h1, h2, h3 {{ font-weight: bold !important; }}
        
        /* Fondo: Crema suave a Arena */
        [data-testid="stAppViewContainer"] {{
            background: radial-gradient(circle at top, #fff8e1 0%, #f5e9da 85%);
        }}
        
        /* Títulos: Marrón Chocolate y Terracota */
        h1 {{ color: #5d4037 !important; }}
        h2 {{ color: #795548 !important; }}
        h3 {{ color: #8d6e63 !important; }}

        /* Métricas: Contraste en Marrón Oscuro */
        [data-testid="stMetricValue"] {{ color: #3e2723 !important; }}
        [data-testid="stMetricLabel"] p {{ color: #5d4037 !important; }}

        /* Botones: Degradado Naranja Cosecha */
        div[data-testid="stButton"] > button {{
            background: linear-gradient(90deg, #ffb74d 0%, #ffa726 100%);
            color: #ffffff !important;
            border: 2px solid #e65100;
        }}
        
        /* Tablas: Cabecera Marrón Oscuro */
        thead tr th {{ background-color: #3e2723 !important; }}
        tbody tr:nth-child(even) {{ background-color: #fff3e0 !important; }}
        
        /* Ajuste para que las pestañas (Tabs) se vean negras */
        button[data-baseweb="tab"] p {{
            color: #000000 !important;
        }}
        </style>
        """, unsafe_allow_html=True)
    
    
def set_techno_agro_style():
    """Variante Tecno-Agro: Tonos fríos, limpios y tecnológicos."""
    try:
        exo2_regular = load_font("fonts/Exo2-Regular.ttf")
        exo2_bold = load_font("fonts/Exo2-Bold.ttf")
    except Exception:
        exo2_regular = ""
        exo2_bold = ""
    st.markdown(f"""
        <style>
         @font-face {{
            font-family: 'Exo2';
            src: url(data:font/ttf;base64,{exo2_regular}) format('truetype');
            font-weight: normal;
        }}
        @font-face {{
            font-family: 'Exo2';
            src: url(data:font/ttf;base64,{exo2_bold}) format('truetype');
            font-weight: bold;
        }}

        /* ✅ Fuente global aplicada */
        html, body, [class*="st-"] {{
            font-family: 'Exo2', sans-serif !important;
        }}

        section.main * {{
            font-family: 'Exo2', sans-serif !important;
        }}

        /* 📏 Jerarquía tipográfica - Tonos Tierra/Verde */
        h1 {{ font-size: 3rem !important; letter-spacing: 1px; color: #1b4332 !important; }}
        h2 {{ font-size: 2.4rem !important; letter-spacing: 0.5px; color: #2d6a4f !important; }}
        h3 {{ font-size: 1.8rem !important; color: #40916c !important; }}
        h1, h2, h3 {{ font-weight: bold !important; }}
        
        /* Fondo: Gris azulado muy claro */
        [data-testid="stAppViewContainer"] {{
            background: linear-gradient(180deg, #f0f4f8 0%, #d9e2ec 100%);
        }}
        
        /* Títulos: Azul Petróleo / Teal */
        h1 {{ color: #102a43 !important; }}
        h2 {{ color: #243b53 !important; }}
        h3 {{ color: #334e68 !important; }}

        /* Métricas: Azul profundo */
        [data-testid="stMetricValue"] {{ color: #102a43 !important; }}

        /* Botones: Verde Esmeralda Tecnológico */
        div[data-testid="stButton"] > button {{
            background: #2cb67d;
            color: #ffffff !important;
            border: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        /* Tablas: Minimalistas */
        thead tr th {{ background-color: #486581 !important; }}
        td {{ border: 0.5px solid #bcccdc !important; }}
        
        /* Ajuste para que las pestañas (Tabs) se vean negras */
        button[data-baseweb="tab"] p {{
            color: #000000 !important;
        }}
        </style>
        """, unsafe_allow_html=True)