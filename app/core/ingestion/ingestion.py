import os
import uuid
import time
from pathlib import Path
from typing import Optional
from app.core.ingestion.parser import extract_text, SUPPORTED_EXTENSIONS
from app.core.ingestion.chunker import chunk_text
from app.models.document import Document, DocumentChunk


class DocumentStore:
    def __init__(self):
        self._documents: dict[str, Document] = {}
        self._chunks: list[DocumentChunk] = []

    @property
    def chunks(self) -> list[DocumentChunk]:
        return self._chunks

    def get_document(self, doc_id: str) -> Optional[Document]:
        return self._documents.get(doc_id)

    def get_all_documents(self) -> list[Document]:
        return list(self._documents.values())

    def add_document(self, doc: Document):
        self._documents[doc.id] = doc

    def add_chunks(self, chunks: list[DocumentChunk]):
        self._chunks.extend(chunks)

    def clear(self):
        self._documents.clear()
        self._chunks.clear()


class DocumentIngestion:
    def __init__(self, document_store: DocumentStore):
        self._store = document_store

    def ingest_file(self, filepath: str, metadata: dict = None) -> list[DocumentChunk]:
        filename = Path(filepath).name
        ext = Path(filepath).suffix.lower()

        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(f'Unsupported file type: {ext}. Supported: {SUPPORTED_EXTENSIONS}')

        text = extract_text(filepath)
        if not text.strip():
            raise ValueError(f'No text content found in {filename}')

        original_name = (metadata or {}).get("original_filename", filename)
        doc = Document(
            content=text,
            source=original_name,
            metadata={
                **(metadata or {}),
                'filename': filename,
                'filepath': filepath,
                'size_bytes': os.path.getsize(filepath),
            }
        )
        self._store.add_document(doc)

        raw_chunks = chunk_text(text)
        chunks = []
        for i, chunk_content in enumerate(raw_chunks):
            chunk = DocumentChunk(
                document_id=doc.id,
                content=chunk_content,
                chunk_index=i,
                metadata={
                    'source': filename,
                    'chunk': i + 1,
                    'total_chunks': len(raw_chunks),
                }
            )
            chunks.append(chunk)

        self._store.add_chunks(chunks)
        return chunks
