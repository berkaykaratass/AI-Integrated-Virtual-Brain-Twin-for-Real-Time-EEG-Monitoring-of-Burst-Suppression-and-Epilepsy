from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
from backend.app.simulation_manager import SimulationManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NeuroSyncAPI")

app = FastAPI(title="NeuroSync Model API", version="1.0.0")

# CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, specify domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Simulation Instance
# In a multi-user app, this would be per-session.
sim_manager = SimulationManager()

@app.get("/")
async def root():
    return {"status": "Neuronal Synchronization System Online"}

@app.websocket("/ws/simulation")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected to WebSocket")
    
    try:
        while True:
            # Check for incoming control messages (non-blocking)
            # This is a simple implementation. For full bidirectional, we might need two tasks.
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                command = json.loads(data)
                logger.info(f"Received command: {command}")
                sim_manager.handle_command(command)
            except asyncio.TimeoutError:
                pass # No message, continue stepping
            except WebSocketDisconnect:
                logger.info("Client disconnected")
                break
                
            # Step Simulation
            if sim_manager.is_running:
                state = sim_manager.step()
                await websocket.send_json(state)
                
            # Control frame rate
            await asyncio.sleep(0.016) # ~60 FPS cap
            
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
