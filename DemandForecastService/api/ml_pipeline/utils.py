from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import get_tables
from .config import Config
import logging
import urllib.parse

logger = logging.getLogger(__name__)

def create_engine_from_url(db_url):
    """Create SQLAlchemy engine with proper configuration for MySQL or MSSQL."""
    connect_args = {}
    # Detect database type from URL
    if db_url.startswith("mysql"):  # MySQL
        connect_args = {
            "charset": "utf8mb4",
            "use_unicode": True,
            "autocommit": False,
        }
        engine = create_engine(
            db_url,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
            connect_args=connect_args
        )
    elif db_url.startswith("mssql"):  # MSSQL
        # For MSSQL, connect_args can be empty or set as needed
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            echo=False,
        )
    else:
        # Default fallback
        engine = create_engine(db_url)
    return engine


def init_database(db_url):
    """Initialize database tables"""
    try:
        engine = create_engine_from_url(db_url)
        orm_mappings = get_tables(engine)
        print(orm_mappings)
        logger.info(f"Database initialized successfully: {db_url}")
        return engine
    except Exception as e:
        logger.error(f"Failed to initialize database {db_url}: {e}")
        raise

def get_session_factory(db_url):
    """Get session factory for database"""
    engine = create_engine_from_url(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal

# Database initialization script
def init_all_databases():
    """Initialize all databases"""
    databases = [
        Config.RAW_DB_URL,
        Config.FEATURE_DB_URL,
        Config.PREDICTIONS_DB_URL
    ]
    
    for db_url in databases:
        try:
            init_database(db_url)
            logger.info(f"Successfully initialized: {db_url}")
        except Exception as e:
            logger.error(f"Failed to initialize {db_url}: {e}")

if __name__ == "__main__":
    init_all_databases()