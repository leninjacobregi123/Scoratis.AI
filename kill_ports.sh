#!/bin/bash

# Script to kill processes on specific ports
# Usage: ./kill_ports.sh [port1] [port2] ...
# Default: kills ports 5001 and 8080

echo "🔧 Port Management Script - Killing Processes..."

# Default ports if none specified
PORTS=${@:-5001 8080}

for PORT in $PORTS; do
    echo "🔍 Checking port $PORT..."
    
    # Find processes using the port
    PIDS=$(lsof -ti :$PORT 2>/dev/null)
    
    if [ -n "$PIDS" ]; then
        echo "❌ Port $PORT is in use by PID(s): $PIDS"
        echo "🔪 Killing processes on port $PORT..."
        
        # Kill the processes
        kill -9 $PIDS 2>/dev/null
        
        # Wait a moment for cleanup
        sleep 1
        
        # Verify the port is free
        if lsof -ti :$PORT >/dev/null 2>&1; then
            echo "⚠️  Warning: Port $PORT may still be in use"
        else
            echo "✅ Port $PORT is now free"
        fi
    else
        echo "✅ Port $PORT is already free"
    fi
done

echo "🎯 Port cleanup completed!"