import schedule
import time
import logging
from datetime import datetime, timedelta
from .extractor import DataExtractor
from .preprocessor import FeatureEngineer
from .feast_store import FeastFeatureStore
from .trainer import XGBoostTrainer
from .predictor import DemandPredictor
from .notification_service import notify_new_predictions
from .config import Config
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLPipelineOrchestrator:
    def __init__(self):
        self.extractor = DataExtractor()
        self.feature_engineer = FeatureEngineer()
        self.feature_store = FeastFeatureStore(Config.FEAST_REPO_PATH)
        self.trainer = XGBoostTrainer(Config.MLFLOW_TRACKING_URI, Config.WANDB_PROJECT, Config.WANDB_API_KEY)
        self.predictor = DemandPredictor(
            Config.MLFLOW_TRACKING_URI, 
            Config.MODEL_NAME,
            Config.PREDICTIONS_DB_URL,
        )
    
    def run_training_pipeline(self):
        """Run complete training pipeline"""
        logger.info("Starting training pipeline")
        
        try:
            # 1. Extract data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            df = self.extractor.extract_orders(start_date, end_date)
            
            # 2. Feature engineering
            features = self.feature_engineer.create_features(df)
            
            # 3. Store features
            # self.feature_store._setup_feature_store()
            # self.feature_store.store_features(features)
            
            # 4. Prepare training data
            X, y, feature_cols = self.feature_engineer.prepare_training_data(features)
            
            # 5. Train model
            model_info = self.trainer.train(X, y, feature_cols)
            return model_info
            
        except Exception as e:
            logger.error(f"Training pipeline failed: {e}")
            raise
    
    async def run_prediction_pipeline(self, latest_model_info):
        """Run daily prediction pipeline"""
        logger.info("Starting prediction pipeline")
        self.predictor._load_model(latest_model_info)
        
        try:
            # Get all restaurants and items (simplified)
            restaurants = ["restaurant_1", "restaurant_2", "restaurant_3"]
            items = ["item_001", "item_002", "item_003", "item_004", "item_005"]
            
            all_predictions = []
            
            for restaurant_id in restaurants:
                predictions = self.predictor.predict_daily_demand(
                    restaurant_id, 
                    items, 
                    datetime.now().date() + timedelta(days=1)
                )
                
                if predictions:
                    all_predictions.extend(predictions)
            
            # Store predictions
            self.predictor.store_predictions(all_predictions)
            
            # Notify dashboard
            await notify_new_predictions(all_predictions)
            
            logger.info(f"Prediction pipeline completed. Generated {len(all_predictions)} predictions")
            
        except Exception as e:
            logger.error(f"Prediction pipeline failed: {e}")
    
    def schedule_jobs(self):
        """Schedule pipeline jobs"""
        # Train model weekly
        schedule.every().tuesday.at("02:00").do(self.run_training_pipeline)
        
        # Generate predictions daily
        schedule.every().hour.at("01:00").do(self.run_prediction_pipeline)
        
        logger.info("Pipeline jobs scheduled")
    
    def run(self):
        """Run the orchestrator"""
        self.schedule_jobs()
        
        while True:
            schedule.run_pending()
            time.sleep(60)