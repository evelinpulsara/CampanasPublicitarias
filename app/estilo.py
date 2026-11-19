"""Capa visual de la app: solo estilos (CSS) y encabezado. No toca datos ni cálculos."""
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --primario: #4F5BEF;
    --primario-oscuro: #3340C9;
    --violeta: #7C4DFF;
    --fondo: #F5F6FB;
    --tarjeta: #FFFFFF;
    --borde: #E6E8F2;
    --texto: #1B1F33;
    --suave: #6B7190;
    --sombra: 0 1px 2px rgba(20, 24, 60, .04), 0 4px 16px rgba(20, 24, 60, .05);
}

html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea, select {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}
/* Conserva la fuente de los íconos de Streamlit */
[data-testid="stIconMaterial"], .material-symbols-rounded { font-family: 'Material Symbols Rounded' !important; }

.stApp, [data-testid="stAppViewContainer"] { background: var(--fondo); }
[data-testid="stHeader"] { background: transparent; }
footer { visibility: hidden; }

.block-container {
    max-width: 1320px;
    padding-top: 2.2rem;
    padding-bottom: 3rem;
}

/* ---------- Encabezado ---------- */
.hero {
    position: relative;
    overflow: hidden;
    background: linear-gradient(120deg, #2B2F77 0%, var(--primario) 55%, var(--violeta) 100%);
    border-radius: 20px;
    padding: 2rem 2.2rem 1.8rem;
    margin-bottom: 1.4rem;
    color: #fff;
    box-shadow: 0 12px 32px rgba(79, 91, 239, .25);
}
.hero::after {
    content: "";
    position: absolute;
    right: -80px; top: -80px;
    width: 300px; height: 300px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,255,255,.18) 0%, rgba(255,255,255,0) 70%);
}
.hero .etiqueta {
    display: inline-block;
    font-size: .72rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
    background: rgba(255,255,255,.16);
    padding: .3rem .7rem; border-radius: 999px; margin-bottom: .8rem;
}
.hero h1 {
    color: #fff !important;
    font-size: 2.1rem !important; font-weight: 800 !important; letter-spacing: -.02em;
    line-height: 1.15 !important; margin: 0 0 .45rem 0 !important; padding: 0 !important;
}
.hero p { color: rgba(255,255,255,.85); font-size: 1rem; margin: 0 0 1.1rem 0; max-width: 760px; }
.hero .chips { display: flex; flex-wrap: wrap; gap: .45rem; }
.hero .chip {
    font-size: .8rem; font-weight: 500;
    background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.25);
    padding: .3rem .75rem; border-radius: 999px;
}

/* ---------- Pestañas (Streamlit 1.6x usa role="tablist"/"tab") ---------- */
[data-testid="stTabs"] [role="tablist"] {
    gap: .35rem;
    background: var(--tarjeta);
    border: 1px solid var(--borde);
    border-radius: 14px;
    padding: .35rem;
    box-shadow: var(--sombra);
    flex-wrap: wrap;
    border-bottom: 1px solid var(--borde) !important;
}
[data-testid="stTabs"] [role="tab"] {
    height: auto;
    padding: .6rem 1.1rem !important;
    border-radius: 10px;
    color: var(--suave);
    background: transparent;
    transition: background .15s, color .15s;
}
[data-testid="stTabs"] [role="tab"] p { font-weight: 600 !important; font-size: .95rem; }
[data-testid="stTabs"] [role="tab"]:hover { background: #F0F1FA; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: var(--primario) !important;
    box-shadow: 0 4px 12px rgba(79, 91, 239, .35);
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] p { color: #fff !important; }
[data-testid="stTabs"] .react-aria-SelectionIndicator { display: none !important; }
[data-testid="stTabs"] [role="tabpanel"] { padding-top: 1.2rem; }

/* Versiones anteriores de Streamlit (baseweb) */
.stTabs [data-baseweb="tab-list"] {
    gap: .35rem;
    background: var(--tarjeta);
    border: 1px solid var(--borde);
    border-radius: 14px;
    padding: .35rem;
    box-shadow: var(--sombra);
    flex-wrap: wrap;
}
.stTabs [data-baseweb="tab"] {
    height: auto;
    padding: .6rem 1.1rem;
    border-radius: 10px;
    font-weight: 600;
    color: var(--suave);
    background: transparent;
    transition: background .15s, color .15s;
}
.stTabs [data-baseweb="tab"]:hover { background: #F0F1FA; color: var(--texto); }
.stTabs [aria-selected="true"] {
    background: var(--primario) !important;
    color: #fff !important;
}
.stTabs [aria-selected="true"] p { color: #fff !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.2rem; }

/* ---------- Títulos ---------- */
h2, h3 { color: var(--texto); font-weight: 700 !important; letter-spacing: -.015em; }
[data-testid="stTabs"] h3 { font-size: 1.55rem !important; }
h4 {
    color: var(--texto);
    font-weight: 700 !important;
    font-size: 1.08rem !important;
    border-left: 4px solid var(--primario);
    padding: .1rem 0 .1rem .7rem !important;
    margin-top: 1.4rem !important;
}
h5 { color: var(--primario-oscuro); font-weight: 700 !important; text-transform: uppercase;
     font-size: .82rem !important; letter-spacing: .06em; }
[data-testid="stCaptionContainer"] { color: var(--suave); }

/* ---------- Tarjetas de métricas ---------- */
[data-testid="stMetric"] {
    background: var(--tarjeta);
    border: 1px solid var(--borde);
    border-radius: 14px;
    padding: 1rem 1.1rem;
    box-shadow: var(--sombra);
    height: 100%;
    transition: transform .15s, box-shadow .15s;
}
[data-testid="stMetric"]:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(20,24,60,.08); }
[data-testid="stMetricLabel"] p {
    font-size: .72rem !important; font-weight: 600 !important;
    text-transform: uppercase; letter-spacing: .04em; color: var(--suave) !important;
    white-space: normal !important; overflow: visible !important; text-overflow: clip !important;
}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] div { overflow: visible !important; }
[data-testid="stMetricValue"] {
    font-size: 1.75rem !important; font-weight: 700 !important; color: var(--texto);
    letter-spacing: -.02em;
}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] div {
    white-space: normal !important; overflow: visible !important; text-overflow: clip !important;
    line-height: 1.15;
}
[data-testid="stMetricDelta"] { font-weight: 600; }

/* ---------- Gráficos, tablas y expanders como tarjetas ---------- */
/* La tarjeta va en el contenedor padre: el gráfico tiene altura fija y el relleno lo recortaría */
[data-testid="stElementContainer"]:has([data-testid="stPlotlyChart"]) {
    background: var(--tarjeta);
    border: 1px solid var(--borde);
    border-radius: 14px;
    padding: .9rem 1rem .7rem;
    box-shadow: var(--sombra);
    height: auto !important;
    overflow: visible !important;
}
[data-testid="stDataFrame"] {
    border: 1px solid var(--borde);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: var(--sombra);
}
[data-testid="stExpander"] details {
    background: var(--tarjeta);
    border: 1px solid var(--borde) !important;
    border-radius: 14px !important;
    box-shadow: var(--sombra);
}
[data-testid="stExpander"] summary { font-weight: 600; }

/* ---------- Avisos ---------- */
[data-testid="stAlert"] > div { border-radius: 12px; border: none; }

/* ---------- Controles ---------- */
[data-baseweb="select"] > div, [data-baseweb="input"], [data-testid="stNumberInput"] input {
    border-radius: 10px !important;
}
[data-testid="stMultiSelectTagsContainer"] [data-tag], span[data-baseweb="tag"] {
    background: #ECEEFF !important;
    color: var(--primario-oscuro) !important;
    border-radius: 8px !important;
    font-weight: 600;
}
span[data-baseweb="tag"] svg { fill: var(--primario-oscuro) !important; }
[data-testid="stMultiSelectTagsContainer"] [data-tag] * { color: var(--primario-oscuro) !important; }
.stButton button, .stDownloadButton button {
    border-radius: 10px; font-weight: 600;
    border: 1px solid var(--borde);
    box-shadow: var(--sombra);
}
.stDownloadButton button:hover, .stButton button:hover { border-color: var(--primario); color: var(--primario); }
[data-testid="stWidgetLabel"] p { font-weight: 600; color: var(--texto); }

hr { border-color: var(--borde) !important; }

/* ---------- Pie ---------- */
.pie {
    text-align: center; color: var(--suave); font-size: .8rem;
    margin-top: 2.5rem; padding-top: 1.2rem; border-top: 1px solid var(--borde);
}

@media (max-width: 640px) {
    .hero { padding: 1.4rem 1.2rem; }
    .hero h1 { font-size: 1.55rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.35rem !important; }
}
</style>
"""

_ENCABEZADO = """
<div class="hero">
  <span class="etiqueta">📈 Dashboard de campañas · Facebook Ads</span>
  <h1>Optimización de Campañas Publicitarias</h1>
  <p>Sistema analítico para optimizar la inversión publicitaria con modelos predictivos,
     pruebas A/B y análisis de atribución.</p>
  <div class="chips">
    <span class="chip">🌲 Random Forest</span>
    <span class="chip">⚡ AdaBoost</span>
    <span class="chip">💰 Recomendación de inversión</span>
    <span class="chip">🧪 A/B testing</span>
    <span class="chip">🔗 Atribución de canales</span>
  </div>
</div>
"""


def aplicar_estilo():
    st.markdown(_CSS, unsafe_allow_html=True)


def encabezado():
    st.markdown(_ENCABEZADO, unsafe_allow_html=True)


def pie():
    st.markdown('<div class="pie">Proyecto académico · Datos: Facebook Ads Campaign Dataset (Kaggle) · '
                'Hecho con Streamlit</div>', unsafe_allow_html=True)
