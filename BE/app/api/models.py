from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class IngestRequest(BaseModel):
    type: Literal["note", "url"] = Field(
        ...,
        description="The source type of content to ingest: 'note' for raw text or 'url' for web links."
    )
    content: str = Field(
        ...,
        min_length=1,
        description="The content to ingest (raw text for notes, or full HTTP/HTTPS URL for web pages)."
    )
    title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional human-readable title. Automatically derived if omitted."
    )
    chunk_size: Optional[int] = Field(
        default=None,
        ge=50,
        le=5000,
        description="Custom chunk size in characters."
    )
    chunk_overlap: Optional[int] = Field(
        default=None,
        ge=0,
        le=1500,
        description="Custom chunk overlap in characters."
    )

class IngestResponse(BaseModel):
    id: str
    type: str
    title: str
    url: Optional[str] = None
    chunk_count: int
    content_length: int
    created_at: str
    preview: str

class ItemResponse(BaseModel):
    id: str
    type: str
    title: str
    content: str
    url: Optional[str] = None
    chunk_count: int
    created_at: str

class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="User's natural language question over saved knowledge."
    )
    top_k: Optional[int] = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of top relevant chunks to retrieve."
    )

class SourceCitation(BaseModel):
    source_num: int
    chunk_id: str
    item_id: str
    title: str
    source_type: str
    url: Optional[str] = None
    similarity_score: float
    snippet: str
    chunk_index: int

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    question: str
    llm_used: str

class HealthResponse(BaseModel):
    status: str
    app: str
    total_items: int
    total_chunks: int
    embedding_provider: str
    splitter_type: str
    queue_status: Optional[str] = "active"
    queue_metrics: Optional[dict] = None
