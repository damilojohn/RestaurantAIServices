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
        # self.orm_mappings = get_tables(self.engine)
        self.repo_path = Config.FEAST_REPO_PATH

        logger.info("Extractor instantiated")
    
    def extract_orders(self, start_date, end_date):
        # Orders = self.orm_mappings["Orders"]
        # OrderDetails = self.orm_mappings["OrderDetails"]
        logger.info("Loading Orders and OrderDetails as DataFrames...")

        # Load tables as DataFrames
        orders_df = pd.read_sql_table("Orders", self.engine)
        order_details_df = pd.read_sql_table("OrderDetails", self.engine)
        logger.info("Extracted data successfully")
        # Ensure start_date and end_date are datetime.date objects
        start_date = start_date.date() if hasattr(start_date, 'date') else start_date
        end_date = end_date.date() if hasattr(end_date, 'date') else end_date

        # Filter orders by date
        orders_df['order_date'] = pd.to_datetime(orders_df['DateCreated']).dt.date
        filtered_orders = orders_df[(orders_df['order_date'] >= start_date) & (orders_df['order_date'] <= end_date)]

        # Join in pandas
        merged_df = pd.merge(
            filtered_orders,
            order_details_df,
            left_on='Id',
            right_on='OrderID',
            how='inner'
        )

        # Build records for downstream processing
        records = []
        for _, row in merged_df.iterrows():
            records.append({
                'order_date': row['order_date'],
                'restaurant_id': row['BusinessID'],
                'item_id': row['ItemID'],
                'quantity': row['Quantity'],
                'unit_price': row['UnitPrice']
            })
        df = pd.DataFrame(records)

        # Aggregate demand per restaurant, item, and day
        # agg_df = df.groupby(
        #     ['restaurant_id', 'item_id', 'order_date'], as_index=False
        # ).agg(
        #     total_quantity_ordered=('quantity', 'sum'),
        #     avg_unit_price=('unit_price', 'mean')
        # )

        # Add datepart features
        df['day_of_week'] = pd.to_datetime(df['order_date']).dt.dayofweek
        df['is_weekend'] = df['day_of_week'] >= 5
        logger.info(df.columns)

        return df
    
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