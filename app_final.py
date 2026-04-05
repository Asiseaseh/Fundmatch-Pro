"""
FundMatch Pro — Motor de Selección de Fondos
Versión completa con todas las mejoras implementadas:
  1. Informe PDF descargable (HTML print-ready)
  2. Gráfico histórico 2020-2025 en ficha de fondo
  3. Selector de perfil directo (1-10) como alternativa al formulario
  4. Filtro de inversión mínima en el Buscador
  5. Indicador de concentración de cartera
  6. Modo oscuro
"""
import warnings; warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import base64, io

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG PÁGINA
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FundMatch Pro",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# MODO OSCURO / CLARO — session state
# ─────────────────────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# ─────────────────────────────────────────────────────────────────────────────
# CSS DINÁMICO (light / dark)
# ─────────────────────────────────────────────────────────────────────────────
def get_css(dark: bool) -> str:
    if dark:
        c = {
            "bg_app":       "#0d1117",
            "bg_card":      "#161b22",
            "bg_sidebar":   "#010409",
            "text_primary": "#c9d1d9",
            "text_sec":     "#8b949e",
            "text_faint":   "#4a5568",
            "border":       "#21262d",
            "accent":       "#58a6ff",
            "accent_dark":  "#1f6feb",
            "btn_bg":       "#238636",
            "btn_hover":    "#2ea043",
            "hr":           "#21262d",
            "input_bg":     "#161b22",
            "table_head":   "#161b22",
            "table_row":    "#0d1117",
            "table_alt":    "#161b22",
            "metric_bg":    "#161b22",
            "chip_a_bg":    "#0a2a1a", "chip_a_fg": "#56d364",
            "chip_b_bg":    "#0a1a2a", "chip_b_fg": "#58a6ff",
            "chip_c_bg":    "#1a0a2a", "chip_c_fg": "#bc8cff",
            "chip_d_bg":    "#2a1a0a", "chip_d_fg": "#f0883e",
            "chip_e_bg":    "#2a0a0a", "chip_e_fg": "#f85149",
            "chip_f_bg":    "#0a2a0a", "chip_f_fg": "#3fb950",
            "page_title":   "#c9d1d9",
            "sb_text":      "#8b949e",
        }
    else:
        c = {
            "bg_app":       "#f7f9fc",
            "bg_card":      "#ffffff",
            "bg_sidebar":   "#0a1628",
            "text_primary": "#0f1f35",
            "text_sec":     "#6a8aaa",
            "text_faint":   "#a0b8cc",
            "border":       "#e0e8f0",
            "accent":       "#0d2d52",
            "accent_dark":  "#061828",
            "btn_bg":       "#0d2d52",
            "btn_hover":    "#1a4a7a",
            "hr":           "#e8edf2",
            "input_bg":     "#ffffff",
            "table_head":   "#0d2d52",
            "table_row":    "#ffffff",
            "table_alt":    "#f7f9fc",
            "metric_bg":    "#ffffff",
            "chip_a_bg":    "#e8f4ec", "chip_a_fg": "#2d6a4f",
            "chip_b_bg":    "#e8f0f8", "chip_b_fg": "#1a4a7a",
            "chip_c_bg":    "#eceaf8", "chip_c_fg": "#3a3a8a",
            "chip_d_bg":    "#fdf0e8", "chip_d_fg": "#8a4a1a",
            "chip_e_bg":    "#f8ecec", "chip_e_fg": "#8a1a1a",
            "chip_f_bg":    "#edf8e8", "chip_f_fg": "#2a6a1a",
            "page_title":   "#0d2d52",
            "sb_text":      "#5a8ab0",
        }
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  background-color: {c['bg_app']} !important;
  color: {c['text_primary']} !important;
}}
.block-container {{ padding-top:1.1rem; padding-bottom:2rem; background:{c['bg_app']}; }}
/* SIDEBAR */
[data-testid="stSidebar"] {{ background:{c['bg_sidebar']} !important; border-right:1px solid #1e3a5f; }}
[data-testid="stSidebar"] * {{ color:{c['sb_text']} !important; }}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 {{ color:#ffffff !important; }}
.sb-brand {{ text-align:center; padding:18px 0 24px 0; border-bottom:1px solid #1e3a5f; margin-bottom:16px; }}
.sb-brand-name {{ font-size:1.2rem; font-weight:700; color:#ffffff !important; letter-spacing:-0.3px; }}
.sb-brand-sub {{ font-size:.68rem; color:#3a6a9a !important; letter-spacing:1.5px; text-transform:uppercase; margin-top:2px; }}
/* CARDS */
.card {{
  background:{c['metric_bg']}; border:1px solid {c['border']};
  border-radius:8px; padding:18px 20px;
  box-shadow:0 1px 3px rgba(0,0,0,{'0.25' if dark else '0.05'});
}}
.metric-label {{font-size:.7rem;font-weight:600;color:{c['text_sec']};letter-spacing:.8px;text-transform:uppercase;margin-bottom:4px;}}
.metric-value {{font-size:1.6rem;font-weight:700;color:{c['text_primary']};line-height:1;}}
.metric-delta {{font-size:.76rem;color:{c['text_sec']};margin-top:3px;}}
/* PAGE HEADER */
.page-hdr {{ border-bottom:2px solid {c['accent']}; padding-bottom:10px; margin-bottom:22px; }}
.page-title {{ font-size:1.3rem; font-weight:700; color:{c['page_title']}; margin:0; }}
.page-sub {{ font-size:.8rem; color:{c['text_sec']}; margin-top:2px; }}
/* CHIPS */
.chip {{ display:inline-block; padding:2px 9px; border-radius:4px; font-size:.7rem; font-weight:600; letter-spacing:.2px; }}
.chip-A {{ background:{c['chip_a_bg']}; color:{c['chip_a_fg']}; }}
.chip-B {{ background:{c['chip_b_bg']}; color:{c['chip_b_fg']}; }}
.chip-C {{ background:{c['chip_c_bg']}; color:{c['chip_c_fg']}; }}
.chip-D {{ background:{c['chip_d_bg']}; color:{c['chip_d_fg']}; }}
.chip-E {{ background:{c['chip_e_bg']}; color:{c['chip_e_fg']}; }}
.chip-F {{ background:{c['chip_f_bg']}; color:{c['chip_f_fg']}; }}
/* PROFILE BADGE */
.profile-badge {{
  display:inline-flex; align-items:center; background:{c['accent']};
  color:#fff; border-radius:6px; padding:6px 14px;
  font-size:.82rem; font-weight:600; margin-bottom:14px;
}}
/* RESTRICTION TAGS */
.rtag {{
  display:inline-block; background:{c['chip_d_bg']}; color:{c['chip_d_fg']};
  border:1px solid {c['chip_d_fg']}40; border-radius:4px;
  padding:2px 7px; font-size:.7rem; font-weight:500; margin:2px;
}}
/* FUND ROW */
.fund-name {{ font-weight:600; color:{c['text_primary']}; font-size:.88rem; }}
.fund-meta {{ font-size:.73rem; color:{c['text_sec']}; margin-top:1px; }}
/* SCORE BAR */
.sbar-wrap {{ background:{c['border']}; border-radius:3px; height:5px; overflow:hidden; margin-top:3px; }}
.sbar-fill {{ height:100%; border-radius:3px; background:linear-gradient(90deg,{c['accent']},{c['accent_dark']}40 0%,{c['accent']}); }}
/* INFO BOX */
.infobox {{
  background:{c['chip_b_bg']}; border-left:3px solid {c['chip_b_fg']};
  border-radius:0 6px 6px 0; padding:9px 13px;
  font-size:.8rem; color:{c['text_primary']}; margin:10px 0;
}}
/* BUTTONS */
.stButton>button {{
  background:{c['btn_bg']} !important; color:#fff !important;
  border:none !important; border-radius:6px !important;
  font-weight:600 !important; font-size:.86rem !important;
  padding:9px 22px !important; transition:background .15s ease !important;
}}
.stButton>button:hover {{ background:{c['btn_hover']} !important; }}
/* INPUTS */
.stSelectbox>div>div, .stMultiSelect>div>div,
.stTextInput>div>div, .stNumberInput>div>div {{
  border-color:{c['border']} !important; border-radius:6px !important;
  background:{c['input_bg']} !important; color:{c['text_primary']} !important;
}}
/* TABS */
.stTabs [data-baseweb="tab-list"] {{ border-bottom:2px solid {c['border']}; gap:4px; }}
.stTabs [data-baseweb="tab"] {{
  font-size:.83rem; font-weight:500; color:{c['text_sec']};
  border-radius:6px 6px 0 0; padding:8px 16px;
  background:transparent !important;
}}
.stTabs [aria-selected="true"] {{
  color:{c['accent']} !important; font-weight:700 !important;
  border-bottom:2px solid {c['accent']} !important;
}}
/* HR */
hr {{ border-color:{c['hr']} !important; }}
/* DATAFRAME */
.stDataFrame {{ border:1px solid {c['border']}; border-radius:8px; overflow:hidden; }}
/* EXPANDER */
.st-expander {{ background:{c['bg_card']}; border:1px solid {c['border']}; border-radius:8px; }}
/* TOGGLE */
.stToggle label {{ color:{c['sb_text']} !important; }}
/* hide streamlit chrome */
#MainMenu, footer, header {{ visibility:hidden; }}
.stDeployButton {{ display:none; }}
/* SEPARATOR */
.row-sep {{ border:none; border-top:1px solid {c['hr']}; margin:5px 0; }}
/* CONCENTRATION */
.conc-bar-wrap {{
  background:{c['border']}; border-radius:4px; height:10px;
  overflow:hidden; margin-bottom:2px;
}}
.conc-label {{ font-size:.75rem; color:{c['text_sec']}; }}
</style>"""

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────
FAMILIA_CONFIG = {
    "A – Conservadora":      {"label":"A — Conservadora",   "color":"#2d6a4f","bg":"#e8f4ec","chip":"chip-A","risk":"Muy Bajo — Bajo",   "vol":"0%–3%",   "desc":"Monetarios y renta fija de alta calidad. Preservación de capital."},
    "B – Moderada":          {"label":"B — Moderada",       "color":"#1a4a7a","bg":"#e8f0f8","chip":"chip-B","risk":"Bajo — Medio",      "vol":"1%–6%",   "desc":"Renta fija flexible y global. Estabilidad con generación de rentas."},
    "C – Crecimiento":       {"label":"C — Crecimiento",    "color":"#3a3a8a","bg":"#eceaf8","chip":"chip-C","risk":"Medio — Medio-Alto","vol":"6%–14%",  "desc":"Renta variable mercados desarrollados. Crecimiento a largo plazo."},
    "D – Agresiva":          {"label":"D — Agresiva",       "color":"#8a4a1a","bg":"#fdf0e8","chip":"chip-D","risk":"Medio-Alto — Alto", "vol":"8%–20%",  "desc":"High yield, emergentes, RV growth. Máximo potencial con alta volatilidad."},
    "E – Reales/Inflación":  {"label":"E — Activos Reales", "color":"#8a1a1a","bg":"#f8ecec","chip":"chip-E","risk":"Medio",            "vol":"4%–14%",  "desc":"RF ligada a inflación, inmobiliario cotizado, materias primas."},
    "F – ESG":               {"label":"F — ESG",            "color":"#2a6a1a","bg":"#edf8e8","chip":"chip-F","risk":"Medio — Alto",     "vol":"8%–18%",  "desc":"Temática sostenible: transición energética, economía circular."},
}

PERFILES_META = {
    1:  {"nombre":"Conservador Liquidez",   "fam":"A – Conservadora",      "riesgo":"Muy Bajo",   "horizonte":"< 1 año"},
    2:  {"nombre":"Conservador Ingresos",   "fam":"A – Conservadora",      "riesgo":"Bajo",       "horizonte":"1-3 años"},
    3:  {"nombre":"Moderado Equilibrado",   "fam":"B – Moderada",          "riesgo":"Bajo-Medio", "horizonte":"3-5 años"},
    4:  {"nombre":"Crecimiento Moderado",   "fam":"C – Crecimiento",       "riesgo":"Medio",      "horizonte":"3-5 años"},
    5:  {"nombre":"Crecimiento Dinámico",   "fam":"D – Agresiva",          "riesgo":"Medio-Alto", "horizonte":"5-10 años"},
    6:  {"nombre":"Protección Inflación",   "fam":"E – Reales/Inflación",  "riesgo":"Medio",      "horizonte":"3-10 años"},
    7:  {"nombre":"ESG de Convicción",      "fam":"F – ESG",               "riesgo":"Medio-Alto", "horizonte":"5+ años"},
    8:  {"nombre":"Prejubilación Prudente", "fam":"A – Conservadora",      "riesgo":"Bajo",       "horizonte":"3-10 años"},
    9:  {"nombre":"Agresivo / Patrimonial", "fam":"D – Agresiva",          "riesgo":"Alto",       "horizonte":"> 10 años"},
    10: {"nombre":"Conservador Básico",     "fam":"A – Conservadora",      "riesgo":"Muy Bajo",   "horizonte":"< 1 año"},
}

RESTRICCIONES_MAP = {
    "Sin Renta Fija":             ["RF - Corporativa IG","RF - Gubernamental","RF - Flexible/Global","RF - High Yield","RF - Mercados Emergentes","RF - Ligada a Inflación","RF - RMB/China","RF - Subordinada/Financiera"],
    "Sin Renta Variable":         ["RV Europa Blend","RV Eurozona","RV Global Blend","RV USA Blend","RV Global Growth","RV USA Growth","RV Europa Growth","RV Global Small/Mid","RV Europa Small/Mid","RV Mercados Emergentes","RV China","RV India","RV Japón","RV Temático - Tecnología","RV Temático - Salud/Biotech","RV Temático - Sostenibilidad/ESG","RV Temático - Recursos Naturales","RV Sectorial - Financiero"],
    "Sin Derivados/Alternativos": ["Otros"],
    "Sin Materias Primas":        ["Materias Primas - Broad"],
    "Sin High Yield":             ["RF - High Yield"],
    "Sin Mercados Emergentes":    ["RF - Mercados Emergentes","RV Mercados Emergentes","RV China","RV India","RF - RMB/China"],
    "Sin Inmobiliario":           ["Inmobiliario Cotizado"],
    "Sin Deuda Subordinada":      ["RF - Subordinada/Financiera"],
}

RISK_COLORS = {
    "Riesgo Muy Bajo":"#2d6a4f","Riesgo Bajo":"#40916c",
    "Riesgo Medio":"#f4a261","Riesgo Medio-Alto":"#e76f51",
    "Riesgo Alto":"#c0392b","Riesgo Muy Alto":"#7d3c98",
}

ANOS_RET = ["2020","2021","2022","2023","2024","2025"]

# ─────────────────────────────────────────────────────────────────────────────
# CARGA DE DATOS
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def cargar_datos():
    df = pd.read_excel("Fondos_familias_EXTENDIDO.xlsx", sheet_name="Fondos_clasificados")
    for col in ["AUM_EUR","Vol_3Y","MaxDrawdown","Ret_1Y","TER_KIID","Morningstar Rating","MinInv"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["AUM_M"] = df["AUM_EUR"] / 1e6

    # Intentar cargar retornos anuales del Excel original
    try:
        df_orig = pd.read_excel("Base_de_datos_fondos.xlsx", usecols=[
            "ISIN",
            "Annual Ret 2020 EUR","Annual Ret 2021 EUR","Annual Ret 2022 EUR",
            "Annual Ret 2023 EUR","Annual Ret 2024 EUR","Annual Ret 2025 EUR",
        ])
        df_orig = df_orig.rename(columns={
            "Annual Ret 2020 EUR":"Ret_2020","Annual Ret 2021 EUR":"Ret_2021",
            "Annual Ret 2022 EUR":"Ret_2022","Annual Ret 2023 EUR":"Ret_2023",
            "Annual Ret 2024 EUR":"Ret_2024","Annual Ret 2025 EUR":"Ret_2025",
        })
        df = df.merge(df_orig, on="ISIN", how="left")
    except Exception:
        for yr in ANOS_RET:
            df[f"Ret_{yr}"] = np.nan

    return df

@st.cache_data(show_spinner=False)
def stats_familias(df):
    return df.groupby("Familia_Perfil").agg(
        N=("Name","count"),
        Vol_med=("Vol_3Y","median"),
        Ret_med=("Ret_1Y","median"),
        DD_med=("MaxDrawdown","median"),
        TER_med=("TER_KIID","median"),
    ).round(2).reset_index()

with st.spinner("Cargando base de fondos..."):
    fondos = cargar_datos()
    stats_fam = stats_familias(fondos)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def fmt_pct(v, sign=True):
    if pd.isna(v): return "—"
    s = "+" if (sign and v > 0) else ""
    return f"{s}{v:.2f}%"

def fmt_aum(v):
    if pd.isna(v): return "—"
    if v >= 1000: return f"{v/1000:.1f}B €"
    return f"{v:.0f}M €"

def stars(r):
    if pd.isna(r): return "—"
    f = int(r); return "★"*f + "☆"*(5-f)

def chip(fam):
    cfg = FAMILIA_CONFIG.get(fam,{})
    lbl = cfg.get("label", fam)
    cls = cfg.get("chip","chip-A")
    return f'<span class="chip {cls}">{lbl}</span>'

def sbar(score, mx=100):
    p = min(score/mx*100, 100)
    return f'<div class="sbar-wrap"><div class="sbar-fill" style="width:{p:.0f}%"></div></div>'

def page_hdr(title, sub=""):
    st.markdown(f"""
    <div class="page-hdr">
      <div class="page-title">{title}</div>
      {"<div class='page-sub'>"+sub+"</div>" if sub else ""}
    </div>""", unsafe_allow_html=True)

def hr():
    st.markdown('<hr class="row-sep">', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# LÓGICA NEGOCIO
# ─────────────────────────────────────────────────────────────────────────────
def determinar_perfil(riesgo, horizonte, objetivo, esg_oblig):
    if esg_oblig: return 7
    if objetivo == "Protección ante inflación": return 6
    if riesgo == "Muy Bajo":
        return 1 if horizonte in ("< 6 meses","6-12 meses") else 10
    if riesgo == "Bajo":
        if horizonte in ("< 6 meses","6-12 meses","1-3 años"): return 2
        if horizonte in ("3-5 años",): return 3
        return 8
    if riesgo == "Medio-Bajo":
        return 3 if horizonte in ("1-3 años","3-5 años") else 8
    if riesgo == "Medio":
        return 4 if horizonte in ("1-3 años","3-5 años") else 5
    if riesgo == "Medio-Alto":
        return 5 if horizonte in ("3-5 años","5-10 años") else 9
    return 9  # Alto

def recomendar(df, pnum, restricciones, capital, top_n=15):
    ec, sc = f"Elig_Perfil_{pnum}", f"Score_Perfil_{pnum}"
    if ec not in df.columns: return pd.DataFrame()
    mask = df[ec] == 1
    if capital > 0:
        mask &= df["MinInv"].fillna(0) <= capital
    for r in restricciones:
        excl = RESTRICCIONES_MAP.get(r, [])
        if excl:
            mask &= ~df["Familia_L2"].isin(excl)
    res = df[mask].copy()
    if res.empty: return pd.DataFrame()
    res["Score"] = res[sc]
    return res.sort_values("Score", ascending=False).head(top_n).reset_index(drop=True)

# ─────────────────────────────────────────────────────────────────────────────
# GENERACIÓN DE INFORME HTML (descargable, imprimible a PDF)
# ─────────────────────────────────────────────────────────────────────────────
def generar_informe_html(resultado, perfil_num, perfil_meta, restricciones, capital, dark):
    today = date.today().strftime("%d/%m/%Y")
    rows = ""
    for _, r in resultado.head(10).iterrows():
        color = "#2d6a4f" if (not pd.isna(r.get("Ret_1Y")) and r.get("Ret_1Y",0)>=0) else "#c0392b"
        rows += f"""
        <tr>
          <td style='font-weight:600'>{str(r.get('Name',''))[:50]}</td>
          <td>{r.get('ISIN','—')}</td>
          <td>{r.get('Familia_L2','—')}</td>
          <td><span style='color:{color}'>{fmt_pct(r.get('Ret_1Y'))}</span></td>
          <td>{fmt_pct(r.get('Vol_3Y'), sign=False)}</td>
          <td>{fmt_pct(r.get('MaxDrawdown'))}</td>
          <td>{fmt_pct(r.get('TER_KIID'), sign=False)}</td>
          <td style='font-weight:700'>{r.get('Score',0):.1f}</td>
        </tr>"""

    restricciones_txt = ", ".join(restricciones) if restricciones else "Ninguna"
    bg = "#0d1117" if dark else "#ffffff"
    fg = "#c9d1d9" if dark else "#0f1f35"
    acc = "#58a6ff" if dark else "#0d2d52"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>FundMatch Pro — Informe de Recomendación</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  body {{ font-family:'Inter',sans-serif; background:{bg}; color:{fg}; margin:0; padding:0; }}
  @media print {{
    body {{ background:#fff !important; color:#000 !important; }}
    .no-print {{ display:none; }}
    h1,h2,h3 {{ color:#0d2d52 !important; }}
    table th {{ background:#0d2d52 !important; color:#fff !important; }}
  }}
  .container {{ max-width:900px; margin:0 auto; padding:40px 32px; }}
  .header {{ border-bottom:3px solid {acc}; padding-bottom:20px; margin-bottom:28px; }}
  .logo {{ font-size:1.4rem; font-weight:700; color:{acc}; letter-spacing:-0.3px; }}
  .logo-sub {{ font-size:.7rem; color:#8a9ab0; letter-spacing:1.5px; text-transform:uppercase; }}
  .report-title {{ font-size:1.6rem; font-weight:700; margin:16px 0 4px 0; }}
  .report-meta {{ font-size:.82rem; color:#8a9ab0; }}
  .section {{ margin-bottom:28px; }}
  .section-title {{ font-size:1rem; font-weight:700; color:{acc}; border-bottom:1px solid #e8edf2; padding-bottom:8px; margin-bottom:14px; }}
  .profile-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:20px; }}
  .profile-card {{ background:{'#161b22' if dark else '#f7f9fc'}; border:1px solid {'#21262d' if dark else '#e8edf2'}; border-radius:6px; padding:12px 14px; }}
  .profile-card .lbl {{ font-size:.68rem; color:#8a9ab0; text-transform:uppercase; letter-spacing:.8px; margin-bottom:4px; }}
  .profile-card .val {{ font-size:.95rem; font-weight:600; color:{fg}; }}
  table {{ width:100%; border-collapse:collapse; font-size:.8rem; }}
  th {{ background:{acc}; color:#ffffff; padding:9px 10px; text-align:left; font-weight:600; font-size:.75rem; }}
  td {{ padding:8px 10px; border-bottom:1px solid {'#21262d' if dark else '#edf1f5'}; }}
  tr:nth-child(even) td {{ background:{'#161b22' if dark else '#f7f9fc'}; }}
  .badge {{ display:inline-block; background:{'#1f6feb' if dark else '#e8f0f8'}; color:{'#58a6ff' if dark else '#1a4a7a'}; border-radius:4px; padding:2px 8px; font-size:.72rem; font-weight:600; }}
  .footer {{ margin-top:40px; padding-top:16px; border-top:1px solid {'#21262d' if dark else '#e8edf2'}; font-size:.72rem; color:#8a9ab0; text-align:center; }}
  .print-btn {{ background:{acc}; color:#fff; border:none; border-radius:6px; padding:10px 20px; font-size:.88rem; font-weight:600; cursor:pointer; margin-bottom:20px; }}
</style>
</head>
<body>
<div class="container">
  <div class="no-print">
    <button class="print-btn" onclick="window.print()">Imprimir / Guardar como PDF</button>
  </div>
  <div class="header">
    <div class="logo">FundMatch Pro</div>
    <div class="logo-sub">Motor de Selección de Fondos</div>
    <div class="report-title">Informe de Recomendación de Fondos</div>
    <div class="report-meta">Generado el {today} &nbsp;·&nbsp; Base Morningstar EAA (mar. 2026)</div>
  </div>

  <div class="section">
    <div class="section-title">Perfil del Inversor</div>
    <div class="profile-grid">
      <div class="profile-card"><div class="lbl">Perfil asignado</div><div class="val">{perfil_meta.get('nombre','')}</div></div>
      <div class="profile-card"><div class="lbl">Tolerancia al riesgo</div><div class="val">{perfil_meta.get('riesgo','')}</div></div>
      <div class="profile-card"><div class="lbl">Horizonte</div><div class="val">{perfil_meta.get('horizonte','')}</div></div>
      <div class="profile-card"><div class="lbl">Capital disponible</div><div class="val">{capital:,.0f} €</div></div>
      <div class="profile-card"><div class="lbl">Familia de referencia</div><div class="val">{perfil_meta.get('fam','')}</div></div>
      <div class="profile-card"><div class="lbl">Restricciones</div><div class="val" style='font-size:.82rem'>{restricciones_txt}</div></div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">Fondos Recomendados — Top 10</div>
    <table>
      <thead>
        <tr>
          <th>Fondo</th><th>ISIN</th><th>Sub-familia</th>
          <th>Rent. 1A</th><th>Vol. 3A</th><th>Max DD</th>
          <th>TER</th><th>Score</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </div>

  <div class="footer">
    FundMatch Pro &nbsp;·&nbsp; Trabajo de Fin de Grado — ADE + Business Analytics &nbsp;·&nbsp;
    Francisco de Asís Herrero Granados, 2026<br>
    Este informe tiene carácter académico y no constituye asesoramiento de inversión regulado (MiFID II).
  </div>
</div>
</body>
</html>"""

def html_to_download(html_str, filename="informe_fundmatch.html"):
    b64 = base64.b64encode(html_str.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{filename}" style="text-decoration:none;"><button style="background:#0d2d52;color:#fff;border:none;border-radius:6px;padding:9px 18px;font-weight:600;font-size:.84rem;cursor:pointer;font-family:Inter,sans-serif;">Descargar informe (HTML → imprime a PDF)</button></a>'

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
# Inyectar CSS según modo
st.markdown(get_css(st.session_state.dark_mode), unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
      <div class="sb-brand-name">FundMatch Pro</div>
      <div class="sb-brand-sub">Motor de Selección de Fondos</div>
    </div>""", unsafe_allow_html=True)

    pagina = st.radio("", [
        "Resumen del Universo",
        "Recomendador",
        "Buscador de Fondos",
        "Familias de Inversión",
        "Comparador",
    ], label_visibility="collapsed")

    st.markdown("---")

    dark_toggle = st.toggle("Modo oscuro", value=st.session_state.dark_mode)
    if dark_toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_toggle
        st.rerun()

    st.markdown("---")
    st.markdown(f"""
    <div style="font-size:.69rem;color:#3a6a9a;padding:0 4px;line-height:1.6;">
      Base Morningstar EAA · {len(fondos):,} fondos<br>
      10 perfiles MiFID II · Actualizado mar. 2026
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# COLORES DEL MODO ACTUAL PARA PLOTLY
# ─────────────────────────────────────────────────────────────────────────────
dark = st.session_state.dark_mode
plt_bg    = "#0d1117" if dark else "#ffffff"
plt_paper = "#0d1117" if dark else "#ffffff"
plt_grid  = "#21262d" if dark else "#edf1f5"
plt_text  = "#c9d1d9" if dark else "#0f1f35"
FAM_COLORS = {k: FAMILIA_CONFIG[k]["color"] for k in FAMILIA_CONFIG}

# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA 1 — RESUMEN DEL UNIVERSO
# ─────────────────────────────────────────────────────────────────────────────
if pagina == "Resumen del Universo":
    page_hdr("Universo de Fondos", "Base Morningstar EAA — 7.004 fondos clasificados en 6 familias de inversión")

    cols = st.columns(5)
    kpis = [
        ("Fondos totales", f"{len(fondos):,}", "Base Morningstar EAA"),
        ("Familias", "6", "A, B, C, D, E, F"),
        ("Sub-familias", str(fondos["Familia_L2"].nunique()), "por tipo de activo"),
        ("Fondos ESG", str(int((fondos["ESG_Flag"]==1).sum())), "con sello sostenible"),
        ("Mediana TER", f"{fondos['TER_KIID'].median():.2f}%", "coste anual universo"),
    ]
    for col,(lbl,val,sub) in zip(cols, kpis):
        col.markdown(f"""<div class="card">
          <div class="metric-label">{lbl}</div>
          <div class="metric-value">{val}</div>
          <div class="metric-delta">{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([1.15, 1])

    with c1:
        st.markdown("**Distribución por familia de inversión**")
        dist = fondos["Familia_Perfil"].value_counts().reset_index()
        dist.columns = ["Familia","Fondos"]
        dist = dist[dist["Familia"] != "Otros"]
        fig = px.bar(dist, x="Fondos", y="Familia", orientation="h",
                     color="Familia", color_discrete_map=FAM_COLORS, text="Fondos")
        fig.update_layout(showlegend=False, height=280, font=dict(family="Inter",size=11),
                          plot_bgcolor=plt_bg, paper_bgcolor=plt_paper,
                          margin=dict(l=0,r=20,t=6,b=6),
                          xaxis=dict(showgrid=False,zeroline=False,visible=False,color=plt_text),
                          yaxis=dict(title="",color=plt_text))
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("**Mapa riesgo / rentabilidad por familia**")
        sp = stats_fam[stats_fam["Familia_Perfil"] != "Otros"].copy()
        fig2 = px.scatter(sp, x="Vol_med", y="Ret_med", size="N", color="Familia_Perfil",
                          color_discrete_map=FAM_COLORS, text="Familia_Perfil",
                          hover_data={"N":True,"TER_med":True},
                          labels={"Vol_med":"Volatilidad mediana 3A (%)","Ret_med":"Rentabilidad mediana 1A (%)"})
        fig2.update_traces(textposition="top center", textfont_size=9, marker_line_width=0)
        fig2.update_layout(showlegend=False, height=280, font=dict(family="Inter",size=11),
                           plot_bgcolor=plt_bg, paper_bgcolor=plt_paper,
                           margin=dict(l=0,r=10,t=6,b=6),
                           xaxis=dict(gridcolor=plt_grid,zeroline=False,color=plt_text),
                           yaxis=dict(gridcolor=plt_grid,zeroline=False,color=plt_text))
        fig2.add_hline(y=0, line_dash="dash", line_color=plt_grid, line_width=1)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown("**Características por familia**")
    hdr = st.columns([1.5, 0.6, 0.7, 0.7, 0.8, 0.6, 2.4])
    for col, txt in zip(hdr, ["Familia","Fondos","Vol. 3A","Rent. 1A","Max DD","TER","Descripción"]):
        col.markdown(f"<span style='font-size:.69rem;font-weight:600;color:{'#8b949e' if dark else '#8a9ab0'};text-transform:uppercase;letter-spacing:.7px;'>{txt}</span>", unsafe_allow_html=True)
    hr()

    for _, row in stats_fam[stats_fam["Familia_Perfil"] != "Otros"].iterrows():
        fam = row["Familia_Perfil"]
        cfg = FAMILIA_CONFIG.get(fam, {})
        c0,c1,c2,c3,c4,c5,c6 = st.columns([1.5,0.6,0.7,0.7,0.8,0.6,2.4])
        c0.markdown(chip(fam), unsafe_allow_html=True)
        c1.markdown(f"<span style='font-size:.82rem;font-weight:600'>{int(row['N'])}</span>", unsafe_allow_html=True)
        c2.markdown(f"<span style='font-size:.82rem'>{row['Vol_med']:.1f}%</span>", unsafe_allow_html=True)
        col_ret = "#3fb950" if (row['Ret_med']>=0) else "#f85149"
        c3.markdown(f"<span style='font-size:.82rem;color:{col_ret}'>{fmt_pct(row['Ret_med'])}</span>", unsafe_allow_html=True)
        c4.markdown(f"<span style='font-size:.82rem;color:#f85149'>{row['DD_med']:.1f}%</span>", unsafe_allow_html=True)
        c5.markdown(f"<span style='font-size:.82rem'>{row['TER_med']:.2f}%</span>", unsafe_allow_html=True)
        c6.markdown(f"<span style='font-size:.76rem;color:{'#8b949e' if dark else '#5a7a9a'}'>{cfg.get('desc','')}</span>", unsafe_allow_html=True)
        hr()

# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA 2 — RECOMENDADOR
# ─────────────────────────────────────────────────────────────────────────────
elif pagina == "Recomendador":
    page_hdr("Recomendador de Fondos", "Selección personalizada según el perfil del inversor")

    # ── FORMULARIO ───────────────────────────────────────────────────────────
    with st.expander("Configurar perfil del inversor", expanded=True):

        # SELECTOR DIRECTO vs FORMULARIO
        modo_sel = st.radio("Modo de selección", ["Configurar parámetros","Seleccionar perfil directamente (1-10)"], horizontal=True)

        if modo_sel == "Seleccionar perfil directamente (1-10)":
            perfil_labels = {k: f"Perfil {k} — {v['nombre']} ({v['riesgo']}, {v['horizonte']})" for k,v in PERFILES_META.items()}
            perfil_sel = st.selectbox("Perfil", list(perfil_labels.keys()),
                                      format_func=lambda x: perfil_labels[x],
                                      label_visibility="collapsed")
            perfil_num = perfil_sel
            perfil_meta = PERFILES_META[perfil_num]
            # Restricciones y capital siguen siendo configurables
            c1, c2 = st.columns(2)
            with c1:
                capital = st.number_input("Capital disponible (€)", min_value=0, value=50000, step=5000, label_visibility="collapsed")
            with c2:
                restricciones_sel = st.multiselect("Restricciones de inversión", list(RESTRICCIONES_MAP.keys()),
                                                   placeholder="Ninguna restricción", label_visibility="collapsed")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**Tolerancia al riesgo**")
                riesgo = st.select_slider("riesgo", options=["Muy Bajo","Bajo","Medio-Bajo","Medio","Medio-Alto","Alto"], value="Medio", label_visibility="collapsed")
                st.markdown("**Horizonte de inversión**")
                horizonte = st.selectbox("horizonte", ["< 6 meses","6-12 meses","1-3 años","3-5 años","5-10 años","> 10 años"], index=3, label_visibility="collapsed")
            with c2:
                st.markdown("**Objetivo principal**")
                objetivo = st.selectbox("objetivo", ["Preservar capital","Generar rentas periódicas","Crecimiento equilibrado","Crecimiento a largo plazo","Crecimiento agresivo","Protección ante inflación"], index=2, label_visibility="collapsed")
                st.markdown("**Capital disponible (€)**")
                capital = st.number_input("capital", min_value=0, value=50000, step=5000, label_visibility="collapsed")
            with c3:
                st.markdown("**Sostenibilidad (ESG)**")
                esg_pref = st.selectbox("esg", ["Indiferente","Preferible","Obligatorio"], label_visibility="collapsed")
                st.markdown("**Restricciones** (selección múltiple)")
                restricciones_sel = st.multiselect("restricciones", list(RESTRICCIONES_MAP.keys()),
                                                   placeholder="Ninguna restricción", label_visibility="collapsed")
            esg_oblig = (esg_pref == "Obligatorio")
            perfil_num = determinar_perfil(riesgo, horizonte, objetivo, esg_oblig)
            perfil_meta = PERFILES_META[perfil_num]

        top_n = st.slider("Resultados a mostrar", 5, 30, 15)
        buscar = st.button("Obtener recomendaciones")

    # ── RESULTADOS ────────────────────────────────────────────────────────────
    if buscar:
        sc_col = f"Score_Perfil_{perfil_num}"
        resultado = recomendar(fondos, perfil_num, restricciones_sel, capital, top_n)

        # Badge del perfil
        st.markdown(f"""<div class="profile-badge">
          Perfil {perfil_num}: {perfil_meta.get('nombre','')} &nbsp;·&nbsp;
          {perfil_meta.get('riesgo','')} &nbsp;·&nbsp; {perfil_meta.get('horizonte','')}
        </div>""", unsafe_allow_html=True)

        if restricciones_sel:
            tags = "".join([f'<span class="rtag">{r}</span>' for r in restricciones_sel])
            st.markdown(f"Restricciones activas: {tags}", unsafe_allow_html=True)

        if resultado.empty:
            st.markdown('<div class="infobox">No se encontraron fondos con los criterios seleccionados. Prueba a relajar alguna restricción o aumentar el capital disponible.</div>', unsafe_allow_html=True)
        else:
            tabs = st.tabs(["Lista de fondos", "Gráfico riesgo/rentabilidad", "Concentración por familia"])

            # ── TAB 1: LISTA ──────────────────────────────────────────────────
            with tabs[0]:
                st.markdown(f"<span style='font-size:.8rem;color:{'#8b949e' if dark else '#6a8aaa'}'>{len(resultado)} fondos seleccionados para el perfil <b>{perfil_meta.get('nombre','')}</b></span>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

                # Cabecera
                hdr_cols = st.columns([3.2, 1.5, 0.85, 0.85, 0.9, 0.75, 1.1])
                for col, txt in zip(hdr_cols, ["Fondo","Sub-familia","Rent. 1A","Vol. 3A","Max DD","TER","Score"]):
                    col.markdown(f"<span style='font-size:.69rem;font-weight:600;color:{'#8b949e' if dark else '#8a9ab0'};text-transform:uppercase;letter-spacing:.7px;'>{txt}</span>", unsafe_allow_html=True)
                hr()

                for _, r in resultado.iterrows():
                    cc = st.columns([3.2, 1.5, 0.85, 0.85, 0.9, 0.75, 1.1])
                    with cc[0]:
                        st.markdown(f"""<div class="fund-name">{str(r.get('Name',''))[:55]}</div>
                        <div class="fund-meta">{r.get('ISIN','')} · {r.get('Base Currency','')}</div>""", unsafe_allow_html=True)
                    with cc[1]:
                        st.markdown(f"""{chip(r.get('Familia_Perfil',''))}<br>
                        <span style='font-size:.7rem;color:{'#8b949e' if dark else '#8a9ab0'}'>{r.get('Familia_L2','')}</span>""", unsafe_allow_html=True)

                    ret = r.get("Ret_1Y", np.nan)
                    ret_col = ("#3fb950" if dark else "#2d6a4f") if (not pd.isna(ret) and ret>=0) else "#f85149"
                    cc[2].markdown(f"<span style='font-size:.85rem;font-weight:600;color:{ret_col}'>{fmt_pct(ret)}</span>", unsafe_allow_html=True)
                    cc[3].markdown(f"<span style='font-size:.85rem'>{fmt_pct(r.get('Vol_3Y'), sign=False)}</span>", unsafe_allow_html=True)
                    cc[4].markdown(f"<span style='font-size:.85rem;color:#f85149'>{fmt_pct(r.get('MaxDrawdown'))}</span>", unsafe_allow_html=True)
                    cc[5].markdown(f"<span style='font-size:.85rem'>{fmt_pct(r.get('TER_KIID'), sign=False)}</span>", unsafe_allow_html=True)
                    with cc[6]:
                        sv = r.get("Score", 0)
                        st.markdown(f"<span style='font-size:.9rem;font-weight:700'>{sv:.1f}</span>{sbar(sv)}", unsafe_allow_html=True)

                    hr()

                # Botón de descarga informe
                st.markdown("<br>", unsafe_allow_html=True)
                html_informe = generar_informe_html(resultado, perfil_num, perfil_meta, restricciones_sel, capital, dark)
                st.markdown(html_to_download(html_informe), unsafe_allow_html=True)
                st.markdown('<span style="font-size:.72rem;color:#8a9ab0;margin-left:8px;">Abre el archivo en el navegador y usa Ctrl+P → Guardar como PDF</span>', unsafe_allow_html=True)

            # ── TAB 2: SCATTER ────────────────────────────────────────────────
            with tabs[1]:
                plot_df = resultado.dropna(subset=["Vol_3Y","Ret_1Y"])
                if not plot_df.empty:
                    fig_sc = px.scatter(plot_df, x="Vol_3Y", y="Ret_1Y",
                                        color="Familia_Perfil", size="Score",
                                        hover_name="Name",
                                        hover_data={"TER_KIID":":.2f","Score":":.1f","Familia_L2":True},
                                        color_discrete_map=FAM_COLORS,
                                        labels={"Vol_3Y":"Volatilidad 3A (%)","Ret_1Y":"Rentabilidad 1A (%)"})
                    fig_sc.update_layout(height=420, showlegend=True,
                                         plot_bgcolor=plt_bg, paper_bgcolor=plt_paper,
                                         font=dict(family="Inter",size=11,color=plt_text),
                                         margin=dict(l=0,r=0,t=10,b=10),
                                         xaxis=dict(gridcolor=plt_grid,zeroline=False),
                                         yaxis=dict(gridcolor=plt_grid,zeroline=False),
                                         legend=dict(orientation="h",yanchor="bottom",y=1.02))
                    fig_sc.add_hline(y=0, line_dash="dash", line_color=plt_grid, line_width=1)
                    st.plotly_chart(fig_sc, use_container_width=True)

            # ── TAB 3: CONCENTRACIÓN ──────────────────────────────────────────
            with tabs[2]:
                st.markdown("**Distribución de los fondos recomendados por familia**")
                st.markdown('<div class="infobox">Verifica que las recomendaciones no están demasiado concentradas en una sola categoría. Una buena selección suele tener fondos en 2-3 familias complementarias.</div>', unsafe_allow_html=True)

                conc = resultado.groupby("Familia_Perfil").agg(N=("Name","count"), Score_med=("Score","mean")).reset_index()
                conc["Pct"] = conc["N"] / conc["N"].sum() * 100

                # Barras horizontales de concentración
                for _, rr in conc.sort_values("N", ascending=False).iterrows():
                    fam = rr["Familia_Perfil"]
                    cfg = FAMILIA_CONFIG.get(fam, {})
                    col_c = cfg.get("color","#333")
                    st.markdown(f"""
                    <div style="margin-bottom:12px">
                      {chip(fam)}
                      <span style="font-size:.78rem;color:{'#8b949e' if dark else '#6a8aaa'};margin-left:8px;">{int(rr['N'])} fondos ({rr['Pct']:.0f}%)</span>
                      <div class="conc-bar-wrap" style="margin-top:4px">
                        <div style="height:10px;border-radius:4px;background:{col_c};width:{rr['Pct']:.0f}%"></div>
                      </div>
                    </div>""", unsafe_allow_html=True)

                # Pie chart
                col_pie, col_sub = st.columns([1, 1.2])
                with col_pie:
                    fig_pie = px.pie(conc, names="Familia_Perfil", values="N",
                                     color="Familia_Perfil", color_discrete_map=FAM_COLORS, hole=0.42)
                    fig_pie.update_layout(height=300, showlegend=False,
                                          plot_bgcolor=plt_bg, paper_bgcolor=plt_paper,
                                          margin=dict(l=0,r=0,t=10,b=10),
                                          font=dict(family="Inter",size=11,color=plt_text))
                    fig_pie.update_traces(textinfo="percent", textfont_size=11)
                    st.plotly_chart(fig_pie, use_container_width=True)

                with col_sub:
                    st.markdown("**Sub-familias representadas**")
                    sub_conc = resultado.groupby("Familia_L2")["Name"].count().reset_index()
                    sub_conc.columns = ["Sub-familia","Fondos"]
                    sub_conc = sub_conc.sort_values("Fondos", ascending=False)
                    st.dataframe(sub_conc, use_container_width=True, hide_index=True, height=260)

# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA 3 — BUSCADOR
# ─────────────────────────────────────────────────────────────────────────────
elif pagina == "Buscador de Fondos":
    page_hdr("Buscador de Fondos", f"Explora los {len(fondos):,} fondos de la base de datos")

    with st.container():
        f1, f2, f3, f4, f5 = st.columns([2.2, 1.2, 1.2, 1, 0.8])
        with f1:
            texto = st.text_input("Nombre / ISIN", placeholder="Buscar fondo...", label_visibility="collapsed")
        with f2:
            familia_f = st.multiselect("Familia", list(FAMILIA_CONFIG.keys()), placeholder="Todas las familias", label_visibility="collapsed")
        with f3:
            restricciones_b = st.multiselect("Excluir activos", list(RESTRICCIONES_MAP.keys()), placeholder="Sin exclusiones", label_visibility="collapsed")
        with f4:
            riesgo_f = st.selectbox("Riesgo", ["Todos","Riesgo Muy Bajo","Riesgo Bajo","Riesgo Medio","Riesgo Medio-Alto","Riesgo Alto","Riesgo Muy Alto"], label_visibility="collapsed")
        with f5:
            esg_f = st.checkbox("Solo ESG")

    # Filtro de inversión mínima — prominente e independiente
    st.markdown("**Capital disponible del inversor (filtro de inversión mínima)**")
    col_inv1, col_inv2 = st.columns([3, 1])
    with col_inv1:
        cap_buscador = st.slider(
            "inv_min_buscador",
            min_value=0, max_value=2_000_000,
            value=50_000, step=5_000, format="%d €",
            label_visibility="collapsed",
        )
    with col_inv2:
        st.markdown(f"<div style='padding-top:8px;font-size:.9rem;font-weight:600'>{cap_buscador:,.0f} €</div>", unsafe_allow_html=True)

    # Aplicar filtros
    mask = pd.Series([True]*len(fondos), index=fondos.index)
    if texto:
        mask &= fondos["Name"].str.contains(texto, case=False, na=False) | fondos["ISIN"].str.contains(texto, case=False, na=False)
    if familia_f:
        mask &= fondos["Familia_Perfil"].isin(familia_f)
    if riesgo_f != "Todos":
        mask &= fondos["Riesgo_Banda"] == riesgo_f
    if esg_f:
        mask &= fondos["ESG_Flag"] == 1
    if cap_buscador > 0:
        mask &= fondos["MinInv"].fillna(0) <= cap_buscador
    for r in restricciones_b:
        excl = RESTRICCIONES_MAP.get(r, [])
        if excl:
            mask &= ~fondos["Familia_L2"].isin(excl)

    sub = fondos[mask].copy()
    st.markdown(f"<span style='font-size:.8rem;color:{'#8b949e' if dark else '#6a8aaa'}'>{len(sub):,} fondos encontrados · mostrando hasta 200</span>", unsafe_allow_html=True)

    show_cols = ["Name","ISIN","Familia_Perfil","Familia_L2","Riesgo_Banda","Morningstar Rating","Ret_1Y","Vol_3Y","MaxDrawdown","TER_KIID","MinInv","AUM_M"]
    display = sub[[c for c in show_cols if c in sub.columns]].head(200).copy()
    display.columns = ["Fondo","ISIN","Familia","Sub-familia","Riesgo","Rating","Rent.1A%","Vol.3A%","MaxDD%","TER%","Min.Inv€","AUM(M€)"]

    st.dataframe(
        display.style.format({
            "Rent.1A%": lambda v: fmt_pct(v) if not pd.isna(v) else "—",
            "Vol.3A%":  lambda v: f"{v:.2f}%" if not pd.isna(v) else "—",
            "MaxDD%":   lambda v: f"{v:.2f}%" if not pd.isna(v) else "—",
            "TER%":     lambda v: f"{v:.2f}%" if not pd.isna(v) else "—",
            "Min.Inv€": lambda v: f"{v:,.0f} €" if not pd.isna(v) else "—",
            "AUM(M€)":  lambda v: fmt_aum(v) if not pd.isna(v) else "—",
            "Rating":   lambda v: stars(v) if not pd.isna(v) else "—",
        }),
        use_container_width=True, height=480,
    )

    # Ficha detallada con gráfico histórico
    st.markdown("---")
    st.markdown("**Ficha de fondo**")
    nombres = sub["Name"].dropna().head(200).tolist()
    if nombres:
        sel = st.selectbox("Selecciona un fondo para ver la ficha", nombres, label_visibility="collapsed")
        det = fondos[fondos["Name"] == sel]
        if not det.empty:
            det = det.iloc[0]
            c1,c2,c3,c4 = st.columns(4)
            for col,(lbl,val,color) in zip([c1,c2,c3,c4],[
                ("Volatilidad 3A",  fmt_pct(det.get("Vol_3Y"), sign=False), plt_text),
                ("Rentabilidad 1A", fmt_pct(det.get("Ret_1Y")),
                    ("#3fb950" if dark else "#2d6a4f") if (not pd.isna(det.get("Ret_1Y",np.nan)) and det.get("Ret_1Y",0)>=0) else "#f85149"),
                ("Max Drawdown",    fmt_pct(det.get("MaxDrawdown")), "#f85149"),
                ("TER",             fmt_pct(det.get("TER_KIID"), sign=False), plt_text),
            ]):
                col.markdown(f"""<div class="card">
                  <div class="metric-label">{lbl}</div>
                  <div class="metric-value" style="color:{color}">{val}</div>
                </div>""", unsafe_allow_html=True)

            st.markdown(f"""<br><div style="font-size:.8rem;color:{'#8b949e' if dark else '#6a8aaa'};line-height:1.8">
              <b>ISIN:</b> {det.get('ISIN','—')} &nbsp;·&nbsp;
              <b>Divisa:</b> {det.get('Base Currency','—')} &nbsp;·&nbsp;
              <b>Familia:</b> {det.get('Familia_Perfil','—')} &nbsp;·&nbsp;
              <b>Sub-familia:</b> {det.get('Familia_L2','—')}<br>
              <b>Riesgo:</b> {det.get('Riesgo_Banda','—')} &nbsp;·&nbsp;
              <b>Rating:</b> {stars(det.get('Morningstar Rating'))} &nbsp;·&nbsp;
              <b>AUM:</b> {fmt_aum(det.get('AUM_M'))} &nbsp;·&nbsp;
              <b>Min. inversión:</b> {f"{det.get('MinInv',0):,.0f} €" if not pd.isna(det.get('MinInv',np.nan)) else '—'} &nbsp;·&nbsp;
              <b>ESG:</b> {'Sí' if det.get('ESG_Flag')==1 else 'No'}
            </div>""", unsafe_allow_html=True)

            # Gráfico histórico rentabilidades anuales 2020-2025
            hist_data = []
            for yr in ANOS_RET:
                col_yr = f"Ret_{yr}"
                if col_yr in fondos.columns:
                    v = det.get(col_yr, np.nan)
                    if not pd.isna(v):
                        hist_data.append({"Año": yr, "Rentabilidad (%)": round(float(v), 2)})

            if hist_data:
                st.markdown("<br>**Rentabilidades anuales históricas**")
                hist_df = pd.DataFrame(hist_data)
                colors_bar = ["#3fb950" if v >= 0 else "#f85149" for v in hist_df["Rentabilidad (%)"]]
                fig_hist = go.Figure(go.Bar(
                    x=hist_df["Año"], y=hist_df["Rentabilidad (%)"],
                    marker_color=colors_bar,
                    text=[f"{v:+.1f}%" for v in hist_df["Rentabilidad (%)"]],
                    textposition="outside",
                ))
                fig_hist.add_hline(y=0, line_color=plt_grid, line_width=1)
                fig_hist.update_layout(
                    height=280, showlegend=False,
                    plot_bgcolor=plt_bg, paper_bgcolor=plt_paper,
                    font=dict(family="Inter", size=11, color=plt_text),
                    margin=dict(l=0, r=0, t=10, b=10),
                    xaxis=dict(gridcolor=plt_grid, zeroline=False),
                    yaxis=dict(gridcolor=plt_grid, zeroline=False, ticksuffix="%"),
                    bargap=0.3,
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.markdown('<div class="infobox">No hay datos de rentabilidades anuales disponibles para este fondo. Coloca el archivo "Base_de_datos_fondos.xlsx" junto a la aplicación para activar el gráfico histórico.</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA 4 — FAMILIAS DE INVERSIÓN
# ─────────────────────────────────────────────────────────────────────────────
elif pagina == "Familias de Inversión":
    page_hdr("Familias de Inversión", "Análisis de las 6 familias y sus sub-categorías")

    fam_sel = st.selectbox("", list(FAMILIA_CONFIG.keys()), label_visibility="collapsed",
                           format_func=lambda x: FAMILIA_CONFIG[x]["label"])

    cfg = FAMILIA_CONFIG[fam_sel]
    sub_fam = fondos[fondos["Familia_Perfil"] == fam_sel].copy()

    # Info banner de la familia
    rs = stats_fam[stats_fam["Familia_Perfil"] == fam_sel]
    n_fam = int(rs["N"].values[0]) if not rs.empty else 0
    st.markdown(f"""
    <div style="background:{'#161b22' if dark else cfg['bg']};border-left:4px solid {cfg['color']};
                border-radius:0 8px 8px 0;padding:16px 20px;margin-bottom:18px">
      <span style="font-size:1rem;font-weight:700;color:{cfg['color']}">{cfg['label']}</span>
      <span style="font-size:.75rem;color:{'#8b949e' if dark else '#5a7a9a'};margin-left:12px">{n_fam} fondos &nbsp;·&nbsp; Riesgo: {cfg['risk']} &nbsp;·&nbsp; Vol. típica: {cfg['vol']}</span>
      <div style="font-size:.8rem;color:{'#c9d1d9' if dark else '#3a4a5a'};margin-top:6px;">{cfg['desc']}</div>
    </div>""", unsafe_allow_html=True)

    tab_sf, tab_vol, tab_hist, tab_top = st.tabs(["Sub-familias","Distribución de volatilidad","Rentabilidades históricas","Top fondos"])

    with tab_sf:
        sub_dist = sub_fam.groupby("Familia_L2").agg(
            N=("Name","count"),
            Vol_med=("Vol_3Y","median"),
            Ret_med=("Ret_1Y","median"),
            TER_med=("TER_KIID","median"),
            DD_med=("MaxDrawdown","median"),
        ).round(2).reset_index().sort_values("N", ascending=False)
        st.dataframe(sub_dist.rename(columns={"Familia_L2":"Sub-familia","N":"Fondos",
                                               "Vol_med":"Vol.3A%","Ret_med":"Rent.1A%",
                                               "TER_med":"TER%","DD_med":"Max DD%"}),
                     use_container_width=True, hide_index=True)

    with tab_vol:
        clean = sub_fam.dropna(subset=["Vol_3Y"])
        if not clean.empty:
            fig_h = px.histogram(clean, x="Vol_3Y", nbins=40,
                                  color_discrete_sequence=[cfg["color"]],
                                  labels={"Vol_3Y":"Volatilidad 3A (%)"})
            fig_h.update_layout(height=280, showlegend=False, bargap=0.05,
                                 plot_bgcolor=plt_bg, paper_bgcolor=plt_paper,
                                 font=dict(family="Inter",size=11,color=plt_text),
                                 margin=dict(l=0,r=0,t=6,b=6),
                                 xaxis=dict(gridcolor=plt_grid,zeroline=False),
                                 yaxis=dict(gridcolor=plt_grid,title=""))
            st.plotly_chart(fig_h, use_container_width=True)

    with tab_hist:
        # Rentabilidades medias anuales de la familia 2020-2025
        hist_fam = []
        for yr in ANOS_RET:
            col_yr = f"Ret_{yr}"
            if col_yr in sub_fam.columns:
                v = sub_fam[col_yr].median()
                if not pd.isna(v):
                    hist_fam.append({"Año": yr, "Rentabilidad (%)": round(float(v), 2)})

        if hist_fam:
            hist_fam_df = pd.DataFrame(hist_fam)
            bar_colors = ["#3fb950" if v>=0 else "#f85149" for v in hist_fam_df["Rentabilidad (%)"]]
            fig_fhist = go.Figure(go.Bar(
                x=hist_fam_df["Año"], y=hist_fam_df["Rentabilidad (%)"],
                marker_color=bar_colors,
                text=[f"{v:+.1f}%" for v in hist_fam_df["Rentabilidad (%)"]],
                textposition="outside",
            ))
            fig_fhist.add_hline(y=0, line_color=plt_grid, line_width=1)
            fig_fhist.update_layout(
                height=300, showlegend=False, title=f"Rentabilidad mediana anual — {cfg['label']}",
                plot_bgcolor=plt_bg, paper_bgcolor=plt_paper,
                font=dict(family="Inter",size=11,color=plt_text),
                margin=dict(l=0,r=0,t=36,b=10),
                xaxis=dict(gridcolor=plt_grid,zeroline=False),
                yaxis=dict(gridcolor=plt_grid,zeroline=False,ticksuffix="%"),
                bargap=0.3,
            )
            st.plotly_chart(fig_fhist, use_container_width=True)
        else:
            st.markdown('<div class="infobox">Coloca "Base_de_datos_fondos.xlsx" junto a la aplicación para activar el gráfico de rentabilidades históricas.</div>', unsafe_allow_html=True)

    with tab_top:
        sc_ref = "Score_Perfil_3" if "Score_Perfil_3" in sub_fam.columns else None
        if sc_ref:
            top15 = sub_fam.nlargest(15, sc_ref)[["Name","ISIN","Familia_L2","Riesgo_Banda","Morningstar Rating","Ret_1Y","Vol_3Y","TER_KIID","AUM_M"]].reset_index(drop=True)
            st.dataframe(top15.style.format({
                "Ret_1Y": lambda v: fmt_pct(v) if not pd.isna(v) else "—",
                "Vol_3Y": lambda v: f"{v:.2f}%" if not pd.isna(v) else "—",
                "TER_KIID": lambda v: f"{v:.2f}%" if not pd.isna(v) else "—",
                "AUM_M": lambda v: fmt_aum(v) if not pd.isna(v) else "—",
                "Morningstar Rating": lambda v: stars(v) if not pd.isna(v) else "—",
            }), use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA 5 — COMPARADOR
# ─────────────────────────────────────────────────────────────────────────────
elif pagina == "Comparador":
    page_hdr("Comparador de Fondos", "Análisis lado a lado de hasta 4 fondos")

    st.markdown('<div class="infobox">Escribe el nombre o ISIN para buscar fondos. Puedes comparar hasta 4 simultáneamente.</div>', unsafe_allow_html=True)

    todos = sorted(fondos["Name"].dropna().unique().tolist())
    seleccion = st.multiselect("", todos, max_selections=4,
                               placeholder="Escribe para buscar fondos...",
                               label_visibility="collapsed")

    if seleccion:
        comp = fondos[fondos["Name"].isin(seleccion)].drop_duplicates("Name")

        # Tabla comparativa
        metricas_comp = {
            "Familia":           ("Familia_Perfil",      None),
            "Sub-familia":       ("Familia_L2",          None),
            "Banda de riesgo":   ("Riesgo_Banda",        None),
            "Rating Morningstar":("Morningstar Rating",  stars),
            "Rentabilidad 1A":   ("Ret_1Y",              fmt_pct),
            "Volatilidad 3A":    ("Vol_3Y",              lambda v: fmt_pct(v, sign=False)),
            "Max Drawdown":      ("MaxDrawdown",         fmt_pct),
            "TER":               ("TER_KIID",            lambda v: fmt_pct(v, sign=False)),
            "AUM":               ("AUM_M",               fmt_aum),
            "Min. inversión":    ("MinInv",              lambda v: f"{v:,.0f} €" if not pd.isna(v) else "—"),
            "ESG":               ("ESG_Flag",            lambda v: "Sí" if v==1 else "No"),
        }
        tabla = {}
        for lbl,(col,fn) in metricas_comp.items():
            if col in comp.columns:
                tabla[lbl] = {row["Name"]: fn(row[col]) if fn else row[col]
                               for _,row in comp.iterrows()}

        df_comp = pd.DataFrame(tabla).T
        st.dataframe(df_comp, use_container_width=True)

        # Gráfico histórico comparado (si hay datos)
        hist_cols = [f"Ret_{yr}" for yr in ANOS_RET if f"Ret_{yr}" in fondos.columns]
        if hist_cols:
            st.markdown("**Rentabilidades anuales comparadas**")
            traces = []
            palette = [FAMILIA_CONFIG.get(
                fondos[fondos["Name"]==n]["Familia_Perfil"].values[0] if len(fondos[fondos["Name"]==n])>0 else "",{}
            ).get("color","#1a4a7a") for n in seleccion]

            for nombre, color in zip(seleccion, palette):
                row = fondos[fondos["Name"]==nombre]
                if row.empty: continue
                row = row.iloc[0]
                yvals = [row.get(f"Ret_{yr}", np.nan) for yr in ANOS_RET]
                traces.append(go.Bar(
                    name=nombre[:35], x=ANOS_RET, y=yvals,
                    marker_color=color,
                    text=[f"{v:+.1f}%" if not pd.isna(v) else "" for v in yvals],
                    textposition="outside",
                ))

            fig_comp_hist = go.Figure(data=traces)
            fig_comp_hist.update_layout(
                barmode="group", height=340, bargap=0.2, bargroupgap=0.05,
                plot_bgcolor=plt_bg, paper_bgcolor=plt_paper,
                font=dict(family="Inter",size=11,color=plt_text),
                margin=dict(l=0,r=0,t=10,b=10),
                xaxis=dict(gridcolor=plt_grid,zeroline=False),
                yaxis=dict(gridcolor=plt_grid,zeroline=False,ticksuffix="%"),
                legend=dict(orientation="h",yanchor="bottom",y=1.01),
            )
            fig_comp_hist.add_hline(y=0, line_color=plt_grid, line_width=1)
            st.plotly_chart(fig_comp_hist, use_container_width=True)

        # Cards resumen
        st.markdown("**Métricas clave**")
        comp_cols = st.columns(len(seleccion))
        for col, nombre in zip(comp_cols, seleccion):
            row = fondos[fondos["Name"]==nombre]
            if row.empty: continue
            r = row.iloc[0]
            fam_color = FAMILIA_CONFIG.get(r.get("Familia_Perfil",""),{}).get("color","#1a4a7a")
            ret_v = r.get("Ret_1Y", np.nan)
            ret_color = ("#3fb950" if dark else "#2d6a4f") if (not pd.isna(ret_v) and ret_v>=0) else "#f85149"
            col.markdown(f"""
            <div class="card" style="text-align:center">
              <div style="font-size:.8rem;font-weight:700;color:{fam_color};margin-bottom:10px">{nombre[:32]}</div>
              <div style="font-size:1.25rem;font-weight:700;color:{ret_color}">{fmt_pct(ret_v)}</div>
              <div style="font-size:.7rem;color:{'#8b949e' if dark else '#8a9ab0'}">Rentabilidad 1A</div>
              <hr style="margin:8px 0;border-color:{'#21262d' if dark else '#e8edf2'}">
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:.78rem">
                <div><b>{fmt_pct(r.get('Vol_3Y'), sign=False)}</b><br><span style="color:{'#8b949e' if dark else '#8a9ab0'}">Vol. 3A</span></div>
                <div><b style="color:#f85149">{fmt_pct(r.get('MaxDrawdown'))}</b><br><span style="color:{'#8b949e' if dark else '#8a9ab0'}">Max DD</span></div>
                <div><b>{fmt_pct(r.get('TER_KIID'), sign=False)}</b><br><span style="color:{'#8b949e' if dark else '#8a9ab0'}">TER</span></div>
                <div><b>{stars(r.get('Morningstar Rating'))}</b><br><span style="color:{'#8b949e' if dark else '#8a9ab0'}">Rating</span></div>
              </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="text-align:center;padding:70px 0;color:{'#4a5568' if dark else '#a0b8cc'}">
          <div style="font-size:1.3rem;font-weight:300">Selecciona fondos para comparar</div>
          <div style="font-size:.82rem;margin-top:8px">Usa el selector de arriba para añadir hasta 4 fondos</div>
        </div>""", unsafe_allow_html=True)
