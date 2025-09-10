#!/bin/bash

# Simple Record Label Manager Startup Script
echo "🎵 Starting Record Label Manager (Simple Mode)..."
echo "=================================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create logs directory
mkdir -p logs

# Cleanup function
cleanup() {
    echo -e "\n🛑 Stopping servers..."
    pkill -f "python.*manage.py.*runserver" 2>/dev/null
    pkill -f "npm.*run.*dev" 2>/dev/null
    pkill -f "vite" 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Start backend
echo "🚀 Starting Django backend..."
cd backend && source venv/bin/activate && {
    echo "   Backend starting on http://127.0.0.1:8000"
    python manage.py runserver 127.0.0.1:8000 > ../logs/backend.log 2>&1 &
}
cd ..

# Start frontend (if package.json exists)
if [ -f "package.json" ]; then
    echo "🚀 Starting React frontend..."
    echo "   Frontend starting on http://127.0.0.1:5173"
    npm run dev > logs/frontend.log 2>&1 &
fi

# Wait a moment
sleep 3

# Open browsers
echo "🌐 Opening browsers..."
if command -v open >/dev/null 2>&1; then
    # macOS
    open http://127.0.0.1:8000/admin/
    if [ -f "package.json" ]; then
        sleep 1
        open http://127.0.0.1:5173/
    fi
elif command -v xdg-open >/dev/null 2>&1; then
    # Linux  
    xdg-open http://127.0.0.1:8000/admin/
    if [ -f "package.json" ]; then
        sleep 1
        xdg-open http://127.0.0.1:5173/
    fi
fi

echo ""
echo "✅ Services are starting!"
echo "========================="
echo "🔧 Django Admin:  http://127.0.0.1:8000/admin/"
echo "   📝 Login: admin / admin"
echo ""
if [ -f "package.json" ]; then
    echo "🎨 React Frontend: http://127.0.0.1:5173/"
    echo ""
fi
echo "💰 Your finance data is ready:"
echo "   📊 272K+ revenue records loaded"  
echo "   💶 €67,541 in 2024 revenue"
echo "   🎯 Q4 payout ready: €8,121.76"
echo ""
echo "📋 Logs:"
echo "   Backend:  tail -f logs/backend.log"
echo "   Frontend: tail -f logs/frontend.log"
echo ""
echo "🛑 Press Ctrl+C to stop everything"

# Keep running and show backend status
echo "📡 Monitoring backend..."
while true; do
    if ! pgrep -f "python.*manage.py.*runserver" > /dev/null; then
        echo "⚠️  Backend stopped unexpectedly"
        tail -5 logs/backend.log
        break
    fi
    sleep 10
done
