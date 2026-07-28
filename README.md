# Advanced RAG Pipeline System

Pipeline **Retrieval-Augmented Generation (RAG)** modular dengan query processing tingkat lanjut, hybrid retrieval, cross-encoder reranking, evaluasi otomatis, dan observability terintegrasi.

## Arsitektur

`
User → FastAPI → Query Processing (Rewrite/HyDE/Decompose)
                → Hybrid Retrieval (BM25 + Embedding)
                → Cross-Encoder Reranking
                → LLM Generation
                → Evaluation & Observability
`

## Fitur

- **Query Processing** — Rewrite, HyDE, Decompose untuk memperkaya query
- **Hybrid Retrieval** — BM25 (sparse) + Dense Embedding dengan Reciprocal Rank Fusion
- **Cross-Encoder Reranking** — Presisi tinggi dengan model reranker
- **Evaluation Module** — Faithfulness, Relevancy, Precision/Recall, MRR, nDCG
- **Observability** — Latency, token usage, cost tracking, logging terstruktur
- **Modular Design** — Setiap komponen dapat dikembangkan & di-scale independen

## Quick Start

### 1. Clone & Setup

`ash
git clone <repo-url> && cd rag-advanced
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
.\\venv\\Scripts\\Activate  # Windows
`

### 2. Install Dependencies

`ash
pip install -r requirements.txt
`

### 3. Konfigurasi

`ash
cp .env.example .env
# Edit .env dengan API key dan konfigurasi yang sesuai
`

### 4. Menyiapkan Dokumen

Siapkan dokumen dalam format teks dan index ke BM25 & Vector DB:

`python
from app.core.retrieval.bm25_retriever import BM25Retriever
from app.models.document import DocumentChunk

bm25 = BM25Retriever()
documents = [
    DocumentChunk(id="1", content="Isi dokumen 1...", metadata={"source": "file1.pdf"}),
    DocumentChunk(id="2", content="Isi dokumen 2...", metadata={"source": "file2.pdf"}),
]
bm25.index_documents(documents)
`

### 5. Jalankan Server

`ash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
`

### 6. API Documentation

Buka http://localhost:8000/docs untuk Swagger UI.

## API Endpoints

| Method | Path | Deskripsi |
|--------|------|-----------|
| POST | /api/v1/query | Query utama RAG pipeline |
| GET  | /api/v1/health | Health check |
| GET  | /api/v1/metrics | Metrik operasional |

### Contoh Request

`json
POST /api/v1/query
{
  "query": "Apa dampak kenaikan suku bunga terhadap sektor properti?",
  "top_k": 5,
  "enable_rewrite": true,
  "enable_hyde": true,
  "enable_decompose": false,
  "ground_truth": "Kenaikan suku bunga menyebabkan..."
}
`

## Struktur Proyek

`
rag-advanced/
├── app/
│   ├── main.py                       # FastAPI entry point
│   ├── config.py                     # Konfigurasi
│   ├── api/
│   │   ├── routes.py                 # API endpoints
│   │   └── schemas.py                # Pydantic schemas
│   ├── core/
│   │   ├── pipeline.py               # Pipeline orchestrator
│   │   ├── query_processing/
│   │   │   ├── rewrite.py            # Query Rewrite
│   │   │   ├── hyde.py               # HyDE generator
│   │   │   └── decompose.py          # Query Decomposition
│   │   ├── retrieval/
│   │   │   ├── bm25_retriever.py     # BM25 sparse retriever
│   │   │   ├── embedding_retriever.py # Dense retriever
│   │   │   └── hybrid_retriever.py   # Hybrid fusion
│   │   ├── reranking/
│   │   │   └── cross_encoder.py      # Cross-encoder reranker
│   │   └── generation/
│   │       └── llm_generator.py      # LLM abstraction
│   ├── evaluation/
│   │   ├── evaluator.py              # RAG evaluator
│   │   └── metrics.py                # Metric functions
│   └── observability/
│       ├── logger.py                 # Structured logging
│       ├── metrics.py                # Metrics collector
│       └── tracer.py                 # Tracing
├── .env.example
├── requirements.txt
└── README.md
`

## Fase Pengembangan (PRD)

| Fase | Cakupan | Status |
|------|---------|--------|
| Fase 1 | FastAPI skeleton + Hybrid Retrieval + LLM Generation | ✅ |
| Fase 2 | Query Processing + Cross-Encoder Reranking | ✅ |
| Fase 3 | Evaluation Module | ✅ |
| Fase 4 | Observability | ✅ |
| Fase 5 | Hardening, Testing, Dokumentasi | 📝 |
