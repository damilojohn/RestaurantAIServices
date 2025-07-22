import threading
import logging
import structlog
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import router as api_router

from ml_pipeline.notification_service import manager
from ml_pipeline.orchestrator import MLPipelineOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOG = structlog.stdlib.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator:
    LOG.info("AI API starting.....")
    
    orchestrator = MLPipelineOrchestrator()

    # orchestrator_thread = threading.Thread(target=orchestrator.run, daemon=True)
    # orchestrator_thread.start()

    orchestrator.run_training_pipeline()

    try:
        LOG.info("API Started.....")

        yield
    
    finally:
        LOG.info("API Shutting down .....")

app = FastAPI(
    title="Restaurant AI Service",
    description="Complete ML Pipeline for Restaurant Demand Forecasting",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api", tags=["api"])

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# @app.on_event("startup")
# def on_startup():
#     """Initialize services on startup"""
#     logger.info("Starting Restaurant AI Service")
    
#     # Start ML pipeline orchestrator in background
#     orchestrator = MLPipelineOrchestrator()
    
#     # Run orchestrator in separate thread
#     orchestrator_thread = threading.Thread(target=orchestrator.run, daemon=True)
#     orchestrator_thread.start()
    
#     logger.info("ML Pipeline orchestrator started")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
