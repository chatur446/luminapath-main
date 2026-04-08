#!/bin/bash

################################################################################
# LuminaPath - Automated One-Click Launcher
# This script handles everything: venv creation, installation, and launching
################################################################################

# Color codes for terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directories
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
LOGS_DIR="$PROJECT_DIR/logs"
STATIC_DIR="$PROJECT_DIR/static/uploaded_images"
REPORTS_DIR="$PROJECT_DIR/reports/pdf_files"
MODEL_DIR="$PROJECT_DIR/model"

# Backend/Frontend paths
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Log files
BACKEND_LOG="$LOGS_DIR/backend.log"
FRONTEND_LOG="$LOGS_DIR/frontend.log"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${BLUE}"
    echo "================================================================================"
    echo "                         🚀 LuminaPath Launcher 🚀"
    echo "                   AI-Powered Retinal Report Generator"
    echo "================================================================================"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_step() {
    echo -e "${BLUE}→ $1${NC}"
}

check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python 3.8+ and try again."
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_success "Found Python $PYTHON_VERSION"
}

################################################################################
# Main Setup Process
################################################################################

main() {
    clear
    print_header
    
    # Step 1: Check Python installation
    print_step "Checking Python installation..."
    check_python
    echo
    
    # Step 2: Create virtual environment if not exists
    if [ ! -d "$VENV_DIR" ]; then
        print_step "Creating virtual environment..."
        $PYTHON_CMD -m venv "$VENV_DIR" 2>&1 | tee -a "$LOGS_DIR/setup.log" > /dev/null
        if [ $? -eq 0 ]; then
            print_success "Virtual environment created successfully"
        else
            print_error "Failed to create virtual environment"
            exit 1
        fi
    else
        print_success "Virtual environment already exists"
    fi
    echo
    
    # Step 3: Activate virtual environment
    print_step "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    if [ $? -eq 0 ]; then
        print_success "Virtual environment activated"
    else
        print_error "Failed to activate virtual environment"
        exit 1
    fi
    echo
    
    # Step 4: Create necessary directories
    print_step "Creating project directories..."
    mkdir -p "$STATIC_DIR" 2>/dev/null
    mkdir -p "$REPORTS_DIR" 2>/dev/null
    mkdir -p "$MODEL_DIR" 2>/dev/null
    mkdir -p "$LOGS_DIR" 2>/dev/null
    print_success "All directories created"
    echo
    
    # Step 5: Check if .env exists
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        print_error ".env file not found!"
        print_info "Please create .env file from .env.example and configure your API keys"
        print_info "Run: cp .env.example .env"
        exit 1
    fi
    print_success ".env file found"
    echo
    
    # Step 6: Load environment variables
    print_step "Loading environment variables..."
    set -a
    source "$PROJECT_DIR/.env" 2>/dev/null
    set +a
    print_success "Environment variables loaded"
    echo
    
    # Step 7: Check if model file exists
    if [ ! -f "$MODEL_DIR/Retinal_OCT_C8_model.h5" ]; then
        print_error "Model file not found at $MODEL_DIR/Retinal_OCT_C8_model.h5"
        print_info "Please place your model file in the model/ directory"
        exit 1
    fi
    print_success "Model file found"
    echo
    
    # Step 8: Install/Update dependencies
    print_step "Checking and installing dependencies..."
    
    # Check if requirements are already installed
    pip show fastapi &> /dev/null
    if [ $? -ne 0 ]; then
        print_info "Installing backend dependencies (this may take a few minutes)..."
        pip install -q -r "$BACKEND_DIR/requirements.txt" 2>&1 | tee -a "$LOGS_DIR/setup.log" > /dev/null
        if [ $? -eq 0 ]; then
            print_success "Backend dependencies installed"
        else
            print_error "Failed to install backend dependencies"
            print_info "Check logs/setup.log for details"
            exit 1
        fi
    else
        print_success "Backend dependencies already installed"
    fi
    
    pip show streamlit &> /dev/null
    if [ $? -ne 0 ]; then
        print_info "Installing frontend dependencies..."
        pip install -q streamlit requests 2>&1 | tee -a "$LOGS_DIR/setup.log" > /dev/null
        if [ $? -eq 0 ]; then
            print_success "Frontend dependencies installed"
        else
            print_error "Failed to install frontend dependencies"
            exit 1
        fi
    else
        print_success "Frontend dependencies already installed"
    fi
    echo
    
    # Step 9: Clean up old log files
    print_step "Preparing log files..."
    > "$BACKEND_LOG"
    > "$FRONTEND_LOG"
    print_success "Log files ready"
    echo
    
    # Step 10: Check if ports are available
    print_step "Checking port availability..."
    
    # Check if port 8000 is in use
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        print_error "Port 8000 is already in use"
        print_info "Please stop the process using port 8000 or change the backend port"
        exit 1
    fi
    print_success "Port 8000 is available"
    
    # Check if port 8501 is in use
    if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        print_error "Port 8501 is already in use"
        print_info "Please stop the process using port 8501 or Streamlit will choose another port"
    else
        print_success "Port 8501 is available"
    fi
    echo
    
    # Step 11: Start Backend Server
    print_step "Starting backend server..."
    cd "$BACKEND_DIR"
    nohup uvicorn main:app --host 127.0.0.1 --port 8000 --reload > "$BACKEND_LOG" 2>&1 &
    BACKEND_PID=$!
    cd "$PROJECT_DIR"
    
    if [ $? -eq 0 ]; then
        print_success "Backend server started (PID: $BACKEND_PID)"
        echo "$BACKEND_PID" > "$LOGS_DIR/backend.pid"
    else
        print_error "Failed to start backend server"
        exit 1
    fi
    echo
    
    # Step 12: Wait for backend to initialize
    print_step "Waiting for backend to initialize..."
    sleep 3
    
    # Verify backend is running
    if curl -s http://127.0.0.1:8000/ > /dev/null 2>&1; then
        print_success "Backend is running successfully"
    else
        print_error "Backend failed to start properly"
        print_info "Check logs/backend.log for details"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    echo
    
    # Step 13: Start Frontend
    print_step "Starting frontend application..."
    cd "$FRONTEND_DIR"
    
    # Store frontend PID for cleanup
    nohup streamlit run app.py --server.headless true > "$FRONTEND_LOG" 2>&1 &
    FRONTEND_PID=$!
    echo "$FRONTEND_PID" > "$LOGS_DIR/frontend.pid"
    cd "$PROJECT_DIR"
    
    print_success "Frontend started (PID: $FRONTEND_PID)"
    echo
    
    # Step 14: Wait for frontend to be ready
    print_step "Waiting for frontend to be ready..."
    sleep 3
    echo
    
    # Step 15: Display success message
    echo -e "${GREEN}"
    echo "================================================================================"
    echo "                    ✅ LuminaPath is Running! ✅"
    echo "================================================================================"
    echo -e "${NC}"
    echo
    echo -e "${BLUE}Backend API:${NC}      http://127.0.0.1:8000"
    echo -e "${BLUE}API Docs:${NC}         http://127.0.0.1:8000/docs"
    echo -e "${BLUE}Frontend UI:${NC}      http://localhost:8501"
    echo
    echo -e "${YELLOW}Logs:${NC}"
    echo -e "  Backend:  logs/backend.log"
    echo -e "  Frontend: logs/frontend.log"
    echo
    echo -e "${YELLOW}To stop LuminaPath:${NC}"
    echo -e "  Run: ${BLUE}bash stop.sh${NC}"
    echo -e "  Or:  ${BLUE}kill $BACKEND_PID $FRONTEND_PID${NC}"
    echo
    echo -e "${GREEN}Open your browser and navigate to: http://localhost:8501${NC}"
    echo
    
    # Step 16: Monitor processes (optional)
    echo -e "${YELLOW}Press Ctrl+C to view logs, or close this terminal to run in background${NC}"
    echo
    
    # Follow logs (can be interrupted with Ctrl+C)
    tail -f "$BACKEND_LOG" "$FRONTEND_LOG" 2>/dev/null
}

################################################################################
# Cleanup on Exit
################################################################################

cleanup() {
    echo
    print_info "LuminaPath is still running in the background"
    print_info "Access the application at: http://localhost:8501"
    print_info "To stop all services, run: bash stop.sh"
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT SIGTERM

################################################################################
# Execute Main Function
################################################################################

main
