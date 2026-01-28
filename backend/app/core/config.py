from pydantic_settings import BaseSettings
from typing import Optional, Literal
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Student Counsellor API"
    DEBUG: bool = False
    
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "student_counsellor"
    
    # JWT
    # SECRET_KEY is REQUIRED in production - must be set via environment variable
    # Generate with: openssl rand -hex 32
    # Default provided for development only - NEVER use default in production
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS Configuration
    ALLOWED_ORIGINS: str = ""  # Comma-separated list of allowed origins
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate SECRET_KEY after initialization
        self._validate_secret_key()
    
    def _validate_secret_key(self):
        """Validate SECRET_KEY - warn in dev, error in production"""
        default_key = "your-super-secret-key-change-in-production"
        if not self.SECRET_KEY or self.SECRET_KEY == default_key:
            if self.DEBUG:
                import warnings
                warnings.warn(
                    f"⚠️  SECRET_KEY is using default value. This is INSECURE for production! "
                    f"Set SECRET_KEY environment variable. Generate with: openssl rand -hex 32",
                    UserWarning
                )
            else:
                raise ValueError(
                    "SECRET_KEY is required in production and must not be the default value. "
                    "Set it via environment variable. Generate with: openssl rand -hex 32"
                )
        elif len(self.SECRET_KEY) < 32:
            raise ValueError(
                f"SECRET_KEY must be at least 32 characters long. "
                f"Current length: {len(self.SECRET_KEY)}. "
                f"Generate with: openssl rand -hex 32"
            )
    
    # Multi-tenancy Configuration
    # Deployment mode: 'saas' (cloud) or 'onprem' (on-premises)
    DEPLOYMENT_MODE: Literal["saas", "onprem"] = "saas"
    
    # Tenant isolation strategy (auto-detected from DEPLOYMENT_MODE if not set)
    # - row_level: All tenants share collections, filtered by institution_id (default for SaaS low-isolation)
    # - collection_per_tenant: Each tenant gets separate collections (default for on-prem)
    # - database_per_tenant: Each tenant gets separate database (SaaS high-isolation)
    TENANT_STRATEGY: Optional[Literal["row_level", "collection_per_tenant", "database_per_tenant"]] = None
    
    # SaaS Isolation Level (only applies when DEPLOYMENT_MODE=saas)
    # - low: Shared database and collections, filtered by institution_id (cost-effective)
    # - high: Separate database per tenant (maximum isolation, higher cost)
    SAAS_ISOLATION_LEVEL: Literal["low", "high"] = "low"
    
    # Audit logging
    AUDIT_LOGGING_ENABLED: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 365  # 1 year default
    
    # Super Admin Configuration
    # Comma-separated list of super admin emails who can reassign counsellors between institutions
    SUPER_ADMIN_EMAILS: str = ""  # e.g., "superadmin@system.com,admin@system.com"
    
    # Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""  # Email address for sending emails
    SMTP_PASSWORD: str = ""  # Email password or app password
    SMTP_FROM_EMAIL: str = ""  # From email address (defaults to SMTP_USER if not set)
    SMTP_FROM_NAME: str = "Student Counsellor"
    SMTP_USE_TLS: bool = True
    FRONTEND_URL: str = "http://localhost:3000"  # Frontend URL for password reset links
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
