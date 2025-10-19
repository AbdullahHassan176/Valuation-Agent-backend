# Valuation Agent Backend

FastAPI backend service for the Valuation Agent platform.

## Features

- FastAPI with async support
- Pydantic v2 for data validation
- Document ingestion and processing
- Text chunking and vector storage
- File-based vector store (ChromaDB-ready)
- Document upload and processing endpoints
- Audit logging middleware
- Health check endpoints

## IFRS Agent Quickstart

### 1. Environment Setup
```bash
# Install dependencies
make install

# Setup development environment
make setup
```

### 2. Start the Server
```bash
# Start development server
make run
```
Server will be available at `http://localhost:8001`

### 3. Ingest Sample Documents
```bash
# Ingest sample IFRS documents
make docs.ingest.sample
```

### 4. Ask IFRS Questions
```bash
# Ask a question about IFRS standards
curl -X POST "http://localhost:8001/api/v1/ifrs/ask" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{"question": "What is fair value measurement?", "standard_filter": "IFRS 13"}'
```

### 5. Analyze Documents
```bash
# Analyze a document for IFRS compliance
curl -X POST "http://localhost:8001/api/v1/feedback/analyze" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{"doc_id": "sample_ifrs13", "standard": "IFRS 13"}'
```

## Prerequisites

- Python 3.11+
- Poetry (for dependency management)

## Installation

1. Clone the repository and navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Copy the environment file and configure:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Running Locally

### Development Mode

```bash
poetry run uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/healthz

### Production Mode

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Docker

Build and run with Docker:

```bash
docker build -t valuation-backend .
docker run -p 8000:8000 valuation-backend
```

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `EMBEDDINGS_MODEL`: Embedding model to use
- `LLM_MODEL`: LLM model to use
- `VECTOR_DIR`: Directory for vector storage
- `DOC_STORE`: Directory for document storage

## API Endpoints

### Core Endpoints
- `GET /`: Root endpoint with API information
- `GET /healthz`: Health check endpoint
- `GET /docs`: Interactive API documentation

### Document Ingestion Endpoints
- `POST /api/v1/docs/upload`: Upload a document file
- `POST /api/v1/docs/ingest`: Ingest a document into the vector store
- `GET /api/v1/docs/count`: Get the number of documents in the vector store
- `GET /api/v1/docs/health`: Health check for ingestion service

### IFRS Question-Answering Endpoints
- `POST /api/v1/ifrs/ask`: Ask questions about IFRS standards (with policy guardrails)
- `GET /api/v1/ifrs/health`: Health check for IFRS service
- `GET /api/v1/ifrs/standards`: Get available IFRS standards
- `POST /api/v1/ifrs/validate-policy`: Validate IFRS answer against policy guardrails

### Document Feedback Analysis Endpoints
- `POST /api/v1/feedback/analyze`: Analyze document against IFRS standards
- `GET /api/v1/feedback/health`: Health check for feedback service
- `GET /api/v1/feedback/checklist/{standard}`: Get checklist for specific IFRS standard
- `GET /api/v1/feedback/standards`: Get supported IFRS standards for analysis

### Constrained Chat Agent Endpoints
- `POST /api/v1/chat`: Send chat message and get response
- `GET /api/v1/chat/stream`: Stream chat response with Server-Sent Events
- `GET /api/v1/chat/health`: Health check for chat service
- `GET /api/v1/chat/tools`: Get available chat tools
- `GET /api/v1/chat/intent`: Classify user intent from message

### Security Features
- **API Key Authentication**: X-API-Key header required for protected endpoints
- **PII Sanitization**: Automatic redaction of emails, phones, IBANs, SSNs, credit cards
- **Rate Limiting**: 60 requests/minute per IP with 10 request burst
- **Request Size Limits**: 10MB maximum request size
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, CSP, etc.
- **Audit Logging**: PII-sanitized interaction logging

### Audit and Logging
- All interactions are automatically logged to SQLite database
- Database location: `.run/audit.db`
- Captures: request, response, citations, confidence, tool used, documents
- PII sanitization applied to all audit logs

## Policy Guardrails

The system includes comprehensive policy guardrails to ensure safe and compliant IFRS responses:

### Policy Configuration (`app/policy/policies.yml`)
- **Citation Requirements**: Minimum citations, required fields
- **Confidence Thresholds**: Minimum confidence levels (0.65)
- **Language Restrictions**: Disallowed overconfident language
- **Content Restrictions**: Prohibited advice types
- **IFRS-Specific Policies**: Standard-specific restrictions

### Guardrail Features
- **Overconfident Language Detection**: Catches "guarantee", "certainly", "always", etc.
- **Restricted Advice Detection**: Blocks "tax structuring", "legal representation", etc.
- **Confidence Enforcement**: Automatically ABSTAIN if confidence < 0.65
- **Citation Validation**: Requires proper IFRS citations
- **Content Length Limits**: Enforces appropriate response lengths

### Policy Violations → ABSTAIN
When policy violations are detected, responses are automatically converted to ABSTAIN status with detailed violation reasons.

## Document Feedback Analysis

The system provides structured feedback analysis for uploaded documents against IFRS standards:

### Feedback Components
- **ChecklistItem**: Individual compliance items with met/unmet status
- **Feedback**: Overall analysis with status, summary, and confidence
- **Citations**: Source references for each checklist item
- **Critical Items**: High-priority requirements that must be met

### Analysis Process
1. **Document Loading**: Retrieve document content from vector store
2. **Checklist Generation**: Create questions for each IFRS requirement
3. **RAG Analysis**: Use IFRS agent to analyze each requirement
4. **Status Determination**: 
   - `OK`: All critical items met, high confidence
   - `NEEDS_REVIEW`: Critical items failed, requires attention
   - `ABSTAIN`: Low confidence or insufficient information

### IFRS 13 Checklist (20 Items)
- **Hierarchy**: Level classification and justification
- **Market**: Principal market identification and access
- **Day-1 P&L**: Calculation and disclosure requirements
- **Risk**: Non-performance risk assessment
- **Observability**: Input observability requirements
- **Valuation**: Technique appropriateness and consistency
- **Disclosure**: Required financial statement disclosures
- **Assumptions**: Market participant perspective

## Constrained Chat Agent

The system includes a constrained chat agent that only uses specific tools and never answers off-the-cuff:

### Chat Agent Features
- **Tool-Only Responses**: Never generates responses without using tools
- **Intent Classification**: Automatically classifies user intent
- **Policy Validation**: All responses validated by policy guardrails
- **SSE Streaming**: Real-time streaming with Server-Sent Events
- **Constrained Capabilities**: Limited to IFRS questions, document analysis, and document search

### Available Tools
1. **`ifrs_ask`**: Ask questions about IFRS standards
2. **`analyze_document`**: Analyze documents for IFRS compliance
3. **`search_documents`**: Search for available documents

### Intent Classification
- **`ask_ifrs`**: IFRS questions and compliance queries
- **`analyze_doc`**: Document analysis requests
- **`search_docs`**: Document search requests
- **`unknown`**: Unrecognized intents (returns guidance)

### SSE Streaming Events
- **`TOOL_CALLED`**: Tool execution started
- **`TOKEN`**: Individual response tokens
- **`CITATIONS`**: Source citations
- **`CONFIDENCE`**: Confidence score and status
- **`DONE`**: Response complete

### Response Format
```json
{
  "message": "Based on IFRS 13, fair value measurement...",
  "citations": [{"standard": "IFRS 13", "paragraph": "4.1.1", "section": "Fair Value"}],
  "confidence": 0.85,
  "tool_used": "ifrs_ask",
  "status": "OK"
}
```

## Audit and Interaction Logging

The system includes comprehensive audit logging for all interactions:

### Audit Database Schema
- **`interactions`**: Main interaction records with user, question, response, status, confidence
- **`interaction_citations`**: Citations linked to interactions
- **`interaction_documents`**: Document IDs linked to interactions

### Captured Data
- **User Information**: User ID from `X-USER` header
- **Request Details**: Question, intent, tool used, document ID
- **Response Details**: Generated response, status, confidence score
- **Citations**: Standard, paragraph, section references
- **Documents**: Document IDs used in analysis
- **Metadata**: Timestamp, model version, vector directory

### Automatic Logging
- **IFRS Questions**: `/api/v1/ifrs/ask` endpoint interactions
- **Chat Messages**: `/api/v1/chat` endpoint interactions  
- **Document Analysis**: `/api/v1/feedback/analyze` endpoint interactions
- **Middleware Integration**: Automatic capture without code changes

### Database Location
- **SQLite Database**: `.run/audit.db`
- **Automatic Creation**: Tables created on first use
- **Persistent Storage**: All interactions preserved across restarts

## Document Ingestion

The system supports document ingestion with the following workflow:

1. **Upload**: Upload a document file (currently supports .txt files)
2. **Parse**: Extract text content from the document
3. **Chunk**: Split text into manageable chunks with metadata
4. **Store**: Save chunks to the vector store with embeddings

### Supported File Types
- `.txt` - Text files (currently supported)
- `.pdf` - PDF documents (planned)
- `.docx` - Word documents (planned)

### Example Usage

```bash
# Upload a document
curl -X POST "http://localhost:8001/api/v1/docs/upload" \
  -F "file=@document.txt"

# Ingest the document
curl -X POST "http://localhost:8001/api/v1/docs/ingest" \
  -H "Content-Type: application/json" \
  -d '{"doc_id": "your-doc-id", "standard": "IFRS 13"}'

# Check document count
curl "http://localhost:8001/api/v1/docs/count"

# Ask IFRS question
curl -X POST "http://localhost:8001/api/v1/ifrs/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is fair value measurement?", "standard_filter": "IFRS 13"}'

# Get available IFRS standards
curl "http://localhost:8001/api/v1/ifrs/standards"

# Validate policy compliance
curl -X POST "http://localhost:8001/api/v1/ifrs/validate-policy" \
  -H "Content-Type: application/json" \
  -d '{"status": "OK", "answer": "Based on IFRS 13...", "citations": [...], "confidence": 0.8}'

# Analyze document feedback
curl -X POST "http://localhost:8001/api/v1/feedback/analyze" \
  -H "Content-Type: application/json" \
  -d '{"doc_id": "valuation-memo-2023", "standard": "IFRS 13"}'

# Get IFRS 13 checklist
curl "http://localhost:8001/api/v1/feedback/checklist/IFRS%2013"

# Chat with agent
curl -X POST "http://localhost:8001/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is fair value measurement?", "standard": "IFRS 13"}'

# Stream chat response
curl "http://localhost:8001/api/v1/chat/stream?message=What%20is%20fair%20value%20measurement?&standard=IFRS%2013"

# Get available tools
curl "http://localhost:8001/api/v1/chat/tools"

# With API key authentication
curl -X POST "http://localhost:8001/api/v1/ifrs/ask" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key" \
  -d '{"question": "What is fair value measurement?", "standard_filter": "IFRS 13"}'
```

## API Contracts

### IFRSAnswer Response
```json
{
  "status": "OK" | "ABSTAIN",
  "answer": "string",
  "citations": [
    {
      "standard": "string",
      "paragraph": "string | null",
      "section": "string | null"
    }
  ],
  "confidence": 0.0-1.0
}
```

### Feedback Response
```json
{
  "status": "OK" | "NEEDS_REVIEW" | "ABSTAIN",
  "summary": "string",
  "items": [
    {
      "id": "string",
      "key": "string", 
      "description": "string",
      "met": boolean,
      "notes": "string | null",
      "citations": [
        {
          "standard": "string",
          "paragraph": "string | null",
          "section": "string | null"
        }
      ],
      "is_critical": boolean
    }
  ],
  "confidence": 0.0-1.0
}
```

### Error Responses
```json
{
  "detail": "string",
  "status_code": 400 | 401 | 413 | 429 | 500
}
```

**Error Codes:**
- `400` - Bad Request (empty question, invalid data)
- `401` - Unauthorized (missing/invalid API key)
- `413` - Payload Too Large (request > 10MB)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error

## Development

### Code Quality

```bash
# Format code
poetry run black app/
poetry run isort app/

# Lint code
poetry run flake8 app/
poetry run mypy app/
```

### Testing

```bash
poetry run pytest
```

## Architecture

```
app/
├── main.py              # FastAPI application
├── settings.py          # Configuration
├── deps.py              # Dependencies
├── models/
│   └── documents.py     # Document data models
├── utils/
│   └── hashing.py       # File hashing utilities
├── rag/
│   ├── loader.py        # Document parsing
│   ├── chunking.py      # Text chunking
│   ├── embed.py         # Embedding utilities
│   └── store.py         # Vector storage
├── routers/
│   ├── health.py        # Health endpoints
│   └── ingest.py        # Document ingestion endpoints
└── middleware/
    └── audit.py         # Audit logging
```

## Directory Structure

- `app/`: Main application code
- `data/bootstrap/`: Directory for IFRS files (empty, ready for files)
- `.docs/`: Document storage (created automatically)
- `.vector/ifrs/`: Vector store (created automatically)

## License

Proprietary - Valuation Agent Platform