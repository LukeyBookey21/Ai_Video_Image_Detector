#!/bin/bash
# AI Detector — start both servers
set -e

echo "=========================================="
echo "  AI Detector - Starting..."
echo "=========================================="

# Install deps if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    (cd frontend && npm install)
fi

# Start backend
echo "Starting backend..."
(cd backend && python main.py) &
BACKEND_PID=$!

# Wait for backend
sleep 5

# Start frontend
echo "Starting frontend..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

sleep 3
echo ""
echo "=========================================="
echo "  App is running!"
echo "  Web UI:  http://localhost:5173"
echo "  API:     http://localhost:8000"
echo "  CLI:     python cli.py --help"
echo "=========================================="
echo ""
echo "Press Ctrl+C to stop"

# Open browser
if command -v xdg-open &>/dev/null; then
    xdg-open http://localhost:5173
elif command -v open &>/dev/null; then
    open http://localhost:5173
fi

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
