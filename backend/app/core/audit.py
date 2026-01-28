"""
Audit logging system for multi-tenant data access.
Tracks all data access for compliance and security monitoring.
"""
from datetime import datetime
from typing import Optional, Any
from enum import Enum
from functools import wraps
from fastapi import Request
import asyncio

from app.core.database import get_database


class AuditAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"


class AuditLog:
    """Audit log entry structure"""
    
    def __init__(
        self,
        institution_id: str,
        user_id: str,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        self.institution_id = institution_id
        self.user_id = user_id
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.metadata = metadata or {}
        self.success = success
        self.error_message = error_message
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            "institution_id": self.institution_id,
            "user_id": self.user_id,
            "action": self.action.value,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "metadata": self.metadata,
            "success": self.success,
            "error_message": self.error_message,
            "timestamp": self.timestamp
        }


class AuditLogger:
    """
    Async audit logger that writes to MongoDB.
    Designed to be non-blocking - failures don't affect main operations.
    """
    
    COLLECTION_NAME = "audit_logs"
    
    @classmethod
    async def log(cls, audit_entry: AuditLog):
        """
        Log an audit entry asynchronously.
        Failures are silently ignored to not affect main operations.
        """
        try:
            database = await get_database()
            await database[cls.COLLECTION_NAME].insert_one(audit_entry.to_dict())
        except Exception as e:
            # Log to console but don't raise - audit failures shouldn't break the app
            print(f"Audit log failed: {e}")
    
    @classmethod
    async def log_action(
        cls,
        institution_id: str,
        user_id: str,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        request: Optional[Request] = None,
        metadata: Optional[dict] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Convenience method to log an action"""
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
        
        entry = AuditLog(
            institution_id=institution_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
            success=success,
            error_message=error_message
        )
        
        # Fire and forget - don't await
        asyncio.create_task(cls.log(entry))
    
    @classmethod
    async def get_logs(
        cls,
        institution_id: str,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        skip: int = 0
    ) -> list[dict]:
        """Query audit logs for an institution"""
        database = await get_database()
        
        query = {"institution_id": institution_id}
        
        if user_id:
            query["user_id"] = user_id
        if action:
            query["action"] = action.value
        if resource_type:
            query["resource_type"] = resource_type
        if start_date:
            query["timestamp"] = {"$gte": start_date}
        if end_date:
            query.setdefault("timestamp", {})["$lte"] = end_date
        
        cursor = database[cls.COLLECTION_NAME].find(query)\
            .sort("timestamp", -1)\
            .skip(skip)\
            .limit(limit)
        
        logs = []
        async for log in cursor:
            log["id"] = str(log.pop("_id"))
            logs.append(log)
        
        return logs


def audit_endpoint(
    action: AuditAction,
    resource_type: str,
    get_resource_id: Optional[callable] = None
):
    """
    Decorator to automatically audit API endpoint calls.
    
    Usage:
        @router.post("/notes")
        @audit_endpoint(AuditAction.CREATE, "notes")
        async def create_note(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract tenant context and request from kwargs
            tenant = kwargs.get('tenant')
            request = kwargs.get('request')
            
            resource_id = None
            if get_resource_id:
                resource_id = get_resource_id(kwargs)
            
            success = True
            error_message = None
            
            try:
                result = await func(*args, **kwargs)
                
                # Try to extract resource_id from result if not provided
                if resource_id is None and hasattr(result, 'id'):
                    resource_id = result.id
                elif resource_id is None and isinstance(result, dict) and 'id' in result:
                    resource_id = result['id']
                
                return result
                
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            
            finally:
                # Log the audit entry
                if tenant:
                    await AuditLogger.log_action(
                        institution_id=tenant.institution_id,
                        user_id=tenant.user_id,
                        action=action,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        request=request,
                        success=success,
                        error_message=error_message
                    )
        
        return wrapper
    return decorator


async def create_audit_indexes():
    """Create indexes for efficient audit log queries"""
    database = await get_database()
    collection = database[AuditLogger.COLLECTION_NAME]
    
    # Index for querying by institution
    await collection.create_index("institution_id")
    
    # Compound index for common queries
    await collection.create_index([
        ("institution_id", 1),
        ("timestamp", -1)
    ])
    
    # Index for user-specific queries
    await collection.create_index([
        ("institution_id", 1),
        ("user_id", 1),
        ("timestamp", -1)
    ])
    
    # TTL index to auto-delete old logs (optional - 1 year retention)
    # await collection.create_index("timestamp", expireAfterSeconds=31536000)
    
    print("Audit log indexes created")
