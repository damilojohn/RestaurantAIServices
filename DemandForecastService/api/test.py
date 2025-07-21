import requests
import json
from datetime import date, timedelta

BASE_URL = "http://127.0.0.1:8000/api"

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check:", response.json())

def test_menu_items():
    response = requests.get(f"{BASE_URL}/demandforecast/menu")
    print("Menu Items:", response.json())

def test_demand_forecast():
    # Basic forecast request
    payload = {
        "restaurant_id": "restaurant_123",
        "forecast_days": "7"
    }
    
    response = requests.post(f"{BASE_URL}/demandforecast/predict", json=payload)
    print("Demand Forecast Response:")
    print(response.json())

def test_specific_items_forecast():
    # Forecast for specific items
    payload = {
        "restaurant_id": "restaurant_456", 
        "forecast_days": "3",
        "item_ids": ["item_001", "item_002", "item_005"],
        "start_date": str(date.today() + timedelta(days=2))
    }
    
    response = requests.post(f"{BASE_URL}/demandforecast/predict", json=payload)
    print("Specific Items Forecast:")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_health()
    test_menu_items()
    test_demand_forecast()
    test_specific_items_forecast()