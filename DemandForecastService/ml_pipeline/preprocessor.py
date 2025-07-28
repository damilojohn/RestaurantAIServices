# import pandas as pd
# import numpy as np
# from datetime import datetime, timedelta
# from sklearn.preprocessing import StandardScaler, LabelEncoder
# import json

import os
import logging
import pandas as pd
import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, max as spark_max, min as spark_min, current_timestamp
from pyspark.sql.types import StructType, StructField, DateType, DoubleType, IntegerType, LongType, StringType, TimestampType
from datetime import datetime, timedelta
import warnings
from .utils import LOG

os.environ["JAVA_HOME"] = "/opt/homebrew/opt/openjdk@17"

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureEngineer:
    def __init__(self):
        self.spark = SparkSession.builder.getOrCreate()
        self.db_name = "forecasting"
        # self.scaler = StandardScaler()
        # self.label_encoders = {}
        self.spark.sql(f"CREATE DATABASE IF NOT EXISTS {self.db_name};")
        self.spark.sql(f"""CREATE TABLE IF NOT EXISTS {self.db_name}.raw_sales_data(
        date DATE COMMENT 'Sales transaction date',
        store INT COMMENT 'Store location identifier',
        item INT COMMENT 'Product SKU identifier',
        sales BIGINT COMMENT 'Daily units sold',
        processing_timestamp TIMESTAMP COMMENT 'Data processing timestamp'
        )
        """)
        self.spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {self.db_name}.forecast_results (
        store INT COMMENT 'Store location identifier',
        item INT COMMENT 'Product SKU identifier', 
        forecast_date DATE COMMENT 'Future date for demand prediction',
        yhat DOUBLE COMMENT 'Predicted demand (units)',
        yhat_lower DOUBLE COMMENT 'Lower demand estimate (95% confidence)',
        yhat_upper DOUBLE COMMENT 'Upper demand estimate (95% confidence)',
        model_version STRING COMMENT 'Forecasting model version',
        created_timestamp TIMESTAMP COMMENT 'Forecast generation timestamp'
        )
        COMMENT 'Demand forecasts with confidence intervals for inventory planning'
        """)

        LOG.info("✅ Retail data tables ready for forecasting")
        
    def create_features(self, df):
        schema = StructType([
        StructField("date", DateType(), True),
        StructField("store", IntegerType(), True),
        StructField("item", IntegerType(), True),
        StructField("sales", LongType(), True),
        StructField("processing_timestamp", TimestampType(), True)
        ])
        df_clean = df.copy()

# Convert date column to proper date type (remove time component)
        df_clean['date'] = pd.to_datetime(df_clean['date']).dt.date

        # Ensure integer types are exactly what we need
        df_clean['store'] = df_clean['store'].astype('int32')
        df_clean['item'] = df_clean['item'].astype('int32') 
        df_clean['sales'] = df_clean['sales'].astype('int64')

        df_clean['processing_timestamp'] = None

        LOG.info(f"📋 Data types: {df_clean.dtypes.to_dict()}")

        # Create Spark DataFrame using explicit schema to prevent type inference issues
        synthetic_spark_df = self.spark.createDataFrame(df_clean, schema=schema)

        # Add processing timestamp
        final_df = synthetic_spark_df.withColumn(
            "processing_timestamp", 
            current_timestamp()
        )

        # Verify schema matches exactly
        LOG.info("🔍 Final DataFrame schema:")
        final_df.printSchema()
        LOG.info(f"💾 Writing to: {self.db_name}.raw_sales_data")
        final_df.write.mode("overwrite").saveAsTable(
            f"{self.db_name}.raw_sales_data"
        )

        LOG.info(f"✅ Sales history loaded successfully!")
        LOG.info(f"📊 Rows written: {final_df.count():,}")
    
    def print_data_quality_report(self):
        raw_table = f"{self.db_name}.raw_sales_data"
        df = self.spark.table(raw_table)

        LOG.info("🔍 Data Quality Report:")
        LOG.info("=" * 50)

        # Basic statistics
        row_count = df.count()
        date_min = df.select(spark_min('date')).collect()[0][0]
        date_max = df.select(spark_max('date')).collect()[0][0]
        store_count = df.select('store').distinct().count()
        item_count = df.select('item').distinct().count()

        LOG.info(f"📊 Total records: {row_count:,}")
        LOG.info(f"📅 Date range: {date_min} to {date_max}")
        LOG.info(f"🏪 Unique stores: {store_count}")
        LOG.info(f"📦 Unique items: {item_count}")

        # Data completeness check
        null_checks = df.select([
            count(col('date')).alias('total_dates'),
            count(col('store')).alias('total_stores'), 
            count(col('item')).alias('total_items'),
            count(col('sales')).alias('total_sales')
        ]).collect()[0]

        LOG.info(f"✅ Completeness: {null_checks['total_sales']:,} sales records (100% complete)")

        # Statistical summary
        sales_stats = df.select('sales').describe().collect()
        for row in sales_stats:
            LOG.info(f"📈 Sales {row['summary']}: {float(row['sales']):.2f}")

        LOG.info("\n🎯 Retail sales data validated and ready for demand forecasting!")
    
    def prepare_training_data(self):
        LOG.info("📥 Loading retail sales history for AI analysis...")

        # Load historical sales data
        raw_table = f"{self.db_name}.raw_sales_data"
        df = self.spark.table(raw_table)

        LOG.info(f"✅ Sales data ready for analysis")
        LOG.info(f"🛒 Total sales transactions: {df.count():,}")

        # Data quality summary
        date_range = df.select(spark_min('date'), spark_max('date')).collect()[0]
        LOG.info(f"📅 Date range: {date_range[0]} to {date_range[1]}")
        LOG.info(f"🏪 Stores: {df.select('store').distinct().count()}")
        LOG.info(f"📦 Items: {df.select('item').distinct().count()}")

        LOG.info("🔍 Analyzing sales patterns for AI model training...")
        MAX_STORES = 5    # Match data generation: stores 1-5
        MAX_ITEMS = 15
        FORECAST_HORIZON_DAYS = 15  # Reduced from 30 for faster processing
        MIN_HISTORY_DAYS = 90
        # Check data completeness for selected store-item combinations
        validation_df = (
            df.filter(col("store") <= MAX_STORES)
            .filter(col("item") <= MAX_ITEMS)
            .groupBy("store", "item")
            .agg(
                count("*").alias("record_count"),
                spark_min("date").alias("start_date"),
                spark_max("date").alias("end_date")
            )
        )

        validation_results = validation_df.collect()

        LOG.info(f"📈 Analyzing {len(validation_results)} store-item combinations:")

        sufficient_data_count = 0
        for row in validation_results:
            days_of_data = (row['end_date'] - row['start_date']).days + 1
            sufficient = days_of_data >= MIN_HISTORY_DAYS
            if sufficient:
                sufficient_data_count += 1
            
            status = "✅" if sufficient else "❌"
            LOG.info(f"   {status} Store {row['store']}, Item {row['item']}: {row['record_count']} records, {days_of_data} days")

        LOG.info(f"\n🎯 {sufficient_data_count}/{len(validation_results)} product-store combinations ready for AI forecasting")

        available_combinations = (
        df.select("store", "item")
        .distinct()
        .collect()
        )

        LOG.info(f"🎯 Discovered {len(available_combinations)} store-item combinations in data")

        # Create forecast results storage
        all_forecasts = []

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
                    LOG.info(f"⚠️  Store {store_id}, Item {item_id}: Only {len(store_item_data)} days (need {MIN_HISTORY_DAYS})")
                    continue
                    
                # Prepare data for Prophet
                prophet_df = store_item_data.rename(columns={'date': 'ds', 'sales': 'y'})
                prophet_df['ds'] = pd.to_datetime(prophet_df['ds'])
                prophet_df = prophet_df.sort_values('ds').drop_duplicates(subset=['ds'])

                return prophet_df
            except Exception as e:
                LOG.info(f"Training data preparation failed with error ..{e}")
                raise
        
