#!/bin/bash

# Test runner script for Smart Heating integration

set -e

echo "================================"
echo "Smart Heating Unit Tests Runner"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists (in parent directory)
if [[ ! -d "venv" ]]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update test dependencies
echo -e "${YELLOW}Installing test dependencies...${NC}"
pip install -q -r tests/requirements_test.txt

# Run tests with coverage
echo -e "${GREEN}Running tests with coverage...${NC}"
echo ""

pytest tests/unit \
    --cov=smart_heating \
    --cov-report=term-missing \
    --cov-report=html:coverage_html \
    --cov-report=xml:coverage.xml \
    --cov-branch \
    -v

# Check coverage
echo ""
echo -e "${GREEN}Coverage report generated in coverage_html/index.html${NC}"

# Check if coverage meets threshold
COVERAGE=$(coverage report | grep TOTAL | awk '{print $NF}' | sed 's/%//')
THRESHOLD=85

if (( $(echo "$COVERAGE >= $THRESHOLD" | bc -l) )); then
    echo -e "${GREEN}✓ Coverage ($COVERAGE%) meets threshold ($THRESHOLD%)${NC}"
    exit 0
else
    echo -e "${RED}✗ Coverage ($COVERAGE%) below threshold ($THRESHOLD%)${NC}"
    exit 1
fi
