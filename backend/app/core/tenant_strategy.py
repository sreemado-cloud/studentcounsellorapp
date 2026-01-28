"""
Tenant isolation strategy pattern.
Supports switching between different isolation levels based on deployment mode.

Strategies:
- RowLevelStrategy: All data in shared collections, filtered by institution_id
- CollectionPerTenantStrategy: Separate collections per institution (e.g., inst_abc_notes)
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, AsyncIterator
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.core.config import settings


class TenantStrategy(ABC):
    """Abstract base class for tenant isolation strategies"""
    
    @abstractmethod
    def get_collection_name(self, base_name: str, institution_id: str) -> str:
        """Get the actual collection name based on strategy"""
        pass
    
    @abstractmethod
    def get_tenant_filter(self, institution_id: str, additional_filter: dict = None) -> dict:
        """Get the query filter to apply for tenant isolation"""
        pass
    
    @abstractmethod
    def prepare_document(self, document: dict, institution_id: str) -> dict:
        """Prepare a document for insertion with tenant information"""
        pass


class RowLevelStrategy(TenantStrategy):
    """
    Row-level security strategy.
    All institutions share the same collections.
    Isolation is achieved through query filters on institution_id.
    
    Best for: SaaS deployments, cost-effective, simple management
    """
    
    def get_collection_name(self, base_name: str, institution_id: str) -> str:
        # All tenants share the same collection
        return base_name
    
    def get_tenant_filter(self, institution_id: str, additional_filter: dict = None) -> dict:
        # Always filter by institution_id
        base_filter = {"institution_id": institution_id}
        if additional_filter:
            return {**base_filter, **additional_filter}
        return base_filter
    
    def prepare_document(self, document: dict, institution_id: str) -> dict:
        # Add institution_id to every document
        return {**document, "institution_id": institution_id}


class CollectionPerTenantStrategy(TenantStrategy):
    """
    Collection-per-tenant strategy.
    Each institution has its own set of collections.
    Collection names are prefixed with institution_id.
    
    Best for: On-premises deployments, stronger isolation, regulatory compliance
    """
    
    def get_collection_name(self, base_name: str, institution_id: str) -> str:
        # Each tenant gets their own collection: inst_abc123_notes
        safe_id = institution_id.replace("-", "_")
        return f"inst_{safe_id}_{base_name}"
    
    def get_tenant_filter(self, institution_id: str, additional_filter: dict = None) -> dict:
        # No institution_id filter needed - collection itself provides isolation
        # But we still store it for consistency and potential migration
        if additional_filter:
            return additional_filter
        return {}
    
    def prepare_document(self, document: dict, institution_id: str) -> dict:
        # Still add institution_id for consistency and audit purposes
        return {**document, "institution_id": institution_id}


class DatabasePerTenantStrategy(TenantStrategy):
    """
    Database-per-tenant strategy.
    Each institution has its own database.
    Provides maximum isolation for SaaS deployments.
    
    Best for: SaaS high-isolation mode, maximum security, regulatory compliance
    """
    
    def get_collection_name(self, base_name: str, institution_id: str) -> str:
        # Collection name is unchanged - isolation is at database level
        return base_name
    
    def get_tenant_filter(self, institution_id: str, additional_filter: dict = None) -> dict:
        # No institution_id filter needed - database itself provides isolation
        if additional_filter:
            return additional_filter
        return {}
    
    def prepare_document(self, document: dict, institution_id: str) -> dict:
        # Still add institution_id for consistency and audit purposes
        return {**document, "institution_id": institution_id}
    
    def get_database_name(self, institution_id: str, base_database_name: str) -> str:
        """Get the database name for this institution"""
        # Use a safe version of institution_id for database name
        # MongoDB database names must be valid identifiers
        safe_id = institution_id.replace("-", "_").replace(".", "_")
        return f"{base_database_name}_{safe_id}"


class TenantStrategyFactory:
    """Factory to create the appropriate tenant strategy based on configuration"""
    
    _strategies = {
        "row_level": RowLevelStrategy,
        "collection_per_tenant": CollectionPerTenantStrategy,
        "database_per_tenant": DatabasePerTenantStrategy,
    }
    
    _instance: Optional[TenantStrategy] = None
    
    @classmethod
    def get_strategy(cls) -> TenantStrategy:
        """Get the configured tenant strategy (singleton)"""
        if cls._instance is None:
            strategy_name = cls._detect_strategy()
            strategy_class = cls._strategies.get(strategy_name)
            if not strategy_class:
                raise ValueError(f"Unknown tenant strategy: {strategy_name}")
            cls._instance = strategy_class()
        return cls._instance
    
    @classmethod
    def _detect_strategy(cls) -> str:
        """
        Auto-detect the appropriate strategy based on deployment mode.
        Can be overridden by explicit TENANT_STRATEGY env var.
        """
        # Check for explicit strategy override
        explicit_strategy = getattr(settings, 'TENANT_STRATEGY', None)
        if explicit_strategy:
            return explicit_strategy
        
        # Auto-detect based on deployment mode
        deployment_mode = getattr(settings, 'DEPLOYMENT_MODE', 'saas')
        
        if deployment_mode == 'onprem':
            return 'collection_per_tenant'
        else:  # saas or default
            # Check SaaS isolation level
            isolation_level = getattr(settings, 'SAAS_ISOLATION_LEVEL', 'low')
            if isolation_level == 'high':
                return 'database_per_tenant'
            else:
                return 'row_level'
    
    @classmethod
    def reset(cls):
        """Reset the singleton (useful for testing)"""
        cls._instance = None


class TenantAwareRepository:
    """
    Repository that uses the configured tenant strategy for all operations.
    Provides a consistent interface regardless of isolation strategy.
    """
    
    def __init__(self, database: AsyncIOMotorDatabase, base_collection: str):
        self.database = database
        self.base_collection = base_collection
        self.strategy = TenantStrategyFactory.get_strategy()
    
    def _get_database(self, institution_id: str):
        """Get the appropriate database for this institution"""
        if isinstance(self.strategy, DatabasePerTenantStrategy):
            # For database-per-tenant, get the tenant-specific database
            db_name = self.strategy.get_database_name(
                institution_id,
                self.database.name
            )
            return self.database.client[db_name]
        else:
            # For other strategies, use the same database
            return self.database
    
    def _get_collection(self, institution_id: str):
        """Get the appropriate collection for this institution"""
        db = self._get_database(institution_id)
        collection_name = self.strategy.get_collection_name(
            self.base_collection, 
            institution_id
        )
        return db[collection_name]
    
    async def find_one(
        self, 
        institution_id: str, 
        query: dict = None
    ) -> Optional[dict]:
        """Find a single document within the tenant's scope"""
        collection = self._get_collection(institution_id)
        tenant_filter = self.strategy.get_tenant_filter(institution_id, query)
        return await collection.find_one(tenant_filter)
    
    async def find(
        self, 
        institution_id: str, 
        query: dict = None,
        sort: list = None,
        limit: int = None,
        skip: int = None
    ) -> AsyncIterator[dict]:
        """Find documents within the tenant's scope"""
        collection = self._get_collection(institution_id)
        tenant_filter = self.strategy.get_tenant_filter(institution_id, query)
        
        cursor = collection.find(tenant_filter)
        
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        
        return cursor
    
    async def insert_one(
        self, 
        institution_id: str, 
        document: dict
    ):
        """Insert a document with tenant information"""
        collection = self._get_collection(institution_id)
        prepared_doc = self.strategy.prepare_document(document, institution_id)
        return await collection.insert_one(prepared_doc)
    
    async def update_one(
        self, 
        institution_id: str, 
        query: dict, 
        update: dict
    ):
        """Update a document within the tenant's scope"""
        collection = self._get_collection(institution_id)
        tenant_filter = self.strategy.get_tenant_filter(institution_id, query)
        return await collection.update_one(tenant_filter, update)
    
    async def delete_one(
        self, 
        institution_id: str, 
        query: dict
    ):
        """Delete a document within the tenant's scope"""
        collection = self._get_collection(institution_id)
        tenant_filter = self.strategy.get_tenant_filter(institution_id, query)
        return await collection.delete_one(tenant_filter)
    
    async def count(
        self, 
        institution_id: str, 
        query: dict = None
    ) -> int:
        """Count documents within the tenant's scope"""
        collection = self._get_collection(institution_id)
        tenant_filter = self.strategy.get_tenant_filter(institution_id, query or {})
        return await collection.count_documents(tenant_filter)
    
    async def aggregate(
        self, 
        institution_id: str, 
        pipeline: list
    ):
        """Run an aggregation pipeline within the tenant's scope"""
        collection = self._get_collection(institution_id)
        
        # Prepend tenant filter to pipeline
        tenant_filter = self.strategy.get_tenant_filter(institution_id)
        if tenant_filter:
            pipeline = [{"$match": tenant_filter}] + pipeline
        
        return collection.aggregate(pipeline)
