# # import xgboost
# from fastapi import FastAPI, HTTPException
# from .schemas import DemandForecastRequest, DemandForecastResponse
# import joblib

# model = None

# def load_model():
#     global model
#     model = joblib.load("models/xgboost_demand_model.pkl")


# def predict_demand(data: DemandForecastRequest) -> DemandForecastResponse:
#     if model is None:
#         load_model()
    
#     # Example: simple feature extraction from past_orders
#     features = [sum(data.past_orders), max(data.past_orders), len(data.past_orders)]
#     prediction = model.predict([features])[0]
    
#     return DemandForecastResponse(prediction=prediction)

import random
from datetime import datetime, date, timedelta
from typing import List, Dict
import numpy as np
from .schemas import DemandForecastRequest, DemandForecastResponse, ItemDemand


class MockXGBoostModel:
    """Mock XGBoost model for demo purposes"""
    
    def __init__(self):
        # Mock restaurant menu items with realistic names
        self.menu_items = {
            "item_001": "Margherita Pizza",
            "item_002": "Pepperoni Pizza", 
            "item_003": "Caesar Salad",
            "item_004": "Chicken Alfredo",
            "item_005": "Beef Burger",
            "item_006": "Fish Tacos",
            "item_007": "Chocolate Cake",
            "item_008": "Grilled Salmon",
            "item_009": "Veggie Wrap",
            "item_010": "Chicken Wings"
        }
        
        # Mock historical demand patterns (simulating seasonal/trend data)
        self.base_demand = {
            "item_001": 45,  # Popular items
            "item_002": 38,
            "item_003": 25,
            "item_004": 32,
            "item_005": 42,
            "item_006": 28,
            "item_007": 18,
            "item_008": 35,
            "item_009": 22,
            "item_010": 48
        }
    
    def predict_demand(self, restaurant_id: str, item_ids: List[str], forecast_days: int) -> List[ItemDemand]:
        """Simulate XGBoost prediction with realistic variations"""
        predictions = []
        
        # Add some restaurant-specific multiplier
        restaurant_multiplier = hash(restaurant_id) % 20 / 10 + 0.8  # 0.8 to 2.8
        
        for item_id in item_ids:
            if item_id not in self.menu_items:
                continue
                
            base_qty = self.base_demand.get(item_id, 20)
            
            # Simulate model prediction with some randomness
            # Factor in day of week, seasonality, trends
            daily_variation = random.uniform(0.7, 1.3)
            seasonal_factor = random.uniform(0.9, 1.1)
            trend_factor = random.uniform(0.95, 1.05)
            
            predicted_qty = int(base_qty * restaurant_multiplier * daily_variation * seasonal_factor * trend_factor)
            
            # Ensure minimum of 1
            predicted_qty = max(1, predicted_qty)
            
            # Generate confidence score
            confidence = random.uniform(0.75, 0.95)
            
            # Determine trend
            trend_rand = random.random()
            if trend_rand < 0.3:
                trend = "increasing"
            elif trend_rand < 0.6:
                trend = "decreasing"
            else:
                trend = "stable"
            
            predictions.append(ItemDemand(
                item_id=item_id,
                item_name=self.menu_items[item_id],
                forecasted_quantity=predicted_qty,
                confidence_score=round(confidence, 2),
                trend=trend
            ))
        
        return predictions


# Global model instance
model = MockXGBoostModel()


def load_model():
    """Load the trained XGBoost model"""
    global model
    print("Loading XGBoost demand forecasting model...")
    # In a real implementation, you'd load from file:
    # model = joblib.load("models/xgboost_demand_model.pkl")
    print("Model loaded successfully!")


def predict_demand(data: DemandForecastRequest) -> DemandForecastResponse:
    """Run inference on demand forecasting model"""
    
    # Set default start date to tomorrow
    start_date = data.start_date or (date.today() + timedelta(days=1))
    end_date = start_date + timedelta(days=data.forecast_days - 1)
    
    # If no specific items requested, use all menu items
    item_ids = data.item_ids or list(model.menu_items.keys())
    
    # Get predictions from model
    predictions = model.predict_demand(
        restaurant_id=data.restaurant_id,
        item_ids=item_ids,
        forecast_days=data.forecast_days
    )
    
    # Build response
    response = DemandForecastResponse(
        restaurant_id=data.restaurant_id,
        forecast_period={
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "days": data.forecast_days
        },
        total_items_forecasted=len(predictions),
        predictions=predictions,
        generated_at=datetime.now()
    )
    
    return response