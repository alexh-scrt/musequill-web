#!/bin/bash
# MuseQuill Newsletter Service Startup Script
# This script sets up and runs the newsletter service using conda environment

set -e

echo "🖋️ MuseQuill Newsletter Service Setup"
echo "======================================"

# Configuration
SERVICE_NAME="musequill-newsletter"
SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONDA_ENV_NAME="musequill.ink"
LOG_DIR="$SERVICE_DIR/logs"
DATA_DIR="$SERVICE_DIR/data"
PID_FILE="$SERVICE_DIR/newsletter.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Create necessary directories
create_directories() {
    log_info "Creating directories..."
    mkdir -p "$LOG_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$SERVICE_DIR/backups"
}

# Check if conda is available
check_conda() {
    if ! command -v conda &> /dev/null; then
        log_error "Conda is not installed or not in PATH"
        log_error "Please install Anaconda/Miniconda or ensure conda is in your PATH"
        return 1
    fi
    
    log_debug "Conda found: $(which conda)"
    return 0
}

# Check if the conda environment exists and is active
check_conda_env() {
    if ! check_conda; then
        return 1
    fi
    
    # Check if environment exists
    if ! conda env list | grep -q "^${CONDA_ENV_NAME} "; then
        log_error "Conda environment '${CONDA_ENV_NAME}' does not exist"
        log_error "Please create the environment first:"
        log_error "  conda create -n ${CONDA_ENV_NAME} python=3.13"
        log_error "  conda activate ${CONDA_ENV_NAME}"
        log_error "  pip install -r newsletter_requirements.txt"
        return 1
    fi
    
    # Check if environment is active
    if [[ "$CONDA_DEFAULT_ENV" == "$CONDA_ENV_NAME" ]]; then
        log_info "Conda environment '${CONDA_ENV_NAME}' is already active"
        return 0
    else
        log_info "Activating conda environment '${CONDA_ENV_NAME}'..."
        activate_conda_env
        return 2  # Need to activate
    fi
}

# Activate conda environment
activate_conda_env() {
    if ! check_conda; then
        return 1
    fi
    
    log_info "Activating conda environment: ${CONDA_ENV_NAME}"
    
    # Initialize conda for bash (if not already done)
    if ! declare -f conda > /dev/null; then
        log_debug "Initializing conda for bash..."
        eval "$(conda shell.bash hook)"
    fi
    
    # Activate the environment
    conda activate "$CONDA_ENV_NAME"
    
    if [[ "$CONDA_DEFAULT_ENV" == "$CONDA_ENV_NAME" ]]; then
        log_info "Successfully activated conda environment: ${CONDA_ENV_NAME}"
        return 0
    else
        log_error "Failed to activate conda environment: ${CONDA_ENV_NAME}"
        return 1
    fi
}

# Setup conda environment with dependencies
setup_conda_env() {
    check_conda_env
    check_conda_env_result=$?
    
    if [ $check_conda_env_result -eq 1 ]; then
        # Environment doesn't exist, create it
        log_info "Creating conda environment: ${CONDA_ENV_NAME}"
        conda create -n "$CONDA_ENV_NAME" python=3.13 -y
        activate_conda_env
    elif [ $check_conda_env_result -eq 2 ]; then
        # Environment exists but not active
        activate_conda_env
    fi
    
    # Ensure we're in the right environment
    if [[ "$CONDA_DEFAULT_ENV" != "$CONDA_ENV_NAME" ]]; then
        log_error "Not in the correct conda environment. Expected: ${CONDA_ENV_NAME}, Current: ${CONDA_DEFAULT_ENV:-none}"
        return 1
    fi
    
    log_info "Upgrading pip..."
    pip install --upgrade pip
    
    if [ -f "$SERVICE_DIR/newsletter_requirements.txt" ]; then
        log_info "Installing newsletter service dependencies..."
        pip install -r "$SERVICE_DIR/newsletter_requirements.txt"
    else
        log_warn "Requirements file not found, installing basic dependencies..."
        pip install fastapi uvicorn pydantic
    fi
    
    log_info "Dependencies installed in conda environment: ${CONDA_ENV_NAME}"
}

# Check if service is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Start the service
start_service() {
    if is_running; then
        log_warn "Newsletter service is already running (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    # Ensure conda environment is ready
    check_conda_env
    check_result=$?
    
    if [ $check_result -ne 0 ]; then
        if [ $check_result -eq 2 ]; then
            log_info "Need to activate conda environment for service startup..."
            # We'll activate in the subprocess below
        else
            log_error "Conda environment not ready. Run '$0 setup' first."
            return 1
        fi
    fi
    
    log_info "Starting newsletter service..."
    
    # Load environment variables if .env file exists
    if [ -f "$SERVICE_DIR/.env" ]; then
        log_info "Loading environment variables from .env"
        export $(grep -v '^#' "$SERVICE_DIR/.env" | xargs)
    fi
    
    # Set default environment variables
    export DATABASE_PATH="${DATABASE_PATH:-$DATA_DIR/newsletter.db}"
    export HOST="${HOST:-localhost}"
    export PORT="${PORT:-8044}"
    export ADMIN_TOKEN="${ADMIN_TOKEN:-musequill-admin-2025}"
    
    # Start service in background with conda environment
    # Create a startup script that handles conda activation
    cat > "$SERVICE_DIR/start_service_with_conda.sh" << EOF
#!/bin/bash
# Auto-generated conda activation script
eval "\$(conda shell.bash hook)"
conda activate ${CONDA_ENV_NAME}
cd "${SERVICE_DIR}"
python newsletter_service.py
EOF
    
    chmod +x "$SERVICE_DIR/start_service_with_conda.sh"
    
    # Start the service
    nohup "$SERVICE_DIR/start_service_with_conda.sh" \
        > "$LOG_DIR/newsletter.log" 2>&1 & echo $! > "$PID_FILE"
    
    sleep 2
    
    if is_running; then
        local pid=$(cat "$PID_FILE")
        log_info "Newsletter service started successfully!"
        log_info "PID: $pid"
        log_info "Port: $PORT"
        log_info "Conda Environment: $CONDA_ENV_NAME"
        log_info "Admin Dashboard: http://localhost:$PORT/admin?token=$ADMIN_TOKEN"
        log_info "Logs: $LOG_DIR/newsletter.log"
        
        # Cleanup temporary script
        rm -f "$SERVICE_DIR/start_service_with_conda.sh"
    else
        log_error "Failed to start newsletter service"
        # Cleanup temporary script
        rm -f "$SERVICE_DIR/start_service_with_conda.sh"
        return 1
    fi
}

# Stop the service
stop_service() {
    if ! is_running; then
        log_warn "Newsletter service is not running"
        return 1
    fi
    
    local pid=$(cat "$PID_FILE")
    log_info "Stopping newsletter service (PID: $pid)..."
    
    kill "$pid"
    
    # Wait for graceful shutdown
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        log_warn "Force killing service..."
        kill -9 "$pid"
    fi
    
    rm -f "$PID_FILE"
    log_info "Newsletter service stopped"
}

# Restart the service
restart_service() {
    log_info "Restarting newsletter service..."
    stop_service
    sleep 2
    start_service
}

# Show service status
show_status() {
    echo ""
    echo "📊 Newsletter Service Status"
    echo "============================"
    
    # Check conda environment
    echo "Conda Environment: $CONDA_ENV_NAME"
    if check_conda; then
        if conda env list | grep -q "^${CONDA_ENV_NAME} "; then
            echo -e "Environment Status: ${GREEN}EXISTS${NC}"
            if [[ "$CONDA_DEFAULT_ENV" == "$CONDA_ENV_NAME" ]]; then
                echo -e "Environment Active: ${GREEN}YES${NC}"
            else
                echo -e "Environment Active: ${YELLOW}NO${NC} (use: conda activate $CONDA_ENV_NAME)"
            fi
        else
            echo -e "Environment Status: ${RED}MISSING${NC}"
        fi
    else
        echo -e "Conda Status: ${RED}NOT AVAILABLE${NC}"
    fi
    
    echo ""
    
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo -e "Service Status: ${GREEN}RUNNING${NC} (PID: $pid)"
        echo "Port: ${PORT:-8044}"
        echo "Database: ${DATABASE_PATH:-$DATA_DIR/newsletter.db}"
        echo "Log File: $LOG_DIR/newsletter.log"
        echo ""
        
        # Show recent log entries
        if [ -f "$LOG_DIR/newsletter.log" ]; then
            echo "Recent Log Entries:"
            echo "==================="
            tail -n 10 "$LOG_DIR/newsletter.log"
        fi
        
        # Show service health
        echo ""
        echo "Health Check:"
        echo "============="
        if command -v curl > /dev/null; then
            local health_response=$(curl -s "http://localhost:${PORT:-8044}/health" 2>/dev/null || echo "Connection failed")
            echo "$health_response"
        else
            echo "curl not available for health check"
        fi
        
    else
        echo -e "Service Status: ${RED}STOPPED${NC}"
    fi
    
    echo ""
}

# Show logs
show_logs() {
    local lines=${1:-50}
    
    if [ -f "$LOG_DIR/newsletter.log" ]; then
        log_info "Showing last $lines lines of newsletter.log..."
        echo ""
        tail -n "$lines" "$LOG_DIR/newsletter.log"
    else
        log_warn "Log file not found: $LOG_DIR/newsletter.log"
    fi
}

# Follow logs
follow_logs() {
    if [ -f "$LOG_DIR/newsletter.log" ]; then
        log_info "Following newsletter.log (Ctrl+C to stop)..."
        echo ""
        tail -f "$LOG_DIR/newsletter.log"
    else
        log_warn "Log file not found: $LOG_DIR/newsletter.log"
    fi
}

# Create backup
create_backup() {
    local backup_name="newsletter_backup_$(date +%Y%m%d_%H%M%S)"
    local backup_file="$SERVICE_DIR/backups/${backup_name}.tar.gz"
    
    log_info "Creating backup: $backup_name"
    
    tar -czf "$backup_file" \
        -C "$SERVICE_DIR" \
        --exclude="backups" \
        --exclude="logs" \
        --exclude="start_service_with_conda.sh" \
        .
    
    log_info "Backup created: $backup_file"
}

# Setup environment file
setup_env() {
    local env_file="$SERVICE_DIR/.env"
    
    if [ -f "$env_file" ]; then
        log_warn ".env file already exists"
        read -p "Overwrite existing .env file? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 0
        fi
    fi
    
    log_info "Creating .env file..."
    
    cat > "$env_file" << EOF
# MuseQuill Newsletter Service Configuration
# Generated on $(date)

# Server Configuration
HOST=localhost
PORT=8044

# Database
DATABASE_PATH=$DATA_DIR/newsletter.db

# Security
ADMIN_TOKEN=musequill-admin-$(openssl rand -hex 8 2>/dev/null || echo "change-this-token")

# Email Configuration (Optional - Configure for email sending)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=sky.sentient.ai@gmail.com
SMTP_PASSWORD=
FROM_EMAIL=noreply@musequill.ink
FROM_NAME=MuseQuill.ink Team

# CORS (Add your domains)
CORS_ORIGINS=https://musequill.ink,https://www.musequill.ink,http://localhost:3000

# Launch Configuration
LAUNCH_DATE=2025-09-01T00:00:00Z
EOF
    
    log_info ".env file created at: $env_file"
    log_warn "Please update the SMTP settings in .env for email functionality"
}

# Install as system service (Linux only)
install_systemd_service() {
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        log_error "Systemd installation only supported on Linux"
        return 1
    fi
    
    if [ "$EUID" -ne 0 ]; then
        log_error "Please run with sudo to install systemd service"
        return 1
    fi
    
    local service_file="/etc/systemd/system/musequill-newsletter.service"
    local current_user=$(logname 2>/dev/null || whoami)
    
    log_info "Installing systemd service..."
    
    cat > "$service_file" << EOF
[Unit]
Description=MuseQuill Newsletter Service
After=network.target

[Service]
Type=forking
User=$current_user
WorkingDirectory=$SERVICE_DIR
Environment=PATH=/home/$current_user/anaconda3/bin:/home/$current_user/miniconda3/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$SERVICE_DIR/startup.sh start
ExecStop=$SERVICE_DIR/startup.sh stop
ExecReload=$SERVICE_DIR/startup.sh restart
PIDFile=$PID_FILE
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable musequill-newsletter
    
    log_info "Systemd service installed and enabled"
    log_info "Use: sudo systemctl start musequill-newsletter"
}

# Test conda environment
test_env() {
    log_info "Testing conda environment setup..."
    
    check_conda_env
    local env_check_result=$?
    
    if [ $env_check_result -eq 0 ] || [ $env_check_result -eq 2 ]; then
        echo ""
        log_info "Conda environment test results:"
        echo "Current environment: ${CONDA_DEFAULT_ENV:-none}"
        echo "Python version: $(python --version 2>/dev/null || echo 'Python not found')"
        echo "Pip version: $(pip --version 2>/dev/null || echo 'Pip not found')"
        
        echo ""
        log_info "Testing newsletter service dependencies..."
        python -c "
import sys
try:
    import fastapi
    import uvicorn
    import pydantic
    print('✅ All core dependencies available')
    print(f'✅ FastAPI: {fastapi.__version__}')
    print(f'✅ Python: {sys.version.split()[0]}')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
    sys.exit(1)
        " 2>/dev/null || echo "❌ Dependency test failed"
        
        log_info "Environment test completed successfully!"
        return 0
    else
        log_error "Conda environment not ready"
        return 1
    fi
}

# Main script logic
case "${1:-help}" in
    "setup")
        create_directories
        setup_conda_env
        setup_env
        log_info "Setup complete! Run '$0 start' to start the service"
        ;;
    "start")
        create_directories
        start_service
        ;;
    "stop")
        stop_service
        ;;
    "restart")
        restart_service
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs "${2:-50}"
        ;;
    "follow-logs"|"tail")
        follow_logs
        ;;
    "backup")
        create_backup
        ;;
    "test-env")
        test_env
        ;;
    "install-service")
        install_systemd_service
        ;;
    "help"|*)
        echo "MuseQuill Newsletter Service Management"
        echo "======================================"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  setup           - Setup conda environment and install dependencies"
        echo "  start           - Start the newsletter service"
        echo "  stop            - Stop the newsletter service"
        echo "  restart         - Restart the newsletter service"
        echo "  status          - Show service status and conda environment info"
        echo "  logs [lines]    - Show recent log entries (default: 50)"
        echo "  follow-logs     - Follow log output in real-time"
        echo "  test-env        - Test conda environment and dependencies"
        echo "  backup          - Create a backup of the service"
        echo "  install-service - Install as systemd service (Linux, requires sudo)"
        echo "  help            - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 setup                    # First-time setup with conda"
        echo "  $0 test-env                 # Test conda environment"
        echo "  $0 start                    # Start service"
        echo "  $0 logs 100                 # Show last 100 log entries"
        echo "  $0 follow-logs              # Watch logs in real-time"
        echo ""
        echo "Conda Environment:"
        echo "  Name: $CONDA_ENV_NAME"
        echo "  Current: ${CONDA_DEFAULT_ENV:-none}"
        echo ""
        echo "Files:"
        echo "  Service: $SERVICE_DIR/newsletter_service.py"
        echo "  Config:  $SERVICE_DIR/.env"
        echo "  Logs:    $LOG_DIR/newsletter.log"
        echo "  Data:    $DATA_DIR/newsletter.db"
        echo ""
        ;;
esac