"""
TDD Tests for RAG API Schema Changes (repository_id → user_id)

Following TDD methodology:
1. RED: Write failing tests for new schema
2. GREEN: Update API to make tests pass
3. REFACTOR: Clean up implementation
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Mock CodeAnalyzer to avoid tree-sitter import issues in test environment
with patch('app.services.code_analyzer.CodeAnalyzer'):
    from app.main import app

client = TestClient(app)


class TestRAGReindexAPISchema:
    """Test RAG reindex endpoint accepts user_id parameter"""

    def test_reindex_endpoint_accepts_user_id_in_request_body(self):
        """
        POST /api/v1/rag/reindex should accept user_id in request body

        Expected behavior:
        - Request body: {"user_id": 1}
        - Should NOT require repository_id
        """
        with patch('app.tasks.rag_indexing.reindex_repository') as mock_task:
            mock_task.delay.return_value = MagicMock(id="task-123")

            response = client.post(
                "/api/v1/rag/reindex",
                json={"user_id": 1}
            )

            # Should accept the request
            assert response.status_code == 202

    def test_reindex_endpoint_rejects_repository_id_parameter(self):
        """
        POST /api/v1/rag/reindex should reject old repository_id parameter

        Expected behavior:
        - Request body: {"repository_id": 1}
        - Should return 422 Unprocessable Entity (validation error)
        """
        response = client.post(
            "/api/v1/rag/reindex",
            json={"repository_id": 1}
        )

        # Should reject old parameter name
        assert response.status_code == 422
        assert "user_id" in response.text or "required" in response.text.lower()

    def test_reindex_endpoint_calls_celery_task_with_user_id(self):
        """
        POST /api/v1/rag/reindex should pass user_id to Celery task

        Expected behavior:
        - Calls reindex_repository.delay(user_id=1)
        - NOT reindex_repository.delay(repository_id=1)
        """
        with patch('app.tasks.rag_indexing.reindex_repository') as mock_task:
            mock_task.delay.return_value = MagicMock(id="task-456")

            response = client.post(
                "/api/v1/rag/reindex",
                json={"user_id": 1}
            )

            # Should call Celery task with user_id
            mock_task.delay.assert_called_once_with(1)  # positional arg = user_id

    def test_reindex_endpoint_returns_correct_response_format(self):
        """
        POST /api/v1/rag/reindex should return proper response with task_id

        Expected response:
        {
            "status": "queued",
            "task_id": "task-789",
            "message": "User 1 repository reindexing queued. Task ID: task-789"
        }
        """
        with patch('app.tasks.rag_indexing.reindex_repository') as mock_task:
            mock_task.delay.return_value = MagicMock(id="task-789")

            response = client.post(
                "/api/v1/rag/reindex",
                json={"user_id": 1}
            )

            data = response.json()

            assert data["status"] == "queued"
            assert data["task_id"] == "task-789"
            assert "User 1" in data["message"]
            assert "task-789" in data["message"]

    def test_reindex_endpoint_validates_user_id_is_integer(self):
        """
        POST /api/v1/rag/reindex should validate user_id is an integer

        Expected behavior:
        - Invalid types should return 422 validation error
        """
        # String should fail
        response = client.post(
            "/api/v1/rag/reindex",
            json={"user_id": "not_an_integer"}
        )
        assert response.status_code == 422

        # Null should fail
        response = client.post(
            "/api/v1/rag/reindex",
            json={"user_id": None}
        )
        assert response.status_code == 422

    def test_reindex_endpoint_requires_user_id(self):
        """
        POST /api/v1/rag/reindex should require user_id parameter

        Expected behavior:
        - Missing user_id should return 422 validation error
        """
        response = client.post(
            "/api/v1/rag/reindex",
            json={}
        )

        assert response.status_code == 422
        data = response.json()
        # FastAPI validation error should mention missing field
        assert "user_id" in str(data).lower() or "required" in str(data).lower()


class TestRAGReindexRequestModel:
    """Test ReindexRequest Pydantic model"""

    def test_reindex_request_model_accepts_user_id(self):
        """
        ReindexRequest model should have user_id field, not repository_id
        """
        from app.routers.rag import ReindexRequest

        # Should successfully create with user_id
        request = ReindexRequest(user_id=1)
        assert request.user_id == 1

    def test_reindex_request_model_rejects_repository_id(self):
        """
        ReindexRequest model should NOT have repository_id field
        """
        from app.routers.rag import ReindexRequest
        from pydantic import ValidationError

        # Should raise validation error for old field name
        with pytest.raises(ValidationError):
            ReindexRequest(repository_id=1)

    def test_reindex_request_model_schema_has_correct_field_description(self):
        """
        ReindexRequest model schema should describe user_id correctly
        """
        from app.routers.rag import ReindexRequest

        schema = ReindexRequest.model_json_schema()

        # Should have user_id in schema
        assert "user_id" in schema["properties"]

        # Should NOT have repository_id in schema
        assert "repository_id" not in schema["properties"]

        # Field description should mention user
        user_id_field = schema["properties"]["user_id"]
        assert "user" in user_id_field.get("description", "").lower()
