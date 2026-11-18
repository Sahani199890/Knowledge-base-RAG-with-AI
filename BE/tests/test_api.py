import os
import pytest
from fastapi.testclient import TestClient

# Ensure test DB is used
os.environ["DATABASE_PATH"] = "test_knowledge_inbox.db"

from app.main import app
from app.db.database import init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists("test_knowledge_inbox.db"):
        os.remove("test_knowledge_inbox.db")
    init_db()
    yield
    if os.path.exists("test_knowledge_inbox.db"):
        try:
            os.remove("test_knowledge_inbox.db")
        except Exception:
            pass

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "embedding_provider" in data

def test_ingest_note_and_query():
    # 1. Ingest a note
    note_content = (
        "Project Apollo was the third United States human spaceflight program carried out by NASA. "
        "It succeeded in landing the first humans on the Moon in 1969 with Neil Armstrong and Buzz Aldrin. "
        "The Apollo program used Saturn V rockets to launch the missions."
    )
    ingest_res = client.post("/ingest", json={
        "type": "note",
        "title": "Apollo Program History",
        "content": note_content
    })
    assert ingest_res.status_code == 201
    item = ingest_res.json()
    assert item["title"] == "Apollo Program History"
    assert item["type"] == "note"
    assert item["chunk_count"] >= 1
    item_id = item["id"]

    # 2. Verify in /items
    items_res = client.get("/items")
    assert items_res.status_code == 200
    items = items_res.json()
    assert len(items) == 1
    assert items[0]["id"] == item_id

    # 3. Query the RAG inbox
    query_res = client.post("/query", json={
        "question": "Who were the first humans to land on the Moon?",
        "top_k": 3
    })
    assert query_res.status_code == 200
    q_data = query_res.json()
    assert len(q_data["sources"]) >= 1
    assert "sources" in q_data
    assert "answer" in q_data
    assert q_data["sources"][0]["title"] == "Apollo Program History"

    # 4. Delete item
    del_res = client.delete(f"/items/{item_id}")
    assert del_res.status_code == 200

    # 5. Verify deleted
    items_after = client.get("/items").json()
    assert len(items_after) == 0

def test_invalid_ingest_type():
    res = client.post("/ingest", json={
        "type": "unsupported_type",
        "content": "test"
    })
    assert res.status_code == 422

def test_empty_content_validation():
    res = client.post("/ingest", json={
        "type": "note",
        "content": ""
    })
    assert res.status_code == 422
