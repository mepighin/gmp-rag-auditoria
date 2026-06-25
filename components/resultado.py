"""
components/resultado.py
Renderiza la respuesta RAG con fuentes, metadata y scores.
"""

import streamlit as st


def _badge_html(tipo: str) -> str:
    """Badge HTML — solo usar dentro de st.markdown(..., unsafe_allow_html=True)."""
    t = (tipo or "").upper()
    if t.startswith("QMS"):
        return '<span class="badge-qms">QMS</span>'
    if t.startswith("SOP"):
        return '<span class="badge-sop">SOP</span>'
    return '<span class="badge-gmp">GMP</span>'


def _badge_text(tipo: str) -> str:
    """Badge texto plano — para st.expander() que NO renderiza HTML en el label."""
    t = (tipo or "").upper()
    if t.startswith("QMS"):
        return "📘 QMS"
    if t.startswith("SOP"):
        return "📗 SOP"
    return "📄 GMP"


def render_resultado(resultado, consulta: str):
    import pandas as pd

    st.markdown("---")

    # ── 1. Respuesta principal ─────────────────────────────────────────────────
    st.markdown("### 💬 Respuesta del asistente")
    respuesta_texto = str(resultado.response) if resultado.response else "Sin respuesta."
    st.markdown(respuesta_texto)

    # ── 2. Fuentes recuperadas ─────────────────────────────────────────────────
    source_nodes = getattr(resultado, "source_nodes", [])
    if not source_nodes:
        st.info("No se recuperaron fuentes para esta consulta.")
        return

    # Agrupar fragmentos por documento
    docs_agrupados: dict[str, list] = {}
    for node in source_nodes:
        # NodeWithScore tiene .node; nodos directos tienen .metadata
        meta_node = getattr(node, "node", node)
        nombre = (meta_node.metadata or {}).get("file_name", "Desconocido")
        docs_agrupados.setdefault(nombre, []).append(node)

    n_docs  = len(docs_agrupados)
    n_frags = len(source_nodes)
    st.markdown(f"### 📂 Documentos utilizados — {n_docs} documento{'s' if n_docs != 1 else ''}, {n_frags} fragmentos")

    for doc_nombre, nodos in docs_agrupados.items():
        meta_node = getattr(nodos[0], "node", nodos[0])
        meta   = meta_node.metadata or {}
        codigo = meta.get("codigo", "–")
        tipo   = meta.get("tipo_documento", "–")
        area   = meta.get("area", "–")
        titulo = meta.get("titulo", "–")

        # st.expander NO renderiza HTML — usamos texto plano con emoji
        label = f"{_badge_text(tipo)}  {codigo} · {titulo[:65]}{'…' if len(titulo) > 65 else ''}"
        with st.expander(label, expanded=False):

            # Badges HTML dentro del expander — acá sí funcionan
            st.markdown(
                f'{_badge_html(tipo)} &nbsp; **{codigo}** &nbsp;|&nbsp; {area}',
                unsafe_allow_html=True
            )
            if titulo != "–":
                st.markdown(f"**Título:** {titulo}")

            st.markdown("**Evidencia documental:**")
            for i, nodo in enumerate(nodos, 1):
                meta_n = getattr(nodo, "node", nodo)
                texto  = meta_n.get_content() if hasattr(meta_n, "get_content") else str(meta_n)
                texto_corto = texto[:400] + ("…" if len(texto) > 400 else "")
                score = getattr(nodo, "score", None)
                score_txt = f" · score {score:.3f}" if score is not None else ""
                st.markdown(
                    f'<div class="evidencia-box">'
                    f'<strong>Fragmento {i}{score_txt}</strong><br><br>'
                    f'{texto_corto}'
                    f'</div>',
                    unsafe_allow_html=True
                )

    # ── 3. Modo avanzado ──────────────────────────────────────────────────────
    filas = []
    for node in source_nodes:
        meta_n = getattr(node, "node", node)
        meta   = meta_n.metadata or {}
        filas.append({
            "Código":  meta.get("codigo", "–"),
            "Tipo":    meta.get("tipo_documento", "–"),
            "Área":    meta.get("area", "–"),
            "Score":   round(getattr(node, "score", 0) or 0, 4),
            "Archivo": meta.get("file_name", "–"),
        })
    df = pd.DataFrame(filas).sort_values("Score", ascending=False).reset_index(drop=True)

    with st.expander("🔬 Modo avanzado — scores de relevancia y exportación"):
        st.caption("Scores de relevancia semántica. Valores más cercanos a 1.0 = mayor similitud con la consulta.")
        st.dataframe(df, width="stretch", hide_index=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Exportar fuentes (CSV)",
            data=csv,
            file_name=f"fuentes_gmp_{consulta[:30].replace(' ', '_')}.csv",
            mime="text/csv",
        )
