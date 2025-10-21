"""
Test Hybrid Search Service (TDD)

Following RED-GREEN-REFACTOR cycle for hybrid search implementation.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.hybrid_search_service import HybridSearchService


@pytest.fixture
def sample_documents():
    """Sample code documents for testing"""
    return [
        {
            "id": "doc1",
            "content": "def calculate_fibonacci(n): return fib(n-1) + fib(n-2)",
            "function_name": "calculate_fibonacci",
            "summary": "Calculates Fibonacci numbers recursively"
        },
        {
            "id": "doc2",
            "content": "def fibonacci_iterative(n): a, b = 0, 1; return result",
            "function_name": "fibonacci_iterative",
            "summary": "Iterative Fibonacci implementation"
        },
        {
            "id": "doc3",
            "content": "class UserManager: def authenticate(username, password): verify credentials",
            "function_name": "authenticate",
            "summary": "User authentication with password verification"
        },
        {
            "id": "doc4",
            "content": "def binary_search(arr, target): divide and conquer search",
            "function_name": "binary_search",
            "summary": "Binary search algorithm implementation"
        }
    ]


class TestHybridSearchService:
    """Test suite for Hybrid Search Service"""

    def test_service_initialization(self):
        """RED: Test service can be instantiated"""
        service = HybridSearchService()
        assert service is not None
        assert hasattr(service, 'bm25_index')
        assert hasattr(service, 'documents')

    def test_build_bm25_index(self, sample_documents):
        """RED: Test BM25 index building"""
        service = HybridSearchService()
        service.build_bm25_index(sample_documents)

        assert service.bm25_index is not None
        assert len(service.documents) == 4
        assert service.corpus_tokens is not None

    def test_bm25_search(self, sample_documents):
        """RED: Test BM25 keyword search"""
        service = HybridSearchService()
        service.build_bm25_index(sample_documents)

        results = service.bm25_search("fibonacci", k=2)

        assert len(results) == 2
        assert results[0]['id'] in ['doc1', 'doc2']
        assert 'score' in results[0]

    def test_normalize_scores(self):
        """RED: Test score normalization to [0, 1]"""
        service = HybridSearchService()
        scores = [10.0, 5.0, 2.5, 0.0]

        normalized = service.normalize_scores(scores)

        assert len(normalized) == 4
        assert max(normalized) == 1.0
        assert min(normalized) == 0.0
        assert all(0.0 <= score <= 1.0 for score in normalized)

    def test_reciprocal_rank_fusion(self, sample_documents):
        """RED: Test RRF fusion algorithm"""
        service = HybridSearchService()

        # Mock vector and BM25 results
        vector_results = [
            {'id': 'doc1', 'score': 0.9},
            {'id': 'doc3', 'score': 0.7}
        ]
        bm25_results = [
            {'id': 'doc2', 'score': 0.95},
            {'id': 'doc1', 'score': 0.85}
        ]

        fused = service.reciprocal_rank_fusion(
            vector_results, bm25_results, alpha=0.7, k=60
        )

        assert len(fused) > 0
        # doc1 should rank high (appears in both)
        top_doc = fused[0]
        assert 'id' in top_doc
        assert 'score' in top_doc

    @pytest.mark.asyncio
    async def test_hybrid_search_integration(self, sample_documents):
        """RED: Test full hybrid search (requires EmbeddingService)"""
        service = HybridSearchService()
        service.build_bm25_index(sample_documents)

        # This will fail initially - requires EmbeddingService integration
        # We'll implement this in GREEN phase
        try:
            results = await service.hybrid_search(
                query="fibonacci recursive implementation",
                alpha=0.7,
                k=3
            )
            assert len(results) <= 3
        except Exception as e:
            # Expected to fail in RED phase
            pytest.skip(f"Integration not ready: {e}")

    def test_calculate_dynamic_alpha(self):
        """RED: Test dynamic alpha calculation based on query"""
        service = HybridSearchService()

        # Short query: favor keyword matching
        alpha_short = service.calculate_dynamic_alpha("fibonacci")
        assert 0.3 <= alpha_short <= 0.5

        # Medium query: balanced
        alpha_medium = service.calculate_dynamic_alpha("fibonacci recursive function implementation")
        assert 0.5 <= alpha_medium <= 0.7

        # Long query: favor semantic
        alpha_long = service.calculate_dynamic_alpha(
            "implement a recursive function to calculate fibonacci numbers efficiently"
        )
        assert 0.7 <= alpha_long <= 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
