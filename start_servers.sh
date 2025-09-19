#!/bin/bash

# Scoratis Smart Startup Script
# Automatically manages ports and starts both servers with error handling

set -e  # Exit on any error

# Configuration
BACKEND_PORT=5001
FRONTEND_PORT=8080
BACKEND_SCRIPT="main_professional.py"
PYTHON_ENV="/home/lenin/scoratis/.venv/bin/python"
LOG_DIR="/home/lenin/scoratis/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Scoratis Smart Startup Script${NC}"
echo -e "${BLUE}==================================${NC}"

# Create logs directory
mkdir -p "$LOG_DIR"

# Function to kill processes on specific ports
kill_port() {
    local port=$1
    echo -e "${YELLOW}🔍 Checking port $port...${NC}"
    
    local pids=$(lsof -ti :$port 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo -e "${RED}❌ Port $port is in use by PID(s): $pids${NC}"
        echo -e "${YELLOW}🔪 Killing processes on port $port...${NC}"
        kill -9 $pids 2>/dev/null || true
        sleep 2
        
        # Double check
        if lsof -ti :$port >/dev/null 2>&1; then
            echo -e "${RED}⚠️  Warning: Port $port may still be in use${NC}"
            # Force kill any remaining processes
            pkill -f "python.*$BACKEND_SCRIPT" 2>/dev/null || true
            pkill -f "http.server.*$FRONTEND_PORT" 2>/dev/null || true
            sleep 1
        else
            echo -e "${GREEN}✅ Port $port is now free${NC}"
        fi
    else
        echo -e "${GREEN}✅ Port $port is already free${NC}"
    fi
}

# Function to check if server is running
check_server() {
    local url=$1
    local name=$2
    if curl -s --max-time 3 "$url" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $name is running${NC}"
        return 0
    else
        echo -e "${RED}❌ $name is not responding${NC}"
        return 1
    fi
}

# Cleanup function for graceful shutdown
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down servers...${NC}"
    kill_port $BACKEND_PORT
    kill_port $FRONTEND_PORT
    echo -e "${GREEN}✅ Cleanup completed${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo -e "${BLUE}📋 Step 1: Cleaning up existing processes${NC}"
kill_port $BACKEND_PORT
kill_port $FRONTEND_PORT

echo -e "\n${BLUE}📋 Step 2: Starting Backend Server${NC}"
echo -e "${YELLOW}Starting Scoratis Professional Server on port $BACKEND_PORT...${NC}"

# Start backend in background with logging
nohup $PYTHON_ENV $BACKEND_SCRIPT > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to start
echo -e "${YELLOW}⏳ Waiting for backend to initialize...${NC}"
sleep 5

# Check if backend is running
if ! check_server "http://127.0.0.1:$BACKEND_PORT/" "Backend Server"; then
    echo -e "${RED}💥 Backend failed to start! Check logs: $LOG_DIR/backend.log${NC}"
    tail -n 20 "$LOG_DIR/backend.log"
    exit 1
fi

echo -e "\n${BLUE}📋 Step 3: Starting Frontend Server${NC}"
echo -e "${YELLOW}Starting HTTP server on port $FRONTEND_PORT...${NC}"

# Start frontend in background with logging
nohup python3 -m http.server $FRONTEND_PORT > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

# Wait for frontend to start
sleep 2

# Check if frontend is running
if ! check_server "http://127.0.0.1:$FRONTEND_PORT/" "Frontend Server"; then
    echo -e "${RED}💥 Frontend failed to start! Check logs: $LOG_DIR/frontend.log${NC}"
    tail -n 10 "$LOG_DIR/frontend.log"
    exit 1
fi

echo -e "\n${GREEN}🎉 SUCCESS! Both servers are running:${NC}"
echo -e "${GREEN}  📱 Frontend: http://127.0.0.1:$FRONTEND_PORT/index_professional.html${NC}"
echo -e "${GREEN}  🔧 Backend:  http://127.0.0.1:$BACKEND_PORT/${NC}"
echo -e "${GREEN}  📊 API Health: http://127.0.0.1:$BACKEND_PORT/stats${NC}"

echo -e "\n${BLUE}📋 Server Management:${NC}"
echo -e "  📝 Backend logs:  tail -f $LOG_DIR/backend.log"
echo -e "  📝 Frontend logs: tail -f $LOG_DIR/frontend.log"
echo -e "  🔪 Kill ports:    ./kill_ports.sh"
echo -e "  🛑 Stop all:      Press Ctrl+C"

echo -e "\n${YELLOW}⏳ Servers are running. Press Ctrl+C to stop all servers.${NC}"

# Keep script running and monitor servers
while true; do
    sleep 10
    
    # Check if servers are still running
    if ! check_server "http://127.0.0.1:$BACKEND_PORT/" "Backend Server" >/dev/null 2>&1; then
        echo -e "${RED}💥 Backend server crashed! Check logs: $LOG_DIR/backend.log${NC}"
        break
    fi
    
    if ! check_server "http://127.0.0.1:$FRONTEND_PORT/" "Frontend Server" >/dev/null 2>&1; then
        echo -e "${RED}💥 Frontend server crashed! Check logs: $LOG_DIR/frontend.log${NC}"
        break
    fi
done

# If we get here, something crashed
echo -e "${RED}🚨 One or more servers crashed. Running cleanup...${NC}"
cleanup