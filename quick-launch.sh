#!/bin/bash

echo "🚀 Quick Launch - Record Label Manager"
echo "======================================"

cd "$(dirname "$0")"

# Kill any existing processes
pkill -f "python.*runserver" 2>/dev/null
pkill -f "npm.*dev\|vite" 2>/dev/null
sleep 1

# Start Django backend
echo "🔧 Starting Django backend..."
cd backend
source venv/bin/activate
python manage.py runserver 127.0.0.1:8000 &
BACKEND_PID=$!
cd ..

# Start React frontend  
echo "🎨 Starting React frontend..."
npm run dev &
FRONTEND_PID=$!

# Wait and open browsers
sleep 5
echo ""
echo "✅ Servers starting..."
echo "📊 Analytics: http://127.0.0.1:5173/analytics (or :5174)"
echo "🔧 Django Admin: http://127.0.0.1:8000/admin/"
echo ""
echo "🎯 Your realistic 2024 revenue: €7,096.66"
echo "💰 Distribution: €5,297 (~€1,324/quarter) ✅"
echo "💿 Bandcamp: €1,799"
echo ""
echo "🌐 Opening browsers..."

# Open browsers
if command -v open >/dev/null 2>&1; then
    open http://127.0.0.1:8000/admin/
    sleep 1
    open http://127.0.0.1:5173/analytics 2>/dev/null || open http://127.0.0.1:5174/analytics 2>/dev/null
fi

echo "✅ Both servers launched!"
echo "💡 Django login: admin / admin"
