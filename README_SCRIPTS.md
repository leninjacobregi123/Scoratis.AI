# Scoratis Development Scripts

This directory contains automated scripts to manage your development servers and handle port conflicts.

## 🚀 Quick Start Scripts

### 1. `start_servers.sh` - Smart Startup (Recommended)
```bash
./start_servers.sh
```
**Features:**
- Automatically kills processes on ports 5001 and 8080
- Starts both backend and frontend servers
- Health checks and error detection
- Graceful shutdown with Ctrl+C
- Logs to `logs/` directory
- Monitors server health

### 2. `kill_ports.sh` - Port Management
```bash
./kill_ports.sh          # Kills processes on default ports 5001, 8080
./kill_ports.sh 3000     # Kill specific port
./kill_ports.sh 5001 8080 3000  # Kill multiple ports
```
**Use when:**
- Servers are stuck/frozen
- Port conflicts occur
- Need to clean up before restart

### 3. `auto_restart.sh` - Development Mode
```bash
./auto_restart.sh
```
**Features:**
- Watches files for changes
- Automatically restarts servers on code changes
- Perfect for active development
- Monitors: `main_professional.py`, `database.py`, `index_professional.html`

## 📁 File Structure
```
/home/lenin/scoratis/
├── start_servers.sh     # Smart startup script
├── kill_ports.sh        # Port management
├── auto_restart.sh      # Auto-restart on changes
├── logs/                # Server logs
│   ├── backend.log      # Backend server logs
│   └── frontend.log     # Frontend server logs
├── main_professional.py # Backend server
└── index_professional.html # Frontend UI
```

## 🎯 Common Usage Patterns

### Starting Development Session
```bash
# Option 1: Manual control
./start_servers.sh

# Option 2: Auto-restart on changes (recommended for development)
./auto_restart.sh
```

### Fixing Port Conflicts
```bash
# If you get "Address already in use" errors:
./kill_ports.sh
./start_servers.sh
```

### Checking Server Status
```bash
# Backend health check
curl http://127.0.0.1:5001/

# View logs
tail -f logs/backend.log
tail -f logs/frontend.log
```

### Emergency Stop
```bash
# Stop everything
./kill_ports.sh
# or
pkill -f "python.*main_professional"
pkill -f "http.server"
```

## 🔧 Server URLs

- **Frontend Application**: http://127.0.0.1:8080/index_professional.html
- **Backend API**: http://127.0.0.1:5001/
- **API Health Check**: http://127.0.0.1:5001/stats

## 🚨 Troubleshooting

### Port Already in Use
```bash
./kill_ports.sh
# Wait 2 seconds
./start_servers.sh
```

### Server Won't Start
```bash
# Check logs
cat logs/backend.log
cat logs/frontend.log

# Force cleanup
./kill_ports.sh
pkill -f "python"
./start_servers.sh
```

### Auto-restart Not Working
```bash
# Install file monitoring tools
sudo apt-get install inotify-tools
./auto_restart.sh
```

## 💡 Tips

1. **Use `start_servers.sh` for regular development** - it handles everything automatically
2. **Use `auto_restart.sh` when actively coding** - saves time on manual restarts
3. **Use `kill_ports.sh` when things get stuck** - nuclear option for port cleanup
4. **Check logs if servers fail** - they're in the `logs/` directory
5. **Always use Ctrl+C to stop servers gracefully** - prevents port conflicts