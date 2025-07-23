import mlflow
import mlflow.xgboost
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import PredictionResults
import logging

logger = logging.getLogger(__name__)

class DemandPredictor:
    def __init__(self, mlflow_uri, model_name, db_url):
        self.mlflow_uri = mlflow_uri
        self.model_name = model_name
        self.db_url = db_url
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.model = None
        
        mlflow.set_tracking_uri(mlflow_uri)
    
    def _load_model(self, model_info):
        """Load model from MLflow"""
        try:
            self.model = mlflow.xgboost.load_model(model_info.model_uri)
            logger.info("Model loaded successfully from MLflow")
            return self.model
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None
    
    def predict_daily_demand(self, restaurant_id, item_ids, prediction_date):
        """Generate daily demand predictions"""
        if not self.model:
            logger.error("Model not loaded")
            return None
        
        predictions = []
        
        for item_id in item_ids:
            # Create feature vector (simplified for demo)
            features = self._create_prediction_features(restaurant_id, item_id, prediction_date)
            
            # Make prediction
            pred = self.model.predict([features])[0]
            confidence = min(0.95, max(0.60, 0.85 + np.random.normal(0, 0.05)))
            
            predictions.append({
                'restaurant_id': restaurant_id,
                'item_id': item_id,
                'prediction_date': prediction_date,
                'predicted_demand': float(pred),
                'confidence_score': float(confidence),
                'model_version': 'v1.0'
            })
        
        return predictions
    
    def _create_prediction_features(self, restaurant_id, item_id, prediction_date):
        """Create feature vector for prediction"""
        # Simplified feature creation for demo
        # In practice, this would fetch from feature store
        features = [
            hash(restaurant_id) % 100,  # restaurant encoding
            hash(item_id) % 50,         # item encoding
            prediction_date.weekday(),  # day of week
            prediction_date.month,      # month
            1 if prediction_date.weekday() >= 5 else 0,  # is_weekend
            25.0,  # mock lag features
            30.0,
            28.0,
            5.0,
            40.0,
            15000.0,
            100
        ]
        return features
    
    def store_predictions(self, predictions):
        """Store predictions in database"""
        session = self.Session()
        try:
            for pred in predictions:
                prediction_obj = PredictionResults(**pred)
                session.add(prediction_obj)
            
            session.commit()
            logger.info(f"Stored {len(predictions)} predictions")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to store predictions: {e}")
        finally:
            session.close()