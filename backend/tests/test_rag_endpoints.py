"""
Test RAG API Endpoints (TDD)

Following RED-GREEN-REFACTOR cycle for RAG endpoint implementation.
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.routers.rag import hybrid_search

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_index():
    """Initialize BM25 index with sample documents for testing"""
    sample_docs = [
        {
            "id": "doc1",
            "content": "def calculate_fibonacci(n): return fib(n-1) + fib(n-2)",
            "file_path": "app/utils/math.py",
            "language": "python",
            "function_name": "calculate_fibonacci",
            "summary": "Recursive Fibonacci calculation"
        },
        {
            "id": "doc2",
            "content": "def fibonacci_iterative(n): a, b = 0, 1; return result",
            "file_path": "app/utils/math.py",
            "language": "python",
            "function_name": "fibonacci_iterative",
            "summary": "Iterative Fibonacci implementation"
        },
        {
            "id": "doc3",
            "content": "class UserManager: def authenticate(username, password): verify credentials",
            "file_path": "app/models/user.py",
            "language": "python",
            "function_name": "authenticate",
            "summary": "User authentication system"
        },
        {
            "id": "doc4",
            "content": "def binary_search(arr, target): divide and conquer search algorithm",
            "file_path": "app/utils/search.py",
            "language": "python",
            "function_name": "binary_search",
            "summary": "Binary search implementation"
        }
    ]

    # Build BM25 index for testing
    hybrid_search.build_bm25_index(sample_docs)

    yield  # Run tests

    # Cleanup (if needed)
    pass


class TestRAGEndpoints:
    """Test suite for RAG API endpoints"""

    def test_search_code_endpoint_exists(self):
        """RED: Test /api/v1/rag/search endpoint exists"""
        response = client.post(
            "/api/v1/rag/search",
            json={"query": "fibonacci implementation"}
        )
        # Should return 200 or appropriate response, not 404
        assert response.status_code != 404

    def test_search_code_requires_query(self):
        """RED: Test search endpoint validates query parameter"""
        response = client.post("/api/v1/rag/search", json={})
        assert response.status_code == 422  # Validation error

    def test_search_code_basic_functionality(self):
        """RED: Test basic code search with BM25"""
        response = client.post(
            "/api/v1/rag/search",
            json={
                "query": "calculate fibonacci",
                "limit": 5,
                "search_type": "bm25"
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert "results" in data
        assert "query" in data
        assert "search_type" in data
        assert isinstance(data["results"], list)
        assert len(data["results"]) <= 5

    def test_search_code_hybrid_mode(self):
        """RED: Test hybrid search (BM25 + Vector)"""
        response = client.post(
            "/api/v1/rag/search",
            json={
                "query": "user authentication system",
                "limit": 10,
                "search_type": "hybrid",
                "alpha": 0.7
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert data["search_type"] == "hybrid"
        assert "alpha" in data
        assert data["alpha"] == 0.7
        assert isinstance(data["results"], list)

    def test_search_code_vector_only_mode(self):
        """RED: Test vector-only semantic search"""
        response = client.post(
            "/api/v1/rag/search",
            json={
                "query": "recursive algorithm implementation",
                "limit": 5,
                "search_type": "vector"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["search_type"] == "vector"

    def test_search_code_with_filters(self):
        """RED: Test search with language/file filters"""
        response = client.post(
            "/api/v1/rag/search",
            json={
                "query": "class definition",
                "limit": 10,
                "filters": {
                    "language": "python",
                    "file_path": "app/models/"
                }
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Results should be filtered
        if len(data["results"]) > 0:
            assert all(r.get("language") == "python" for r in data["results"])

    def test_ask_code_question_endpoint(self):
        """RED: Test /api/v1/rag/ask endpoint for Q&A"""
        response = client.post(
            "/api/v1/rag/ask",
            json={
                "question": "How does user authentication work in this codebase?",
                "max_context": 5
            }
        )
        assert response.status_code == 200
        data = response.json()

        assert "question" in data
        assert "answer" in data
        assert "sources" in data
        assert isinstance(data["sources"], list)

    def test_ask_with_insufficient_context(self):
        """RED: Test Q&A when no relevant code found"""
        response = client.post(
            "/api/v1/rag/ask",
            json={
                "question": "quantum physics implementation in codebase",
                "max_context": 3
            }
        )
        assert response.status_code == 200
        data = response.json()

        # Should still return answer (LLM acknowledges no context)
        assert "answer" in data
        # Confidence should be relatively low for irrelevant queries
        # BM25 may still return some results, but with lower relevance
        assert data["confidence"] < 0.7  # Lower than typical good matches

    def test_index_status_endpoint(self):
        """RED: Test /api/v1/rag/status endpoint"""
        response = client.get("/api/v1/rag/status")
        assert response.status_code == 200
        data = response.json()

        assert "bm25_index_built" in data
        assert "total_documents" in data
        assert "vector_collection_exists" in data
        assert isinstance(data["total_documents"], int)

    def test_reindex_trigger_endpoint(self):
        """RED: Test /api/v1/rag/reindex endpoint"""
        response = client.post(
            "/api/v1/rag/reindex",
            json={"repository_id": 1}
        )
        assert response.status_code in [200, 202]  # 200 sync, 202 async
        data = response.json()

        assert "status" in data
        # Should trigger background job
        if response.status_code == 202:
            assert "task_id" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
