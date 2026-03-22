#!/bin/bash
# AI Employee Production Deployment Script

echo "🚀 Starting Production Deployment..."

# 1. Create logs directory
mkdir -p logs

# 2. Setup Backend
echo "📦 Setting up Backend..."
cd backend
python -m venv venv
source venv/Scripts/activate || source venv/bin/activate
pip install -r requirements.txt
cd ..

# 3. Setup Frontend
echo "📦 Building Frontend..."
cd frontend
npm install
npm run build
cd ..

# 4. Start with PM2
echo "⚙️ Starting processes with PM2..."
pm2 start ecosystem.config.js

# 5. Save PM2 list
pm2 save

echo "✅ Deployment Complete! Use 'pm2 status' to check logs."
