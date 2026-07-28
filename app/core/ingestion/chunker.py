import re
from typing import List

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break
        # Try to break at paragraph or sentence boundary
        chunk = text[start:end]
        last_period = chunk.rfind('.')
        last_newline = chunk.rfind('\n')
        break_point = max(last_period + 1 if last_period > chunk_size//2 else 0,
                         last_newline + 1 if last_newline > chunk_size//2 else 0)
        if break_point > 0:
            chunks.append(text[start:start + break_point])
            start = start + break_point
        else:
            chunks.append(chunk)
            start = end
    # Apply overlap
    if overlap > 0 and len(chunks) > 1:
        result = [chunks[0]]
        for i in range(1, len(chunks)):
            prev = result[-1]
            overlap_text = prev[-overlap:] if len(prev) > overlap else prev
            result.append(overlap_text + chunks[i])
        return result
    return chunks
