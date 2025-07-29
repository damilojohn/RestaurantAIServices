from sqlalchemy.orm import Session
import structlog
import random
from .models import PredictionResults as Preds
from datetime import datetime
from .schemas import DemandForecastResponse, Forecast

LOG = structlog.stdlib.get_logger()


def _get_demand_forecast(session: Session, restaurant_id) -> DemandForecastResponse:
    LOG.info(f"Getting forecasts for restaurant{restaurant_id}....")
    restaurant_id = random.randint(0,10)
    LOG.info(f"Mapped to {restaurant_id}....")
    try:
        forecasts = session.query(Preds).filter(
            Preds.store == restaurant_id
        ).order_by(Preds.forecast_date).all()

        forecast_list = [
            Forecast(item_id=f.item,
            forecast_date=f.forecast_date,
            predicted_demand=f.yhat,
            yhat_lower=f.yhat_lower)
            for f in forecasts
        ]
        resp = DemandForecastResponse(
            restaurant_id = str(restaurant_id),
            predictions = forecast_list,
            generated_at = datetime.now(),
            total_items_forecasted=len(forecast_list)
        )
        return resp
    
    except Exception as e:
        LOG.info(f"getting forecast failed with exception{e}")
        raise e

