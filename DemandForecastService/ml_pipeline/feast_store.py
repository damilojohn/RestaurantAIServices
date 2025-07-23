import os
from feast import FeatureStore, Entity, Feature, FeatureView, FileSource, ValueType
from feast.types import Float32, Int64
from datetime import timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class FeastFeatureStore:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.store = None
        self.restaurant_entity = None
        self.item_entity = None
        self.demand_features = None
        # self._setup_feature_store()
    
    def _setup_feature_store(self):
        """Initialize Feast feature store"""
        if not os.path.exists(self.repo_path):
            os.makedirs(self.repo_path)
        
        # Create feature store
        self.store = FeatureStore(repo_path=self.repo_path)
        
        # Define entities
        self.restaurant_entity = Entity(
            name="restaurant_id",
            description="Restaurant identifier",
            value_type=ValueType.STRING
        )
        
        self.item_entity = Entity(
            name="item_id", 
            description="Menu item identifier",
            value_type=ValueType.STRING,
        )
        
        # Define feature view
        self.demand_features = FeatureView(
            name="demand_features",
            entities=[self.item_entity, self.restaurant_entity],
            features=[
                Feature(name="demand_lag_1", dtype=ValueType.FLOAT),
                Feature(name="demand_lag_7", dtype=ValueType.FLOAT),
                Feature(name="demand_rolling_mean_7", dtype=ValueType.FLOAT),
                Feature(name="demand_rolling_std_7", dtype=ValueType.FLOAT),
                Feature(name="item_avg_quantity", dtype=ValueType.FLOAT),
                Feature(name="restaurant_avg_revenue", dtype=ValueType.FLOAT),
                Feature(name="day_of_week", dtype=ValueType.INT64),
                Feature(name="is_weekend", dtype=ValueType.INT64)
            ],
            source=FileSource(
                path=f"{self.repo_path}/data/data.csv",
                event_timestamp_column="event_timestamp",
            ),
            ttl=timedelta(days=365),
        )
        
        # Register entities and feature view with Feast
        self.store.apply([self.restaurant_entity, self.item_entity, self.demand_features])
        logger.info("Feature store setup completed")
    
    def store_features(self, features_df):
        """Store features in Feast"""
        # Add event timestamp
        features_df['event_timestamp'] = pd.to_datetime(features_df['order_date'])
        # Ingest the DataFrame into the feature view
        self.store.ingest(self.demand_features, features_df)
        logger.info(f"Stored {len(features_df)} feature rows in Feast")
    
    def get_features(self, entity_df):
        """Retrieve features for prediction"""
        feature_vector = self.store.get_historical_features(
            entity_df=entity_df,
            features=["demand_features:demand_lag_1", "demand_features:demand_lag_7"]
        )
        return feature_vector.to_df()