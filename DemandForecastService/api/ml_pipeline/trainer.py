import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import mlflow
import mlflow.xgboost
import wandb
import numpy as np
import logging

logger = logging.getLogger(__name__)

class XGBoostTrainer:
    def __init__(self, mlflow_uri, wandb_project):
        self.mlflow_uri = mlflow_uri
        self.wandb_project = wandb_project
        self.model = None
        
        # Setup MLflow
        mlflow.set_tracking_uri(mlflow_uri)
        mlflow.set_experiment("restaurants_demand_forecasting")
        
        # Setup Weights & Biases
        wandb.init(project=wandb_project, name="xgboost_training")
    
    def train(self, X, y, feature_cols):
        """Train XGBoost model"""
        logger.info("Starting model training")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # XGBoost parameters
        params = {
            'objective': 'reg:squarederror',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42
        }
        
        # Log parameters
        wandb.config.update(params)
        
        with mlflow.start_run():
            # Train model
            self.model = xgb.XGBRegressor(**params)
            self.model.fit(X_train, y_train)
            
            # Predictions
            y_pred_train = self.model.predict(X_train)
            y_pred_test = self.model.predict(X_test)
            
            # Calculate metrics
            train_mae = mean_absolute_error(y_train, y_pred_train)
            test_mae = mean_absolute_error(y_test, y_pred_test)
            train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
            test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
            
            # Log metrics
            metrics = {
                'train_mae': train_mae,
                'test_mae': test_mae,
                'train_rmse': train_rmse,
                'test_rmse': test_rmse
            }
            
            mlflow.log_params(params)
            mlflow.log_metrics(metrics)
            wandb.log(metrics)
            
            # Log model
            mlflow.xgboost.log_model(
                self.model,
                "model",
                input_example=X_train[:5],
                registered_model_name="demand_forecasting_xgb"
            )
            
            logger.info(f"Model trained - Test MAE: {test_mae:.2f}, Test RMSE: {test_rmse:.2f}")
            
            return self.model, metrics