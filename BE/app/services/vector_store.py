import json
import uuid
import math
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from app.db.database import get_db_connection
from app.logger import logger

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if len(v1) != len(v2) or not v1:
        return 0.0
    dot = 0.0
    norm1 = 0.0
    norm2 = 0.0
    for a, b in zip(v1, v2):
        dot += a * b
        norm1 += a * a
        norm2 += b * b
    if norm1 <= 0 or norm2 <= 0:
        return 0.0
    return dot / (math.sqrt(norm1) * math.sqrt(norm2))

class SQLiteVectorStore:
    """
    Lightweight, persistent SQLite-backed vector store.
    Stores unstructured text chunks, their embeddings, and metadata.
    Performs cosine similarity search directly against stored vectors.
    """

    def add_chunks(
        self,
        item_id: str,
        chunks: List[Document],
        embeddings: List[List[float]]
    ) -> int:
        if not chunks or not embeddings:
            return 0

        with get_db_connection() as conn:
            cursor = conn.cursor()
            for idx, (doc, emb) in enumerate(zip(chunks, embeddings)):
                chunk_id = str(uuid.uuid4())
                emb_json = json.dumps(emb)
                meta_json = json.dumps(doc.metadata or {})
                cursor.execute(
                    """
                    INSERT INTO chunks (id, item_id, chunk_index, content, embedding_json, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (chunk_id, item_id, idx, doc.page_content, emb_json, meta_json)
                )

            # Update chunk_count in items table
            cursor.execute(
                "UPDATE items SET chunk_count = ? WHERE id = ?",
                (len(chunks), item_id)
            )

        logger.info(f"Persisted {len(chunks)} chunks for item {item_id}")
        return len(chunks)

    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 3,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top_k relevant chunks with associated item metadata.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    c.id AS chunk_id,
                    c.item_id,
                    c.chunk_index,
                    c.content,
                    c.embedding_json,
                    c.metadata_json,
                    i.title AS item_title,
                    i.type AS item_type,
                    i.url AS item_url,
                    i.created_at AS item_created_at
                FROM chunks c
                JOIN items i ON c.item_id = i.id
            """)
            rows = cursor.fetchall()

        results = []
        for row in rows:
            try:
                emb = json.loads(row["embedding_json"])
                score = cosine_similarity(query_embedding, emb)
                if score >= min_score:
                    meta = {}
                    if row["metadata_json"]:
                        try:
                            meta = json.loads(row["metadata_json"])
                        except Exception:
                            meta = {}
                    
                    results.append({
                        "chunk_id": row["chunk_id"],
                        "item_id": row["item_id"],
                        "chunk_index": row["chunk_index"],
                        "content": row["content"],
                        "item_title": row["item_title"],
                        "item_type": row["item_type"],
                        "item_url": row["item_url"],
                        "item_created_at": row["item_created_at"],
                        "score": round(float(score), 4),
                        "metadata": meta
                    })
            except Exception as e:
                logger.error(f"Error calculating similarity for chunk {row['chunk_id']}: {e}")

        # Sort descending by similarity score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def delete_item_chunks(self, item_id: str) -> int:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chunks WHERE item_id = ?", (item_id,))
            deleted = cursor.rowcount
        return deleted

    def get_total_chunks(self) -> int:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM chunks")
            return cursor.fetchone()[0]

vector_store = SQLiteVectorStore()
