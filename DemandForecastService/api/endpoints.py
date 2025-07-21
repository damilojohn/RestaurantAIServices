# from fastapi import APIRouter
# from .schemas import DemandForecastRequest, DemandForecastResponse
# from .service import predict_demand


# router = APIRouter()


# @router.get("/health")
# def health_check():
#     return {"status": "ok"}


# @router.post("/demandforecast/predict",
#              response_model=DemandForecastResponse)
# def predict(data: DemandForecastRequest) -> DemandForecastResponse:
#     """
#     Predict demand based on the provided data.
#     """
#     # Placeholder for actual prediction logic
#     # This should call the model and return the prediction
#     return DemandForecastResponse(prediction="Sample Prediction")


from fastapi import APIRouter, HTTPException
from .schemas import DemandForecastRequest, DemandForecastResponse
from .service import predict_demand as predict_demand_service


router = APIRouter()


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


@router.get("/demandforecast/menu")
def get_menu_items():
    """Get available menu items for forecasting"""
    from .service import model
    return {
        "items": [
            {"item_id": item_id, "item_name": name} 
            for item_id, name in model.menu_items.items()
        ]
    }