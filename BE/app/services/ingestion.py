import uuid
import re
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException

from app.db.database import get_db_connection
from app.services.splitter import text_splitter_service
from app.services.embeddings import embedding_service
from app.services.vector_store import vector_store
from app.services.document_queue import document_store_queue
from app.logger import logger

class IngestionService:
    @staticmethod
    async def fetch_url_content(url: str) -> Dict[str, str]:
        """
        Server-side URL content fetching and HTML sanitization.
        Extracts clean title and textual body without script/nav clutter.
        """
        # Validate URL scheme
        parsed = urlparse(url)
        if not parsed.scheme or parsed.scheme not in ("http", "https"):
            raise HTTPException(status_code=400, detail="Invalid URL scheme. Must start with http:// or https://")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
                response = await client.get(url)
                if response.status_code >= 400:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to fetch URL. Upstream server returned HTTP {response.status_code}."
                    )
                html = response.text
        except httpx.RequestError as e:
            logger.error(f"Network error fetching URL {url}: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Could not reach external URL: {str(e)}"
            )

        # Parse and sanitize HTML
        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.find("meta", property="og:title"):
            title = soup.find("meta", property="og:title").get("content", "").strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text().strip()
        
        if not title:
            title = parsed.netloc + parsed.path

        # Strip noise elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg", "form"]):
            element.decompose()

        # Extract textual content
        text_lines = []
        for p in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "pre"]):
            t = p.get_text().strip()
            if t:
                text_lines.append(t)

        clean_text = "\n\n".join(text_lines)
        if not clean_text or len(clean_text) < 30:
            # Fallback to general stripped text
            clean_text = soup.get_text(separator="\n", strip=True)

        # Collapse excessive newlines
        clean_text = re.sub(r'\n{3,}', '\n\n', clean_text).strip()

        if not clean_text:
            raise HTTPException(
                status_code=422,
                detail="Unable to extract meaningful text content from the provided URL."
            )

        return {
            "title": title[:200],
            "content": clean_text
        }

    async def ingest_content(
        self,
        source_type: str,
        content: str,
        title: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Unified ingestion pipeline:
        1. Validates and extracts content (plain note or server-fetched URL)
        2. Splits content into semantic chunks using the Unstructured text splitter with custom chunk_size/overlap
        3. Computes vector embeddings
        4. Enqueues and atomically stores item and chunks in SQLite via Async Queue
        """
        item_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat() + "Z"
        url: Optional[str] = None
        raw_text: str = ""
        resolved_title: str = ""

        if source_type == "url":
            url = content.strip()
            fetched = await self.fetch_url_content(url)
            raw_text = fetched["content"]
            resolved_title = title.strip() if title and title.strip() else fetched["title"]
        elif source_type == "note":
            raw_text = content.strip()
            if not raw_text:
                raise HTTPException(status_code=400, detail="Note content cannot be empty.")
            if title and title.strip():
                resolved_title = title.strip()
            else:
                # Derive title from first line or timestamp
                first_line = raw_text.split("\n")[0][:60].strip()
                resolved_title = first_line if first_line else f"Note ({datetime.utcnow().strftime('%Y-%m-%d %H:%M')})"
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported source type '{source_type}'. Allowed types: 'note', 'url'"
            )

        # 1. Text Splitting via Unstructured Text Splitter (with optional custom chunk size & overlap)
        metadata = {
            "item_id": item_id,
            "source_type": source_type,
            "title": resolved_title,
            "url": url
        }
        chunks = text_splitter_service.split_text(
            raw_text,
            metadata=metadata,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        if not chunks:
            raise HTTPException(status_code=422, detail="Text splitting resulted in zero chunks.")

        # 2. Embedding Generation
        chunk_texts = [c.page_content for c in chunks]
        embeddings = embedding_service.embed_documents(chunk_texts)

        # 3. Async Queue-Backed Document & Vector Chunk Store (SQLite)
        result = await document_store_queue.store_document(
            item_id=item_id,
            source_type=source_type,
            title=resolved_title,
            content=raw_text,
            url=url,
            chunks=chunks,
            embeddings=embeddings,
            created_at=created_at
        )

        logger.info(
            f"Successfully ingested {source_type} via Async Queue (id={item_id}, title='{resolved_title}', "
            f"chunks={len(chunks)}, chars={len(raw_text)})"
        )

        return result

ingestion_service = IngestionService()
