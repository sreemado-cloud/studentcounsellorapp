# Architecture & Design Documentation

## Overview

This document provides detailed information about the architecture, design decisions, and implementation of the Student Counsellor Application.

## Multi-Tenant Architecture

### Tenant Model

- **Tenant**: Each university/institution is a tenant
- **Users**: Students, Counsellors, and Admins belong to a tenant (institution)
- **Data Isolation**: All data is scoped to an institution_id

### Isolation Strategies

The application supports three isolation strategies:

#### 1. Row-Level Strategy (SaaS Low-Isolation)
- **Use Case**: Cost-effective SaaS deployment
- **Implementation**: All tenants share the same database and collections
- **Isolation**: Achieved through `institution_id` filtering in all queries
- **Configuration**: `DEPLOYMENT_MODE=saas` and `SAAS_ISOLATION_LEVEL=low`

#### 2. Collection-Per-Tenant Strategy (On-Premise)
- **Use Case**: Single-tenant on-premise deployment
- **Implementation**: Each institution has separate collections (e.g., `inst_abc123_messages`)
- **Isolation**: Collection names provide natural isolation
- **Configuration**: `DEPLOYMENT_MODE=onprem`

#### 3. Database-Per-Tenant Strategy (SaaS High-Isolation)
- **Use Case**: Maximum security for SaaS deployment
- **Implementation**: Each institution has a completely separate database
- **Isolation**: Database-level isolation provides maximum security
- **Configuration**: `DEPLOYMENT_MODE=saas` and `SAAS_ISOLATION_LEVEL=high`

### Tenant Context Flow

```
Request → TenantMiddleware → Extract JWT → Get User → Set TenantContext
    ↓
API Endpoint → Get TenantContext → Apply Tenant Filters → Database Query
    ↓
TenantAwareRepository → Apply Strategy → Execute Query
```

## Security Architecture

### Authentication Flow

1. User logs in with email/password
2. Backend validates credentials
3. JWT token generated with user_id, institution_id, and role
4. Token sent to frontend and stored
5. All subsequent requests include token in Authorization header
6. TenantMiddleware extracts and validates token
7. TenantContext set for request lifecycle

### Authorization Rules

#### Students
- Can only access their own data
- Cannot see other students' data
- Can message their assigned counsellor
- Can create appointments with their assigned counsellor

#### Counsellors
- Can only see messages from assigned students (max 10)
- Cannot see other counsellors' students
- Cannot see unassigned students
- Full conversation history available (with masked previous counsellor names)

#### Admins
- Can manage all users in their institution
- Can create students, counsellors, and other admins
- Can assign/reassign students to counsellors
- Can view all data within their institution
- Cannot access other institutions' data

### Data Privacy

#### Student Data Isolation
- All queries automatically filter by `student_id` for students
- Students cannot query other students' data
- Database-level enforcement prevents data leakage

#### Counsellor Scope
- Counsellors can only query messages where `student_id` is in their assigned students list
- Assignment validation ensures max 10 students per counsellor
- Re-assignment preserves history with privacy masking

#### Cross-Tenant Protection
- All queries include `institution_id` filter
- Middleware enforces institution boundaries
- Database strategy provides additional isolation layer

## Re-Assignment with History Preservation

### Process Flow

1. Admin initiates re-assignment via `/api/admin/users/{student_id}/assign-counsellor`
2. System validates counsellor capacity (max 10 students)
3. Previous counsellor_id stored in assignment history
4. All messages from previous counsellor marked with `previous_counsellor_masked: true`
5. New counsellor assigned
6. New counsellor can see full conversation history
7. Previous counsellor names displayed as "Previous Counsellor" for privacy

### Implementation Details

```python
# Assignment history tracking
assignment_history = student.get("counsellor_assignment_history", [])
assignment_history.append({
    "counsellor_id": previous_counsellor_id,
    "assigned_at": student.get("counsellor_assigned_at"),
    "reassigned_at": datetime.utcnow(),
    "reassigned_by": tenant.user_id
})

# Message masking
await repo.update_one(
    tenant.institution_id,
    {
        "student_id": student_id,
        "sender_id": previous_counsellor_id
    },
    {
        "$set": {
            "previous_counsellor_masked": True,
            "masked_counsellor_id": previous_counsellor_id
        }
    }
)
```

## Database Schema

### Users Collection
```javascript
{
  _id: ObjectId,
  email: String (unique),
  password: String (hashed),
  full_name: String,
  role: "student" | "counsellor" | "admin",
  institution_id: String (required),
  assigned_counsellor_id: String (for students),
  counsellor_assignment_history: Array,
  is_active: Boolean,
  created_at: DateTime,
  // ... other fields
}
```

### Messages Collection
```javascript
{
  _id: ObjectId,
  sender_id: String,
  recipient_id: String,
  student_id: String (for tenant isolation),
  institution_id: String,
  subject: String,
  content: String,
  is_read: Boolean,
  previous_counsellor_masked: Boolean,
  masked_counsellor_id: String,
  created_at: DateTime,
  read_at: DateTime
}
```

## Deployment Configurations

### On-Premise Deployment
- Single tenant (one university)
- Collection-per-tenant strategy
- No multi-tenancy concerns
- Simpler configuration

### SaaS Low-Isolation
- Multiple tenants share database
- Row-level filtering
- Cost-effective
- Suitable for universities with standard security requirements

### SaaS High-Isolation
- Each tenant has separate database
- Maximum security
- Higher infrastructure costs
- Suitable for universities with strict compliance requirements

## Performance Considerations

### Indexing Strategy
- `institution_id` indexed on all collections
- `student_id` indexed for student data queries
- Composite indexes for common query patterns
- Unique indexes on email and institution names

### Query Optimization
- Tenant filters applied at database level
- Minimal data transfer (only tenant's data)
- Efficient aggregation pipelines for statistics

## Scalability

### Horizontal Scaling
- Stateless backend services
- Multiple pod replicas in EKS
- Load balancing via AWS ALB

### Database Scaling
- MongoDB replica sets for high availability
- Sharding support for large deployments
- Separate databases per tenant (high-isolation mode) enables independent scaling

## Monitoring & Observability

### Audit Logging
- All administrative actions logged
- User actions tracked with metadata
- Compliance-ready audit trail

### Logging
- Request/response logging
- Tenant context in all logs
- Error tracking with tenant information

## Future Enhancements

1. **Real-time Messaging**: WebSocket support for live chat
2. **File Attachments**: Support for document sharing
3. **Video Conferencing**: Integration with video call services
4. **Analytics Dashboard**: Institution-level analytics
5. **Mobile App**: React Native mobile application
6. **Advanced Reporting**: Custom report generation
7. **Integration APIs**: Third-party system integrations
