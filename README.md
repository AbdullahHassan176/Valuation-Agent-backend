# Valuation-Agent-backend

Backend orchestrator (FastAPI+LangGraph) for Valuation Agent Workspace.

## How to run (Phase 0)

### Local Development
```bash
# Install dependencies
pip install fastapi uvicorn[standard] pydantic httpx

# Set environment variables
export PORT=8000
export API_BASE_URL=http://api:9000

# Run the server
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Docker
```bash
# From parent directory
docker compose up --build
```

### Health Check
- GET http://localhost:8000/healthz → `{"ok": true, "service": "backend", "api_base_url": "http://api:9000", "sdk_available": true}`

### Available Endpoints
- POST /runs - Create a new valuation run (proxies to API)
- GET /runs/{id} - Get run status (proxies to API)
- GET /runs/{id}/result - Get run result (proxies to API)

### Testing
```bash
# Install test dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ -v --cov=. --cov-report=html
```
