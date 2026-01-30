import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Set when DB connection + indexes are ready. App serves /health immediately; API waits on this.
db_ready: Optional[asyncio.Event] = None


def _ensure_db_ready():
    global db_ready
    if db_ready is None:
        db_ready = asyncio.Event()
    return db_ready


class Database:
    client: Optional[AsyncIOMotorClient] = None


db = Database()


def get_default_database():
    """Return the shared database (no tenant). Use for token_sessions, etc."""
    if db.client is None:
        raise RuntimeError("Database not connected")
    return db.client[settings.DATABASE_NAME]


async def get_database(institution_id: Optional[str] = None):
    """
    Get the database instance.
    For database-per-tenant strategy, returns tenant-specific database.
    For other strategies, returns the shared database.

    If institution_id is not provided, tries to get it from tenant context.
    Waits for DB connection to be ready (startup runs in background).
    """
    ev = _ensure_db_ready()
    try:
        await asyncio.wait_for(ev.wait(), timeout=120.0)
    except asyncio.TimeoutError:
        raise RuntimeError("Database connection not ready after 120s. Check MongoDB and backend logs.")

    from app.core.tenant_strategy import TenantStrategyFactory
    from app.core.tenant import get_tenant_context

    # Try to get institution_id from tenant context if not provided
    if institution_id is None:
        tenant_ctx = get_tenant_context()
        if tenant_ctx:
            institution_id = tenant_ctx.institution_id
    
    strategy = TenantStrategyFactory.get_strategy()
    
    # For database-per-tenant strategy, get tenant-specific database
    if hasattr(strategy, 'get_database_name') and institution_id:
        db_name = strategy.get_database_name(institution_id, settings.DATABASE_NAME)
        return db.client[db_name]
    
    # For other strategies, use shared database
    return db.client[settings.DATABASE_NAME]


async def connect_to_mongo():
    _ensure_db_ready()  # create event so get_database waiters can block
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = db.client[settings.DATABASE_NAME]
    max_attempts = 10
    delay = 3

    for attempt in range(1, max_attempts + 1):
        try:
            await database.command("ping")
            break
        except Exception as e:
            if attempt == max_attempts:
                logger.error("MongoDB connection failed after %d attempts: %s", max_attempts, e)
                raise
            logger.warning("MongoDB not ready (attempt %d/%d): %s. Retrying in %ds ...", attempt, max_attempts, e, delay)
            await asyncio.sleep(delay)

    print(f"Connected to MongoDB at {settings.MONGODB_URL}")
    print(f"Deployment mode: {settings.DEPLOYMENT_MODE}")
    print(f"Tenant strategy: {settings.TENANT_STRATEGY or 'auto-detect'}")

    # Create indexes for better query performance
    # Institution indexes
    await database.institutions.create_index("name", unique=True)
    await database.institutions.create_index("domain", unique=True, sparse=True)
    
    # User indexes
    await database.users.create_index("email", unique=True)
    await database.users.create_index("institution_id")
    await database.users.create_index([("institution_id", 1), ("role", 1)])
    
    # Appointments indexes (for multi-tenancy queries)
    await database.appointments.create_index("institution_id")
    await database.appointments.create_index("student_id")
    await database.appointments.create_index([("institution_id", 1), ("student_id", 1), ("date", -1)])
    
    # Messages indexes
    await database.messages.create_index("institution_id")
    await database.messages.create_index("student_id")
    await database.messages.create_index([("institution_id", 1), ("student_id", 1), ("created_at", -1)])
    
    # Notes indexes
    await database.notes.create_index("institution_id")
    await database.notes.create_index("student_id")
    await database.notes.create_index([("institution_id", 1), ("student_id", 1)])
    
    # Password reset tokens indexes
    await database.password_reset_tokens.create_index("token", unique=True)
    await database.password_reset_tokens.create_index("user_id")
    await database.password_reset_tokens.create_index("expires_at", expireAfterSeconds=3600)  # Auto-delete after 1 hour

    # Token sessions (JWT revocation): jti -> user_id, exp
    await database.token_sessions.create_index("jti", unique=True)
    await database.token_sessions.create_index("user_id")
    await database.token_sessions.create_index("exp", expireAfterSeconds=0)  # TTL: delete when exp passed

    print("Database indexes created")
    _ensure_db_ready().set()


async def close_mongo_connection():
    if db.client:
        db.client.close()
        print("Closed MongoDB connection")
