import mlflow
import mlflow.prophet
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, max as spark_max, min as spark_min, current_timestamp
from pyspark.sql.types import StructType, StructField, DateType, DoubleType, IntegerType, LongType, StringType, TimestampType
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import PredictionResults, Base
import logging

logger = logging.getLogger(__name__)

class DemandPredictor:
    def __init__(self, mlflow_uri, model_name, db_url):
        self.mlflow_uri = mlflow_uri
        self.model_name = model_name
        self.db_url = db_url
        self.db_name = "forecasting"
        self.spark = SparkSession.builder.getOrCreate()
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.model = None

        Base.metadata.create_all(bind=self.engine)
        mlflow.set_tracking_uri(mlflow_uri)
    def _load_model(self, model_info):
        """Load model from MLflow"""

        try:
            self.model = mlflow.prophet.load_model(model_info.model_uri)
            logger.info("Model loaded successfully from MLflow")
            return self.model
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None
    
    def predict_daily_demand(self):
        """Generate daily demand predictions"""
        
        # self.model =self._load_model(model_info)
        raw_table = f"{self.db_name}.raw_sales_data"
        df = self.spark.table(raw_table)
        available_combinations = (
            df.select("store", "item")
            .distinct()
            .collect()
        )

        print(f"🎯 Discovered {len(available_combinations)} store-item combinations in data")

        # Create forecast results storage
        all_forecasts = []
        MIN_HISTORY_DAYS = 90
        FORECAST_HORIZON_DAYS = 15 
        MODEL_VERSION = "prophet_v1.1.5_serverless_optimized"

        # Process each combination individually for better error handling
        for i, row in enumerate(available_combinations):
            store_id = row['store']
            item_id = row['item']
            
            try:
                # Filter data for this specific store-item combination
                store_item_data = (
                    df.filter((col("store") == store_id) & (col("item") == item_id))
                    .select("date", "sales")
                    .orderBy("date")
                    .toPandas()
                )
                
                # Check if we have enough data
                if len(store_item_data) < MIN_HISTORY_DAYS:
                    print(f"⚠️  Store {store_id}, Item {item_id}: Only {len(store_item_data)} days (need {MIN_HISTORY_DAYS})")
                    continue
                    
                # Prepare data for Prophet
                prophet_df = store_item_data.rename(columns={'date': 'ds', 'sales': 'y'})
                prophet_df['ds'] = pd.to_datetime(prophet_df['ds'])
                prophet_df = prophet_df.sort_values('ds').drop_duplicates(subset=['ds'])


                future = self.model.make_future_dataframe(periods=FORECAST_HORIZON_DAYS)
                forecast = self.model.predict(future)
        
                # Get only future predictions
                last_date = prophet_df['ds'].max()
                future_forecast = forecast[forecast['ds'] > last_date].copy()
        
                    
                # Prepare results
                for _, forecast_row in future_forecast.iterrows():
                    all_forecasts.append({
                        'store': int(store_id),
                        'item': int(item_id),
                        'forecast_date': forecast_row['ds'].date(),
                        'yhat': max(0, float(forecast_row['yhat'])),
                        'yhat_lower': max(0, float(forecast_row['yhat_lower'])),
                        'yhat_upper': max(0, float(forecast_row['yhat_upper'])),
                        'model_version': MODEL_VERSION
                    })
                
                if (i + 1) % 25 == 0:  # Progress update every 25 combinations
                    print(f"📈 Processed {i + 1}/{len(available_combinations)} combinations...")
                    
            except Exception as e:
                print(f"❌ Error with Store {store_id}, Item {item_id}: {str(e)}")
                continue

        print(f"✅ Forecasting complete! Generated predictions for {len(set([(f['store'], f['item']) for f in all_forecasts]))} combinations")

        # Convert to Spark DataFrame with explicit schema to prevent type inference issues
        if all_forecasts:
            # Define explicit schema to match the Delta table exactly
            for row in all_forecasts:
                row["yhat"] = float(row["yhat"])
                row["yhat_lower"] = float(row["yhat_lower"])
                row["yhat_upper"] = float(row["yhat_upper"])
            forecast_schema = StructType([
                StructField("store", IntegerType(), True),
                StructField("item", IntegerType(), True),
                StructField("forecast_date", DateType(), True),
                StructField("yhat", DoubleType(), True),
                StructField("yhat_lower", DoubleType(), True),
                StructField("yhat_upper", DoubleType(), True),
                StructField("model_version", StringType(), True)
            ])
                
            forecast_df = self.spark.createDataFrame(all_forecasts, schema=forecast_schema)
            forecast_count = forecast_df.count()
            results = pd.DataFrame(all_forecasts)
            results['yhat'] = results['yhat'].clip(lower=0)
            results['yhat_lower'] = results['yhat_lower'].clip(lower=0)
            results['yhat_upper'] = results['yhat_upper'].clip(lower=0)
            print(f"🔮 Generated {forecast_count:,} individual demand predictions")
            return results
        else:
            forecast_df = None
            forecast_count = 0
            print("❌ No forecasts generated")
        

    
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
        """Store predictions in database using SQLAlchemy ORM"""

        session = self.Session()
        try:
            # Prepare ORM objects with type safety
            orm_objs = []
            for _, pred in predictions.iterrows():
                # Ensure correct types
                pred["yhat"] = float(pred["yhat"])
                pred["yhat_lower"] = float(pred["yhat_lower"])
                pred["yhat_upper"] = float(pred["yhat_upper"])
                # Convert forecast_date to date if it's a string
                if isinstance(pred["forecast_date"], str):
                    pred["forecast_date"] = datetime.strptime(pred["forecast_date"], "%Y-%m-%d").date()
                elif isinstance(pred["forecast_date"], datetime):
                    pred["forecast_date"] = pred["forecast_date"].date()
                # Create ORM object
                orm_objs.append(PredictionResults(**pred))
            session.bulk_save_objects(orm_objs)
            session.commit()
            logger.info(f"Stored {len(orm_objs)} predictions")
        except Exception as e:
            logger.info(f"prediction storing failed.... with error {e}")
            raise e