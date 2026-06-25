# Asistente RAG para Auditorías GMP 🏭

**Universidad Nacional de Luján · Seminario: Agentes Inteligentes y LLM**  
María Eliana Pighin · 2026

---

## ¿Qué hace este sistema?

Asistente conversacional que consulta SOPs y directivas QMS de la industria farmacéutica
en lenguaje natural, fundamentando cada respuesta en evidencia documental recuperada
mediante RAG (Retrieval-Augmented Generation).

---

## Estructura del proyecto

```
gmp_rag/
├── app.py                        # Aplicación principal Streamlit
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── secrets.toml.example      # Plantilla para tu API key (no subir el real)
├── components/
│   ├── sidebar.py                # Panel lateral de configuración
│   └── resultado.py              # Renderizado de respuestas y fuentes
├── utils/
│   └── rag_engine.py             # Carga del índice y lógica de consulta
├── indice_rag_gmp/               # Índice persistido (generado por la notebook)
└── docs/                         # PDFs de SOPs y directivas QMS
```

---

## Instalación y ejecución

### 1. Clonar o copiar el proyecto

```bash
cd gmp_rag
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar la API key

Crear el archivo `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "sk-tu-clave-aqui"
```

### 4. Copiar el índice persistido

Ejecutar la notebook en Google Colab, y luego descargar la carpeta `indice_rag_gmp/`
al directorio raíz del proyecto.

> La notebook persiste el índice con:
> ```python
> index.storage_context.persist(persist_dir="indice_rag_gmp")
> ```

### 5. Ejecutar la aplicación

```bash
streamlit run app.py
```

---

## Cómo reutilizar el índice desde la notebook

En la notebook, asegurarse de ejecutar la celda 18 (persistencia):

```python
PERSIST_DIR = "indice_rag_gmp"
index.storage_context.persist(persist_dir=PERSIST_DIR)
```

Luego descargar esa carpeta desde Colab:
- En el panel de archivos de Colab, hacer clic derecho sobre `indice_rag_gmp/`
- Seleccionar "Descargar"
- Colocarla en la raíz de este proyecto

---

## Seguridad importante

- **Nunca** subas `.streamlit/secrets.toml` a GitHub
- **Nunca** escribas tu API key directamente en el código
- La clave expuesta en la notebook debe ser revocada en https://platform.openai.com/api-keys
