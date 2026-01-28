# SaaS Platform Versioning Strategy

## Overview

This document outlines a comprehensive strategy for supporting multiple versions of the Student Counsellor SaaS platform, allowing institutions to stay 1-2 major versions behind the latest release.

## Versioning Model

### Version Format
- **Semantic Versioning**: `MAJOR.MINOR.PATCH` (e.g., `2.1.3`)
- **Major Version**: Breaking changes, significant feature additions
- **Minor Version**: New features, backward compatible
- **Patch Version**: Bug fixes, security patches

### Supported Versions Policy
- **Latest**: Current production version (e.g., `3.0.0`)
- **N-1**: One version behind (e.g., `2.0.0`)
- **N-2**: Two versions behind (e.g., `1.0.0`)
- **Legacy**: Versions older than N-2 are deprecated (6-month grace period)

## Architecture Components

### 1. Institution Version Tracking

**Database Schema Addition:**
```python
# Institution model enhancement
class InstitutionResponse(InstitutionBase):
    id: str
    platform_version: str = "latest"  # e.g., "2.0.0", "1.0.0", "latest"
    version_pinned: bool = False  # If True, requires manual upgrade
    version_upgrade_scheduled: Optional[datetime] = None
    version_compatibility_mode: str = "strict"  # "strict" or "compatible"
    # ... existing fields
```

### 2. API Versioning Strategy

#### Option A: URL Path Versioning (Recommended)
```
/api/v1/auth/login
/api/v2/auth/login
/api/v3/auth/login
```

#### Option B: Header-Based Versioning
```
X-API-Version: 2.0
```

#### Option C: Query Parameter (Not Recommended)
```
/api/auth/login?version=2.0
```

**Recommendation: Use Option A (URL Path) for clarity and caching benefits**

### 3. Version Middleware

**Purpose**: Route requests to appropriate version handlers based on institution's version

```python
# backend/app/core/versioning.py
class VersionMiddleware:
    """
    Determines API version based on:
    1. Institution's platform_version
    2. Request header (if provided, for testing)
    3. Defaults to institution's version
    """
```

### 4. Feature Flags System

**Purpose**: Enable/disable features per version

```python
# backend/app/core/feature_flags.py
class FeatureFlags:
    """
    Version-specific feature availability
    - v1.0: Basic appointments, messages
    - v2.0: + Notes, advanced search
    - v3.0: + Analytics, bulk operations
    """
```

## Implementation Strategy

### Phase 1: Foundation (Week 1-2)

1. **Version Metadata**
   - Add `platform_version` to Institution model
   - Create version registry/configuration
   - Add version to TenantContext

2. **Version Detection**
   - Middleware to extract version from request
   - Default to institution's version
   - Support override via header for testing

3. **Version Registry**
   - Centralized version configuration
   - Feature availability matrix
   - API endpoint compatibility matrix

### Phase 2: API Versioning (Week 3-4)

1. **Router Versioning**
   ```python
   # Structure:
   backend/app/api/
     v1/
       auth.py
       appointments.py
       messages.py
     v2/
       auth.py  # Enhanced with new features
       appointments.py
       messages.py
       notes.py  # New in v2
     v3/
       # Latest version
   ```

2. **Shared Code Strategy**
   - Common utilities in `app/core/`
   - Version-specific logic in versioned modules
   - Shared models with version-aware serialization

3. **Backward Compatibility Layer**
   - Adapters to convert between versions
   - Deprecation warnings for old endpoints
   - Migration helpers

### Phase 3: Database Schema Versioning (Week 5-6)

1. **Schema Versioning**
   - Track schema version per collection
   - Support multiple schema versions simultaneously
   - Migration scripts per version

2. **Data Access Layer**
   - Version-aware repository pattern
   - Schema adapters for reading/writing
   - Automatic data transformation

3. **Migration Strategy**
   ```python
   # On read: Transform old schema → current
   # On write: Transform current → institution's schema version
   # Background: Gradual migration jobs
   ```

### Phase 4: Frontend Versioning (Week 7-8)

1. **Multi-Version Frontend**
   - Separate build artifacts per version
   - Version-specific routing
   - Feature detection at runtime

2. **CDN/Asset Management**
   ```
   /static/v1.0.0/app.js
   /static/v2.0.0/app.js
   /static/v3.0.0/app.js (latest)
   ```

3. **Version Selection**
   - Frontend reads institution version from API
   - Loads appropriate version bundle
   - Fallback to latest if version unavailable

### Phase 5: Upgrade Management (Week 9-10)

1. **Upgrade Workflow**
   - Admin-initiated upgrades
   - Scheduled automatic upgrades
   - Rollback capability

2. **Testing & Validation**
   - Pre-upgrade compatibility checks
   - Dry-run mode
   - Post-upgrade validation

3. **Communication**
   - Email notifications
   - In-app upgrade prompts
   - Changelog per version

## Technical Implementation Details

### 1. Version Registry

```python
# backend/app/core/version_registry.py
VERSION_REGISTRY = {
    "1.0.0": {
        "release_date": "2024-01-01",
        "end_of_support": "2025-07-01",
        "features": ["appointments", "messages"],
        "api_endpoints": ["/api/v1/*"],
        "schema_version": 1,
        "frontend_bundle": "v1.0.0"
    },
    "2.0.0": {
        "release_date": "2024-07-01",
        "end_of_support": "2026-01-01",
        "features": ["appointments", "messages", "notes"],
        "api_endpoints": ["/api/v2/*"],
        "schema_version": 2,
        "frontend_bundle": "v2.0.0"
    },
    "3.0.0": {
        "release_date": "2025-01-01",
        "end_of_support": None,  # Latest
        "features": ["appointments", "messages", "notes", "analytics"],
        "api_endpoints": ["/api/v3/*"],
        "schema_version": 3,
        "frontend_bundle": "v3.0.0"
    }
}
```

### 2. Version-Aware Middleware

```python
# backend/app/core/versioning.py
class VersionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract version from:
        # 1. X-API-Version header (for testing)
        # 2. Institution's platform_version
        # 3. Default to latest
        
        tenant = request.state.get("tenant")
        if tenant:
            version = tenant.institution.get("platform_version", "latest")
            request.state.api_version = self.resolve_version(version)
        
        response = await call_next(request)
        response.headers["X-API-Version"] = request.state.api_version
        return response
```

### 3. Versioned Router Pattern

```python
# backend/app/api/v1/auth.py
router_v1 = APIRouter(prefix="/api/v1/auth", tags=["Auth v1"])

@router_v1.post("/login")
async def login_v1(...):
    # v1 implementation
    pass

# backend/app/api/v2/auth.py
router_v2 = APIRouter(prefix="/api/v2/auth", tags=["Auth v2"])

@router_v2.post("/login")
async def login_v2(...):
    # v2 implementation with enhancements
    pass
```

### 4. Database Schema Adapters

```python
# backend/app/core/schema_adapters.py
class SchemaAdapter:
    """
    Converts data between schema versions
    """
    @staticmethod
    def to_v1(data: dict) -> dict:
        # Convert current schema to v1
        pass
    
    @staticmethod
    def to_v2(data: dict) -> dict:
        # Convert current schema to v2
        pass
```

## Deployment Strategy

### 1. Blue-Green Deployment
- Deploy new version alongside existing
- Route traffic based on institution version
- Gradual migration

### 2. Canary Releases
- Test new version with select institutions
- Monitor for issues
- Roll out gradually

### 3. Rollback Plan
- Keep previous version running
- Quick switch mechanism
- Data consistency checks

## Testing Strategy

### 1. Version Compatibility Testing
- Test all supported versions
- Cross-version API calls
- Data migration scenarios

### 2. Regression Testing
- Ensure old versions still work
- No breaking changes in supported versions
- Feature flag validation

### 3. Integration Testing
- Multi-version environments
- Upgrade/downgrade paths
- Data integrity checks

## Monitoring & Observability

### 1. Version Metrics
- Usage per version
- Error rates by version
- Performance metrics

### 2. Upgrade Tracking
- Institutions pending upgrade
- Failed upgrade attempts
- Version adoption rates

### 3. Alerts
- Deprecated version usage
- Approaching end-of-support
- Upgrade failures

## Migration Path

### For Institutions

1. **Automatic (Recommended)**
   - Scheduled upgrades during maintenance windows
   - Pre-upgrade compatibility checks
   - Automatic rollback on failure

2. **Manual**
   - Admin-initiated upgrades
   - Testing period before production
   - Custom upgrade schedules

3. **Pinned Versions**
   - Enterprise customers can pin to specific versions
   - Extended support contracts
   - Custom migration timelines

## Best Practices

### 1. Backward Compatibility
- Maintain API contracts for supported versions
- Deprecation notices 6 months in advance
- Clear migration guides

### 2. Documentation
- Version-specific API docs
- Changelog per version
- Migration guides

### 3. Communication
- Release notes
- Upgrade notifications
- End-of-support warnings

## Cost Considerations

### 1. Infrastructure
- Multiple version deployments
- Storage for versioned assets
- Testing environments

### 2. Maintenance
- Bug fixes for multiple versions
- Security patches
- Documentation updates

### 3. Support
- Training for support team
- Version-specific troubleshooting
- Upgrade assistance

## Recommended Approach

**For Your Current Architecture:**

1. **Start Simple**: Implement URL-based API versioning (v1, v2, v3)
2. **Institution-Level Versioning**: Add `platform_version` to Institution model
3. **Feature Flags**: Use version registry to enable/disable features
4. **Gradual Rollout**: Support 2-3 versions initially, expand as needed
5. **Frontend Bundles**: Build separate frontend bundles per major version

**Priority Order:**
1. ✅ Add version tracking to institutions
2. ✅ Implement API version routing
3. ✅ Create version registry
4. ✅ Add feature flags
5. ✅ Frontend version selection
6. ✅ Upgrade management UI
7. ✅ Automated testing per version

## Next Steps

1. Review and approve this strategy
2. Create detailed implementation plan
3. Set up version registry
4. Implement Phase 1 (Foundation)
5. Test with pilot institutions
