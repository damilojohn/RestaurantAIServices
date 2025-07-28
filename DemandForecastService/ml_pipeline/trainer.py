import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from prophet import Prophet
import mlflow
import mlflow.prophet
import wandb
import numpy as np
import logging
from .utils import LOG

logger = logging.getLogger(__name__)

class ProphetTrainer:
    def __init__(self, mlflow_uri, wandb_project, wandb_api_key):
        self.mlflow_uri = mlflow_uri
        self.wandb_project = wandb_project
        self.model = None
        
        # Setup MLflow
        mlflow.set_tracking_uri(mlflow_uri)
        mlflow.set_experiment("restaurants_demand_forecasting_test_2")
        
        # Setup Weights & Biases
        wandb.login(key=wandb_api_key)
        wandb.init(project=wandb_project, name="DemandForecasting")
    
    def train(self, df):
        """Train XGBoost model"""
        logger.info("Starting model training")
        
        
        CONFIDENCE_INTERVAL = 0.95
        # XGBoost parameters
        params = {
            "Daily_seasonality":"True",
            "weekly_seasonality": "True",
            "yearly_seasonality":"True",
            "interval_width" : CONFIDENCE_INTERVAL,
            "changepoint_prior_scale": 0.05,
            "seasonality_prior_scale":10.0

        }
        # Log parameters
        wandb.config.update(params)
        
        with mlflow.start_run():
            # Train model
            self.model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True,
                interval_width=CONFIDENCE_INTERVAL,
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10.0
            )
            self.model.fit(df)
            logging.getLogger('prophet').setLevel(logging.WARNING)
            
            # Log metrics
            metrics = {
            }
            
            mlflow.log_params(params)
            mlflow.log_metrics(metrics)
            wandb.log(metrics)
            
            # Log model
            model_info = mlflow.prophet.log_model(
                self.model,
                # "model",
                input_example=df[:5],
                name = "demand_forecast_prophet",
            )
            # model_path = mlflow.prophet.save_model(self.model, "./prophet_model")
            
            LOG.info(f"Model Trained successfully....")
            
            return model_info