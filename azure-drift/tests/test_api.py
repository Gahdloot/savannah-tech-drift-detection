import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

from src.api.main import app

@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)

class TestAPI:
    """Test suite for API endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_initialize_drift_detector(self, client, mock_azure_credentials):
        """Test drift detector initialization endpoint."""
        with patch('src.api.main.DriftDetector') as mock_detector:
            mock_detector.return_value = MagicMock()
            
            response = client.post(
                "/initialize",
                json={
                    "subscription_id": mock_azure_credentials["subscription_id"],
                    "resource_group": "test-rg"
                }
            )
            
            assert response.status_code == 200
            assert response.json() == {"status": "initialized"}

    def test_collect_configuration(self, client, mock_snapshot_data):
        """Test configuration collection endpoint."""
        with patch('src.api.main.DriftDetector') as mock_detector:
            mock_instance = MagicMock()
            mock_instance.collect_configuration.return_value = mock_snapshot_data
            mock_detector.return_value = mock_instance
            
            response = client.post("/collect")
            
            assert response.status_code == 200
            assert response.json() == mock_snapshot_data

    def test_get_latest_snapshot(self, client, mock_snapshot_data):
        """Test get latest snapshot endpoint."""
        with patch('src.api.main.DriftDetector') as mock_detector:
            mock_instance = MagicMock()
            mock_instance.get_latest_snapshot.return_value = mock_snapshot_data
            mock_detector.return_value = mock_instance
            
            response = client.get("/latest-snapshot")
            
            assert response.status_code == 200
            assert response.json() == mock_snapshot_data

    def test_get_latest_drift(self, client, mock_drift_report):
        """Test get latest drift report endpoint."""
        with patch('src.api.main.DriftDetector') as mock_detector:
            mock_instance = MagicMock()
            mock_instance.get_latest_drift_report.return_value = mock_drift_report
            mock_detector.return_value = mock_instance
            
            response = client.get("/latest-drift")
            
            assert response.status_code == 200
            assert response.json() == mock_drift_report

    def test_error_handling(self, client):
        """Test error handling in API endpoints."""
        with patch('src.api.main.DriftDetector') as mock_detector:
            mock_instance = MagicMock()
            mock_instance.collect_configuration.side_effect = Exception("API Error")
            mock_detector.return_value = mock_instance
            
            response = client.post("/collect")
            
            assert response.status_code == 500
            assert "error" in response.json()

    def test_invalid_input(self, client):
        """Test handling of invalid input."""
        response = client.post(
            "/initialize",
            json={
                "subscription_id": "invalid-id",
                "resource_group": ""  # Empty resource group
            }
        )
        
        assert response.status_code == 400
        assert "error" in response.json()

    def test_rate_limiting(self, client, mock_snapshot_data):
        """Test rate limiting functionality."""
        with patch('src.api.main.DriftDetector') as mock_detector:
            mock_instance = MagicMock()
            mock_instance.collect_configuration.return_value = mock_snapshot_data
            mock_detector.return_value = mock_instance
            
            # Make multiple requests in quick succession
            responses = [client.post("/collect") for _ in range(10)]
            
            # Check if rate limiting is applied
            assert any(response.status_code == 429 for response in responses)

    def test_authentication(self, client):
        """Test authentication requirements."""
        # Test without authentication
        response = client.get("/latest-snapshot")
        assert response.status_code == 401
        
        # Test with invalid token
        response = client.get(
            "/latest-snapshot",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
        
        # Test with valid token
        with patch('src.api.main.validate_token') as mock_validate:
            mock_validate.return_value = True
            response = client.get(
                "/latest-snapshot",
                headers={"Authorization": "Bearer valid-token"}
            )
            assert response.status_code == 200

    def test_cors_headers(self, client):
        """Test CORS headers in responses."""
        response = client.options("/health")
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers

    def test_content_type(self, client, mock_snapshot_data):
        """Test content type in responses."""
        with patch('src.api.main.DriftDetector') as mock_detector:
            mock_instance = MagicMock()
            mock_instance.get_latest_snapshot.return_value = mock_snapshot_data
            mock_detector.return_value = mock_instance
            
            response = client.get("/latest-snapshot")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json" 