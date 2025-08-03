#!/bin/bash
# Run the Hounslow Bin Collection Calendar sync

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Running ♻️ Hounslow Bin Collection Calendar...${NC}"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the main script
echo -e "${BLUE}♻️ Starting waste sync...${NC}"
python waste_sync.py

echo -e "${GREEN}✅ Waste sync finished${NC}"
