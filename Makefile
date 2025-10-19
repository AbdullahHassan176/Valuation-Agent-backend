# Valuation Agent Backend Makefile

.PHONY: help run test clean vectordb.clean docs.ingest.sample install dev

# Default target
help:
	@echo "Valuation Agent Backend - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make run          - Start the development server"
	@echo "  make test         - Run all tests"
	@echo "  make install      - Install dependencies"
	@echo "  make dev          - Install dev dependencies"
	@echo ""
	@echo "Data Management:"
	@echo "  make vectordb.clean     - Clean vector database"
	@echo "  make docs.ingest.sample - Ingest sample documents"
	@echo "  make clean              - Clean all generated files"
	@echo ""
	@echo "Testing:"
	@echo "  make test.unit     - Run unit tests only"
	@echo "  make test.integration - Run integration tests only"
	@echo "  make test.coverage - Run tests with coverage"

# Development server
run:
	@echo "🚀 Starting Valuation Agent Backend..."
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Run tests
test:
	@echo "🧪 Running all tests..."
	poetry run pytest -q

# Run unit tests only
test.unit:
	@echo "🧪 Running unit tests..."
	poetry run pytest tests/test_*.py -q

# Run integration tests only
test.integration:
	@echo "🧪 Running integration tests..."
	poetry run pytest tests/test_*integration*.py -q

# Run tests with coverage
test.coverage:
	@echo "🧪 Running tests with coverage..."
	poetry run pytest --cov=app --cov-report=html --cov-report=term

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	poetry install

# Install dev dependencies
dev:
	@echo "📦 Installing dev dependencies..."
	poetry install --with dev

# Clean vector database
vectordb.clean:
	@echo "🧹 Cleaning vector database..."
	rm -rf .vector/ifrs
	@echo "✅ Vector database cleaned"

# Ingest sample documents
docs.ingest.sample:
	@echo "📄 Ingesting sample documents..."
	@if [ ! -d "data/bootstrap" ]; then \
		echo "Creating data/bootstrap directory..."; \
		mkdir -p data/bootstrap; \
	fi
	@if [ ! -f "data/bootstrap/sample_ifrs13.txt" ]; then \
		echo "Creating sample IFRS 13 document..."; \
		echo "IFRS 13 - Fair Value Measurement" > data/bootstrap/sample_ifrs13.txt; \
		echo "" >> data/bootstrap/sample_ifrs13.txt; \
		echo "4.1 Fair Value Measurement" >> data/bootstrap/sample_ifrs13.txt; \
		echo "Fair value is the price that would be received to sell an asset or paid to transfer a liability in an orderly transaction between market participants at the measurement date." >> data/bootstrap/sample_ifrs13.txt; \
		echo "" >> data/bootstrap/sample_ifrs13.txt; \
		echo "4.1.1 Principal Market" >> data/bootstrap/sample_ifrs13.txt; \
		echo "The principal market is the market with the greatest volume and level of activity for the asset or liability." >> data/bootstrap/sample_ifrs13.txt; \
	fi
	@echo "Uploading sample document..."
	curl -X POST "http://localhost:8001/api/v1/docs/upload" \
		-F "file=@data/bootstrap/sample_ifrs13.txt" \
		-H "X-API-Key: test-key" || echo "⚠️  Server not running. Start with 'make run' first."
	@echo "Ingesting sample document..."
	curl -X POST "http://localhost:8001/api/v1/docs/ingest" \
		-H "Content-Type: application/json" \
		-H "X-API-Key: test-key" \
		-d '{"doc_id": "sample_ifrs13", "standard": "IFRS 13"}' || echo "⚠️  Server not running. Start with 'make run' first."
	@echo "✅ Sample documents ingested"

# Clean all generated files
clean:
	@echo "🧹 Cleaning generated files..."
	rm -rf .run/
	rm -rf .vector/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf __pycache__/
	rm -rf app/__pycache__/
	rm -rf tests/__pycache__/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	@echo "✅ Cleaned all generated files"

# Setup development environment
setup:
	@echo "🔧 Setting up development environment..."
	make install
	make vectordb.clean
	mkdir -p .run
	mkdir -p .vector/ifrs
	@echo "✅ Development environment ready"

# Check code quality
lint:
	@echo "🔍 Running code quality checks..."
	poetry run black --check .
	poetry run isort --check-only .
	poetry run flake8 .

# Format code
format:
	@echo "🎨 Formatting code..."
	poetry run black .
	poetry run isort .

# Generate API documentation
docs:
	@echo "📚 Generating API documentation..."
	@echo "API documentation available at: http://localhost:8001/docs"
	@echo "ReDoc documentation available at: http://localhost:8001/redoc"

# Health check
health:
	@echo "🏥 Checking service health..."
	curl -f http://localhost:8001/healthz || echo "❌ Service not running"

# Show logs
logs:
	@echo "📋 Showing recent logs..."
	tail -f .run/audit.log 2>/dev/null || echo "No audit log found"

# Evaluation targets
eval.ifrs:
	@echo "🧪 Running IFRS Q&A evaluation..."
	poetry run python eval/run_eval.py
	@echo "✅ IFRS evaluation completed"

eval.redteam:
	@echo "🔴 Running red-team adversarial evaluation..."
	poetry run python eval/run_redteam.py
	@echo "✅ Red-team evaluation completed"
