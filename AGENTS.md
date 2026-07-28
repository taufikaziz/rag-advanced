# AGENTS.md — Panduan untuk AI Agent dalam pengembangan proyek ini
# Proyek: Advanced RAG Pipeline System

## Struktur Proyek

Proyek ini adalah pipeline RAG modular. Setiap modul utama berada di app/core/:

- query_processing/ — Query Rewrite, HyDE, Decompose
- retrieval/ — BM25, Dense, Hybrid retrievers
- reranking/ — Cross-Encoder reranker
- generation/ — LLM abstraction (OpenAI, Anthropic, Ollama)
- evaluation/ — Faithfulness, Relevancy, Precision/Recall, MRR, nDCG
- observability/ — Logging, metrics, tracing

## Konvensi Kode

1. Modular & Testable — Setiap komponen memiliki base class/interface di base.py
2. Async-first — Semua operasi I/O menggunakan async/await
3. Pydantic models — Semua schema menggunakan Pydantic v2
4. Dependency Injection — Pipeline menerima komponen via constructor
5. Config-driven — Setting via environment variables di app/config.py

## Cara Menambahkan Komponen Baru

1. Buat folder baru di app/core/ jika diperlukan
2. Buat base.py dengan abstract class
3. Implementasi konkret mengikuti base class
4. Daftarkan di app/core/pipeline.py (RAGPipeline)
5. Tambahkan endpoint di app/api/routes.py jika perlu
6. Tambahkan test di tests/

## Cara Menjalankan

`ash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (copy dari .env.example)
cp .env.example .env

# Jalankan server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Jalankan test
pytest tests/ -v
`
