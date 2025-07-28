import schedule
import time
import logging
from datetime import datetime, timedelta
from .extractor import DataExtractor
from .preprocessor import FeatureEngineer
from .feast_store import FeastFeatureStore
from .trainer import ProphetTrainer
from .predictor import DemandPredictor
from .notification_service import notify_new_predictions
from .config import Config
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLPipelineOrchestrator:
    def __init__(self):
        self.extractor = DataExtractor(num_stores=20, num_items=20)
        logger.info("Instantiated Data Extraction")
        self.feature_engineer = FeatureEngineer()
        logger.info("Instantiated Feature preprocessor...")
        self.feature_store = FeastFeatureStore(Config.FEAST_REPO_PATH)
        logger.info("Instantiated Feature Store....")
        self.trainer = ProphetTrainer(Config.MLFLOW_TRACKING_URI, Config.WANDB_PROJECT, Config.WANDB_API_KEY)
        logger.info("Instantiated Trainer...")
        self.predictor = DemandPredictor(
            Config.MLFLOW_TRACKING_URI, 
            Config.MODEL_NAME,
            Config.PREDICTIONS_DB_URL,
        )
        logger.info("Instantiated predictor.....")
    
    def run_training_pipeline(self):
        """Run complete training pipeline"""
        logger.info("Starting training pipeline")
        
        try:
            # 1. Extract data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            df = self.extractor.extract_orders(start_date, end_date)
            
            # 2. Feature engineering
            self.feature_engineer.create_features(df)

            self.feature_engineer.print_data_quality_report()
            
            # 3. Store features
            # self.feature_store._setup_feature_store()
            # self.feature_store.store_features(features)
            
            # 4. Prepare training data
            train_features = self.feature_engineer.prepare_training_data()
            
            # 5. Train model
            model_info = self.trainer.train(train_features)
            return model_info
            
        except Exception as e:
            logger.error(f"Training pipeline failed: {e}")
            raise
    
    async def run_prediction_pipeline(self, latest_model_info):
        """Run daily prediction pipeline"""
        logger.info("Starting prediction pipeline")
        
        try:
            # Get all restaurants and items (simplified)
            print(latest_model_info)
            model = self.predictor._load_model(latest_model_info)
            logger.info(f"model loaded....")
            predictions = self.predictor.predict_daily_demand()

            self.predictor.store_predictions(predictions)
            
            # Store predictions
            
            
            # Notify dashboard
            # await notify_new_predictions(all_predictions)
            
            logger.info(f"Prediction pipeline completed. Generated {len(predictions)} predictions")
            
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