"""
Asistente RAG para Auditorías GMP – app.py
Universidad Nacional de Luján · Seminario Agentes Inteligentes y LLM
"""

import streamlit as st
from pathlib import Path

from utils.rag_engine import cargar_indice, consultar_auditoria_gmp
from components.sidebar import render_sidebar
from components.resultado import render_resultado

# ── Configuración de página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Asistente GMP",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personalizado ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Fuente y fondo */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 1.5rem; }

    /* Header de la app */
    .gmp-header {
        background: linear-gradient(135deg, #0f2942 0%, #1a4a7a 100%);
        padding: 1.4rem 2rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .gmp-header h1 { margin: 0; font-size: 1.6rem; font-weight: 700; }
    .gmp-header p  { margin: 0.3rem 0 0 0; font-size: 0.9rem; opacity: 0.8; }

    /* Tarjeta de consulta */
    .query-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #1a4a7a;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
    }

    /* Badges de tipo documental */
    .badge-qms { background:#dbeafe; color:#1e40af;
                 padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:600; }
    .badge-sop { background:#dcfce7; color:#166534;
                 padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:600; }
    .badge-gmp { background:#fef9c3; color:#854d0e;
                 padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:600; }

    /* Score bar */
    .score-bar-wrap { background:#e5e7eb; border-radius:4px; height:6px; width:100%; }
    .score-bar-fill { background:#1a4a7a; border-radius:4px; height:6px; }

    /* Sección de evidencia */
    .evidencia-box {
        background:#eff6ff; border:1px solid #bfdbfe;
        border-radius:6px; padding:0.8rem 1rem; margin-top:0.5rem;
        font-size:0.85rem; color:#1e3a5f;
    }

    /* Aviso de disclaimer */
    .disclaimer {
        background:#fefce8; border:1px solid #fde68a;
        border-radius:6px; padding:0.7rem 1rem;
        font-size:0.8rem; color:#78350f; margin-top:1rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="gmp-header">
    <h1>🏭 Asistente GMP para Auditorías</h1>
    <p>Consultá SOPs y directivas QMS en lenguaje natural · Sistemas Computarizados GxP</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar (configuración) ────────────────────────────────────────────────────
config = render_sidebar()

# ── Carga del índice ───────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Cargando índice documental…")
def get_index(persist_dir: str, top_k: int):
    return cargar_indice(persist_dir, top_k=top_k)

try:
    index = get_index(config["persist_dir"], config["top_k"])
    indice_ok = True
except Exception as e:
    st.error(f"❌ No se pudo cargar el índice: {e}")
    st.info("Asegurate de haber persistido el índice desde el notebook con `index.storage_context.persist()`")
    indice_ok = False

# ── Ejemplos de consulta ───────────────────────────────────────────────────────
EJEMPLOS = [
    # IT / Validación de Sistemas
    "¿Qué actividades deben realizarse durante el ciclo de vida de sistemas computarizados GxP?",
    "¿Qué controles deben mantenerse durante la operación y mantenimiento de un sistema GxP?",
    "¿Qué documentación debe revisar un auditor para una migración de sistema GxP?",
    "¿Qué evidencias se requieren para retirar o decomisionar un sistema computarizado GxP?",
    "¿Quiénes son los responsables de la validación de sistemas computarizados?",
    # Producción
    "¿Cuáles son los pasos para desarrollar una orden de producción de empaque?",
    "¿Qué controles en proceso deben realizarse durante la fabricación?",
    "¿Qué información debe contener un Master Batch Record?",
    "¿Cuáles son las responsabilidades del operador al cerrar un lote de producción?",
    # Calidad / Otras áreas
    "¿Cuáles son los requisitos de calidad para cleanrooms y áreas controladas?",
    "¿Qué requisitos aplican para el etiquetado y reempaque de productos?",
]

# ── Panel de consulta ──────────────────────────────────────────────────────────
st.markdown("#### 🔍 Consulta")

# Selector de ejemplos
ejemplo_sel = st.selectbox(
    "Usar una consulta de ejemplo (opcional):",
    ["— escribí tu propia consulta —"] + EJEMPLOS,
    key="ejemplo"
)

# Área de texto
valor_inicial = "" if ejemplo_sel.startswith("—") else ejemplo_sel
consulta = st.text_area(
    "Tu pregunta:",
    value=valor_inicial,
    key=f"consulta_{ejemplo_sel[:20]}",
)

boton = st.button("🔎 Consultar documentación GMP", type="primary",
                  disabled=not indice_ok, use_container_width=True)

# ── Resultado ─────────────────────────────────────────────────────────────────
if boton and consulta.strip():
    with st.spinner("Consultando base documental…"):
        resultado = consultar_auditoria_gmp(index, consulta.strip())

    render_resultado(resultado, consulta.strip())

    # Disclaimer regulatorio
    st.markdown("""
    <div class="disclaimer">
        ⚠️ <strong>Aviso:</strong> Este sistema es un prototipo académico.
        Las respuestas están fundamentadas en los documentos indexados, pero no reemplazan
        la revisión por personal calificado ni constituyen asesoramiento regulatorio oficial.
    </div>
    """, unsafe_allow_html=True)

elif boton and not consulta.strip():
    st.warning("⚠️ Escribí una consulta antes de enviar.")

# ── Historial de consultas ────────────────────────────────────────────────────
if "historial" not in st.session_state:
    st.session_state.historial = []

if boton and consulta.strip() and indice_ok:
    st.session_state.historial.insert(0, consulta.strip())
    st.session_state.historial = st.session_state.historial[:10]  # max 10

if st.session_state.historial:
    with st.expander("🕓 Historial de consultas recientes"):
        for i, q in enumerate(st.session_state.historial, 1):
            st.markdown(f"**{i}.** {q}")
