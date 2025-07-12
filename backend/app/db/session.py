from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import logging

from app.core.settings import settings

logger = logging.getLogger(__name__)

# Create async engine with connection pooling
# Handle Supabase SSL requirements
database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Remove sslmode parameter if present (asyncpg doesn't support it in URL)
if "sslmode=require" in database_url:
    database_url = database_url.replace("?sslmode=require", "").replace("&sslmode=require", "")

# Configure SSL and connection args for Supabase
connect_args = {}
if "supabase.com" in settings.DATABASE_URL:
    connect_args = {
        "ssl": "require",
        "server_settings": {
            "application_name": "recipe_scraper_api",
        }
    }

engine = create_async_engine(
    database_url,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections every hour
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    connect_args=connect_args
)

# Create async session factory
SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create declarative base
Base = declarative_base()


# Database event listeners for performance monitoring
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set database pragmas for better performance."""
    if "sqlite" in settings.DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=1000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


@event.listens_for(engine.sync_engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log database connection checkout."""
    logger.debug("Database connection checked out")


@event.listens_for(engine.sync_engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log database connection checkin."""
    logger.debug("Database connection checked in")


async def get_db() -> AsyncSession:
    """
    Dependency function that yields db sessions.
    This is the recommended way to get database sessions.
    """
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")


async def drop_tables():
    """Drop all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped successfully")


class DatabaseManager:
    """Database manager for handling connections and transactions."""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with SessionLocal() as session:
                result = await session.execute(text("SELECT 1"))
                result.fetchone()  # Don't await this - it's not async
                logger.info("Database health check passed")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            logger.error(f"Database URL (masked): {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'Invalid URL format'}")
            return False
    
    async def get_connection_info(self) -> dict:
        """Get database connection information."""
        pool = self.engine.pool
        try:
            return {
                "pool_size": pool.size(),
                "checked_in_connections": pool.checkedin(),
                "checked_out_connections": pool.checkedout(),
                "overflow_connections": pool.overflow(),
                # AsyncAdaptedQueuePool doesn't have invalid() method
                "pool_status": "healthy"
            }
        except Exception as e:
            logger.error(f"Error getting connection info: {e}")
            return {
                "pool_status": "error",
                "error": str(e)
            }
    
    async def close_all_connections(self):
        """Close all database connections."""
        await self.engine.dispose()
        logger.info("All database connections closed")


# Global database manager instance
db_manager = DatabaseManager()


# Context manager for database transactions
class DatabaseTransaction:
    """Context manager for database transactions with automatic rollback on error."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def __aenter__(self):
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.session.rollback()
            logger.error(f"Transaction rolled back due to error: {exc_val}")
        else:
            await self.session.commit()
            logger.debug("Transaction committed successfully")


async def get_db_transaction() -> DatabaseTransaction:
    """Get database session wrapped in transaction context manager."""
    async with SessionLocal() as session:
        yield DatabaseTransaction(session)


# Database utilities
async def execute_raw_sql(query: str, params: dict = None) -> list:
    """Execute raw SQL query and return results."""
    async with SessionLocal() as session:
        try:
            result = await session.execute(text(query), params or {})
            return result.fetchall()
        except Exception as e:
            logger.error(f"Raw SQL execution failed: {e}")
            raise


async def get_database_stats() -> dict:
    """Get database statistics."""
    try:
        async with SessionLocal() as session:
            # Get table sizes (PostgreSQL specific)
            if "postgresql" in settings.DATABASE_URL:
                query = text("""
                SELECT
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats
                WHERE schemaname = 'public'
                ORDER BY tablename, attname;
                """)
                result = await session.execute(query)
                stats = result.fetchall()
                
                return {
                    "table_stats": [dict(row) for row in stats],
                    "connection_info": await db_manager.get_connection_info()
                }
            else:
                return {
                    "connection_info": await db_manager.get_connection_info()
                }
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {"error": str(e)}