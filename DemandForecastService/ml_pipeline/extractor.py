# data_ingestion/extractor.py
import pandas as pd
import numpy as np
from .models import get_tables
from .utils import create_engine_from_url, get_session_factory, LOG
from .config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataExtractor:
    def __init__(self, num_stores, num_items):
        self.engine = create_engine_from_url(Config.RAW_DB_URL)
        # self.orm_mappings = get_tables(self.engine)
        self.repo_path = Config.FEAST_REPO_PATH
        self.num_stores = num_stores
        self.num_items = num_items

        LOG.info("Extractor instantiated")
    
    def extract_orders(self, start_date, end_date):
        # Use synthetic data for now. Later we would actually pull from Henry's DB
        synthetic_data = self._generate_synthetic_data(
            start_date,
            end_date,
            self.num_stores,
            self.num_items
        )
        LOG.info(f"✅ Created {len(synthetic_data):,} sales transactions")
        LOG.info(f"📈 Average daily sales per SKU: {synthetic_data['sales'].mean():.1f} units")
        LOG.info(f"📊 Sales volume range: {synthetic_data['sales'].min()} to {synthetic_data['sales'].max()} units/day")
        return synthetic_data


    def _generate_synthetic_data(self, start_date, end_date, num_stores, num_items):
        """
        Generate realistic synthetic sales data with multiple patterns
        
        Returns:
            pd.DataFrame: Sales data with columns [date, store, item, sales]
        """
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        data = []
        np.random.seed(42)  # For reproducible results
        
        print(f"🛒 Simulating {len(date_range)} days of retail operations across {num_stores} stores")
        
        for store in range(1, num_stores + 1):
            # Store characteristics
            store_size_factor = np.random.uniform(0.7, 1.3)  # Some stores are bigger
            store_location_factor = np.random.normal(1.0, 0.2)  # Location effects
            
            for item in range(1, num_items + 1):
                # Item characteristics
                base_demand = np.random.normal(100, 30) * store_size_factor
                item_popularity = np.random.uniform(0.5, 2.0)  # Some items more popular
                
                for date in date_range:
                    # Seasonal patterns (yearly cycle)
                    day_of_year = date.timetuple().tm_yday
                    seasonal = 30 * np.sin(2 * np.pi * day_of_year / 365.25) * item_popularity
                    
                    # Weekly patterns (higher demand on weekends)
                    weekly = 15 if date.weekday() >= 5 else 0
                    
                    # Holiday effects (increased demand around major holidays)
                    month_day = (date.month, date.day)
                    holiday_boost = 0
                    if month_day in [(12, 25), (1, 1), (7, 4), (11, 24)]:  # Major holidays
                        holiday_boost = 50
                    elif date.month == 12 and date.day > 15:  # Holiday season
                        holiday_boost = 25
                    
                    # Growth trend (business expanding over time)
                    days_since_start = (date - pd.to_datetime(start_date)).days
                    trend = 0.02 * days_since_start * store_location_factor
                    
                    # Random noise (real-world variation)
                    noise = np.random.normal(0, 15)
                    
                    # Calculate final sales (ensure non-negative)
                    sales = max(0, int(
                        base_demand + 
                        seasonal + 
                        weekly + 
                        holiday_boost + 
                        trend + 
                        noise
                    ))
                    
                    data.append({
                        'date': date,
                        'store': store,
                        'item': item,
                        'sales': sales
                    })
        
        return pd.DataFrame(data)
        
    
    def extract_orders_raw_sql(self, start_date, end_date):
        """Extract orders using raw SQL for better performance"""
        LOG.info(f"Extracting orders with raw SQL from {start_date} to {end_date}")
        
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
            LOG.info(f"Extracted {len(df)} order items using raw SQL")
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