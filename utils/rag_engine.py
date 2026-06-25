"""
utils/rag_engine.py
Carga el índice persistido por LlamaIndex y expone la función de consulta.
"""

import os
import streamlit as st
from pathlib import Path

from llama_index.core import (
    Settings,
    StorageContext,
    load_index_from_storage,
)
from llama_index.core.query_engine import CitationQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.schema import QueryBundle, NodeWithScore
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

# ── Constantes de retrieval ────────────────────────────────────────────────────
_TOP_K_CANDIDATOS = 12
_MAX_POR_DOC      = 2
_SCORE_MINIMO     = 0.30

# ── Expansión bilingüe — afecta al retriever vectorial, no al prompt ──────────
_EXPANSIONES: dict[str, str] = {
    "retiro":                "retire retirement decommission decommissioning",
    "retirar":               "retire decommission retirement decommissioning",
    "decomisión":            "decommission decommissioning retire",
    "entregables":           "deliverables outputs evidence documentation artifacts",
    "validación":            "validation qualification IQ OQ PQ validation plan",
    "ciclo de vida":         "lifecycle life cycle SDLC system lifecycle",
    "migración":             "migration data migration system migration",
    "operación":             "operation maintenance operational controls operate",
    "implementar":           "implementation setup configuration install deploy",
    "sistema computarizado": "computerized system GxP system CSV computer system",
}


def _configurar_llm():
    api_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "No se encontró OPENAI_API_KEY. "
            "Agregala en .streamlit/secrets.toml o como variable de entorno."
        )
    os.environ["OPENAI_API_KEY"] = api_key
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")


def _expandir_query(consulta: str) -> str:
    """Enriquece la query con términos en inglés ANTES del retrieval vectorial."""
    consulta_lower = consulta.lower()
    terminos_extra = [
        exp for term, exp in _EXPANSIONES.items()
        if term in consulta_lower
    ]
    if not terminos_extra:
        return consulta
    return f"{consulta} {' '.join(terminos_extra)}"


def _filtrar_por_diversidad(nodes: list, max_por_doc: int) -> list:
    """Limita cuántos fragmentos del mismo documento entran en el resultado."""
    conteo: dict[str, int] = {}
    resultado = []
    for node in nodes:
        doc_id = node.node.metadata.get("file_name", node.node_id)
        conteo[doc_id] = conteo.get(doc_id, 0)
        if conteo[doc_id] < max_por_doc:
            resultado.append(node)
            conteo[doc_id] += 1
    return resultado


def cargar_indice(persist_dir: str, top_k: int = 6):
    """Carga el índice persistido y devuelve el objeto index."""
    _configurar_llm()
    if not Path(persist_dir).exists():
        raise FileNotFoundError(
            f"No se encontró el directorio de índice: '{persist_dir}'. "
            "Ejecutá primero la notebook y persistí el índice."
        )
    storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
    return load_index_from_storage(storage_context)


def _construir_contexto_documentos(nodes: list) -> str:
    lineas = []
    for i, node in enumerate(nodes, 1):
        meta   = node.node.metadata or {}
        codigo = meta.get("codigo", "–")
        tipo   = meta.get("tipo_documento", "–")
        titulo = meta.get("titulo", "–")
        area   = meta.get("area", "–")
        texto  = node.node.get_content()[:600]
        lineas.append(
            f"[DOC {i}]\n"
            f"  codigo: {codigo}\n"
            f"  tipo_documento: {tipo}\n"
            f"  titulo: {titulo}\n"
            f"  area: {area}\n"
            f"  contenido:\n{texto}\n"
        )
    return "\n".join(lineas)


def construir_prompt_auditoria_gmp(consulta: str, nodes: list) -> str:
    """
    Prompt con contexto explícito de documentos.

    Por qué se inyecta el contexto aquí:
    CitationQueryEngine hace su propio retrieval internamente. Si dejamos
    que construya el contexto solo, puede ignorar los nodos que ya filtramos.
    Al inyectar el contexto directamente en el prompt, el LLM trabaja con
    exactamente los fragmentos que seleccionamos (con diversidad aplicada).
    """
    contexto = _construir_contexto_documentos(nodes)
    codigos  = sorted({n.node.metadata.get("codigo", "?") for n in nodes})
    lista_docs = ", ".join(codigos)

    return f"""
Actuás como un asistente especializado en auditorías GMP para la industria farmacéutica.

A continuación tenés los fragmentos documentales recuperados del sistema RAG.
Debés basar tu respuesta ÚNICAMENTE en estos fragmentos. No inventés información.

=== DOCUMENTOS RECUPERADOS ===
{contexto}
==============================

Consulta: "{consulta}"

INSTRUCCIONES:
1. Respondé específicamente lo que se pregunta, con detalle técnico.
2. Mencioná TODOS los documentos del contexto que sean relevantes (tenés: {lista_docs}).
3. No ignores documentos recuperados aunque parezcan secundarios.
4. Para cada documento mencionado indicá: código, tipo y área.
5. Listá los entregables, registros y evidencias concretas que menciona la documentación.
6. Si un documento tiene información parcial, decilo.
7. Si la documentación no alcanza para responder algo, decilo explícitamente.

Estructurá la respuesta así:

## Respuesta
Explicación directa y técnica de lo que se pregunta.
No uses referencias como (DOC 1), (DOC 2) etc. en el texto. 
Las fuentes se listan en la sección "Documentos relevantes".

## Documentos relevantes
Agrupá por documento (no por fragmento). Por cada documento distinto que aparezca 
en el contexto, listá UNA SOLA VEZ usando exactamente estos valores del encabezado [DOC N]:
- Código: (el valor después de "QMS" o "SOP" en el encabezado)
- Tipo: (QMS o SOP según el encabezado)  
- Título: (el título del encabezado)
- Área: (el valor del campo "area" del encabezado, ignorá "Internal" que es confidencialidad)
- Evidencia encontrada: (resumí la evidencia de TODOS los fragmentos de ese documento)

## Evidencia para auditoría
Listá registros, entregables, controles y responsabilidades concretos mencionados.

## Observación final
¿La documentación recuperada es suficiente para responder? ¿Falta algo?
""".strip()


def consultar_auditoria_gmp(index, consulta: str):
    """
    Pipeline completo:
      1. Expande la query con términos en inglés → mejor recall en QMS
      2. Recupera _TOP_K_CANDIDATOS fragmentos
      3. Filtra por score mínimo
      4. Aplica diversidad (máx _MAX_POR_DOC por documento)
      5. Inyecta los nodos filtrados directamente en el prompt
      6. El LLM sintetiza con exactamente esos fragmentos
    """
    # 1. Expandir query para el retriever vectorial
    query_expandida = _expandir_query(consulta)

    # 2. Recuperar candidatos
    retriever = VectorIndexRetriever(index=index, similarity_top_k=_TOP_K_CANDIDATOS)
    nodes = retriever.retrieve(QueryBundle(query_str=query_expandida))

    # 3. Filtrar por score mínimo
    nodes = [n for n in nodes if (n.score or 0) >= _SCORE_MINIMO]

    # 4. Diversidad de documentos
    nodes = _filtrar_por_diversidad(nodes, _MAX_POR_DOC)

    # 5. Construir prompt con contexto explícito de los nodos filtrados
    prompt = construir_prompt_auditoria_gmp(consulta, nodes)

    # 6. Usar el LLM directamente con el prompt ya enriquecido
    #    (sin dejar que CitationQueryEngine haga su propio retrieval)
    llm = Settings.llm
    from llama_index.core.llms import ChatMessage
    response_text = llm.complete(prompt).text

    # 7. Construir un objeto compatible con render_resultado
    class _Response:
        def __init__(self, text, src_nodes):
            self.response     = text
            self.source_nodes = src_nodes
        def __str__(self):
            return self.response

    return _Response(response_text, nodes)
