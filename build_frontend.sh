#!/bin/bash

# Build script for Zone Heater Manager frontend

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Building Zone Heater Manager Frontend${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
FRONTEND_DIR="${SCRIPT_DIR}/custom_components/zone_heater_manager/frontend"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    echo "Please install Node.js 18 or higher from https://nodejs.org/"
    exit 1
fi

# Check Node version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo -e "${RED}Error: Node.js version 18 or higher is required${NC}"
    echo "Current version: $(node -v)"
    exit 1
fi

echo -e "${GREEN}✓${NC} Node.js $(node -v) detected"

# Navigate to frontend directory
cd "$FRONTEND_DIR"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo ""
    echo -e "${BLUE}Installing dependencies...${NC}"
    npm install
    echo -e "${GREEN}✓${NC} Dependencies installed"
fi

# Build the frontend
echo ""
echo -e "${BLUE}Building frontend...${NC}"
npm run build

echo ""
echo -e "${GREEN}✓${NC} Frontend built successfully!"
echo ""
echo -e "${BLUE}The frontend is ready to use.${NC}"
echo "Restart Home Assistant to load the new build."
echo ""
echo "Access the frontend at:"
echo "  http://your-ha-instance:8123/zone_heater_manager/"
