#!/bin/bash

echo "🚀 Railway Deployment Script for TikTok Vibe App"
echo "================================================"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

echo "📋 Manual steps you need to complete:"
echo ""
echo "1. Run: railway login"
echo "   This will open your browser for authentication"
echo ""
echo "2. Run: railway init"
echo "   Select 'Create new project' when prompted"
echo ""
echo "3. Set environment variables:"
echo "   railway variables set VENICE_API_KEY=VENICE_INFERENCE_KEY_IPKxzZhAO1g8PR_x8W6nUaCVMhpwJqi_JR3vQpVwIj"
echo "   railway variables set SECRET_KEY=your-secret-jwt-key-here"
echo ""
echo "4. Deploy:"
echo "   railway up"
echo ""
echo "🔧 Your app is configured with:"
echo "   - FastAPI backend"
echo "   - Venice AI integration"
echo "   - Docker deployment"
echo "   - Port $PORT (Railway managed)"
echo ""
echo "📁 Current directory: $(pwd)"
echo "🌐 After deployment, your app will be available at a Railway URL"