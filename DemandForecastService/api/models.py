from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy import create_engine, declarative_base


base = declarative_base()

class Orders(base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_number = Column(String(50), nullable=False, unique=True)
    customer_name = Column(String(100), nullable=False)
    order_date = Column(DateTime, nullable=False)
    total_amount = Column(Integer, nullable=False)