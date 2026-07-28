# API Routes — FastAPI endpoints untuk RAG pipeline

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from app.api.schemas import QueryRequest, QueryResponse
from app.core.pipeline import RAGPipeline
from app.observability.metrics import get_metrics

router = APIRouter()


@router.get("/")
async def root():
    """Redirect root to frontend."""
    return RedirectResponse(url="/static/index.html")


async def get_pipeline() -> RAGPipeline:
    """Dependency injection for pipeline."""
    from app.main import pipeline
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    return pipeline


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest, pipe: RAGPipeline = Depends(get_pipeline)):
    """Main endpoint — process a query through the full RAG pipeline."""
    try:
        response = await pipe.run(request)
        return response
    except Exception as e:
        from app.observability.metrics import record_error
        record_error()
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "rag-pipeline"}


@router.get("/metrics")
async def metrics():
    """Return current pipeline metrics."""
    return get_metrics()


import os as _os
import base64 as _b64
import uuid as _uuid
from pathlib import Path as _Path
from fastapi.responses import RedirectResponse
from pydantic import BaseModel as _BaseModel

_UPLOAD_DIR = _Path(__file__).resolve().parent.parent.parent / "uploads"
_UPLOAD_DIR.mkdir(exist_ok=True)
_SUPPORTED = {".txt", ".md", ".pdf", ".csv", ".json", ".xml", ".html"}

class UploadRequest(_BaseModel):
    filename: str
    content: str  # base64-encoded file content


@router.post("/documents/upload")
async def upload_document(req: UploadRequest):
    if not req.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    ext = _Path(req.filename).suffix.lower()
    if ext not in _SUPPORTED:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    safe_name = _uuid.uuid4().hex + ext
    filepath = _UPLOAD_DIR / safe_name
    try:
        decoded = _b64.b64decode(req.content)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 content")
    with open(filepath, "wb") as f:
        f.write(decoded)
    from app.main import doc_ingestion, bm25_retriever, dense_retriever
    try:
        chunks = doc_ingestion.ingest_file(str(filepath), metadata={"original_filename": req.filename})
        bm25_retriever.index_documents(doc_ingestion._store.chunks)
        if dense_retriever:
            dense_retriever.index_documents(doc_ingestion._store.chunks)
    except ValueError as e:
        _os.remove(filepath)
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": f"Document uploaded successfully", "filename": req.filename, "chunks": len(chunks)}
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    ext = _Path(file.filename).suffix.lower()
    if ext not in _SUPPORTED:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    safe_name = _uuid.uuid4().hex + ext
    filepath = _UPLOAD_DIR / safe_name
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    from app.main import doc_ingestion, bm25_retriever, dense_retriever
    try:
        chunks = doc_ingestion.ingest_file(str(filepath), metadata={"original_filename": req.filename})
        bm25_retriever.index_documents(doc_ingestion._store.chunks)
        if dense_retriever:
            dense_retriever.index_documents(doc_ingestion._store.chunks)
    except ValueError as e:
        _os.remove(filepath)
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": f"Document uploaded successfully", "filename": file.filename, "chunks": len(chunks)}

@router.get("/documents")
async def list_documents():
    from app.main import doc_ingestion
    docs = doc_ingestion._store.get_all_documents()
    return {"total": len(docs), "documents": [{"id": d.id, "source": d.source or "unknown", "created_at": d.created_at.isoformat(), "size": len(d.content)} for d in docs]}

@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    from app.main import doc_ingestion, bm25_retriever, dense_retriever
    store = doc_ingestion._store
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404)
    store._chunks = [c for c in store._chunks if c.document_id != doc_id]
    del store._documents[doc_id]
    bm25_retriever.index_documents(store.chunks)
    return {"message": "deleted"}
