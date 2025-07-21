import os
from feast import FeatureStore, Entity, Feature, FeatureView, FileSource
from feast.types import Float32, Int64, String
from datetime import timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class FeastFeatureStore:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.store = None
        self._setup_feature_store()
    
    def _setup_feature_store(self):
        """Initialize Feast feature store"""
        if not os.path.exists(self.repo_path):
            os.makedirs(self.repo_path)
        
        # Create feature store
        self.store = FeatureStore(repo_path=self.repo_path)
        
        # Define entities
        restaurant_entity = Entity(
            name="restaurant_id",
            description="Restaurant identifier",
            value_type=String,
        )
        
        item_entity = Entity(
            name="item_id", 
            description="Menu item identifier",
            value_type=String,
        )
        
        # Define feature views
        demand_features = FeatureView(
            name="demand_features",
            entities=["restaurant_id", "item_id"],
            features=[
                Feature(name="demand_lag_1", dtype=Float32),
                Feature(name="demand_lag_7", dtype=Float32),
                Feature(name="demand_rolling_mean_7", dtype=Float32),
                Feature(name="demand_rolling_std_7", dtype=Float32),
                Feature(name="item_avg_quantity", dtype=Float32),
                Feature(name="restaurant_avg_revenue", dtype=Float32),
                Feature(name="day_of_week", dtype=Int64),
                Feature(name="is_weekend", dtype=Int64),
            ],
            source=FileSource(
                path=f"{self.repo_path}/features.parquet",
                event_timestamp_column="event_timestamp",
            ),
            ttl=timedelta(days=365),
        )
        
        logger.info("Feature store setup completed")
    
    def store_features(self, features_df):
        """Store features in Feast"""
        # Add event timestamp
        features_df['event_timestamp'] = pd.to_datetime(features_df['date'])
        
        # Save to parquet
        features_path = f"{self.repo_path}/features.parquet"
        features_df.to_parquet(features_path)
        
        # Apply feature store
        self.store.apply([])
        
        logger.info(f"Stored {len(features_df)} feature rows")
    
    def get_features(self, entity_df):
        """Retrieve features for prediction"""
        feature_vector = self.store.get_historical_features(
            entity_df=entity_df,
            features=["demand_features:demand_lag_1", "demand_features:demand_lag_7"]
        )
        
        return feature_vector.to_df()