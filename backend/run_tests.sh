#!/bin/bash
# Quick test script for backend API

set -e

echo "=================================="
echo "Backend API Testing Script"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if server is running
echo "Checking if server is running..."
if curl -s http://localhost:8080/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Server is running${NC}"
else
    echo -e "${RED}❌ Server is not running${NC}"
    echo ""
    echo "Please start the server first:"
    echo "  cd backend"
    echo "  source .venv/bin/activate"
    echo "  uvicorn main:app --reload --port 8080"
    exit 1
fi

echo ""
echo "=================================="
echo "Test 1: Health Check"
echo "=================================="
HEALTH_RESPONSE=$(curl -s http://localhost:8080/)
echo "Response: $HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    exit 1
fi

echo ""
echo "=================================="
echo "Test 2: Process 10 Segments"
echo "=================================="
echo -e "${YELLOW}⚠️  This will take 2-3 minutes and cost ~\$1-2${NC}"
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting processing..."
    echo "(This may take 2-3 minutes, please wait...)"

    PROCESS_RESPONSE=$(curl -s -X POST http://localhost:8080/process-test \
        -H "Content-Type: application/json" \
        -d '{"url": "https://news.smol.ai/issues/26-01-16-chatgpt-ads/"}')

    echo ""
    echo "Response:"
    echo "$PROCESS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$PROCESS_RESPONSE"

    # Extract issue_id
    ISSUE_ID=$(echo "$PROCESS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('issue_id', ''))" 2>/dev/null)

    if [ ! -z "$ISSUE_ID" ]; then
        echo ""
        echo -e "${GREEN}✅ Processing completed!${NC}"
        echo ""
        echo "Issue ID: $ISSUE_ID"
        echo ""
        echo "Next steps:"
        echo "1. Check Supabase: https://supabase.com/dashboard/project/akxytmuwjomxlneqzgic/editor"
        echo "2. Verify 10 segments in 'segments' table"
        echo "3. Click an audio_url to test playback"
        echo ""
        echo "Test issue status with:"
        echo "  curl http://localhost:8080/issues/$ISSUE_ID"
    else
        echo -e "${RED}❌ Processing failed${NC}"
        exit 1
    fi
else
    echo "Skipping processing test."
fi

echo ""
echo "=================================="
echo "Testing Complete!"
echo "=================================="
