
from fastapi import APIRouter, HTTPException, Depends
from .schemas import DemandForecastRequest, DemandForecastResponse
from .service import _get_demand_forecast
from .db import get_db_session


router = APIRouter(prefix="/ai")


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "Restaurant AI Demand Forecasting"}


@router.post("/demandforecast/predict", response_model=DemandForecastResponse)
def predict_demand_endpoint(data: DemandForecastRequest) -> DemandForecastResponse:
    """
    Predict demand for restaurant items based on historical data.
    
    - **restaurant_id**: Unique identifier for the restaurant
    - **forecast_days**: Number of days to forecast (default: 7)
    - **item_ids**: Specific items to forecast (optional, forecasts all if not provided)
    - **start_date**: Start date for forecast (optional, defaults to tomorrow)
    """
    try:
        result = predict_demand_service(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/demandforecast/predict", response_model=DemandForecastResponse)
def get_demand_forecast(restaurant_id: str, db_session = Depends(get_db_session)) -> DemandForecastResponse:
    """Get latest demand forecasts for all items in a restaurant
    Args:
        restaurant_id : Restaurant ID in Orders Table

    Returns:
        DemandForecastObject
    """
    try:

        return _get_demand_forecast(db_session, restaurant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to get forecasts with error {e}")

