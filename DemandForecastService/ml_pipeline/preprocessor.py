import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, LabelEncoder
import json
import logging

logger = logging.getLogger(__name__)

class FeatureEngineer:
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
    

    def create_features(self, df):
        logger.info("Starting feature engineering")
        
        # Ensure datetime and sort
        df['order_date'] = pd.to_datetime(df['order_date'])
        df = df.sort_values('order_date')
        
        # Create additional time-based features
        df['hour'] = df['order_date'].dt.hour
        df['day_of_month'] = df['order_date'].dt.day
        df['month'] = df['order_date'].dt.month
        # day_of_week and is_weekend already exist
        
        # Aggregate daily demand per item per restaurant
        daily_demand = df.groupby(
            ['restaurant_id', 'item_id', df['order_date'].dt.date], as_index=False
        ).agg(
            daily_demand=('quantity', 'sum'),
            avg_unit_price=('unit_price', 'mean')
        )
        daily_demand = daily_demand.rename(columns={'order_date': 'date'})
        daily_demand['date'] = pd.to_datetime(daily_demand['order_date'])
        daily_demand = daily_demand.drop(columns=['order_date'], errors='ignore')
        
        # Lag features
        daily_demand = daily_demand.sort_values(['restaurant_id', 'item_id', 'date'])
        for lag in [1, 2, 3, 7, 14]:
            daily_demand[f'demand_lag_{lag}'] = daily_demand.groupby(['restaurant_id', 'item_id'])['daily_demand'].shift(lag)
        
        # Rolling statistics
        for window in [3, 7, 14]:
            daily_demand[f'demand_rolling_mean_{window}'] = (
                daily_demand.groupby(['restaurant_id', 'item_id'])['daily_demand']
                .rolling(window, min_periods=1).mean().reset_index(0, drop=True)
            )
            daily_demand[f'demand_rolling_std_{window}'] = (
                daily_demand.groupby(['restaurant_id', 'item_id'])['daily_demand']
                .rolling(window, min_periods=1).std().reset_index(0, drop=True)
            )
        
        # Item stats
        item_stats = df.groupby('item_id').agg({
            'quantity': ['mean', 'std', 'count'],
            'unit_price': 'mean'
        }).reset_index()
        item_stats.columns = ['item_id', 'item_avg_quantity', 'item_std_quantity', 'item_total_orders', 'item_avg_price']
        
        # Restaurant stats
        restaurant_stats = df.groupby('restaurant_id').agg({
            'quantity': 'sum'
        }).reset_index()
        restaurant_stats.columns = ['restaurant_id', 'restaurant_total_quantity']
        
        # Merge all features
        features = daily_demand.merge(item_stats, on='item_id', how='left')
        features = features.merge(restaurant_stats, on='restaurant_id', how='left')
        
        # Add temporal features
        features['date'] = pd.to_datetime(features['date'])
        features['day_of_week'] = features['date'].dt.dayofweek
        features['month'] = features['date'].dt.month
        features['is_weekend'] = features['day_of_week'].isin([5, 6]).astype(int)
        
        # Fill missing values
        features = features.fillna(0)
        
        logger.info(f"Created {len(features)} feature rows with {len(features.columns)} columns")
        return features
    
    # def create_features(self, df):
    #     """Create features for demand forecasting"""
    #     logger.info("Starting feature engineering")
        
    #     # Sort by date
    #     df = df.sort_values('order_date')
    #     logger.info(df.columns)
    #     df['order_date'] = pd.to_datetime(df['order_date'])
        
    #     # Create time-based features
    #     df['hour'] = df['order_date'].dt.hour
    #     df['day_of_week'] = df['order_date'].dt.dayofweek
    #     df['day_of_month'] = df['order_date'].dt.day
    #     df['month'] = df['order_date'].dt.month
    #     df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
    #     # Aggregate daily demand per item per restaurant
    #     daily_demand = df.groupby(
    #         ['restaurant_id', 'item_id', 'order_date'], as_index=False
    #     ).agg(
    #         total_quantity_ordered=('quantity', 'sum'),
    #         avg_unit_price=('unit_price', 'mean')
    #     )
    #     # daily_demand = df.groupby([
    #     #     'restaurant_id', 'item_id', 
    #     #     df['order_date'].dt.date
    #     # ]).agg({
    #     #     'quantity': 'sum',
    #     #     'total_amount': 'sum',
    #     #     'order_id': 'nunique'
    #     # }).reset_index()
        
    #     daily_demand.columns = ['restaurant_id', 'item_id', 'date', 'daily_demand', 'daily_revenue', 'daily_orders']
        
    #     # Create lag features
    #     daily_demand = daily_demand.sort_values(['restaurant_id', 'item_id', 'date'])
        
    #     for lag in [1, 2, 3, 7, 14]:
    #         daily_demand[f'demand_lag_{lag}'] = daily_demand.groupby(['restaurant_id', 'item_id'])['daily_demand'].shift(lag)
        
    #     # Rolling statistics
    #     for window in [3, 7, 14]:
    #         daily_demand[f'demand_rolling_mean_{window}'] = daily_demand.groupby(['restaurant_id', 'item_id'])['daily_demand'].rolling(window, min_periods=1).mean().reset_index(0, drop=True)
    #         daily_demand[f'demand_rolling_std_{window}'] = daily_demand.groupby(['restaurant_id', 'item_id'])['daily_demand'].rolling(window, min_periods=1).std().reset_index(0, drop=True)
        
    #     # Item popularity features
    #     item_stats = df.groupby('item_id').agg({
    #         'quantity': ['mean', 'std', 'count'],
    #         'unit_price': 'mean'
    #     }).reset_index()
        
    #     item_stats.columns = ['item_id', 'item_avg_quantity', 'item_std_quantity', 'item_total_orders', 'item_avg_price']
        
    #     # Restaurant features
    #     restaurant_stats = df.groupby('restaurant_id').agg({
    #         'total_amount': 'mean',
    #         'order_id': 'nunique'
    #     }).reset_index()
        
    #     restaurant_stats.columns = ['restaurant_id', 'restaurant_avg_revenue', 'restaurant_total_orders']
        
    #     # Merge all features
    #     features = daily_demand.merge(item_stats, on='item_id', how='left')
    #     features = features.merge(restaurant_stats, on='restaurant_id', how='left')
        
    #     # Add temporal features
    #     features['date'] = pd.to_datetime(features['date'])
    #     features['day_of_week'] = features['date'].dt.dayofweek
    #     features['month'] = features['date'].dt.month
    #     features['is_weekend'] = features['day_of_week'].isin([5, 6]).astype(int)
        
    #     # Fill missing values
    #     features = features.fillna(0)
        
    #     logger.info(f"Created {len(features)} feature rows with {len(features.columns)} columns")
    #     return features
    
    def prepare_training_data(self, features):
        """Prepare data for XGBoost training"""
        
        # Select feature columns
        feature_cols = [col for col in features.columns if col not in ['restaurant_id', 'item_id', 'date', 'daily_demand']]
        
        # Encode categorical variables
        categorical_cols = ['restaurant_id', 'item_id']
        
        for col in categorical_cols:
            if col in features.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                features[f'{col}_encoded'] = self.label_encoders[col].fit_transform(features[col])
                feature_cols.append(f'{col}_encoded')
        
        # Prepare X and y
        X = features[feature_cols]
        y = features['daily_demand']
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=feature_cols)
        
        return X_scaled, y, feature_cols