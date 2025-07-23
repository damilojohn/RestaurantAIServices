import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    HOST = "127.0.0.1"
    PORT = 54300
    # Database connections
    # RAW_DB_URL = (
    # "mssql+pyodbc://hobwiseuser:Khadilac6363%25@mssql-198211-0.cloudclusters.net:10297/EnterpriseDB"
    # "?driver=ODBC+Driver+17+for+SQL+Server"
    # "&Encrypt=yes"
    # "&TrustServerCertificate=yes"
    # "&Connection+Timeout=30"
    # )

    RAW_DB_URL = os.getenv("RAW_DB_URL")

    FEATURE_DB_URL = os.getenv("FEATURE_DB_URL")
    PREDICTIONS_DB_URL = os.getenv("PREDICTIONS_DB_URL")
    
    # Feature Store
    FEAST_REPO_PATH = os.getenv("FEAST_REPO_PATH", "./feature_store")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Model Registry
    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:8000")
    WANDB_PROJECT = os.getenv("WANDB_PROJECT", "restaurant-demand-forecast")
    WANDB_API_KEY = os.getenv("WANDB_API_KEY")
    
    # Model settings
    MODEL_NAME = "demand_forecasting_xgb"
    MODEL_STAGE = "Production"
