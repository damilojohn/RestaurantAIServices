from sqlalchemy import Column, Integer, String, DateTime, Float, Date, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime


base = declarative_base()

class Orders(base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_number = Column(String(50), nullable=False, unique=True)
    customer_name = Column(String(100), nullable=False)
    order_date = Column(DateTime, nullable=False)
    total_amount = Column(Integer, nullable=False)


class PredictionResults(base):
    __tablename__ = "forecasts"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    store = Column(Integer)
    item = Column(Integer)
    forecast_date = Column(Date)
    yhat = Column(Float)
    yhat_lower = Column(Float)
    yhat_upper = Column(Float)
    model_version = Column(String)