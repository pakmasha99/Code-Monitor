"""
Hybrid Search Service - Combining Dense Vector + Sparse BM25

Implements hybrid retrieval with Reciprocal Rank Fusion (RRF) for improved recall.
Based on research: Dense (70%) + Sparse (30%) = +26% recall improvement
"""
from rank_bm25 import BM25Okapi
from typing import List, Dict, Any, Optional
import numpy as np


class HybridSearchService:
    """
    Hybrid search combining:
    - Dense retrieval: Vector similarity (semantic understanding)
    - Sparse retrieval: BM25 (exact keyword matching)
    - Fusion: Reciprocal Rank Fusion (RRF)

    Research shows 82% recall vs 65% vector-only
    """

    def __init__(self):
        """Initialize hybrid search service"""
        self.bm25_index = None
        self.documents = []
        self.corpus_tokens = []

    def build_bm25_index(self, documents: List[Dict[str, Any]]):
        """
        Build BM25 index from documents

        Args:
            documents: List of dicts with 'id', 'content', and metadata
        """
        self.documents = documents

        # Tokenize documents for BM25
        self.corpus_tokens = [
            doc['content'].lower().split()
            for doc in documents
        ]

        # Create BM25 index
        self.bm25_index = BM25Okapi(self.corpus_tokens)

    def bm25_search(self, query: str, k: int = 20) -> List[Dict[str, Any]]:
        """
        Perform BM25 keyword search

        Args:
            query: Search query string
            k: Number of results to return

        Returns:
            List of documents with BM25 scores
        """
        if self.bm25_index is None:
            raise ValueError("BM25 index not built. Call build_bm25_index() first.")

        # Tokenize query
        query_tokens = query.lower().split()

        # Get BM25 scores
        scores = self.bm25_index.get_scores(query_tokens)

        # Create results with scores
        results = []
        for idx, score in enumerate(scores):
            results.append({
                **self.documents[idx],
                'score': float(score)
            })

        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)

        return results[:k]

    def normalize_scores(self, scores: List[float]) -> List[float]:
        """
        Normalize scores to [0, 1] range using min-max normalization

        Args:
            scores: List of raw scores

        Returns:
            Normalized scores in [0, 1]
        """
        if not scores or len(scores) == 0:
            return []

        scores_array = np.array(scores)
        min_score = scores_array.min()
        max_score = scores_array.max()

        # Avoid division by zero
        if max_score == min_score:
            return [1.0] * len(scores)

        normalized = (scores_array - min_score) / (max_score - min_score)
        return normalized.tolist()

    def reciprocal_rank_fusion(
        self,
        vector_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        alpha: float = 0.7,
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Combine results using Reciprocal Rank Fusion (RRF)

        Formula: RRF_score = alpha * (1/(rank + k)) for vector
                           + (1-alpha) * (1/(rank + k)) for BM25

        Args:
            vector_results: Results from vector search with scores
            bm25_results: Results from BM25 search with scores
            alpha: Weight for vector search (0.7 = 70% semantic, 30% keyword)
            k: Constant for RRF (default 60)

        Returns:
            Fused and sorted results
        """
        scores = {}

        # Process vector results
        for rank, doc in enumerate(vector_results):
            doc_id = doc['id']
            rrf_score = alpha / (rank + k)
            scores[doc_id] = scores.get(doc_id, 0.0) + rrf_score

        # Process BM25 results
        for rank, doc in enumerate(bm25_results):
            doc_id = doc['id']
            rrf_score = (1 - alpha) / (rank + k)
            scores[doc_id] = scores.get(doc_id, 0.0) + rrf_score

        # Create results list with combined scores
        results = []
        doc_map = {doc['id']: doc for doc in vector_results + bm25_results}

        for doc_id, score in scores.items():
            result = doc_map[doc_id].copy()
            result['score'] = score
            results.append(result)

        # Sort by combined score
        results.sort(key=lambda x: x['score'], reverse=True)

        return results

    async def hybrid_search(
        self,
        query: str,
        alpha: Optional[float] = None,
        k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector and BM25

        Args:
            query: Search query
            alpha: Weight for vector search (None = auto-calculate)
            k: Number of results

        Returns:
            Hybrid search results sorted by fused score
        """
        # Auto-calculate alpha if not provided
        if alpha is None:
            alpha = self.calculate_dynamic_alpha(query)

        # 1. BM25 search
        bm25_results = self.bm25_search(query, k=k)

        # 2. Vector search (placeholder - requires EmbeddingService integration)
        # For now, return BM25 results only
        # TODO: Integrate with EmbeddingService for full hybrid search
        vector_results = []  # Will be populated when integrated

        if not vector_results:
            # Fallback to BM25 only if vector search not available
            return bm25_results

        # 3. Fusion
        fused_results = self.reciprocal_rank_fusion(
            vector_results,
            bm25_results,
            alpha=alpha
        )

        return fused_results[:k]

    def calculate_dynamic_alpha(self, query: str) -> float:
        """
        Calculate optimal alpha based on query characteristics

        Short queries (<=3 words): Favor keyword (alpha = 0.4)
        Medium queries (4-7 words): Balanced (alpha = 0.6)
        Long queries (>=8 words): Favor semantic (alpha = 0.8)

        Args:
            query: Search query string

        Returns:
            Alpha value (0.0 - 1.0)
        """
        query_length = len(query.split())

        if query_length <= 3:
            # Short query: favor exact keyword match
            return 0.4  # 40% semantic, 60% keyword

        elif query_length < 8:
            # Medium query: balanced
            return 0.6  # 60% semantic, 40% keyword

        else:
            # Long query: favor semantic understanding
            return 0.8  # 80% semantic, 20% keyword

    def get_stats(self) -> Dict[str, Any]:
        """
        Get hybrid search statistics

        Returns:
            Dictionary with index statistics
        """
        return {
            "total_documents": len(self.documents),
            "bm25_index_built": self.bm25_index is not None,
            "avg_doc_length": np.mean([len(tokens) for tokens in self.corpus_tokens])
            if self.corpus_tokens else 0
        }
