from sqlalchemy.ext.automap import automap_base
from sqlalchemy import MetaData, Table
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


def get_tables(engine):
    """
    Reflect all tables in the database and return a dictionary mapping table names to ORM classes.
    """
    Base = automap_base()
    Base.prepare(engine, reflect=True)
    table_classes = {table_name: getattr(Base.classes, table_name) for table_name in Base.classes.keys()}
    return table_classes


class PredictionResults(Base):
    __tablename__ = "prediction_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(String(255), nullable=False)
    item_id = Column(String(255), nullable=False)
    prediction_date = Column(DateTime, nullable=False)
    predicted_demand = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    model_version = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
