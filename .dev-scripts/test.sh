#!/bin/bash
# Run tests for this project only

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🧪 Testing ♻️ Hounslow Bin Collection Calendar...${NC}"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run pytest
echo -e "${BLUE}🔬 Running pytest...${NC}"
if pytest -v; then
    echo -e "${GREEN}✅ All tests passed${NC}"
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
