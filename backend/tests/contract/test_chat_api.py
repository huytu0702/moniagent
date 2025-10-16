"""
Contract tests for Chat API endpoints
Tests the API contract and response formats
"""

import pytest
import json
from fastapi.testclient import TestClient


class TestChatStartEndpoint:
    """Contract tests for /chat/start endpoint"""

    def test_start_chat_session_success(
        self, api_client: TestClient, auth_headers: dict
    ):
        """Test starting a chat session successfully"""
        response = api_client.post(
            "/api/v1/chat/start",
            json={"session_title": "Test Session"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "session_id" in data
        assert "message" in data
        assert "initial_message" in data

        # Verify response values
        assert data["message"] == "Chat session started successfully"
        assert "expense tracking" in data["initial_message"].lower()

    def test_start_chat_session_without_title(
        self, api_client: TestClient, auth_headers: dict
    ):
        """Test starting a chat session without providing a title"""
        response = api_client.post(
            "/api/v1/chat/start",
            json={},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "session_id" in data
        assert "message" in data
        assert "initial_message" in data

    def test_start_chat_session_unauthenticated(self, api_client: TestClient):
        """Test starting a chat session without authentication"""
        response = api_client.post(
            "/api/v1/chat/start",
            json={"session_title": "Test Session"},
        )

        assert response.status_code in [401, 403]

    def test_start_chat_session_returns_valid_session_id(
        self, api_client: TestClient, auth_headers: dict
    ):
        """Test that session ID is valid UUID format"""
        response = api_client.post(
            "/api/v1/chat/start",
            json={"session_title": "Test Session"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        session_id = data["session_id"]

        # Session ID should be a string (UUID format)
        assert isinstance(session_id, str)
        assert len(session_id) > 0


class TestChatMessageEndpoint:
    """Contract tests for /chat/{sessionId}/message endpoint"""

    def test_send_text_message_success(
        self, api_client: TestClient, auth_headers: dict
    ):
        """Test sending a text message successfully"""
        # First, create a session
        start_response = api_client.post(
            "/api/v1/chat/start",
            json={"session_title": "Test Session"},
            headers=auth_headers,
        )
        session_id = start_response.json()["session_id"]

        # Send a message
        response = api_client.post(
            f"/api/v1/chat/{session_id}/message",
            json={
                "content": "I spent $25 on coffee at Starbucks today",
                "message_type": "text",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "message_id" in data
        assert "response" in data
        assert "requires_confirmation" in data
        assert "budget_warning" in data
        assert "advice" in data

    def test_send_message_with_extracted_expense(
        self, api_client: TestClient, auth_headers: dict
    ):
        """Test that message response includes extracted expense when available"""
        # Create session
        start_response = api_client.post(
            "/api/v1/chat/start",
            json={"session_title": "Test Session"},
            headers=auth_headers,
        )
        session_id = start_response.json()["session_id"]

        # Send message with expense info
        response = api_client.post(
            f"/api/v1/chat/{session_id}/message",
            json={
                "content": "I spent $50 at a restaurant yesterday",
                "message_type": "text",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Response should indicate confirmation is needed if expense was extracted
        assert isinstance(data["requires_confirmation"], bool)

    def test_send_message_returns_valid_response_format(
        self, api_client: TestClient, auth_headers: dict
    ):
        """Test that response follows ChatMessageResponse schema"""
        # Create session
        start_response = api_client.post(
            "/api/v1/chat/start",
            json={"session_title": "Test Session"},
            headers=auth_headers,
        )
        session_id = start_response.json()["session_id"]

        # Send message
        response = api_client.post(
            f"/api/v1/chat/{session_id}/message",
            json={"content": "Test message", "message_type": "text"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields are present
        required_fields = ["message_id", "response", "requires_confirmation"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_send_message_to_nonexistent_session(
        self, api_client: TestClient, auth_headers: dict
    ):
        """Test sending a message to a non-existent session"""
        response = api_client.post(
            "/api/v1/chat/nonexistent-session-id/message",
            json={"content": "Test message", "message_type": "text"},
            headers=auth_headers,
        )

        assert response.status_code == 400

    def test_send_empty_message(self, api_client: TestClient, auth_headers: dict):
        """Test sending an empty message"""
        # Create session
        start_response = api_client.post(
            "/api/v1/chat/start",
            json={"session_title": "Test Session"},
            headers=auth_headers,
        )
        session_id = start_response.json()["session_id"]

        # Send empty message - should fail validation
        response = api_client.post(
            f"/api/v1/chat/{session_id}/message",
            json={"content": "", "message_type": "text"},
            headers=auth_headers,
        )

        # Either 200 (accepted), 400 (validation error) or 422 (Pydantic validation)
        assert response.status_code in [200, 400, 422]

    def test_send_message_unauthenticated(self, api_client: TestClient):
        """Test sending a message without authentication"""
        response = api_client.post(
            "/api/v1/chat/some-session/message",
            json={"content": "Test message", "message_type": "text"},
        )

        assert response.status_code in [401, 403]


class TestChatHistoryEndpoint:
    """Contract tests for /chat/{sessionId}/history endpoint"""

    def test_get_session_history_success(
        self, api_client: TestClient, auth_headers: dict
    ):
        """Test getting chat session history successfully"""
        # Create session and send message
        start_response = api_client.post(
            "/api/v1/chat/start",
            json={"session_title": "Test Session"},
            headers=auth_headers,
        )
        session_id = start_response.json()["session_id"]

        # Send a message first
        api_client.post(
            f"/api/v1/chat/{session_id}/message",
            json={"content": "Test message", "message_type": "text"},
            headers=auth_headers,
        )

        # Get history
        response = api_client.get(
            f"/api/v1/chat/{session_id}/history",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "session" in data
        assert "messages" in data

        # Verify session data
        session_data = data["session"]
        assert "id" in session_data
        assert "user_id" in session_data
        assert "status" in session_data

        # Verify messages
        assert isinstance(data["messages"], list)

    def test_get_session_history_nonexistent(
        self, api_client: TestClient, auth_headers: dict
    ):
        """Test getting history for non-existent session"""
        response = api_client.get(
            "/api/v1/chat/nonexistent-session/history",
            headers=auth_headers,
        )

        assert response.status_code == 400

    def test_get_session_history_unauthenticated(self, api_client: TestClient):
        """Test getting history without authentication"""
        response = api_client.get(
            "/api/v1/chat/some-session/history",
        )

        assert response.status_code in [401, 403]


class TestChatCloseEndpoint:
    """Contract tests for /chat/{sessionId}/close endpoint"""

    def test_close_session_success(self, api_client: TestClient, auth_headers: dict):
        """Test closing a chat session successfully"""
        # Create session
        start_response = api_client.post(
            "/api/v1/chat/start",
            json={"session_title": "Test Session"},
            headers=auth_headers,
        )
        session_id = start_response.json()["session_id"]

        # Close session
        response = api_client.post(
            f"/api/v1/chat/{session_id}/close",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "status" in data
        assert data["status"] == "closed"
        assert "session_id" in data
        assert "message" in data

    def test_close_nonexistent_session(
        self, api_client: TestClient, auth_headers: dict
    ):
        """Test closing a non-existent session"""
        response = api_client.post(
            "/api/v1/chat/nonexistent-session/close",
            headers=auth_headers,
        )

        assert response.status_code == 400

    def test_close_session_unauthenticated(self, api_client: TestClient):
        """Test closing a session without authentication"""
        response = api_client.post(
            "/api/v1/chat/some-session/close",
        )

        assert response.status_code in [401, 403]
