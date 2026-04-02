.PHONY: dev backend frontend test lint format docker clean

# Start both servers for development
dev:
	@echo "Starting backend and frontend..."
	@cd backend && python main.py &
	@cd frontend && npm run dev

# Start backend only
backend:
	cd backend && python main.py

# Start frontend only
frontend:
	cd frontend && npm run dev

# Run all tests
test:
	cd backend && python test_detector.py
	python scripts/test_api.py

# Run benchmark
benchmark:
	python scripts/download_test_data.py
	python scripts/benchmark.py test_data/real test_data/ai_generated

# Lint and format
lint:
	black --check --line-length 120 backend/ scripts/
	bandit -r backend/ -ll --exclude backend/test_detector.py -q

format:
	black --line-length 120 backend/ scripts/

# Docker
docker:
	docker-compose up --build

docker-bg:
	docker-compose up --build -d

docker-down:
	docker-compose down

# Install dependencies
install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

# Install ML models for better accuracy
install-ml:
	cd backend && python install_ml.py

# Generate API key
api-key:
	@read -p "Key name: " name; python scripts/generate_api_key.py --name "$$name"

# Clean build artifacts
clean:
	find backend -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/dist frontend/node_modules/.vite
	rm -rf test_data benchmark_results.json
