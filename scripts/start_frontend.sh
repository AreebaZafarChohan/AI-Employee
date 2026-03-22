#!/bin/bash
# Start Next.js Frontend
echo "Starting AI Employee Frontend..."
cd "$(dirname "$0")/../frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    npm install
fi

# Run next dev in foreground
exec npm run dev -- --hostname 0.0.0.0 --port 3000
