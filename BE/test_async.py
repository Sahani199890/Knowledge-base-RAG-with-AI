import asyncio
import os
import sys

be_dir = os.path.dirname(os.path.abspath(__file__))
if be_dir not in sys.path:
    sys.path.insert(0, be_dir)

import httpx
from app.main import app
from app.db.database import init_db

async def main():
    print("Initializing test DB...")
    init_db()
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("GET /health:")
        r = await client.get("/health")
        print("Status:", r.status_code)
        print("Body:", r.json())

        print("\nPOST /ingest note:")
        r2 = await client.post("/ingest", json={
            "type": "note",
            "title": "Unstructured RAG Demo",
            "content": "Retrieval Augmented Generation combines semantic search with generative language models. By using LangChain with an unstructured text splitter, long documents are decomposed into semantic chunks for vector similarity retrieval."
        })
        print("Status:", r2.status_code)
        data = r2.json()
        print("Body:", data)
        item_id = data["id"]

        print("\nGET /items:")
        r3 = await client.get("/items")
        print("Status:", r3.status_code)
        print("Items count:", len(r3.json()))

        print("\nPOST /query:")
        r4 = await client.post("/query", json={
            "question": "How does text splitting work in RAG?",
            "top_k": 3
        })
        print("Status:", r4.status_code)
        q_res = r4.json()
        print("Answer:", q_res["answer"])
        print("Sources:", len(q_res["sources"]))

        print("\nDELETE /items:")
        r5 = await client.delete(f"/items/{item_id}")
        print("Status:", r5.status_code)
        print("Delete:", r5.json())

if __name__ == "__main__":
    asyncio.run(main())
