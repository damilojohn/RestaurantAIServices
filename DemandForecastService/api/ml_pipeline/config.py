import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database connections
    RAW_DB_URL = (
    "mssql+pyodbc://hobwiseuser:Khadilac6363%25@mssql-198211-0.cloudclusters.net:10297/EnterpriseDB"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&Encrypt=yes"
    "&TrustServerCertificate=yes"
    "&Connection+Timeout=30"
    )

    FEATURE_DB_URL = os.getenv("FEATURE_DB_URL", "postgresql://user:password@localhost/restaurant_features")
    PREDICTIONS_DB_URL = os.getenv("PREDICTIONS_DB_URL", "postgresql://user:password@localhost/restaurant_predictions")
    
    # Feature Store
    FEAST_REPO_PATH = os.getenv("FEAST_REPO_PATH", "./feature_store")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Model Registry
    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    WANDB_PROJECT = os.getenv("WANDB_PROJECT", "restaurant-demand-forecast")
    
    # Model settings
    MODEL_NAME = "demand_forecasting_xgb"
    MODEL_STAGE = "Production"


# # database/models.py
# from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker, relationship
# from datetime import datetime

# Base = declarative_base()

# class RawOrder(Base):
#     __tablename__ = "raw_orders"
    
#     id = Column(Integer, primary_key=True)
#     order_id = Column(String, unique=True, nullable=False)
#     restaurant_id = Column(String, nullable=False)
#     customer_id = Column(String, nullable=False)
#     order_date = Column(DateTime, nullable=False)
#     total_amount = Column(Float, nullable=False)
#     created_at = Column(DateTime, default=datetime.utcnow)

# class RawOrderItem(Base):
#     __tablename__ = "raw_order_items"
    
#     id = Column(Integer, primary_key=True)
#     order_id = Column(String, ForeignKey('raw_orders.order_id'), nullable=False)
#     item_id = Column(String, nullable=False)
#     item_name = Column(String, nullable=False)
#     quantity = Column(Integer, nullable=False)
#     unit_price = Column(Float, nullable=False)
#     created_at = Column(DateTime, default=datetime.utcnow)
    
#     order = relationship("RawOrder", back_populates="items")

# RawOrder.items = relationship("RawOrderItem", back_populates="order")

# class FeatureStore(Base):
#     __tablename__ = "feature_store"
    
#     id = Column(Integer, primary_key=True)
#     restaurant_id = Column(String, nullable=False)
#     item_id = Column(String, nullable=False)
#     feature_date = Column(DateTime, nullable=False)
#     features = Column(Text, nullable=False)  # JSON string
#     created_at = Column(DateTime, default=datetime.utcnow)

# class PredictionResults(Base):
#     __tablename__ = "prediction_results"
    
#     id = Column(Integer, primary_key=True)
#     restaurant_id = Column(String, nullable=False)
#     item_id = Column(String, nullable=False)
#     prediction_date = Column(DateTime, nullable=False)
#     predicted_demand = Column(Float, nullable=False)
#     confidence_score = Column(Float, nullable=False)
#     model_version = Column(String, nullable=False)
#     created_at = Column(DateTime, default=datetime.utcnow)