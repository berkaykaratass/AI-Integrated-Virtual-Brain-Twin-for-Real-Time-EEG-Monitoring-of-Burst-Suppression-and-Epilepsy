#!/bin/bash

# Renkler
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== NeuroSync Cortex Simulation System ===${NC}"

# 0. Check Environment (Fix for moving folder)
if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    echo -e "${RED}[System] Virtual Environment invalid or missing (Moved Folder?). Re-creating...${NC}"
    rm -rf venv
    python3 -m venv venv
    source venv/bin/activate
    pip install fastapi uvicorn websockets numpy scipy networkx matplotlib seaborn mne
else
    source venv/bin/activate
fi

if [ ! -d "frontend/node_modules" ]; then
    echo -e "${RED}[System] Frontend dependencies missing. Installing...${NC}"
    cd frontend
    npm install
    cd ..
fi

echo -e "${BLUE}Starting Systems...${NC}"

# 1. Start Backend
echo -e "${GREEN}[Backend] Initializing FastAPI Server...${NC}"
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 1 > backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}[Backend] Online (PID: $BACKEND_PID)${NC}"

# 2. Start Frontend
echo -e "${GREEN}[Frontend] Initializing React Interface...${NC}"
cd frontend
# Check if vite is executable, if not npm install again just in case
if [ ! -x "./node_modules/.bin/vite" ]; then
    npm install
fi
npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}[Frontend] Online (PID: $FRONTEND_PID)${NC}"

echo -e "${BLUE}=== SYSTEM READY ===${NC}"
echo -e "Access the Clinical Dashboard at: http://localhost:5173"
echo -e "Logs are being written to backend.log and frontend/frontend.log"
echo -e "Press CTRL+C to Shutdown."

# Wait for user interrupt
wait $BACKEND_PID $FRONTEND_PID
