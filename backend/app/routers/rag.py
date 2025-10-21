"""
RAG (Retrieval-Augmented Generation) API Endpoints

Provides code search and Q&A capabilities using hybrid retrieval.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from app.services.hybrid_search_service import HybridSearchService
from app.services.embedding_service import EmbeddingService
from app.services.code_analyzer import CodeAnalyzer

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])

# Initialize services (singleton pattern)
hybrid_search = HybridSearchService()
embedding_service = EmbeddingService()
code_analyzer = CodeAnalyzer()


# === Request/Response Models ===

class SearchRequest(BaseModel):
    """Code search request"""
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Max results")
    search_type: Literal["bm25", "vector", "hybrid"] = Field(
        default="hybrid",
        description="Search strategy"
    )
    alpha: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Hybrid weight (0.7 = 70% semantic, 30% keyword)"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Filter by language, file_path, etc."
    )


class AskRequest(BaseModel):
    """Q&A request"""
    question: str = Field(..., min_length=1, description="Question about codebase")
    max_context: int = Field(default=5, ge=1, le=20, description="Max code chunks")
    include_sources: bool = Field(default=True, description="Include source code")


class ReindexRequest(BaseModel):
    """Reindex request"""
    repository_id: int = Field(..., description="Repository ID to reindex")


class SearchResult(BaseModel):
    """Search result item"""
    id: str
    content: str
    score: float
    file_path: Optional[str] = None
    language: Optional[str] = None
    function_name: Optional[str] = None
    summary: Optional[str] = None


class SearchResponse(BaseModel):
    """Search response"""
    query: str
    search_type: str
    alpha: Optional[float] = None
    results: List[SearchResult]
    total: int


class AskResponse(BaseModel):
    """Q&A response"""
    question: str
    answer: str
    sources: List[SearchResult]
    confidence: float = Field(ge=0.0, le=1.0)


class IndexStatusResponse(BaseModel):
    """Index status"""
    bm25_index_built: bool
    vector_collection_exists: bool
    total_documents: int
    avg_doc_length: float


class ReindexResponse(BaseModel):
    """Reindex status"""
    status: str
    task_id: Optional[str] = None
    message: str


# === Endpoints ===

@router.post("/search", response_model=SearchResponse)
async def search_code(request: SearchRequest):
    """
    Search code using BM25, vector, or hybrid search

    **Search Types**:
    - `bm25`: Keyword-based search (fast, exact matches)
    - `vector`: Semantic search (slower, conceptual matches)
    - `hybrid`: Combined approach (best recall, recommended)

    **Dynamic Alpha**: If alpha not provided, automatically calculated based on query length
    """
    try:
        results = []

        if request.search_type == "bm25":
            # BM25 keyword search
            results = hybrid_search.bm25_search(request.query, k=request.limit)

        elif request.search_type == "vector":
            # Vector semantic search
            results = await embedding_service.search_similar_code(
                request.query,
                limit=request.limit
            )

        elif request.search_type == "hybrid":
            # Hybrid search with RRF fusion
            results = await hybrid_search.hybrid_search(
                request.query,
                alpha=request.alpha,
                k=request.limit
            )

        # Apply filters if provided
        if request.filters:
            results = _apply_filters(results, request.filters)

        # Convert to response model
        search_results = [
            SearchResult(**{
                "id": r.get("id", "unknown"),
                "content": r.get("content", ""),
                "score": r.get("score", 0.0),
                "file_path": r.get("file_path"),
                "language": r.get("language"),
                "function_name": r.get("function_name"),
                "summary": r.get("summary")
            })
            for r in results
        ]

        return SearchResponse(
            query=request.query,
            search_type=request.search_type,
            alpha=request.alpha,
            results=search_results,
            total=len(search_results)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/ask", response_model=AskResponse)
async def ask_code_question(request: AskRequest):
    """
    Ask questions about the codebase using RAG

    **Process**:
    1. Retrieve relevant code chunks via hybrid search
    2. Build context from top results
    3. Generate answer using LLM with context
    4. Return answer with source citations
    """
    try:
        # 1. Retrieve relevant code
        search_results = await hybrid_search.hybrid_search(
            request.question,
            k=request.max_context
        )

        if not search_results or len(search_results) == 0:
            # No relevant code found
            return AskResponse(
                question=request.question,
                answer="I don't have enough information in the codebase to answer this question.",
                sources=[],
                confidence=0.0
            )

        # 2. Build context for LLM
        context_chunks = [
            f"[{r['file_path']}:{r.get('function_name', 'unknown')}]\n{r['content']}"
            for r in search_results[:request.max_context]
        ]
        context = "\n\n".join(context_chunks)

        # 3. Generate answer with LLM
        prompt = f"""Answer the following question about this codebase using ONLY the provided code context.

Question: {request.question}

Code Context:
{context}

Instructions:
- Answer based ONLY on the code provided
- Cite specific functions/files when relevant
- If context is insufficient, acknowledge it
- Be concise and technical

Answer:"""

        message = code_analyzer.anthropic.messages.create(
            model=code_analyzer.llm_model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        answer = message.content[0].text

        # 4. Calculate confidence based on retrieval scores
        avg_score = sum(r['score'] for r in search_results) / len(search_results)
        confidence = min(avg_score, 1.0)

        # Convert sources to response model
        sources = [
            SearchResult(**{
                "id": r.get("id", "unknown"),
                "content": r.get("content", ""),
                "score": r.get("score", 0.0),
                "file_path": r.get("file_path"),
                "language": r.get("language"),
                "function_name": r.get("function_name"),
                "summary": r.get("summary")
            })
            for r in search_results
        ] if request.include_sources else []

        return AskResponse(
            question=request.question,
            answer=answer,
            sources=sources,
            confidence=confidence
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Q&A failed: {str(e)}")


@router.get("/status", response_model=IndexStatusResponse)
async def get_index_status():
    """
    Get RAG index status

    Returns information about BM25 and vector indices
    """
    try:
        stats = hybrid_search.get_stats()

        # Check vector collection
        vector_exists = False
        try:
            collections = embedding_service.client.get_collections()
            vector_exists = any(
                c.name == embedding_service.collection_name
                for c in collections.collections
            )
        except:
            vector_exists = False

        return IndexStatusResponse(
            bm25_index_built=stats["bm25_index_built"],
            vector_collection_exists=vector_exists,
            total_documents=stats["total_documents"],
            avg_doc_length=stats["avg_doc_length"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.post("/reindex", response_model=ReindexResponse)
async def trigger_reindex(request: ReindexRequest, background_tasks: BackgroundTasks):
    """
    Trigger codebase reindexing

    **Process**:
    1. Fetch repository files
    2. Parse code with tree-sitter
    3. Generate embeddings
    4. Build BM25 + vector indices

    **Note**: This is an async background task
    """
    try:
        # TODO: Implement background reindexing with Celery
        # For now, return 501 Not Implemented
        return ReindexResponse(
            status="not_implemented",
            task_id=None,
            message="Background reindexing not yet implemented. Will be added in Phase 3."
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reindex failed: {str(e)}")


# === Helper Functions ===

def _apply_filters(results: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
    """Apply filters to search results"""
    filtered = results

    if "language" in filters:
        language = filters["language"].lower()
        filtered = [r for r in filtered if r.get("language", "").lower() == language]

    if "file_path" in filters:
        path_pattern = filters["file_path"]
        filtered = [r for r in filtered if path_pattern in r.get("file_path", "")]

    return filtered
