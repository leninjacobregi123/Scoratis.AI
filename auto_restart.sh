#!/bin/bash

# Auto-Restart Script for Development
# Monitors files for changes and automatically restarts servers

# Configuration
WATCH_FILES=("main_professional.py" "database.py" "index_professional.html")
RESTART_SCRIPT="./start_servers.sh"
LOG_DIR="/home/lenin/scoratis/logs"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔄 Auto-Restart Development Server${NC}"
echo -e "${BLUE}===================================${NC}"

# Check if inotify-tools is installed
if ! command -v inotifywait &> /dev/null; then
    echo -e "${YELLOW}📦 Installing inotify-tools for file monitoring...${NC}"
    sudo apt-get update && sudo apt-get install -y inotify-tools
fi

mkdir -p "$LOG_DIR"

# Function to restart servers
restart_servers() {
    echo -e "${YELLOW}🔄 File change detected! Restarting servers...${NC}"
    
    # Kill existing servers
    ./kill_ports.sh 5001 8080
    
    # Wait a moment
    sleep 2
    
    # Start servers
    $RESTART_SCRIPT &
    SERVER_PID=$!
    
    echo -e "${GREEN}✅ Servers restarted with PID: $SERVER_PID${NC}"
}

# Initial server start
echo -e "${GREEN}🚀 Starting initial servers...${NC}"
restart_servers

echo -e "${BLUE}👀 Watching files for changes: ${WATCH_FILES[*]}${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop monitoring${NC}"

# Monitor files for changes
while true; do
    inotifywait -e modify,create,delete,move "${WATCH_FILES[@]}" 2>/dev/null
    
    echo -e "${YELLOW}⚡ Change detected, waiting 2 seconds for more changes...${NC}"
    sleep 2
    
    # Kill current servers
    ./kill_ports.sh 5001 8080
    pkill -f "start_servers.sh" 2>/dev/null || true
    
    # Restart
    restart_servers
    
    # Wait before monitoring again
    sleep 3
done