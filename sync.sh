#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HA_CONTAINER="homeassistant-test"
INTEGRATION_DIR="smart_heating"
FRONTEND_DIR="$INTEGRATION_DIR/frontend"

echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Smart Heating - Sync Script${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""

# Check if container is running
if ! docker ps | grep -q "$HA_CONTAINER"; then
    echo -e "${RED}✗${NC} Container '$HA_CONTAINER' is not running"
    echo "  Run './setup.sh' first to start the container"
    exit 1
fi

echo -e "${YELLOW}[1/3]${NC} Building frontend..."
if [ -d "$FRONTEND_DIR" ]; then
    cd "$FRONTEND_DIR"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "  Installing dependencies..."
        npm install --silent
    fi
    
    # Build frontend
    echo "  Building React app..."
    npm run build --silent
    
    if [ ! -d "dist" ]; then
        echo -e "${RED}✗${NC} Frontend build failed - dist directory not found"
        exit 1
    fi
    
    cd - > /dev/null
    echo -e "${GREEN}✓${NC} Frontend built successfully"
else
    echo -e "${RED}✗${NC} Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi
echo ""

echo -e "${YELLOW}[2/3]${NC} Syncing integration files..."

# Create tarball excluding unnecessary files
cd "$INTEGRATION_DIR"
tar czf /tmp/smart_heating_sync.tar.gz \
    --exclude='frontend/node_modules' \
    --exclude='frontend/src' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='._*' \
    .

cd - > /dev/null

# Ensure directory exists in container
docker exec "$HA_CONTAINER" mkdir -p /config/custom_components/smart_heating > /dev/null 2>&1 || true

# Copy tarball to container
docker cp /tmp/smart_heating_sync.tar.gz "$HA_CONTAINER:/tmp/" > /dev/null

# Extract in container
docker exec "$HA_CONTAINER" tar xzf /tmp/smart_heating_sync.tar.gz -C /config/custom_components/smart_heating/

# Clean up
docker exec "$HA_CONTAINER" rm /tmp/smart_heating_sync.tar.gz
rm /tmp/smart_heating_sync.tar.gz

# Count files synced
file_count=$(docker exec "$HA_CONTAINER" find /config/custom_components/smart_heating -type f | wc -l | tr -d ' ')
echo -e "  → Synced $file_count files"
echo -e "${GREEN}✓${NC} Integration synced"
echo ""

echo -e "${YELLOW}[3/3]${NC} Restarting Home Assistant..."
docker restart "$HA_CONTAINER" > /dev/null

# Check if container is running
if docker ps | grep -q "$HA_CONTAINER"; then
    echo -e "${GREEN}✓${NC} Home Assistant restarted successfully"
else
    echo -e "${RED}✗${NC} Home Assistant failed to restart"
    echo "  Check logs: docker logs -f $HA_CONTAINER"
    exit 1
fi
echo ""

echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Sync Complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Changes synced:${NC}"
echo "  ✓ Backend Python files (.py)"
echo "  ✓ Configuration files (.yaml, .json)"
echo "  ✓ Frontend build (dist/)"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  • Open http://localhost:8123"
echo "  • Clear browser cache (Cmd+Shift+R / Ctrl+Shift+R)"
echo "  • Check logs: docker logs -f $HA_CONTAINER"
echo ""
