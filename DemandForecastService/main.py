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
from ml_pipeline.notification_service import router as ws_router
from ml_pipeline.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOG = structlog.stdlib.get_logger()
config = Config


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator:
    LOG.info("AI API starting.....")
    
    orchestrator = MLPipelineOrchestrator()
    LOG.info("ML pipeline orchestrator instantiated....")

    # orchestrator_thread = threading.Thread(target=orchestrator.run, daemon=True)
    # orchestrator_thread.start()
    LOG.info("Instantiating training pipeline....")
    model_info = orchestrator.run_training_pipeline()

    try:
        LOG.info("API Started.....")
        await orchestrator.run_prediction_pipeline(model_info)

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
app.include_router(ws_router, prefix="/api", tags=["notification service"])
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

if __name__ == "__main__":
    import uvicorn
    LOG.info(f"Starting server on port {config.PORT}")
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")
