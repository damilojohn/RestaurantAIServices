import threading
from typing import TypedDict
import logging
import structlog
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.endpoints import router as api_router
from api.db import _create_engine, DB_CONN_STRING, create_session, Engine, SessionMaker


from ml_pipeline.orchestrator import MLPipelineOrchestrator
from ml_pipeline.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOG = structlog.stdlib.get_logger()
config = Config()

class State(TypedDict):
    engine: Engine
    sessionmaker: SessionMaker


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator:
    LOG.info("AI API starting.....")
    
    orchestrator = MLPipelineOrchestrator()
    LOG.info("ML pipeline orchestrator instantiated....")

    # # orchestrator_thread = threading.Thread(target=orchestrator.run, daemon=True)
    # # orchestrator_thread.start()
    LOG.info("Instantiating training pipeline....")
    model_info = orchestrator.run_training_pipeline()

    engine = _create_engine(DB_CONN_STRING)
    sessionmaker = create_session(engine)
    app.state.sessionmaker = sessionmaker

    try:
        LOG.info("API Started.....")
        await orchestrator.run_prediction_pipeline(model_info)

        yield {
            "engine":engine,
            "sessionmaker":sessionmaker
        }
    
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


if __name__ == "__main__":
    import uvicorn
    LOG.info(f"Starting server on port {config.PORT}")
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")
