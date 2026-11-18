import os
import sys
from dotenv import load_dotenv

# Add Turium AI/BE to sys.path
be_dir = os.path.dirname(os.path.abspath(__file__))
if be_dir not in sys.path:
    sys.path.insert(0, be_dir)

test_db_path = os.path.join(be_dir, "test_knowledge_inbox.db")
os.environ["DATABASE_PATH"] = test_db_path

load_dotenv(os.path.join(be_dir, ".env"), override=False)

from fastapi.testclient import TestClient
from app.config import settings
settings.DATABASE_PATH = test_db_path
from app.main import app
from app.db.database import init_db

def run_all_tests():
    print("=== Starting Knowledge Inbox Backend Verification ===")
    test_db = os.environ["DATABASE_PATH"]
    if os.path.exists(test_db):
        os.remove(test_db)
    init_db()

    client = TestClient(app)

    # 1. Health Check
    print("Testing GET /health...")
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    health_data = res.json()
    print(f" Health check passed: {health_data}")

    # 2. Ingest Note
    print("\nTesting POST /ingest (note)...")
    sample_text = (
        "LangChain is a framework designed to simplify the creation of applications using large language models. "
        "It provides standard interfaces for chains, agents, and retrieval-augmented generation (RAG). "
        "Text splitting is essential in RAG to partition unstructured documents into manageable chunks."
    )
    res = client.post("/ingest", json={
        "type": "note",
        "title": "Introduction to LangChain & RAG",
        "content": sample_text
    })
    assert res.status_code == 201, f"Ingest note failed: {res.text}"
    ingested = res.json()
    item_id = ingested["id"]
    print(f" Note ingested successfully: id={item_id}, chunks={ingested['chunk_count']}")

    # 3. List Items
    print("\nTesting GET /items...")
    res = client.get("/items")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["id"] == item_id
    print(f" List items verified. Total items: {len(items)}")

    # 4. RAG Query
    print("\nTesting POST /query (RAG pipeline)...")
    res = client.post("/query", json={
        "question": "What is LangChain and why is text splitting essential?",
        "top_k": 3
    })
    assert res.status_code == 200, f"Query failed: {res.text}"
    q_data = res.json()
    print(f" RAG Query Answer: {q_data['answer']}")
    print(f" Cited Sources count: {len(q_data['sources'])}")
    assert len(q_data["sources"]) > 0
    assert q_data["sources"][0]["item_id"] == item_id
    print(f" Top cited source: {q_data['sources'][0]['title']} (Score: {q_data['sources'][0]['similarity_score']}%)")

    # 5. Delete Item
    print("\nTesting DELETE /items/{id}...")
    res = client.delete(f"/items/{item_id}")
    assert res.status_code == 200
    items_after = client.get("/items").json()
    assert len(items_after) == 0
    print(" Item deleted and cascade confirmed.")

    # Clean up test DB
    if os.path.exists(test_db):
        os.remove(test_db)

    print("\n=== All Backend Verification Tests Passed Successfully! ===")

if __name__ == "__main__":
    run_all_tests()
