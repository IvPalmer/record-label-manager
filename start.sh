#!/bin/bash

# Record Label Manager - One-Click Startup Script
# This script starts both backend and frontend and opens the browser

echo "🎵 Starting Record Label Manager..."
echo "=================================="

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to cleanup background processes on exit
cleanup() {
    echo -e "\n🛑 Shutting down servers..."
    pkill -f "python.*manage.py.*runserver" 2>/dev/null
    pkill -f "npm.*run.*dev" 2>/dev/null || pkill -f "vite" 2>/dev/null
    exit 0
}

# Set up trap to cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Check if backend virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "❌ Virtual environment not found. Please set up the backend first:"
    echo "   cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if frontend node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Node modules not found. Installing frontend dependencies..."
    if command -v npm >/dev/null 2>&1; then
        npm install
    else
        echo "❌ npm not found. Please install Node.js first."
        exit 1
    fi
fi

# Start Django backend
echo "🚀 Starting Django backend server..."
cd backend

# Check if virtual environment activation works
if [ ! -f "venv/bin/activate" ]; then
    echo "❌ Virtual environment not found at backend/venv/bin/activate"
    echo "💡 Setting up virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Test if Django is working
if ! python manage.py check --deploy 2>/dev/null; then
    echo "⚠️  Django check failed, but attempting to start server anyway..."
fi

python manage.py runserver 127.0.0.1:8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start React frontend  
echo "🚀 Starting React frontend server..."
npm run dev > logs/frontend.log 2>&1 &
FRONTEND_PID=$!

# Create logs directory if it doesn't exist
mkdir -p logs

# Wait for servers to fully start
echo "⏳ Waiting for servers to start..."
sleep 5

# Check if servers are running
echo "🔍 Checking if backend server started..."
BACKEND_READY=false
for i in {1..10}; do
    if curl -s http://127.0.0.1:8000 >/dev/null 2>&1; then
        BACKEND_READY=true
        break
    fi
    echo "   Attempt $i/10... waiting 2 more seconds"
    sleep 2
done

if [ "$BACKEND_READY" = false ]; then
    echo "❌ Backend server failed to start. Here are the last few lines of the log:"
    echo "----------------------------------------"
    tail -10 logs/backend.log 2>/dev/null || echo "No log file found"
    echo "----------------------------------------"
    echo "💡 Try running manually: cd backend && source venv/bin/activate && python manage.py runserver"
    exit 1
fi

echo "✅ Backend server is running!"

if ! curl -s http://127.0.0.1:5173 >/dev/null; then
    echo "⚠️  Frontend server may not be ready yet, trying alternative port..."
    if ! curl -s http://127.0.0.1:3000 >/dev/null; then
        echo "⚠️  Frontend server not responding on common ports. It may still be starting..."
    fi
fi

# Open browser windows
echo "🌐 Opening applications in browser..."

# Open Django Admin
if command -v open >/dev/null 2>&1; then
    # macOS
    open http://127.0.0.1:8000/admin/
    sleep 1
    open http://127.0.0.1:5173/
elif command -v xdg-open >/dev/null 2>&1; then
    # Linux
    xdg-open http://127.0.0.1:8000/admin/
    sleep 1
    xdg-open http://127.0.0.1:5173/
elif command -v start >/dev/null 2>&1; then
    # Windows
    start http://127.0.0.1:8000/admin/
    sleep 1
    start http://127.0.0.1:5173/
else
    echo "🌐 Please manually open these URLs in your browser:"
    echo "   Django Admin:    http://127.0.0.1:8000/admin/"
    echo "   Frontend App:    http://127.0.0.1:5173/"
fi

echo ""
echo "✅ Record Label Manager is now running!"
echo "=================================="
echo "🔧 Django Admin:    http://127.0.0.1:8000/admin/"
echo "   Login: admin / admin"
echo ""
echo "🎨 Frontend App:    http://127.0.0.1:5173/"
echo ""
echo "💰 Finance Features Available:"
echo "   • View 272K+ revenue records"
echo "   • Export Q4 2024 payout (€8,121.76)"
echo "   • Platform performance analytics"
echo ""
echo "📊 Quick Finance Commands:"
echo "   cd backend && source venv/bin/activate"
echo "   python manage.py finances_payout --label 'Tropical Twista Records' --period '2024-Q4' --preview"
echo ""
echo "🛑 Press Ctrl+C to stop all servers"
echo "📋 Server logs: logs/backend.log & logs/frontend.log"
echo ""

# Keep the script running and show live logs
echo "📡 Live Backend Logs:"
echo "===================="
tail -f logs/backend.log 2>/dev/null &

# Wait for user to stop
wait
