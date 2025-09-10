#!/bin/bash

echo "🎨 Starting Record Label Manager Frontend"
echo "========================================="

# Clean up any existing processes
pkill -f "npm.*dev\|vite" 2>/dev/null
sleep 2

# Navigate to project root
cd "$(dirname "$0")"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the frontend
echo "🚀 Starting React frontend..."
echo "   This will show any error messages"
echo ""

npm run dev
