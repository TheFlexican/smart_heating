#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Home Assistant - Create Backup${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""

# Configuration
HA_HOST="192.168.2.2"
HA_PORT="22222"
BACKUP_NAME="manual_backup_$(date +%Y%m%d_%H%M%S)"

echo -e "${YELLOW}Creating backup...${NC}"
echo "  Name: $BACKUP_NAME"
echo ""

# Create backup using Home Assistant CLI
echo -e "${YELLOW}Executing backup command...${NC}"
ssh root@${HA_HOST} -p ${HA_PORT} "ha backups new --name \"${BACKUP_NAME}\""

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Backup Created Successfully!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${GREEN}Backup name:${NC} $BACKUP_NAME"
    echo ""
    echo "You can view and download backups at:"
    echo "  http://${HA_HOST}:8123/hassio/backups"
else
    echo ""
    echo -e "${RED}════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  Backup Failed!${NC}"
    echo -e "${RED}════════════════════════════════════════════════════════${NC}"
    exit 1
fi
