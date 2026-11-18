import os
from typing import List, Dict, Any, Optional
from app.config import settings
from app.services.embeddings import embedding_service
from app.services.vector_store import vector_store
from app.logger import logger

class RAGService:
    def __init__(self):
        self._llm = None
        self._provider_label = "RAG Database Engine (No External LLM)"
        self._init_llm()

    def _init_llm(self):
        # If external LLM is disabled, answer strictly from RAG database chunks
        if not getattr(settings, "USE_EXTERNAL_LLM", False):
            self._llm = None
            self._provider_label = "RAG Database Engine (No External LLM)"
            return

        groq_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        openai_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")

        # 1. Check for Groq API Key first (fast, free/cheap Llama-3 models)
        if groq_key and groq_key.strip() and not groq_key.startswith("your-"):
            try:
                from langchain_openai import ChatOpenAI
                self._llm = ChatOpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=groq_key.strip(),
                    model=settings.GROQ_MODEL,
                    temperature=0.2
                )
                self._provider_label = f"Groq ({settings.GROQ_MODEL})"
                logger.info(f"Initialized Groq LLM with model: {settings.GROQ_MODEL}")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize Groq LLM: {e}")

        # 2. Check for OpenAI API Key
        if openai_key and openai_key.strip() and not openai_key.startswith("your-"):
            try:
                from langchain_openai import ChatOpenAI
                self._llm = ChatOpenAI(
                    model=settings.LLM_MODEL,
                    temperature=0.2,
                    api_key=openai_key.strip()
                )
                self._provider_label = f"OpenAI ({settings.LLM_MODEL})"
                logger.info(f"Initialized ChatOpenAI with model: {settings.LLM_MODEL}")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize ChatOpenAI: {e}")

        # 3. Default fallback
        self._llm = None
        self._provider_label = "RAG Database Engine (No External LLM)"

    def _generate_extractive_answer(self, question: str, sources: List[Dict[str, Any]]) -> str:
        """
        Grounded RAG synthesis engine: extracts and synthesizes answers directly from
        retrieved SQLite vector database chunks with zero external LLM calls.
        """
        # Stopwords to filter out for keyword scoring
        stopwords = {
            "what", "whats", "what's", "is", "are", "was", "were", "the", "a", "an",
            "and", "or", "in", "on", "at", "by", "for", "with", "about", "to", "from",
            "of", "how", "can", "could", "would", "should", "tell", "me", "give", "you",
            "your", "my", "our", "do", "does", "did", "this", "that", "these", "those"
        }
        
        q_tokens = [w.lower().strip("?,!.:;'\"") for w in question.split()]
        q_keywords = [w for w in q_tokens if len(w) > 2 and w not in stopwords]
        if not q_keywords:
            q_keywords = [w for w in q_tokens if len(w) > 1]

        extracted_insights: List[str] = []
        best_overall_sentence = ""
        best_overall_score = -1
        best_source_idx = 1

        for idx, src in enumerate(sources, 1):
            text_chunk = src.get("snippet") or src.get("content") or ""
            title = src.get("title", "Saved Item")
            
            # Split into natural sentences
            raw_sentences = [
                s.strip() for s in text_chunk.replace("\n", " ").split(". ")
                if len(s.strip()) > 15
            ]

            scored_sentences = []
            for s in raw_sentences:
                s_lower = s.lower()
                # Keyword overlap score
                kw_matches = sum(1 for kw in q_keywords if kw in s_lower)
                # Boost if phrase or multiple keywords match
                score = kw_matches * 10
                if len(s) > 40:
                    score += 2  # slight preference for substantive sentences
                scored_sentences.append((score, s))

            scored_sentences.sort(key=lambda x: x[0], reverse=True)

            if scored_sentences:
                top_score, top_sentence = scored_sentences[0]
                if top_score > best_overall_score:
                    best_overall_score = top_score
                    best_overall_sentence = top_sentence
                    best_source_idx = idx

                # Collect informative sentences for bullet points
                for sc, st in scored_sentences[:2]:
                    clean_st = st.strip(". ")
                    bullet = f"• {clean_st} [Source {idx}: {title}]."
                    if bullet not in extracted_insights:
                        extracted_insights.append(bullet)

        if not best_overall_sentence and sources:
            # Fallback to the opening sentence of top matching chunk
            first_chunk = sources[0].get("snippet") or ""
            best_overall_sentence = first_chunk.split(".")[0].strip()
            best_source_idx = 1

        if not best_overall_sentence:
            return "Based on your saved notes and URLs, no specific information was found matching this query in the database."

        # Assemble structured grounded answer
        top_src_title = sources[best_source_idx - 1].get("title", "Saved Content")
        answer_parts = [
            f"**Answer from Database:**\n{best_overall_sentence.strip('.')} [Source {best_source_idx}: {top_src_title}]."
        ]

        # Add key points if available
        remaining_insights = [
            ins for ins in extracted_insights
            if not best_overall_sentence.lower()[:30] in ins.lower()
        ][:3]

        if remaining_insights:
            answer_parts.append("\n**Key Extracted Points:**\n" + "\n".join(remaining_insights))

        # Privacy / Grounding note
        answer_parts.append(
            "\n\n*(Retrieved directly from your local SQLite RAG database without external LLM calls. Fully grounded in your saved content.)*"
        )

        return "\n".join(answer_parts)

    @staticmethod
    def _filter_relevant_chunks(question: str, candidate_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Strict relevance gate: ensures only genuinely relevant chunks are returned,
        completely filtering out out-of-domain or unwanted data.
        """
        stopwords = {
            "what", "whats", "what's", "is", "are", "was", "were", "the", "a", "an",
            "and", "or", "in", "on", "at", "by", "for", "with", "about", "to", "from",
            "of", "how", "can", "could", "would", "should", "tell", "me", "give", "you",
            "your", "my", "our", "do", "does", "did", "this", "that", "these", "those",
            "i", "we", "he", "she", "it", "they", "them", "there", "where", "when", "why",
            "which", "who", "whom", "whose", "please", "know", "much", "many", "some"
        }

        # Tokenize and extract substantive keywords
        tokens = [w.lower().strip("?,!.:;'\"()[]{}") for w in question.split()]
        keywords = [w for w in tokens if len(w) > 2 and w not in stopwords]
        
        # If question contains only short words (e.g. "go", "AI"), retain non-stopwords
        if not keywords:
            keywords = [w for w in tokens if len(w) > 1 and w not in stopwords]

        relevant_chunks: List[Dict[str, Any]] = []

        for chunk in candidate_chunks:
            score = chunk.get("score", 0.0)
            content = (chunk.get("content") or "").lower()
            title = (chunk.get("item_title") or "").lower()
            combined_text = f"{title} {content}"

            # High semantic similarity threshold (for dense neural embeddings)
            if score >= 0.70:
                relevant_chunks.append(chunk)
                continue

            # If keywords were identified, require at least one substantive keyword or stem match
            if keywords:
                matched_kws = []
                for kw in keywords:
                    if kw in combined_text:
                        matched_kws.append(kw)
                    # Morphological prefix/stem matching for words with length >= 4
                    elif len(kw) >= 5 and (kw[:4] in combined_text or kw[:-1] in combined_text):
                        matched_kws.append(kw)

                # Only keep chunk if it has keyword presence AND a non-trivial similarity score
                if matched_kws and score > 0.05:
                    chunk["matched_keywords"] = matched_kws
                    relevant_chunks.append(chunk)
            else:
                # If no keywords could be extracted, rely on strict similarity score
                if score >= 0.25:
                    relevant_chunks.append(chunk)

        return relevant_chunks

    async def query(self, question: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        k = top_k or settings.DEFAULT_TOP_K
        clean_question = question.strip()
        if not clean_question:
            return {
                "answer": "Please provide a non-empty question.",
                "sources": [],
                "llm_used": "None"
            }

        logger.info(f"Processing RAG query: '{clean_question}' (top_k={k})")

        # 1. Embed query
        query_vector = embedding_service.embed_query(clean_question)

        # 2. Retrieve top-k candidates from SQLite Vector Store
        raw_chunks = vector_store.similarity_search(query_vector, top_k=k)

        # 3. Filter for genuine relevance (discards any unwanted/irrelevant data)
        retrieved_chunks = self._filter_relevant_chunks(clean_question, raw_chunks)

        if not retrieved_chunks:
            logger.info(f"Query '{clean_question}' yielded 0 relevant chunks (filtered {len(raw_chunks)} unwanted candidates)")
            return {
                "answer": (
                    f"No relevant information about \"{clean_question}\" was found in your saved knowledge inbox.\n\n"
                    f"*(Filtered to ensure zero unwanted or irrelevant data is returned. Try ingesting notes or URLs related to this topic.)*"
                ),
                "sources": [],
                "question": clean_question,
                "llm_used": self._provider_label
            }

        # 4. Format citations
        sources = []
        context_blocks = []
        for idx, chunk in enumerate(retrieved_chunks, 1):
            src_info = {
                "source_num": idx,
                "chunk_id": chunk["chunk_id"],
                "item_id": chunk["item_id"],
                "title": chunk["item_title"],
                "source_type": chunk["item_type"],
                "url": chunk["item_url"],
                "similarity_score": round(chunk["score"] * 100, 1),
                "snippet": chunk["content"],
                "chunk_index": chunk["chunk_index"]
            }
            sources.append(src_info)
            context_blocks.append(
                f"[Source {idx}] (Title: {chunk['item_title']}, Type: {chunk['item_type']}):\n{chunk['content']}"
            )

        context_str = "\n\n---\n\n".join(context_blocks)

        # 4. Synthesize Answer
        # Refresh LLM instance in case env variable changed
        self._init_llm()

        if self._llm is not None:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                
                system_prompt = (
                    "You are an expert AI assistant for the AI Knowledge Inbox.\n"
                    "Your job is to provide a clear, accurate, complete, and well-structured answer to the user's question "
                    "strictly based on the retrieved context snippets from their saved notes and URLs.\n\n"
                    "Instructions:\n"
                    "1. Thoroughly address the user's request using the facts, explanations, and code provided in the context.\n"
                    "2. If the user asks for sample code or programming examples, extract and format all relevant code snippets cleanly in markdown code blocks with syntax highlighting (e.g., ```python ... ```).\n"
                    "3. Always cite the corresponding source number (e.g., [Source 1], [Source 2]) next to facts or code snippets you present.\n"
                    "4. If a specific part of what the user asks for is not in the retrieved context, explain what is present in the sources and note clearly what is not provided in the saved content. Do not hallucinate external facts."
                )
                user_prompt = f"Context:\n{context_str}\n\nQuestion: {clean_question}\n\nAnswer:"
                
                response = await self._llm.ainvoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ])
                answer = response.content.strip()
                llm_used = self._provider_label
            except Exception as e:
                logger.error(f"Error during LLM invocation: {e}. Falling back to extractive synthesis.", exc_info=True)
                answer = self._generate_extractive_answer(clean_question, sources)
                llm_used = "Extractive Fallback"
        else:
            answer = self._generate_extractive_answer(clean_question, sources)
            llm_used = self._provider_label

        logger.info(f"Generated RAG answer using {llm_used} citing {len(sources)} sources")

        return {
            "answer": answer,
            "sources": sources,
            "question": clean_question,
            "llm_used": llm_used
        }

rag_service = RAGService()
