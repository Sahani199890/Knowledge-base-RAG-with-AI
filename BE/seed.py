import asyncio
import os
import sys

be_dir = os.path.dirname(os.path.abspath(__file__))
if be_dir not in sys.path:
    sys.path.insert(0, be_dir)

from app.db.database import init_db
from app.services.ingestion import ingestion_service

async def seed():
    init_db()
    print("Seeding sample items...")
    
    # Note 1
    await ingestion_service.ingest_content(
        source_type="note",
        title="LangChain & Unstructured RAG Pipeline",
        content=(
            "LangChain enables modular LLM application development. In Retrieval-Augmented Generation (RAG), "
            "chunking unstructured text using RecursiveCharacterTextSplitter maintains paragraph and sentence coherence. "
            "The splitter cascades through separators to prevent truncation of critical conceptual boundaries."
        )
    )
    
    # Note 2
    await ingestion_service.ingest_content(
        source_type="note",
        title="Turium AI Knowledge Inbox Architecture",
        content=(
            "The AI Knowledge Inbox uses a lightweight SQLite vector store storing chunk vectors as serialized dense "
            "embeddings with cosine similarity search. This eliminates external vector database infrastructure requirements "
            "while preserving persistence across server restarts."
        )
    )
    print("Database seeded with sample knowledge successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
