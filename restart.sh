#!/bin/bash

echo "Record Label Manager - Fresh Start"
echo "=================================="

cd "$(dirname "$0")"

# Clean up everything
echo "Cleaning up processes..."
pkill -f "python.*runserver" 2>/dev/null
pkill -f "npm.*dev\|vite\|node.*vite" 2>/dev/null
sleep 2

# Ensure logs directory exists
mkdir -p logs

# Start Django Backend
echo "Starting Django backend..."
cd backend
source venv/bin/activate
python manage.py runserver 127.0.0.1:8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Start React Frontend
echo "Starting React frontend..."
npm run dev > logs/frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for startup
echo "Waiting for servers to start..."
sleep 5

# Check status
echo "Checking server status..."
if curl -s http://127.0.0.1:8000/admin/ >/dev/null 2>&1; then
    echo "Django backend: Ready"
else
    echo "Django backend: Failed - check logs/backend.log"
fi

# Check frontend ports
if curl -s http://127.0.0.1:5173/ >/dev/null 2>&1; then
    echo "React frontend: Ready on port 5173"
    FRONTEND_PORT=5173
elif curl -s http://127.0.0.1:5174/ >/dev/null 2>&1; then
    echo "React frontend: Ready on port 5174"
    FRONTEND_PORT=5174
else
    echo "React frontend: Failed - check logs/frontend.log"
    FRONTEND_PORT=5173
fi

echo ""
echo "Record Label Manager Running!"
echo "============================"
echo "Analytics Dashboard: http://127.0.0.1:$FRONTEND_PORT/analytics"
echo "Django Admin: http://127.0.0.1:8000/admin/"
echo "Login: admin / admin"
echo ""
echo "Your 2024 Revenue Data Ready:"
echo "Total: EUR 7,096.66 (realistic)"
echo "Distribution: EUR 5,297.22 (~EUR 1,324/quarter)"
echo "Bandcamp: EUR 1,799.44"
echo "Track-level attribution for payouts"
echo ""
echo "Press Ctrl+C to stop (in this terminal)"

# Open browsers
if command -v open >/dev/null 2>&1; then
    sleep 2
    open "http://127.0.0.1:8000/admin/"
    sleep 1
    open "http://127.0.0.1:$FRONTEND_PORT/analytics"
fi

# Keep script running to monitor
trap 'echo "Stopping servers..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit' INT

# Monitor servers
while true; do
    sleep 10
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "Backend stopped"
        break
    fi
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "Frontend stopped"
        break
    fi
done
