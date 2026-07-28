# Product Requirements Document (PRD)
## Advanced RAG (Retrieval-Augmented Generation) Pipeline System

| | |
|---|---|
| **Versi Dokumen** | 1.0 |
| **Tanggal** | 28 Juli 2026 |
| **Status** | Draft |
| **Pemilik Produk** | TBD |
| **Reviewer** | TBD |

---

## 1. Latar Belakang & Ringkasan Eksekutif

Sistem yang diusulkan adalah sebuah pipeline **Retrieval-Augmented Generation (RAG)** yang menggabungkan teknik query processing tingkat lanjut, hybrid retrieval, reranking berbasis cross-encoder, serta lapisan evaluasi dan observability yang terintegrasi. Tujuannya adalah menghasilkan jawaban yang akurat, relevan, dan dapat dipertanggungjawabkan (grounded) dari basis pengetahuan internal, sambil menjaga kualitas jawaban dapat diukur dan performa sistem dapat dipantau secara berkelanjutan.

Sistem ini akan diekspos melalui **FastAPI** sebagai backend service, dan dirancang agar modular — setiap komponen (query processing, retrieval, reranking, generation, evaluation, observability) dapat dikembangkan, diuji, dan di-scale secara independen.

---

## 2. Masalah yang Diselesaikan (Problem Statement)

- Pencarian berbasis single-method (hanya keyword atau hanya semantic) sering gagal menangkap query yang ambigu, terlalu pendek, atau kompleks.
- Jawaban LLM tanpa retrieval yang baik cenderung *hallucinate* atau tidak faktual.
- Tanpa reranking, top-K dari retrieval awal sering mengandung dokumen yang kurang relevan, sehingga LLM menerima konteks berkualitas rendah.
- Tim tidak memiliki visibilitas terhadap kualitas jawaban (precision, recall, faithfulness) maupun biaya operasional (latency, token, cost) secara real-time.

---

## 3. Tujuan (Goals)

### 3.1 Tujuan Bisnis
1. Meningkatkan akurasi dan relevansi jawaban sistem tanya-jawab berbasis dokumen internal.
2. Menyediakan sistem yang dapat diaudit — setiap jawaban dapat ditelusuri ke sumber dan diukur kualitasnya.
3. Mengontrol biaya operasional LLM melalui observability token & cost.

### 3.2 Tujuan Produk
1. Membangun pipeline query processing (rewrite, HyDE, decompose) untuk memperkaya query sebelum retrieval.
2. Mengimplementasikan hybrid retrieval (BM25 + embedding/dense vector) untuk menyeimbangkan lexical dan semantic matching.
3. Menambahkan cross-encoder reranking untuk menyaring top-K hasil retrieval agar lebih presisi.
4. Membangun modul evaluasi otomatis (Precision/Recall, MRR, nDCG, Faithfulness, Relevancy).
5. Membangun modul observability (latency, token usage, cost, tracing end-to-end).

### 3.3 Non-Goals (Di Luar Cakupan v1)
- Fine-tuning model embedding atau LLM custom.
- Multi-modal retrieval (gambar, audio, video).
- UI front-end untuk end-user (fokus v1 adalah API/backend).
- Multi-tenant / multi-bahasa penuh (akan dievaluasi di fase berikutnya).

---

## 4. Target Pengguna

| Persona | Kebutuhan |
|---|---|
| Developer/Integrator | API yang stabil, terdokumentasi, mudah diintegrasikan (via FastAPI) |
| Data/ML Engineer | Observability & evaluation metrics untuk iterasi model |
| Product/Business Owner | Laporan kualitas jawaban dan biaya operasional |
| End-user (via aplikasi consumer) | Jawaban cepat, relevan, dan faktual |

---

## 5. Arsitektur Sistem

```
                 User
                   ↓
                FastAPI
                   ↓
           Query Processing
             ↙     ↓      ↘
        Rewrite   HyDE   Decompose
             \      |      /
              ↓     ↓     ↓
          Hybrid Retrieval
          BM25 + Embedding
                  ↓
          Cross-Encoder
             Reranking
                  ↓
             Top-K Context
                  ↓
                  LLM
                  ↓
               Answer
                  ↓
        ┌─────────┴─────────┐
        ↓                   ↓
    Evaluation         Observability
        ↓                   ↓
 Precision/Recall       Latency
 MRR/nDCG              Token Usage
 Faithfulness          Cost
 Relevancy             Traces
```

### 5.1 Alur Data (High-Level)
1. User mengirimkan query ke endpoint FastAPI.
2. Query diproses melalui tiga strategi paralel/kombinasi: **Rewrite**, **HyDE**, **Decompose**.
3. Hasil query yang telah diperkaya dikirim ke **Hybrid Retrieval** (BM25 + embedding search).
4. Kandidat dokumen hasil retrieval di-rerank menggunakan **Cross-Encoder**.
5. Top-K dokumen hasil reranking dijadikan konteks bagi **LLM** untuk menghasilkan jawaban.
6. Jawaban dan seluruh proses dicatat untuk **Evaluation** (kualitas) dan **Observability** (performa & biaya).

---

## 6. Functional Requirements (FR)

### 6.1 API Layer (FastAPI)
| ID | Requirement |
|---|---|
| FR-1.1 | Sistem harus menyediakan endpoint `POST /query` yang menerima query teks dan parameter opsional (top_k, filter metadata, dsb). |
| FR-1.2 | Sistem harus mengembalikan jawaban, daftar sumber/dokumen pendukung (citations), dan metadata trace (latency, token usage). |
| FR-1.3 | API harus mendukung autentikasi (API key / bearer token) dan rate limiting. |
| FR-1.4 | API harus memiliki dokumentasi otomatis (OpenAPI/Swagger). |
| FR-1.5 | Sistem harus mendukung endpoint kesehatan (`/health`) dan versi (`/version`). |

### 6.2 Query Processing
| ID | Requirement |
|---|---|
| FR-2.1 | **Query Rewrite**: sistem harus mampu menulis ulang query untuk memperjelas intent (mis. menghilangkan ambiguitas, memperbaiki tata bahasa, menambah konteks percakapan sebelumnya). |
| FR-2.2 | **HyDE (Hypothetical Document Embeddings)**: sistem harus mampu menghasilkan dokumen hipotetis dari query untuk digunakan sebagai representasi embedding tambahan saat retrieval. |
| FR-2.3 | **Query Decomposition**: sistem harus mampu memecah query kompleks/multi-hop menjadi beberapa sub-query yang lebih sederhana. |
| FR-2.4 | Strategi query processing yang digunakan harus dapat dikonfigurasi (on/off per strategi) melalui parameter atau konfigurasi sistem. |
| FR-2.5 | Sistem harus mencatat waktu eksekusi tiap strategi untuk keperluan observability. |

### 6.3 Hybrid Retrieval
| ID | Requirement |
|---|---|
| FR-3.1 | Sistem harus mendukung retrieval berbasis **BM25** (lexical/sparse search). |
| FR-3.2 | Sistem harus mendukung retrieval berbasis **embedding/dense vector search** (menggunakan vector database). |
| FR-3.3 | Sistem harus menggabungkan hasil BM25 dan embedding menggunakan strategi fusion (mis. Reciprocal Rank Fusion / weighted scoring), dengan bobot yang dapat dikonfigurasi. |
| FR-3.4 | Sistem harus mendukung filtering berdasarkan metadata (mis. tanggal, kategori, source). |
| FR-3.5 | Sistem harus mendukung konfigurasi jumlah kandidat awal (initial top-N sebelum reranking). |

### 6.4 Reranking
| ID | Requirement |
|---|---|
| FR-4.1 | Sistem harus melakukan reranking terhadap kandidat hasil hybrid retrieval menggunakan model **cross-encoder**. |
| FR-4.2 | Sistem harus mengembalikan **Top-K** dokumen final setelah reranking sebagai konteks untuk LLM, dengan K dapat dikonfigurasi. |
| FR-4.3 | Sistem harus mencatat skor reranking untuk setiap dokumen (untuk audit/debugging). |

### 6.5 Answer Generation (LLM)
| ID | Requirement |
|---|---|
| FR-5.1 | Sistem harus menghasilkan jawaban berbasis konteks Top-K menggunakan LLM, dengan prompt template yang mendukung citation/sumber. |
| FR-5.2 | Sistem harus mendukung konfigurasi model LLM (model, temperature, max tokens, dsb). |
| FR-5.3 | Sistem harus menyertakan referensi/sumber dokumen pada jawaban akhir. |
| FR-5.4 | Sistem harus menangani kasus tidak ditemukan konteks relevan (fallback/"tidak ada informasi yang cukup"). |

### 6.6 Evaluation
| ID | Requirement |
|---|---|
| FR-6.1 | Sistem harus dapat menghitung metrik retrieval: **Precision**, **Recall**, **MRR (Mean Reciprocal Rank)**, **nDCG (normalized Discounted Cumulative Gain)** terhadap dataset evaluasi berlabel. |
| FR-6.2 | Sistem harus dapat menghitung metrik kualitas jawaban: **Faithfulness** (kesesuaian jawaban dengan konteks/sumber) dan **Answer Relevancy** (relevansi jawaban terhadap query). |
| FR-6.3 | Sistem harus menyediakan mekanisme evaluasi batch (offline, menggunakan test set) maupun evaluasi sampel online (production monitoring). |
| FR-6.4 | Hasil evaluasi harus dapat diekspor/divisualisasikan (dashboard atau laporan). |

### 6.7 Observability
| ID | Requirement |
|---|---|
| FR-7.1 | Sistem harus mencatat **latency** per komponen (query processing, retrieval, reranking, generation) dan end-to-end. |
| FR-7.2 | Sistem harus mencatat **token usage** (input/output) per request. |
| FR-7.3 | Sistem harus menghitung estimasi **cost** per request berdasarkan token usage dan harga model. |
| FR-7.4 | Sistem harus menyediakan **distributed tracing** end-to-end untuk setiap request (query → jawaban), termasuk trace ID yang dapat digunakan untuk debugging. |
| FR-7.5 | Sistem harus terintegrasi dengan tools observability standar (mis. OpenTelemetry, Langfuse, atau setara) untuk ekspor metrik dan trace. |
| FR-7.6 | Sistem harus menyediakan alerting dasar (mis. latency di atas threshold, error rate tinggi). |

---

## 7. Non-Functional Requirements (NFR)

| Kategori | Requirement |
|---|---|
| **Performa** | Latency end-to-end target p95 < 3–5 detik per query (tergantung kompleksitas & panjang konteks). |
| **Skalabilitas** | Sistem harus dapat menangani peningkatan beban secara horizontal (stateless API layer, retrieval & vector DB dapat di-scale terpisah). |
| **Reliabilitas** | Ketersediaan sistem (uptime) target ≥ 99.5%. |
| **Keamanan** | Autentikasi API, enkripsi data in-transit (TLS), pengelolaan API key/secret yang aman. |
| **Observability** | Semua request harus dapat ditelusuri (traceable) dari input hingga output. |
| **Maintainability** | Arsitektur modular; tiap komponen (query processing, retrieval, reranking, generation) dapat diganti/diupgrade tanpa mengubah komponen lain. |
| **Cost Efficiency** | Sistem harus menyediakan visibilitas biaya agar dapat dioptimalkan (mis. caching, model routing). |

---

## 8. Metrik Keberhasilan (Success Metrics)

| Metrik | Target Awal (Baseline → Target) |
|---|---|
| Retrieval Precision@K | Diukur dari baseline, target peningkatan ≥ 15% setelah hybrid + reranking |
| Recall@K | Target ≥ 85% pada test set evaluasi |
| MRR | Target ≥ 0.75 |
| nDCG@K | Target ≥ 0.80 |
| Faithfulness Score | Target ≥ 90% (jawaban konsisten dengan sumber) |
| Answer Relevancy | Target ≥ 85% |
| Latency p95 (end-to-end) | ≤ 5 detik |
| Cost per query | Dipantau & dioptimalkan secara berkala (target penurunan bertahap) |

---

## 9. Alur Kerja Pengguna (User Flow) — Contoh

1. User mengirim query: *"Apa dampak kenaikan suku bunga terhadap sektor properti tahun ini?"*
2. Sistem melakukan **query rewrite** untuk memperjelas konteks temporal ("tahun ini" → tahun berjalan).
3. Sistem menghasilkan **HyDE document** sebagai representasi tambahan untuk pencarian semantik.
4. Jika query kompleks, sistem melakukan **decomposition** menjadi sub-pertanyaan (mis. "suku bunga saat ini", "dampak historis suku bunga ke properti").
5. **Hybrid retrieval** mengambil kandidat dokumen dari BM25 dan embedding search.
6. **Cross-encoder reranker** menyaring dan mengurutkan ulang kandidat menjadi Top-K paling relevan.
7. **LLM** menghasilkan jawaban berbasis Top-K konteks, lengkap dengan sitasi sumber.
8. Sistem mencatat **evaluation** (jika ada ground truth) dan **observability data** (latency, token, cost, trace).
9. Jawaban dikembalikan ke user melalui API.

---

## 10. Dependensi Teknis (Diusulkan)

| Komponen | Opsi Teknologi (Contoh) |
|---|---|
| API Framework | FastAPI |
| Sparse Retrieval | Elasticsearch / OpenSearch (BM25) |
| Dense Retrieval | Vector DB — Qdrant / Weaviate / Pinecone / pgvector |
| Embedding Model | Model embedding pilihan tim (mis. OpenAI, Cohere, atau open-source) |
| Cross-Encoder | Model reranker (mis. berbasis sentence-transformers cross-encoder) |
| LLM | Model LLM pilihan tim (via API) |
| Evaluation Framework | RAGAS, TruLens, atau custom evaluation harness |
| Observability | OpenTelemetry, Langfuse, Prometheus + Grafana |

*Catatan: Pemilihan teknologi final perlu dikonfirmasi bersama tim engineering sesuai constraint infrastruktur dan budget.*

---

## 11. Risiko & Mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Latency tinggi akibat banyaknya tahap (query processing + hybrid retrieval + reranking + LLM) | Pengalaman user menurun | Paralelisasi proses, caching, optimasi model reranker (batas ukuran) |
| Biaya LLM membengkak (HyDE & decomposition menambah panggilan LLM) | Cost operasional tinggi | Observability cost per komponen, caching hasil query processing, model routing (model kecil untuk sub-task) |
| Reranker menjadi bottleneck saat jumlah kandidat besar | Latency naik | Batasi jumlah kandidat awal sebelum reranking, gunakan model reranker yang efisien |
| Evaluasi bias terhadap dataset test yang tidak representatif | Metrik tidak mencerminkan performa real-world | Update dataset evaluasi secara berkala, kombinasikan evaluasi offline & online |
| Data sensitif bocor melalui LLM/observability logs | Risiko keamanan/compliance | Masking data sensitif pada logs & trace, kontrol akses ketat |

---

## 12. Fase & Milestone (Diusulkan)

| Fase | Cakupan | Estimasi |
|---|---|---|
| **Fase 1** | FastAPI skeleton + Hybrid Retrieval dasar (BM25 + embedding) + LLM generation sederhana | 2–3 minggu |
| **Fase 2** | Query Processing (Rewrite, HyDE, Decompose) + Cross-Encoder Reranking | 2–3 minggu |
| **Fase 3** | Evaluation module (Precision/Recall/MRR/nDCG/Faithfulness/Relevancy) | 2 minggu |
| **Fase 4** | Observability (latency, token usage, cost, tracing) + dashboard | 2 minggu |
| **Fase 5** | Hardening, load testing, dokumentasi, rollout produksi | 1–2 minggu |

---

## 13. Open Questions

1. Apakah sistem perlu mendukung multi-bahasa (Indonesia & Inggris) sejak v1?
2. Berapa volume traffic (QPS) yang diperkirakan pada fase produksi?
3. Vector database dan LLM provider mana yang sudah menjadi standar/preferensi organisasi?
4. Apakah dibutuhkan mekanisme feedback loop dari user (thumbs up/down) untuk memperkaya dataset evaluasi?
5. Apakah ada requirement compliance/data privacy khusus (mis. data tidak boleh keluar region tertentu)?

---

*Dokumen ini adalah draft awal dan terbuka untuk revisi berdasarkan diskusi lebih lanjut dengan stakeholder engineering, data science, dan product.*
