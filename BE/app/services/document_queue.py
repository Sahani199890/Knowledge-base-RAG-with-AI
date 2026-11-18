import asyncio
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from langchain_core.documents import Document

from app.db.database import get_db_connection
from app.logger import logger

@dataclass
class DocumentStoreTask:
    task_id: str
    item_id: str
    source_type: str
    title: str
    content: str
    url: Optional[str]
    chunks: List[Document]
    embeddings: List[List[float]]
    created_at: str
    future: Optional[asyncio.Future] = None
    status: str = "queued"

class AsyncDocumentStoreQueue:
    """
    Asynchronous Document Store & Ingestion Queue for the SQLite Vector Database.
    Serializes write operations to SQLite, ensuring concurrency safety and
    non-blocking async ingestion for chunk and vector persistence.
    """

    def __init__(self):
        self._queue: Optional[asyncio.Queue] = None
        self._worker_task: Optional[asyncio.Task] = None
        self._is_running: bool = False
        self.processed_count: int = 0
        self.failed_count: int = 0

    @property
    def queue(self) -> asyncio.Queue:
        if self._queue is None:
            self._queue = asyncio.Queue()
        return self._queue

    def _ensure_worker(self):
        """Ensures the background queue worker is running in the active event loop."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        if self._worker_task is None or self._worker_task.done():
            self._is_running = True
            self._worker_task = loop.create_task(self._worker())
            logger.info("Async document store queue worker started.")

    async def start(self):
        """Explicitly starts the queue worker (called during FastAPI lifespan)."""
        self._ensure_worker()

    async def stop(self):
        """Gracefully stops the worker."""
        self._is_running = False
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            logger.info("Async document store queue worker stopped.")

    def _sync_store_in_db(self, task: DocumentStoreTask) -> int:
        """
        Synchronous transaction writing the item and its vector chunks into SQLite.
        Runs inside asyncio.to_thread to keep the event loop non-blocking.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 1. Store / Update Parent Item in items table
            cursor.execute(
                """
                INSERT OR REPLACE INTO items (id, type, title, content, url, chunk_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.item_id,
                    task.source_type,
                    task.title,
                    task.content,
                    task.url,
                    len(task.chunks),
                    task.created_at
                )
            )

            # 2. Store all vector chunks in chunks table
            for idx, (doc, emb) in enumerate(zip(task.chunks, task.embeddings)):
                chunk_id = str(uuid.uuid4())
                emb_json = json.dumps(emb)
                meta_json = json.dumps(doc.metadata or {})
                cursor.execute(
                    """
                    INSERT INTO chunks (id, item_id, chunk_index, content, embedding_json, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (chunk_id, task.item_id, idx, doc.page_content, emb_json, meta_json)
                )

        return len(task.chunks)

    async def _worker(self):
        """Background worker that continuously pulls and processes document store tasks."""
        logger.info("Async Document Store Worker loop active.")
        while self._is_running:
            try:
                task: DocumentStoreTask = await self.queue.get()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error reading from document queue: {e}")
                continue

            try:
                task.status = "processing"
                logger.debug(f"Worker dequeued task {task.task_id} for item {task.item_id} ({len(task.chunks)} chunks)")

                # Execute SQLite transaction off the main event loop thread
                chunk_count = await asyncio.to_thread(self._sync_store_in_db, task)

                task.status = "completed"
                self.processed_count += 1
                logger.info(
                    f"Async Document Queue successfully stored item {task.item_id} "
                    f"with {chunk_count} vector chunks (total processed: {self.processed_count})"
                )

                if task.future and not task.future.done():
                    result_data = {
                        "id": task.item_id,
                        "type": task.source_type,
                        "title": task.title,
                        "url": task.url,
                        "chunk_count": chunk_count,
                        "content_length": len(task.content),
                        "created_at": task.created_at,
                        "preview": task.content[:200] + ("..." if len(task.content) > 200 else "")
                    }
                    task.future.set_result(result_data)

            except Exception as e:
                task.status = "failed"
                self.failed_count += 1
                logger.error(f"Failed to store document {task.item_id} via async queue: {e}", exc_info=True)
                if task.future and not task.future.done():
                    task.future.set_exception(e)
            finally:
                self.queue.task_done()

    async def store_document(
        self,
        item_id: str,
        source_type: str,
        title: str,
        content: str,
        url: Optional[str],
        chunks: List[Document],
        embeddings: List[List[float]],
        created_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enqueues a document and its vector embeddings to the async queue,
        awaiting completion non-blockingly without holding database locks.
        """
        self._ensure_worker()
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        task = DocumentStoreTask(
            task_id=str(uuid.uuid4())[:8],
            item_id=item_id,
            source_type=source_type,
            title=title,
            content=content,
            url=url,
            chunks=chunks,
            embeddings=embeddings,
            created_at=created_at or (datetime.utcnow().isoformat() + "Z"),
            future=future,
            status="queued"
        )

        logger.info(f"Enqueued document store task {task.task_id} for item {item_id} (queue size: {self.queue.qsize() + 1})")
        await self.queue.put(task)

        # Non-blocking wait for background queue worker to commit transaction
        return await future

    def get_metrics(self) -> Dict[str, Any]:
        """Returns live async queue operational metrics."""
        return {
            "queue_size": self.queue.qsize() if self._queue is not None else 0,
            "is_running": self._is_running,
            "processed_count": self.processed_count,
            "failed_count": self.failed_count
        }

# Global singleton queue instance
document_store_queue = AsyncDocumentStoreQueue()
