#!/bin/bash
# Gold Tier - Real Social Media Posting Test
# Run this script to test posting on Twitter, Facebook, and Instagram

cd /mnt/d/Gemini_Cli/hackathon/hackathon_0/AI-Employee

echo "======================================================================"
echo "🚀 GOLD TIER - REAL SOCIAL MEDIA POSTING TEST"
echo "======================================================================"
echo ""

# Load environment from .env.gold-tier.example
echo "📂 Loading environment..."
export $(grep -v '^#' .env.gold-tier.example | grep -v '^$' | xargs)

echo "✅ Environment loaded!"
echo ""

# Start MCP Servers
echo "🔧 Starting MCP Servers..."

echo "  🐦 Starting Twitter MCP Server on port 8087..."
cd mcp/twitter-server && node src/index.js > /tmp/twitter-mcp.log 2>&1 &
TWITTER_PID=$!
cd ..

echo "  📘 Starting Facebook MCP Server on port 8085..."
cd facebook-server && node src/index.js > /tmp/facebook-mcp.log 2>&1 &
FACEBOOK_PID=$!
cd ..

echo "  📸 Starting Instagram MCP Server on port 8086..."
cd instagram-server && node src/index.js > /tmp/instagram-mcp.log 2>&1 &
INSTAGRAM_PID=$!
cd ..

sleep 3

echo "✅ MCP Servers started!"
echo "   Twitter PID: $TWITTER_PID"
echo "   Facebook PID: $FACEBOOK_PID"
echo "   Instagram PID: $INSTAGRAM_PID"
echo ""

# Run Python test
echo "🧪 Running social media posting tests..."
echo ""

python3 test_real_social_posting.py

TEST_RESULT=$?

# Cleanup
echo ""
echo "🧹 Cleaning up..."
kill $TWITTER_PID 2>/dev/null
kill $FACEBOOK_PID 2>/dev/null
kill $INSTAGRAM_PID 2>/dev/null

echo ""
echo "======================================================================"
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ ALL TESTS PASSED!"
else
    echo "⚠️  SOME TESTS FAILED - Check logs for details"
fi
echo "======================================================================"
echo ""
echo "📄 MCP Server Logs:"
echo "   Twitter: /tmp/twitter-mcp.log"
echo "   Facebook: /tmp/facebook-mcp.log"
echo "   Instagram: /tmp/instagram-mcp.log"
echo ""
echo "📄 Test Results: test_results_social_posting.json"
echo ""

exit $TEST_RESULT
