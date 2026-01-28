# Multi-Tenant Logging in EKS

## Current State

**Important:** Log separation depends on your isolation level:

- **Low Isolation** (row-level): ✅ Logs can be in the same stream (filter by `institution_id`)
- **High Isolation** (database-per-tenant): ❌ **Logs MUST be separated per tenant** (just like databases)

**For high-isolation deployments**, you **must** use separate log streams/groups per tenant to maintain the same isolation level as your databases.

### How Logs Work Currently

1. **Application Logs**: Go to stdout/stderr of backend pods
   - Collected by Kubernetes → CloudWatch Container Insights
   - All tenants' logs are mixed in the same log stream
   - **But**: Each log entry includes tenant info: `Tenant: <institution_id> | User: <user_id> | Role: <role>`

2. **Audit Logs**: Stored in MongoDB (separate per tenant)
   - Each tenant's audit logs are isolated in MongoDB
   - Queryable by `institution_id`

3. **Kubernetes Logs**: Pod logs via `kubectl logs`
   - Mixed logs from all tenants
   - Can filter by pod, but not by tenant

## Log Format

Current log format includes tenant information:

```
2026-01-26 10:30:45 - app.core.middleware_logging - INFO - 
→ POST /api/messages/ | IP: 10.0.1.5 | Tenant: inst_abc123 | User: user_xyz | Role: student | User-Agent: Mozilla/5.0...
```

## Solutions for Log Separation

### Option 1: Filter Logs by Tenant (Recommended for Most Cases)

**Use CloudWatch Logs Insights** to filter logs by `institution_id`:

```sql
-- Get all logs for a specific tenant
fields @timestamp, @message
| filter @message like /Tenant: inst_abc123/
| sort @timestamp desc
| limit 1000
```

**Or use grep/kubectl:**

```bash
# Filter logs for a specific tenant
kubectl logs -n student-counsellor -l app=backend | grep "Tenant: inst_abc123"
```

**Benefits:**
- ✅ No infrastructure changes needed
- ✅ Works with current setup
- ✅ Cost-effective

**Limitations:**
- ❌ All logs still in same stream
- ❌ Need to filter manually
- ❌ Harder to set retention per tenant

### Option 2: Structured JSON Logging (Better Filtering)

Modify logging to use JSON format with tenant tags:

**Update `backend/app/main.py`:**

```python
import json
import logging
from pythonjsonlogger import jsonlogger

# Configure JSON logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s'
)
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)
```

**Update `middleware_logging.py` to include tenant in JSON:**

```python
logger.info(
    json.dumps({
        "method": method,
        "path": path,
        "institution_id": tenant.institution_id if tenant else None,
        "user_id": tenant.user_id if tenant else None,
        "role": tenant.role if tenant else None,
        "ip": client_ip,
        "user_agent": user_agent
    })
)
```

**Then filter in CloudWatch:**

```sql
fields @timestamp, institution_id, user_id, message
| filter institution_id = "inst_abc123"
| sort @timestamp desc
```

### Option 3: Separate Log Groups per Tenant (Required for High Isolation)

**⚠️ REQUIRED when using `SAAS_ISOLATION_LEVEL=high` or `TENANT_STRATEGY=database_per_tenant`**

Use **Fluent Bit** to route logs to separate CloudWatch Log Groups per tenant. This matches the database-per-tenant isolation strategy.

**Setup Steps:**

1. **Enable in Terraform** (if using Terraform):

   ```hcl
   # terraform/terraform.tfvars
   enable_high_isolation_logging = true
   ```

   Then apply:
   ```bash
   cd terraform
   terraform apply
   ```

2. **Get Fluent Bit IAM role ARN:**

   ```bash
   terraform output fluent_bit_role_arn
   ```

3. **Update Fluent Bit manifest:**

   ```bash
   cd ../k8s
   export FLUENT_BIT_IAM_ROLE_ARN=$(terraform output -raw fluent_bit_role_arn)
   export AWS_REGION=$(terraform output -raw aws_region)
   
   # Replace placeholders
   envsubst < fluent-bit-high-isolation.yaml > fluent-bit-deploy.yaml
   ```

4. **Deploy Fluent Bit:**

   ```bash
   kubectl apply -f fluent-bit-deploy.yaml
   ```

5. **Verify:**

   ```bash
   kubectl get pods -n student-counsellor -l app=fluent-bit
   kubectl logs -n student-counsellor -l app=fluent-bit
   ```

**How it works:**

- Fluent Bit parses logs to extract `institution_id` from log entries
- Routes logs to CloudWatch Log Groups: `/aws/eks/<cluster-name>/tenant-<institution-id>`
- Each tenant gets its own log group (matching database-per-tenant isolation)
- Log groups are created automatically when first log arrives

**Manual Setup (without Terraform):**

1. Create IAM role for Fluent Bit (similar to AWS Load Balancer Controller)
2. Update `k8s/fluent-bit-high-isolation.yaml` with role ARN and region
3. Apply: `kubectl apply -f fluent-bit-high-isolation.yaml`

**Benefits:**
- ✅ Complete log separation per tenant
- ✅ Separate retention policies per tenant
- ✅ Easier compliance/auditing

**Limitations:**
- ❌ More complex setup
- ❌ Higher CloudWatch costs (multiple log groups)
- ❌ Requires Fluent Bit configuration

### Option 4: Kubernetes Labels + Log Routing (Hybrid)

Add tenant labels to pods and route logs accordingly:

**Update `backend.yaml` to include tenant labels:**

```yaml
# In deployment spec
template:
  metadata:
    labels:
      app: backend
      tenant: all  # or specific tenant ID for dedicated pods
```

**Use log aggregation tools** (e.g., Fluentd, Fluent Bit) to route based on labels.

## Recommended Approach

### For Low-Isolation Deployments (Row-Level Strategy)

**Use Option 1 or Option 2:**

1. **Keep current logging** (includes tenant info)
2. **Use CloudWatch Logs Insights** to filter by tenant
3. **Add structured JSON logging** (Option 2) for better querying
4. **Set up log retention** in CloudWatch (e.g., 30-90 days)

**Cost**: Low (single log group)
**Complexity**: Low
**Isolation**: Application-level (matches row-level database strategy)

### For High-Isolation Deployments (Database-Per-Tenant)

**⚠️ MUST use Option 3 (Separate Log Groups per Tenant)**

When using `SAAS_ISOLATION_LEVEL=high` or `TENANT_STRATEGY=database_per_tenant`:
- ✅ Each tenant has separate database → **Each tenant MUST have separate log group**
- ✅ Deploy Fluent Bit with tenant-based routing
- ✅ Create separate log groups per tenant automatically
- ✅ Set tenant-specific retention policies
- ✅ Use IAM policies to restrict log access per tenant

**Cost**: Higher (multiple log groups)
**Complexity**: Medium
**Isolation**: Infrastructure-level (matches database-per-tenant strategy)

**Why this is required:**
- If databases are separated per tenant, logs must also be separated
- Compliance/auditing requirements for high-isolation deployments
- Consistent isolation level across all resources (DB + logs)

## CloudWatch Logs Configuration

### Current Setup (Default)

- **Log Group**: `/aws/containerinsights/<cluster-name>/application`
- **Retention**: 7 days (default)
- **Format**: Plain text with tenant info

### Recommended Configuration

1. **Create dedicated log group:**

```bash
aws logs create-log-group \
  --log-group-name /aws/eks/student-counsellor/application \
  --region us-east-1
```

2. **Set retention:**

```bash
aws logs put-retention-policy \
  --log-group-name /aws/eks/student-counsellor/application \
  --retention-in-days 30 \
  --region us-east-1
```

3. **Enable CloudWatch Container Insights** (if not already):

```bash
# Install CloudWatch Container Insights
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluent-bit-quickstart.yaml
```

## Querying Tenant Logs

### CloudWatch Logs Insights Queries

**1. All logs for a tenant:**
```sql
fields @timestamp, @message
| filter @message like /Tenant: inst_abc123/
| sort @timestamp desc
```

**2. Errors for a tenant:**
```sql
fields @timestamp, @message
| filter @message like /Tenant: inst_abc123/ and @message like /ERROR/
| sort @timestamp desc
```

**3. API requests for a tenant:**
```sql
fields @timestamp, @message
| filter @message like /Tenant: inst_abc123/ and @message like /→/
| stats count() by bin(5m)
```

**4. User activity for a tenant:**
```sql
fields @timestamp, @message
| filter @message like /Tenant: inst_abc123/ and @message like /User: user_xyz/
| sort @timestamp desc
```

### kubectl Commands

```bash
# All logs for a tenant
kubectl logs -n student-counsellor -l app=backend | grep "Tenant: inst_abc123"

# Errors for a tenant
kubectl logs -n student-counsellor -l app=backend | grep "Tenant: inst_abc123" | grep ERROR

# Follow logs for a tenant
kubectl logs -n student-counsellor -l app=backend -f | grep "Tenant: inst_abc123"
```

## Best Practices

1. **Always include `institution_id` in logs** (already done)
2. **Use structured logging** (JSON format) for better querying
3. **Set appropriate retention** (30-90 days for production)
4. **Monitor log volume** per tenant for billing
5. **Set up log alerts** for errors per tenant
6. **Use log aggregation** for compliance/auditing

## Cost Considerations

- **Single log group**: ~$0.50/GB ingested, $0.03/GB stored
- **Multiple log groups**: Same pricing, but easier to track per tenant
- **Retention**: Longer retention = higher storage costs
- **Query costs**: CloudWatch Logs Insights queries cost $0.005/GB scanned

## Summary

**Isolation Level Determines Log Strategy:**

| Isolation Level | Database Strategy | Log Strategy | Required Setup |
|----------------|-------------------|--------------|----------------|
| **Low** | Row-level (shared DB) | Shared log stream | Option 1 or 2 (filter by tenant) |
| **High** | Database-per-tenant | **Separate log groups per tenant** | **Option 3 (Fluent Bit routing)** ⚠️ |

**For Low-Isolation:**
- ✅ Logs include tenant info, all in same stream
- ✅ Use CloudWatch Logs Insights to filter by tenant
- ✅ Cost-effective, simple setup

**For High-Isolation:**
- ⚠️ **MUST use separate log groups per tenant** (matches database isolation)
- ⚠️ Deploy Fluent Bit with tenant-based routing
- ⚠️ Each tenant gets own CloudWatch Log Group: `/aws/eks/<cluster>/tenant-<institution-id>`

**The log isolation level must match the database isolation level** for consistency and compliance.
