# data_ingestion/extractor.py
import pandas as pd
from .models import get_tables
from .utils import create_engine_from_url, get_session_factory
from .config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataExtractor:
    def __init__(self):
        self.engine = create_engine_from_url(Config.RAW_DB_URL)
        self.SessionLocal = get_session_factory(Config.RAW_DB_URL)
        self.orm_mappings = get_tables(self.engine)
        print(self.orm_mappings)
    
    def extract_orders(self, start_date, end_date):
        """Extract raw orders from MySQL database"""
        logger.info(f"Extracting orders from {start_date} to {end_date}")
        
        session = self.SessionLocal()
        try:
            Orders = self.orm_mappings["Orders"]
            OrderDetails = self.orm_mappings["OrderDetails"]
            # Query orders with items using MySQL-optimized query
            query = session.query(Orders, OrderDetails).join(
                OrderDetails, Orders.order_id == OrderDetails.order_id
            ).filter(
                Orders.order_date >= start_date,
                Orders.order_date <= end_date
            )
            
            # Convert to DataFrame
            data = []
            for order, item in query:
                data.append({
                    'order_id': order.order_id,
                    'restaurant_id': order.restaurant_id,
                    'customer_id': order.customer_id,
                    'order_date': order.order_date,
                    'total_amount': order.total_amount,
                    'item_id': item.item_id,
                    'item_name': item.item_name,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price
                })
            
            df = pd.DataFrame(data)
            logger.info(f"Extracted {len(df)} order items")
            return df
            
        except Exception as e:
            logger.error(f"Error extracting orders: {e}")
            raise
        finally:
            session.close()
    
    def extract_orders_raw_sql(self, start_date, end_date):
        """Extract orders using raw SQL for better performance"""
        logger.info(f"Extracting orders with raw SQL from {start_date} to {end_date}")
        
        sql_query = """
        SELECT 
            o.order_id,
            o.restaurant_id,
            o.customer_id,
            o.order_date,
            o.total_amount,
            i.item_id,
            i.item_name,
            i.quantity,
            i.unit_price
        FROM raw_orders o
        JOIN raw_order_items i ON o.order_id = i.order_id
        WHERE o.order_date >= %s AND o.order_date <= %s
        ORDER BY o.order_date
        """
        
        try:
            df = pd.read_sql_query(
                sql_query, 
                self.engine, 
                params=[start_date, end_date],
                parse_dates=['order_date']
            )
            logger.info(f"Extracted {len(df)} order items using raw SQL")
            return df
            
        except Exception as e:
            logger.error(f"Error extracting orders with raw SQL: {e}")
            raise
    
    def get_restaurants(self):
        """Get list of all restaurants"""
        try:
            query = "SELECT DISTINCT restaurant_id FROM raw_orders"
            df = pd.read_sql_query(query, self.engine)
            return df['restaurant_id'].tolist()
        except Exception as e:
            logger.error(f"Error getting restaurants: {e}")
            return []
    
    def get_items_by_restaurant(self, restaurant_id):
        """Get items for a specific restaurant"""
        try:
            query = """
            SELECT DISTINCT i.item_id, i.item_name
            FROM raw_order_items i
            JOIN raw_orders o ON i.order_id = o.order_id
            WHERE o.restaurant_id = %s
            """
            df = pd.read_sql_query(query, self.engine, params=[restaurant_id])
            return df['item_id'].tolist()
        except Exception as e:
            logger.error(f"Error getting items for restaurant {restaurant_id}: {e}")
            return []