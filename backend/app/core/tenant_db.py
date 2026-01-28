"""
Tenant-aware database operations.
Provides automatic tenant filtering at the database layer.

This is the SECOND line of defense for multi-tenancy.
All queries are automatically scoped to the current tenant.
"""
from typing import Any, Optional
from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import get_database
from app.core.tenant import get_required_tenant_context, TenantContext


class TenantAwareCollection:
    """
    Wraps a MongoDB collection to automatically apply tenant filters.
    Prevents cross-tenant data access at the database query level.
    """
    
    def __init__(self, collection_name: str, tenant_field: str = "student_id"):
        self.collection_name = collection_name
        self.tenant_field = tenant_field
    
    async def _get_collection(self):
        db = await get_database()
        return db[self.collection_name]
    
    def _get_tenant_filter(self, ctx: TenantContext) -> dict:
        """Get the tenant filter based on user role"""
        if ctx.role == "student":
            # Students can only access their own data
            return {self.tenant_field: ctx.user_id}
        elif ctx.role == "counsellor":
            # Counsellors can access data where they are the counsellor
            # or where they are assigned
            return {}  # No automatic filter - endpoint handles access
        elif ctx.role == "admin":
            # Admins can access all data
            return {}
        else:
            # Unknown role - deny access
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unknown role"
            )
    
    async def find_one_for_tenant(
        self, 
        query: dict, 
        ctx: Optional[TenantContext] = None
    ) -> Optional[dict]:
        """
        Find a single document, enforcing tenant isolation.
        """
        if ctx is None:
            ctx = get_required_tenant_context()
        
        collection = await self._get_collection()
        tenant_filter = self._get_tenant_filter(ctx)
        
        # Merge tenant filter with query
        full_query = {**query, **tenant_filter}
        
        return await collection.find_one(full_query)
    
    async def find_for_tenant(
        self, 
        query: dict = None, 
        ctx: Optional[TenantContext] = None,
        sort: list = None,
        limit: int = None
    ):
        """
        Find documents, enforcing tenant isolation.
        Returns an async cursor.
        """
        if ctx is None:
            ctx = get_required_tenant_context()
        
        collection = await self._get_collection()
        tenant_filter = self._get_tenant_filter(ctx)
        
        # Merge tenant filter with query
        full_query = {**(query or {}), **tenant_filter}
        
        cursor = collection.find(full_query)
        
        if sort:
            cursor = cursor.sort(sort)
        if limit:
            cursor = cursor.limit(limit)
        
        return cursor
    
    async def insert_for_tenant(
        self, 
        document: dict, 
        ctx: Optional[TenantContext] = None
    ):
        """
        Insert a document, automatically setting tenant field.
        """
        if ctx is None:
            ctx = get_required_tenant_context()
        
        if ctx.role == "student":
            # Automatically set tenant field for students
            document[self.tenant_field] = ctx.user_id
        
        collection = await self._get_collection()
        return await collection.insert_one(document)
    
    async def update_for_tenant(
        self, 
        query: dict, 
        update: dict,
        ctx: Optional[TenantContext] = None
    ):
        """
        Update a document, enforcing tenant isolation.
        """
        if ctx is None:
            ctx = get_required_tenant_context()
        
        collection = await self._get_collection()
        tenant_filter = self._get_tenant_filter(ctx)
        
        # Merge tenant filter with query
        full_query = {**query, **tenant_filter}
        
        return await collection.update_one(full_query, update)
    
    async def delete_for_tenant(
        self, 
        query: dict,
        ctx: Optional[TenantContext] = None
    ):
        """
        Delete a document, enforcing tenant isolation.
        """
        if ctx is None:
            ctx = get_required_tenant_context()
        
        collection = await self._get_collection()
        tenant_filter = self._get_tenant_filter(ctx)
        
        # Merge tenant filter with query
        full_query = {**query, **tenant_filter}
        
        return await collection.delete_one(full_query)
    
    async def count_for_tenant(
        self, 
        query: dict = None,
        ctx: Optional[TenantContext] = None
    ) -> int:
        """
        Count documents, enforcing tenant isolation.
        """
        if ctx is None:
            ctx = get_required_tenant_context()
        
        collection = await self._get_collection()
        tenant_filter = self._get_tenant_filter(ctx)
        
        # Merge tenant filter with query
        full_query = {**(query or {}), **tenant_filter}
        
        return await collection.count_documents(full_query)
    
    async def verify_ownership(
        self, 
        document_id: str, 
        ctx: Optional[TenantContext] = None
    ) -> dict:
        """
        Verify that the current tenant owns the document.
        Raises 404 if not found, 403 if not owned.
        """
        if ctx is None:
            ctx = get_required_tenant_context()
        
        collection = await self._get_collection()
        
        try:
            document = await collection.find_one({"_id": ObjectId(document_id)})
        except:
            raise HTTPException(status_code=404, detail="Not found")
        
        if not document:
            raise HTTPException(status_code=404, detail="Not found")
        
        # Check ownership for students
        if ctx.role == "student":
            if document.get(self.tenant_field) != ctx.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied - you don't own this resource"
                )
        
        return document


# Pre-configured tenant-aware collections
class TenantCollections:
    """Factory for tenant-aware collection access"""
    
    @staticmethod
    def notes():
        return TenantAwareCollection("notes", tenant_field="student_id")
    
    @staticmethod
    def appointments():
        return TenantAwareCollection("appointments", tenant_field="student_id")
    
    @staticmethod
    def messages():
        return TenantAwareCollection("messages", tenant_field="student_id")
