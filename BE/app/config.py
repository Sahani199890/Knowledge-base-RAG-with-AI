import os
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH: str = os.path.join(BASE_DIR, ".env")

# Load environment variables from .env file using python-dotenv
# Checks both the backend directory and the project root directory
if os.path.exists(ENV_PATH):
    load_dotenv(dotenv_path=ENV_PATH, override=False)
else:
    load_dotenv(override=False)

class Settings(BaseSettings):
    APP_NAME: str = "Turium AI Knowledge Inbox"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database - Absolute path to ensure consistency regardless of execution directory
    DATABASE_PATH: str = os.path.join(BASE_DIR, "knowledge_inbox.db")

    # LLM & RAG Configuration
    # Uses Groq / OpenAI LLM strictly grounded on retrieved RAG database chunks
    USE_EXTERNAL_LLM: bool = True
    
    # Optional External LLMs (only used if USE_EXTERNAL_LLM is True)
    OPENAI_API_KEY: Optional[str] = None
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    LLM_MODEL: str = "gpt-4o-mini"
    
    # Groq Configuration (Ultra-fast free/low-cost LLM)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    
    # RAG / Text Splitter Parameters
    # Using unstructured document chunking parameters
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 80
    DEFAULT_TOP_K: int = 3
    
    # Text splitter type: "unstructured" (primary) or "recursive_fallback"
    SPLITTER_TYPE: str = "unstructured"

    class Config:
        env_file = (ENV_PATH, ".env")
        extra = "ignore"

settings = Settings()
