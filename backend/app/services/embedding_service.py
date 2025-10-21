"""
Embedding Service for code vectorization and similarity search

Handles OpenAI embedding generation and Qdrant vector storage.
"""
import openai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib


class EmbeddingService:
    """
    Manages code embeddings and vector search using OpenAI and Qdrant

    Provides embedding generation, storage, and semantic search capabilities.
    """

    def __init__(self):
        """Initialize Qdrant client and ensure collection exists"""
        self.client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", 6333))
        )
        self.collection_name = "code_embeddings"
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.embedding_dimension = int(os.getenv("EMBEDDING_DIMENSION", 1536))

        openai.api_key = os.getenv("OPENAI_API_KEY")

        self.ensure_collection()

    def ensure_collection(self):
        """Create Qdrant collection if it doesn't exist"""
        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
                print(f"✅ Created Qdrant collection: {self.collection_name}")
            else:
                print(f"ℹ️  Using existing collection: {self.collection_name}")

        except Exception as e:
            print(f"⚠️  Error ensuring collection: {e}")
            raise

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using OpenAI text-embedding-3-small

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        try:
            response = openai.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding

        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            raise

    def generate_point_id(self, user_id: int, file_path: str, chunk_name: str, start_line: int) -> str:
        """
        Generate unique point ID for Qdrant

        Args:
            user_id: User identifier
            file_path: File path
            chunk_name: Function/class name
            start_line: Starting line number

        Returns:
            Unique hash-based ID
        """
        unique_string = f"{user_id}_{file_path}_{chunk_name}_{start_line}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    async def store_code_embedding(
        self,
        code_analysis: Dict[str, Any],
        chunk: Dict[str, Any],
        user_info: Dict[str, Any]
    ):
        """
        Store code embedding in Qdrant

        Args:
            code_analysis: LLM analysis results (summary, complexity, etc.)
            chunk: Code chunk metadata (name, code, language, etc.)
            user_info: User metadata (user_id, name, repository, etc.)
        """
        # Prepare text for embedding - combine summary and code snippet
        text_to_embed = f"""
Function: {chunk.get('name', 'unknown')}
Summary: {code_analysis.get('summary', '')}
Purpose: {code_analysis.get('purpose', '')}
Language: {chunk.get('language', 'unknown')}
Code: {chunk['code'][:500]}
"""

        # Generate embedding
        embedding = await self.generate_embedding(text_to_embed.strip())

        # Generate unique ID
        point_id = self.generate_point_id(
            user_info['user_id'],
            chunk.get('file_path', ''),
            chunk.get('name', 'unknown'),
            chunk.get('start_line', 0)
        )

        # Prepare metadata payload
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "user_id": user_info['user_id'],
                "user_name": user_info.get('user_name', ''),
                "repository_url": user_info.get('repository_url', ''),
                "file_path": chunk.get('file_path', ''),
                "function_name": chunk.get('name', ''),
                "class_name": chunk.get('class_name', ''),
                "code_snippet": chunk['code'][:500],  # Store truncated snippet
                "summary": code_analysis.get('summary', ''),
                "purpose": code_analysis.get('purpose', ''),
                "language": chunk.get('language', 'unknown'),
                "complexity_score": code_analysis.get('complexity', 0),
                "quality": code_analysis.get('quality', ''),
                "algorithms": code_analysis.get('algorithms', []),
                "start_line": chunk.get('start_line', 0),
                "end_line": chunk.get('end_line', 0),
                "timestamp": user_info.get('timestamp', datetime.utcnow().isoformat()),
                "commit_hash": user_info.get('commit_hash', '')
            }
        )

        # Store in Qdrant
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            print(f"✅ Stored embedding for {chunk.get('name', 'unknown')} (ID: {point_id})")

        except Exception as e:
            print(f"❌ Error storing embedding: {e}")
            raise

    async def search_similar_code(
        self,
        query: str,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar code using vector similarity

        Args:
            query: Natural language or code query
            limit: Maximum number of results to return
            filters: Optional filters (language, user_id, etc.)

        Returns:
            List of similar code results with metadata and scores
        """
        # Generate query embedding
        query_embedding = await self.generate_embedding(query)

        # Prepare Qdrant filters
        qdrant_filter = None
        if filters:
            conditions = []

            if 'language' in filters:
                conditions.append(
                    FieldCondition(
                        key="language",
                        match=MatchValue(value=filters['language'])
                    )
                )

            if 'user_id' in filters:
                conditions.append(
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=filters['user_id'])
                    )
                )

            if conditions:
                qdrant_filter = Filter(must=conditions)

        # Search in Qdrant
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=qdrant_filter
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "score": result.score,
                    "user_name": result.payload.get("user_name", ""),
                    "repository_url": result.payload.get("repository_url", ""),
                    "file_path": result.payload.get("file_path", ""),
                    "function_name": result.payload.get("function_name", ""),
                    "class_name": result.payload.get("class_name", ""),
                    "code_snippet": result.payload.get("code_snippet", ""),
                    "summary": result.payload.get("summary", ""),
                    "purpose": result.payload.get("purpose", ""),
                    "language": result.payload.get("language", ""),
                    "complexity_score": result.payload.get("complexity_score", 0),
                    "quality": result.payload.get("quality", ""),
                    "algorithms": result.payload.get("algorithms", []),
                    "start_line": result.payload.get("start_line", 0),
                    "end_line": result.payload.get("end_line", 0),
                })

            return formatted_results

        except Exception as e:
            print(f"❌ Error searching similar code: {e}")
            raise

    async def batch_store_embeddings(
        self,
        analyzed_chunks: List[Dict[str, Any]],
        user_info: Dict[str, Any]
    ):
        """
        Store multiple code embeddings in batch

        Args:
            analyzed_chunks: List of analyzed code chunks
            user_info: User metadata
        """
        for chunk in analyzed_chunks:
            analysis = chunk.get('analysis', {})
            await self.store_code_embedding(analysis, chunk, user_info)

    def store_code_embeddings(self, embeddings_data: List[Dict[str, Any]]):
        """
        Store multiple code embeddings in Qdrant (synchronous batch operation)

        This is a simplified version for Celery tasks that don't use async/await.

        Args:
            embeddings_data: List of dicts with 'id', 'content', and 'metadata'
        """
        try:
            points = []
            for data in embeddings_data:
                # Generate embedding synchronously (using openai.Embedding.create)
                import openai
                response = openai.embeddings.create(
                    model=self.embedding_model,
                    input=data['content'][:8000]  # Limit input size
                )
                embedding = response.data[0].embedding

                # Create point
                point = PointStruct(
                    id=data['id'],
                    vector=embedding,
                    payload=data['metadata']
                )
                points.append(point)

            # Batch upsert
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            print(f"✅ Stored {len(points)} embeddings in batch")

        except Exception as e:
            print(f"❌ Error storing code embeddings: {e}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the code embeddings collection

        Returns:
            Collection statistics and configuration
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": collection_info.vectors_count if hasattr(collection_info, 'vectors_count') else 0,
                "points_count": collection_info.points_count if hasattr(collection_info, 'points_count') else 0,
                "status": collection_info.status if hasattr(collection_info, 'status') else 'unknown',
                "config": {
                    "embedding_model": self.embedding_model,
                    "dimension": self.embedding_dimension,
                }
            }

        except Exception as e:
            print(f"❌ Error getting collection info: {e}")
            return {"error": str(e)}
