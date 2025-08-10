#!/bin/bash
# Gunicorn Management Script

GUNICORN_PID_FILE="logs/gunicorn.pid"
VENV_PYTHON="/home/devops/MPESA/mpesa/venv/bin/python"
VENV_GUNICORN="/home/devops/MPESA/mpesa/venv/bin/gunicorn"
PROJECT_DIR="/home/devops/MPESA/mpesa"

cd "$PROJECT_DIR"

# Function to start Gunicorn
start_gunicorn() {
    echo "🚀 Starting Gunicorn on port 5000..."
    
    # Set environment variables
    export DEBUG=False
    export CLOUDFLARE_TUNNEL=True
    export DJANGO_SETTINGS_MODULE=config.settings
    
    # Ensure logs directory exists
    mkdir -p logs
    
    # Check if already running
    if [ -f "$GUNICORN_PID_FILE" ] && kill -0 "$(cat $GUNICORN_PID_FILE)" 2>/dev/null; then
        echo "⚠️  Gunicorn is already running (PID: $(cat $GUNICORN_PID_FILE))"
        return 1
    fi
    
    # Start Gunicorn
    exec $VENV_GUNICORN --config gunicorn.conf.py config.wsgi:application
}

# Function to stop Gunicorn
stop_gunicorn() {
    echo "⏹️  Stopping Gunicorn..."
    
    if [ -f "$GUNICORN_PID_FILE" ] && kill -0 "$(cat $GUNICORN_PID_FILE)" 2>/dev/null; then
        PID=$(cat $GUNICORN_PID_FILE)
        echo "   Sending TERM signal to PID: $PID"
        kill -TERM "$PID"
        
        # Wait for graceful shutdown
        sleep 3
        
        # Check if still running
        if kill -0 "$PID" 2>/dev/null; then
            echo "   Sending KILL signal to PID: $PID"
            kill -KILL "$PID"
        fi
        
        rm -f "$GUNICORN_PID_FILE"
        echo "✅ Gunicorn stopped"
    else
        echo "⚠️  Gunicorn is not running"
    fi
}

# Function to restart Gunicorn
restart_gunicorn() {
    echo "🔄 Restarting Gunicorn..."
    stop_gunicorn
    sleep 2
    start_gunicorn
}

# Function to reload Gunicorn (graceful restart)
reload_gunicorn() {
    echo "🔄 Reloading Gunicorn (graceful restart)..."
    
    if [ -f "$GUNICORN_PID_FILE" ] && kill -0 "$(cat $GUNICORN_PID_FILE)" 2>/dev/null; then
        PID=$(cat $GUNICORN_PID_FILE)
        echo "   Sending HUP signal to PID: $PID"
        kill -HUP "$PID"
        echo "✅ Gunicorn reloaded"
    else
        echo "⚠️  Gunicorn is not running. Starting instead..."
        start_gunicorn
    fi
}

# Function to show status
status_gunicorn() {
    echo "📊 Gunicorn Status:"
    
    if [ -f "$GUNICORN_PID_FILE" ] && kill -0 "$(cat $GUNICORN_PID_FILE)" 2>/dev/null; then
        PID=$(cat $GUNICORN_PID_FILE)
        echo "   ✅ Running (PID: $PID)"
        
        # Show process info
        ps -p "$PID" -o pid,ppid,cmd --no-headers 2>/dev/null | while read line; do
            echo "   Process: $line"
        done
        
        # Test if responsive
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ | grep -q "200\|302"; then
            echo "   ✅ HTTP server is responsive"
        else
            echo "   ⚠️  HTTP server is not responding"
        fi
    else
        echo "   ❌ Not running"
    fi
}

# Function to show logs
logs_gunicorn() {
    echo "📋 Recent Gunicorn logs:"
    echo "--- Error Log ---"
    if [ -f "logs/gunicorn_error.log" ]; then
        tail -20 "logs/gunicorn_error.log"
    else
        echo "No error log found"
    fi
    
    echo "--- Access Log ---"
    if [ -f "logs/gunicorn_access.log" ]; then
        tail -10 "logs/gunicorn_access.log"
    else
        echo "No access log found"
    fi
}

# Main command handling
case "$1" in
    start)
        start_gunicorn
        ;;
    stop)
        stop_gunicorn
        ;;
    restart)
        restart_gunicorn
        ;;
    reload)
        reload_gunicorn
        ;;
    status)
        status_gunicorn
        ;;
    logs)
        logs_gunicorn
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|reload|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start Gunicorn server"
        echo "  stop    - Stop Gunicorn server"
        echo "  restart - Stop and start Gunicorn server"
        echo "  reload  - Gracefully reload Gunicorn (HUP signal)"
        echo "  status  - Show Gunicorn status"
        echo "  logs    - Show recent logs"
        exit 1
        ;;
esac
