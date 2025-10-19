import pytest
import httpx
from fastapi.testclient import TestClient
from unittest.mock import patch
import respx
from datetime import date, datetime

from ..app import app
from ..sdk.models import RunRequest, RunStatus, PVBreakdown, IRSSpec

client = TestClient(app)

# Sample test data
sample_irs_spec = IRSSpec(
    notional=1000000.0,
    currency="USD",
    payFixed=True,
    fixedRate=0.05,
    floatIndex="USD-LIBOR-3M",
    effective=date(2024, 1, 1),
    maturity=date(2025, 1, 1),
    dcFixed="ACT/360",
    dcFloat="ACT/360",
    freqFixed="Q",
    freqFloat="Q",
    calendar="USD",
    bdc="FOLLOWING"
)

sample_run_request = RunRequest(
    spec=sample_irs_spec,
    asOf=date(2024, 1, 1),
    marketDataProfile="default",
    approach=["discount_curve"]
)

sample_run_status = RunStatus(
    id="test-run-123",
    status="queued",
    created_at=datetime(2024, 1, 1, 12, 0, 0),
    updated_at=datetime(2024, 1, 1, 12, 0, 0),
    request=sample_run_request,
    error_message=None
)

sample_pv_breakdown = PVBreakdown(
    total_pv=0.0,
    components={"fixed_leg": 0.0, "floating_leg": 0.0, "net_pv": 0.0},
    currency="USD",
    data_hash="dummy_hash",
    model_hash="dummy_model_hash",
    calculation_time=1.5
)

class TestRunsRouter:
    """Test the runs router endpoints"""
    
    @respx.mock
    def test_create_run_success(self):
        """Test successful run creation"""
        # Mock API response
        respx.post("http://api:9000/runs").mock(
            return_value=httpx.Response(201, json=sample_run_status.dict())
        )
        
        response = client.post("/runs", json=sample_run_request.dict())
        
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "test-run-123"
        assert data["status"] == "queued"
        assert data["request"]["spec"]["notional"] == 1000000.0
    
    @respx.mock
    def test_create_run_api_error(self):
        """Test API error handling"""
        # Mock API error response
        respx.post("http://api:9000/runs").mock(
            return_value=httpx.Response(400, text="Invalid request")
        )
        
        response = client.post("/runs", json=sample_run_request.dict())
        
        assert response.status_code == 400
        assert "API error" in response.json()["detail"]
    
    @respx.mock
    def test_create_run_connection_error(self):
        """Test connection error handling"""
        # Mock connection error
        respx.post("http://api:9000/runs").mock(side_effect=httpx.ConnectError("Connection failed"))
        
        response = client.post("/runs", json=sample_run_request.dict())
        
        assert response.status_code == 503
        assert "Failed to connect to API" in response.json()["detail"]
    
    @respx.mock
    def test_get_run_success(self):
        """Test successful run retrieval"""
        # Mock API response
        respx.get("http://api:9000/runs/test-run-123").mock(
            return_value=httpx.Response(200, json=sample_run_status.dict())
        )
        
        response = client.get("/runs/test-run-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-run-123"
        assert data["status"] == "queued"
    
    @respx.mock
    def test_get_run_not_found(self):
        """Test run not found handling"""
        # Mock 404 response
        respx.get("http://api:9000/runs/nonexistent").mock(
            return_value=httpx.Response(404, text="Run not found")
        )
        
        response = client.get("/runs/nonexistent")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @respx.mock
    def test_get_run_result_success(self):
        """Test successful run result retrieval"""
        # Mock API response
        respx.get("http://api:9000/runs/test-run-123/result").mock(
            return_value=httpx.Response(200, json=sample_pv_breakdown.dict())
        )
        
        response = client.get("/runs/test-run-123/result")
        
        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == "test-run-123"
        assert data["total_pv"] == 0.0
        assert "components" in data
    
    @respx.mock
    def test_get_run_result_not_found(self):
        """Test run result not found handling"""
        # Mock 404 response
        respx.get("http://api:9000/runs/nonexistent/result").mock(
            return_value=httpx.Response(404, text="Run not found")
        )
        
        response = client.get("/runs/nonexistent/result")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_invalid_request_schema(self):
        """Test invalid request schema validation"""
        invalid_request = {
            "spec": {
                "notional": "invalid",  # Should be number
                "ccy": "USD",
                # Missing required fields
            },
            "asOf": "2024-01-01",
            "marketDataProfile": "default",
            "approach": ["discount_curve"]
        }
        
        response = client.post("/runs", json=invalid_request)
        
        assert response.status_code == 422  # Validation error
        assert "validation error" in response.json()["detail"][0]["type"]

