from pydantic import BaseModel
from typing import List, Optional, Dict, Union, Any
from datetime import datetime, date


class ItemDemand(BaseModel):
    item_id: str
    item_name: str
    forecasted_quantity: int
    confidence_score: float
    trend: str  # "increasing", "decreasing", "stable"

class Forecast(BaseModel):
    item_id: int
    forecast_date: Any
    predicted_demand: float
    yhat_lower: float


class DemandForecastRequest(BaseModel):
    restaurant_id: str
    forecast_days: int = 7  # How many days to forecast
    item_ids: Optional[List[str]] = None  # Specific items to forecast, if None forecast all
    start_date: Optional[date] = None  # Start date for forecast, defaults to tomorrow


class DemandForecastResponse(BaseModel):
    restaurant_id: str
    # forecast_period: Dict[str, Union[str, int]]  # start_date, end_date
    total_items_forecasted: int
    predictions: List[Forecast]
    generated_at: datetime