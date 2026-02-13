#!/bin/bash

# Script to restart the FastAPI backend server

echo "🔄 Restarting FastAPI backend server..."

# Kill existing uvicorn process
echo "⏹️  Stopping existing server..."
pkill -f "uvicorn app.main:app"

# Wait for process to fully stop
sleep 2

# Start the server again
echo "▶️  Starting server..."
cd /home/beaunix/Documents/yieldEstimator
./apples/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

# Wait a moment for server to start
sleep 3

# Check if server is running
if curl -s http://localhost:8000/docs > /dev/null; then
    echo "✅ Server restarted successfully!"
    echo "📝 Check the API docs at: http://localhost:8000/docs"
    echo "🌾 The Farming endpoints should now be available"
else
    echo "❌ Server failed to start. Check the logs above."
fi
