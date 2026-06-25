"""
components/sidebar.py
Panel lateral con configuración del sistema.
"""

import json
import streamlit as st
from pathlib import Path


def render_sidebar() -> dict:
    with st.sidebar:
        st.markdown("## ⚙️ Configuración")
        st.markdown("---")

        # ── Índice documental ──────────────────────────────────────────────────
        st.markdown("**📁 Índice documental**")
        persist_dir = st.text_input(
            "Ruta del índice persistido:",
            value="indice_rag_gmp",
            help="Carpeta generada por `index.storage_context.persist()` en la notebook."
        )

        dir_existe = Path(persist_dir).exists()
        if dir_existe:
            st.success("✅ Índice encontrado")
        else:
            st.error("❌ Directorio no encontrado")

        st.markdown("---")

        # ── Documentos indexados (leídos del índice real) ──────────────────────
        st.markdown("**📋 Documentos indexados**")
        try:
            docstore_path = Path(persist_dir) / "docstore.json"
            with open(docstore_path, "r", encoding="utf-8") as f:
                docstore = json.load(f)

            docs_vistos = {}
            for node_id, node_data in docstore.get("docstore/data", {}).items():
                meta = node_data.get("__data__", {}).get("metadata", {})
                codigo = meta.get("codigo")
                if codigo and codigo not in docs_vistos:
                    docs_vistos[codigo] = {
                        "tipo": meta.get("tipo_documento", "GMP"),
                        "titulo": meta.get("titulo", "–")[:100],
                    }

            lineas = []
            for codigo, info in sorted(docs_vistos.items()):
                clase = "qms" if info["tipo"].upper() == "QMS" else "sop"
                lineas.append(
                    f'<span class="badge-{clase}">{codigo}</span> '
                    f'<small>{info["titulo"]}</small>'
                )
            st.markdown(
                "<div style='line-height:2'>" + "<br>".join(lineas) + "</div>",
                unsafe_allow_html=True
            )

            st.markdown("---")
            st.metric("Documentos", len(docs_vistos))

        except Exception:
            st.caption("(lista no disponible)")

        st.markdown("---")

        # ── Parámetros avanzados ───────────────────────────────────────────────
        with st.expander("🔧 Parámetros avanzados"):
            top_k = st.slider(
                "Fragmentos a recuperar (top-k):",
                min_value=2,
                max_value=12,
                value=6,
                help="Más fragmentos = respuestas más completas, pero más lentas y costosas."
            )

        st.markdown("---")

        # ── Info del sistema ───────────────────────────────────────────────────
        st.markdown("**ℹ️ Acerca del sistema**")
        st.markdown("""
Asistente documental GMP con **RAG**:

- 📚 **LlamaIndex** – recuperación
- 🧠 **GPT-4o-mini** – síntesis
- 🔍 **text-embedding-3-small** – semántica
- 📌 **CitationQueryEngine** – con citas
        """)

        st.markdown("---")
        st.caption("UNLu · Agentes Inteligentes y LLM · 2026")

    return {
        "persist_dir": persist_dir,
        "top_k": top_k,
    }