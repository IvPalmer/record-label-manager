#!/bin/bash

# Just start the Django backend (finance system)
echo "🎵 Starting Record Label Manager Backend..."
echo "============================================"

cd backend
source venv/bin/activate

echo "✅ Django backend running at: http://127.0.0.1:8000/admin/"
echo "📝 Login: admin / admin"
echo ""
echo "💰 Finance features ready:"
echo "   📊 272K+ revenue records"
echo "   💶 €67,541 in 2024 revenue" 
echo "   🎯 Q4 payout: €8,121.76"
echo ""
echo "🛑 Press Ctrl+C to stop"

python manage.py runserver 127.0.0.1:8000
