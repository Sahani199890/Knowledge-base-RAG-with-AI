from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings
from app.logger import logger

class UnstructuredTextSplitterService:
    """
    RAG Text Splitter tailored for unstructured content (raw notes, scraped web pages, articles).
    Employs LangChain's RecursiveCharacterTextSplitter with hierarchical semantic boundaries,
    plus integration with unstructured partition chunking where applicable.
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        splitter_type: Optional[str] = None
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.splitter_type = splitter_type or settings.SPLITTER_TYPE

        # Recursive splitter configured specifically for unstructured text documents
        # Priority: Paragraphs -> Newlines -> Sentence boundaries -> Word spaces -> Characters
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", "; ", " ", ""],
            is_separator_regex=False
        )

    def split_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[Document]:
        """
        Splits raw unstructured text into optimal semantic chunks with attached metadata.
        Accepts dynamic chunk_size and chunk_overlap provided by the caller/frontend.
        """
        clean_text = (text or "").strip()
        if not clean_text:
            return []

        c_size = chunk_size or self.chunk_size
        c_overlap = chunk_overlap if chunk_overlap is not None else self.chunk_overlap
        # Ensure overlap is strictly less than chunk_size
        if c_overlap >= c_size:
            c_overlap = max(0, c_size // 4)

        base_meta = metadata or {}

        # Primary: Unstructured document partition and chunking
        if self.splitter_type in ("unstructured", "unstructured_elements"):
            try:
                from unstructured.partition.text import partition_text
                from unstructured.chunking.basic import chunk_elements

                elements = partition_text(text=clean_text)
                chunked_elements = chunk_elements(
                    elements,
                    max_characters=c_size,
                    overlap=c_overlap
                )
                
                docs = []
                for idx, elem in enumerate(chunked_elements):
                    chunk_text = str(elem).strip()
                    if chunk_text:
                        doc_meta = {
                            **base_meta,
                            "chunk_index": idx,
                            "chunk_type": elem.category if hasattr(elem, "category") else "unstructured_element",
                            "char_count": len(chunk_text),
                            "chunk_size": c_size,
                            "chunk_overlap": c_overlap,
                            "splitter": "unstructured_partition_chunker"
                        }
                        docs.append(Document(page_content=chunk_text, metadata=doc_meta))
                
                if docs:
                    logger.info(
                        f"Split text using Unstructured Document Chunker into {len(docs)} chunks "
                        f"(max_chars={c_size}, overlap={c_overlap})"
                    )
                    return docs
            except Exception as e:
                logger.warning(f"Unstructured partitioning encountered ({e}), falling back to recursive character splitter.")

        # Fallback: LangChain Recursive Character Text Splitter
        fallback_splitter = RecursiveCharacterTextSplitter(
            chunk_size=c_size,
            chunk_overlap=c_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", "; ", " ", ""],
            is_separator_regex=False
        )
        raw_chunks = fallback_splitter.split_text(clean_text)
        docs: List[Document] = []
        start_char = 0

        for idx, chunk_str in enumerate(raw_chunks):
            chunk_content = chunk_str.strip()
            if not chunk_content:
                continue

            found_idx = clean_text.find(chunk_content[:30], start_char)
            if found_idx != -1:
                start_char = found_idx

            doc_meta = {
                **base_meta,
                "chunk_index": idx,
                "char_count": len(chunk_content),
                "chunk_size": c_size,
                "chunk_overlap": c_overlap,
                "start_char": start_char,
                "splitter": "langchain_recursive_unstructured"
            }
            docs.append(Document(page_content=chunk_content, metadata=doc_meta))

        logger.info(
            f"Split unstructured text ({len(clean_text)} chars) into {len(docs)} chunks "
            f"(chunk_size={c_size}, overlap={c_overlap})"
        )
        return docs

# Shared singleton instance
text_splitter_service = UnstructuredTextSplitterService()
