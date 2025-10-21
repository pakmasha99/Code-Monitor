"""
RAG Integration Tests

End-to-end workflow testing for complete RAG pipeline.
"""
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.services.code_analyzer import CodeAnalyzer
from app.services.embedding_service import EmbeddingService
from app.services.hybrid_search_service import HybridSearchService
from app.routers.rag import hybrid_search  # Use shared singleton

client = TestClient(app)


class TestRAGIntegration:
    """End-to-end RAG workflow tests"""

    def test_full_search_workflow(self):
        """
        Integration: Index → Search → Retrieve

        Workflow:
        1. Create sample code documents
        2. Build BM25 index
        3. Search via API endpoint
        4. Verify results
        """
        # 1. Setup sample documents
        sample_code = [
            {
                "id": "integration_test_1",
                "content": "def calculate_sum(a, b): return a + b",
                "file_path": "test/math.py",
                "language": "python",
                "function_name": "calculate_sum"
            },
            {
                "id": "integration_test_2",
                "content": "def calculate_product(a, b): return a * b",
                "file_path": "test/math.py",
                "language": "python",
                "function_name": "calculate_product"
            }
        ]

        # 2. Build index (use shared singleton)
        hybrid_search.build_bm25_index(sample_code)

        # 3. Search via API
        response = client.post(
            "/api/v1/rag/search",
            json={
                "query": "calculate sum",
                "limit": 5,
                "search_type": "bm25"
            }
        )

        # 4. Verify
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) > 0
        assert "calculate_sum" in data["results"][0]["content"]

    def test_full_qa_workflow(self):
        """
        Integration: Index → Ask → Generate Answer

        Workflow:
        1. Index code samples
        2. Ask question via API
        3. Verify LLM generates answer with context
        """
        # 1. Index sample code (use shared singleton)
        sample_code = [
            {
                "id": "qa_test_1",
                "content": """
class UserManager:
    def authenticate(self, username, password):
        # Verify credentials against database
        user = db.query(User).filter_by(username=username).first()
        return user.check_password(password)
                """,
                "file_path": "app/auth/manager.py",
                "language": "python",
                "function_name": "authenticate"
            }
        ]
        hybrid_search.build_bm25_index(sample_code)

        # 2. Ask question
        response = client.post(
            "/api/v1/rag/ask",
            json={
                "question": "How does authentication work?",
                "max_context": 3
            }
        )

        # 3. Verify answer
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert len(data["answer"]) > 10  # Non-trivial answer
        assert len(data["sources"]) > 0
        assert "authenticate" in data["sources"][0]["content"]

    def test_code_analyzer_integration(self):
        """
        Integration: File → Parse → Chunk

        Workflow:
        1. Create sample Python code
        2. Parse with tree-sitter
        3. Verify chunks extracted correctly
        """
        analyzer = CodeAnalyzer()

        sample_code = """
def fibonacci(n):
    '''Calculate Fibonacci number'''
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class MathOperations:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b
        """

        # Parse and chunk
        chunks = analyzer.chunk_code_file("test.py", sample_code)

        # Verify chunks
        assert len(chunks) >= 3  # fibonacci function + 2 class methods
        function_chunks = [c for c in chunks if c['type'] == 'function_definition']
        class_chunks = [c for c in chunks if c['type'] == 'class_definition']

        assert len(function_chunks) >= 1  # fibonacci
        assert len(class_chunks) >= 1  # MathOperations

        # Verify metadata
        fib_chunk = [c for c in chunks if c['name'] == 'fibonacci'][0]
        assert fib_chunk['language'] == 'python'
        assert 'fibonacci' in fib_chunk['code']

    def test_dynamic_alpha_workflow(self):
        """
        Integration: Query Length → Dynamic Alpha → Search Weight

        Workflow:
        1. Test short query (keyword-focused)
        2. Test long query (semantic-focused)
        3. Verify alpha adjustments
        """
        # Short query (<=3 words) - use shared singleton
        short_alpha = hybrid_search.calculate_dynamic_alpha("user auth")
        assert 0.3 <= short_alpha <= 0.5  # Favor keyword

        # Medium query (4-7 words)
        medium_alpha = hybrid_search.calculate_dynamic_alpha("user authentication with password check")
        assert 0.5 <= medium_alpha <= 0.7  # Balanced

        # Long query (>=8 words)
        long_alpha = hybrid_search.calculate_dynamic_alpha(
            "implement user authentication system with password verification and session management"
        )
        assert 0.7 <= long_alpha <= 0.9  # Favor semantic

    def test_reciprocal_rank_fusion_integration(self):
        """
        Integration: Vector Results + BM25 Results → RRF → Fused Ranking

        Workflow:
        1. Create mock vector and BM25 results
        2. Apply RRF fusion
        3. Verify combined ranking
        """
        # Mock results (simulating vector + BM25) - use shared singleton
        vector_results = [
            {"id": "doc1", "score": 0.95, "content": "Vector match 1"},
            {"id": "doc3", "score": 0.80, "content": "Vector match 2"}
        ]
        bm25_results = [
            {"id": "doc2", "score": 8.5, "content": "BM25 match 1"},
            {"id": "doc1", "score": 7.2, "content": "BM25 match 2"}  # Also in vector
        ]

        # Apply RRF
        fused = hybrid_search.reciprocal_rank_fusion(
            vector_results, bm25_results, alpha=0.7, k=60
        )

        # Verify fusion
        assert len(fused) == 3  # 3 unique documents
        # doc1 should rank high (appears in both)
        top_doc = fused[0]
        assert top_doc['id'] == 'doc1'
        assert 'score' in top_doc

    def test_index_status_integration(self):
        """
        Integration: Build Index → Check Status → Verify Stats

        Workflow:
        1. Build indices
        2. Query status endpoint
        3. Verify accurate statistics
        """
        # Build index (use shared singleton)
        sample_docs = [
            {"id": "s1", "content": "test document one"},
            {"id": "s2", "content": "test document two"},
            {"id": "s3", "content": "test document three"}
        ]
        hybrid_search.build_bm25_index(sample_docs)

        # Check status
        response = client.get("/api/v1/rag/status")
        assert response.status_code == 200

        data = response.json()
        assert data["bm25_index_built"] == True
        assert data["total_documents"] == 3
        assert data["avg_doc_length"] > 0

    def test_filtering_integration(self):
        """
        Integration: Search with Filters → Filtered Results

        Workflow:
        1. Index multi-language code
        2. Search with language filter
        3. Verify only filtered results returned
        """
        # Use shared singleton
        multi_lang_docs = [
            {
                "id": "py1",
                "content": "def hello(): print('Python')",
                "language": "python",
                "file_path": "app/main.py"
            },
            {
                "id": "js1",
                "content": "function hello() { console.log('JavaScript'); }",
                "language": "javascript",
                "file_path": "app/main.js"
            },
            {
                "id": "py2",
                "content": "def goodbye(): print('Bye')",
                "language": "python",
                "file_path": "app/utils.py"
            }
        ]
        hybrid_search.build_bm25_index(multi_lang_docs)

        # Search with Python filter
        response = client.post(
            "/api/v1/rag/search",
            json={
                "query": "hello",
                "limit": 10,
                "search_type": "bm25",
                "filters": {"language": "python"}
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify only Python results
        for result in data["results"]:
            assert result["language"] == "python"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
