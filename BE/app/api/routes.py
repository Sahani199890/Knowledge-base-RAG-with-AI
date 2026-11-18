from typing import List
from fastapi import APIRouter, HTTPException, status
from app.api.models import (
    IngestRequest,
    IngestResponse,
    ItemResponse,
    QueryRequest,
    QueryResponse,
    HealthResponse
)
from app.services.ingestion import ingestion_service
from app.services.rag import rag_service
from app.services.embeddings import embedding_service
from app.services.vector_store import vector_store
from app.services.document_queue import document_store_queue
from app.db.database import get_db_connection
from app.config import settings
from app.logger import logger

router = APIRouter()

@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest note or URL",
    description="Saves a raw text note or server-fetches a web URL, splits text using the Unstructured splitter, computes embeddings, and stores it in SQLite."
)
async def ingest_content(request: IngestRequest):
    try:
        result = await ingestion_service.ingest_content(
            source_type=request.type,
            content=request.content,
            title=request.title,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )
        return IngestResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during ingestion: {str(e)}"
        )

@router.get(
    "/items",
    response_model=List[ItemResponse],
    summary="List saved knowledge items",
    description="Retrieves all stored notes and URLs ordered by creation date descending."
)
async def get_items():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, type, title, 
                       CASE 
                           WHEN length(content) > 300 THEN substr(content, 1, 300) || '...'
                           ELSE content 
                       END AS content, 
                       url, chunk_count, created_at
                FROM items
                ORDER BY created_at DESC
                """
            )
            rows = cursor.fetchall()
            
        items = [
            ItemResponse(
                id=row["id"],
                type=row["type"],
                title=row["title"],
                content=row["content"],
                url=row["url"],
                chunk_count=row["chunk_count"],
                created_at=row["created_at"]
            )
            for row in rows
        ]
        return items
    except Exception as e:
        logger.error(f"Failed to fetch items: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve items from database."
        )

@router.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    summary="Get single knowledge item"
)
async def get_item(item_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, type, title, content, url, chunk_count, created_at
            FROM items
            WHERE id = ?
            """,
            (item_id,)
        )
        row = cursor.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id '{item_id}' not found."
        )

    return ItemResponse(
        id=row["id"],
        type=row["type"],
        title=row["title"],
        content=row["content"],
        url=row["url"],
        chunk_count=row["chunk_count"],
        created_at=row["created_at"]
    )

@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a knowledge item and its chunks"
)
async def delete_item(item_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM items WHERE id = ?", (item_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id '{item_id}' not found."
            )
        # Foreign key cascade automatically removes associated chunks
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))

    logger.info(f"Deleted item and associated chunks: {item_id}")
    return {"message": f"Item '{item_id}' and all associated vector chunks deleted successfully."}

@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Ask a question over saved knowledge",
    description="Performs semantic search against vector chunks and generates an answer citing specific sources."
)
async def query_knowledge(request: QueryRequest):
    try:
        response = await rag_service.query(
            question=request.question,
            top_k=request.top_k
        )
        return QueryResponse(**response)
    except Exception as e:
        logger.error(f"Query execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while answering the query: {str(e)}"
        )

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check & system telemetry"
)
async def health_check():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM items")
        total_items = cursor.fetchone()[0]

    total_chunks = vector_store.get_total_chunks()
    provider = embedding_service.get_provider_name()
    q_metrics = document_store_queue.get_metrics()

    return HealthResponse(
        status="healthy",
        app=settings.APP_NAME,
        total_items=total_items,
        total_chunks=total_chunks,
        embedding_provider=provider,
        splitter_type=settings.SPLITTER_TYPE,
        queue_status="active" if q_metrics.get("is_running") else "idle",
        queue_metrics=q_metrics
    )
