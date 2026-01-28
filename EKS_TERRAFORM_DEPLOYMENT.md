# Production Deployment: AWS EKS with Terraform

This guide walks you through deploying the Student Counsellor app to AWS EKS using Terraform.

## Quick Start (Automated)

For the fastest deployment, use the automated script:

```powershell
# Prerequisites: AWS CLI configured, Docker running, Terraform/kubectl/Helm installed

# Deploy everything (takes ~20-25 minutes)
.\deploy-aws.ps1

# Verify deployment
.\verify-aws-deployment.ps1

# Destroy all resources when done
.\deploy-aws.ps1 -Destroy
```

The script handles all steps automatically:
1. Creates VPC, EKS cluster, ECR repositories via Terraform
2. Configures kubectl for the new cluster
3. Installs AWS Load Balancer Controller
4. Builds and pushes Docker images to ECR
5. Deploys MongoDB, backend, and frontend to Kubernetes
6. Seeds the database with initial data

**Estimated Cost**: ~$210/month (with single NAT gateway)

---

## Manual Deployment (Step by Step)

If you prefer manual control, follow the steps below.

## Prerequisites

- AWS CLI installed and configured (`aws configure`)
- Terraform >= 1.5.0 installed
- kubectl installed
- Helm 3.x installed
- Docker installed (for building images)
- AWS account with appropriate permissions (IAM, EC2, EKS, ECR, VPC)

## Architecture

- **VPC**: Dedicated VPC with public/private subnets across 3 AZs
- **EKS**: Managed Kubernetes cluster (1.30) - **hosts all tenants**
- **ECR**: Container registries for backend and frontend images
- **ALB**: Application Load Balancer (via AWS Load Balancer Controller)
- **MongoDB**: StatefulSet in EKS (or use AWS DocumentDB for production)

### Multi-Tenancy in EKS

**Yes, all tenants (universities) run in the same EKS cluster.** The application handles tenant isolation at the application layer:

- **Shared Infrastructure**: One EKS cluster, one namespace, shared pods
- **Application-Level Isolation**: Backend enforces tenant boundaries via `institution_id` in JWT and database queries
- **Configurable Strategies**:
  - **Row-Level** (Low Isolation): All tenants share MongoDB, filtered by `institution_id`
  - **Database-Per-Tenant** (High Isolation): Each tenant gets separate MongoDB database
  - **Collection-Per-Tenant** (On-Prem): Each tenant gets separate collections

**Benefits:**
- Cost-effective: Shared infrastructure across all tenants
- Scalable: Horizontal pod autoscaling handles load from all tenants
- Secure: Application-layer isolation ensures data separation

**For maximum isolation**, consider:
- Separate namespaces per tenant (optional)
- Resource quotas per tenant (optional)
- Separate MongoDB instances per tenant (high-isolation mode)

## Step 1: Configure Terraform

1. **Navigate to terraform directory:**
   ```bash
   cd terraform
   ```

2. **Copy and customize variables:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

3. **Review variables:**
   - `aws_region`: Your preferred AWS region
   - `cluster_name`: EKS cluster name
   - `node_instance_types`: EC2 instance types (e.g. `["t3.medium"]`)
   - `node_desired_size`: Number of nodes (start with 2)
   - `vpc_cidr`: VPC CIDR block (default: `10.0.0.0/16`)

## Step 2: Initialize and Apply Terraform

1. **Initialize Terraform:**
   ```bash
   terraform init
   ```

2. **Review the plan:**
   ```bash
   terraform plan
   ```

3. **Apply (creates VPC, EKS, ECR, IAM):**
   ```bash
   terraform apply
   # Type 'yes' to confirm
   ```

   This will take **15-20 minutes** to create the EKS cluster.

4. **Save outputs:**
   ```bash
   terraform output -json > outputs.json
   ```

## Step 3: Configure kubectl

1. **Get the configure command from Terraform:**
   ```bash
   terraform output configure_kubectl
   ```

2. **Run it:**
   ```bash
   aws eks update-kubeconfig --region <region> --name <cluster-name>
   ```

3. **Verify:**
   ```bash
   kubectl get nodes
   ```

## Step 4: Install AWS Load Balancer Controller

1. **Add the Helm repository:**
   ```bash
   helm repo add eks https://aws.github.io/eks-charts
   helm repo update
   ```

2. **Get the IAM role ARN from Terraform:**
   ```bash
   terraform output lb_controller_role_arn
   ```

3. **Install the controller:**
   ```bash
   helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
     -n kube-system \
     --set clusterName=$(terraform output -raw cluster_name) \
     --set serviceAccount.create=true \
     --set serviceAccount.name=aws-load-balancer-controller \
     --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=$(terraform output -raw lb_controller_role_arn)
   ```

4. **Verify:**
   ```bash
   kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
   ```

## Step 5: Build and Push Docker Images

1. **Get ECR login command from Terraform:**
   ```bash
   terraform output ecr_login_command
   ```

2. **Log in to ECR:**
   ```bash
   aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
   ```

3. **Get ECR URLs:**
   ```bash
   terraform output ecr_backend_url
   terraform output ecr_frontend_url
   ```

4. **Build and push backend:**
   ```bash
   cd ../backend
   docker build -t <ecr-backend-url>:latest .
   docker push <ecr-backend-url>:latest
   ```

5. **Build and push frontend:**
   ```bash
   cd ../frontend
   docker build -t <ecr-frontend-url>:latest .
   docker push <ecr-frontend-url>:latest
   ```

## Step 6: Prepare Kubernetes Manifests

1. **Get AWS account ID and region:**
   ```bash
   export AWS_ACCOUNT_ID=$(terraform output -raw aws_account_id)
   export AWS_REGION=$(terraform output -raw aws_region)
   ```

2. **Update k8s manifests with ECR URLs:**
   ```bash
   cd ../k8s
   
   # Option A: Use envsubst (if installed)
   envsubst < backend.yaml > backend-deploy.yaml
   envsubst < frontend.yaml > frontend-deploy.yaml
   
   # Option B: Manual replacement
   # Replace ${AWS_ACCOUNT_ID} and ${AWS_REGION} in backend.yaml and frontend.yaml
   ```

3. **Update secrets.yaml:**
   - Set `SECRET_KEY` (generate with `openssl rand -hex 32`)
   - Set `MONGODB_URL` (e.g. `mongodb://admin:password123@mongodb-service:27017`)
   - Set `MONGO_INITDB_ROOT_PASSWORD` (strong password)

4. **Update configmap.yaml:**
   - Set `VITE_API_URL` (e.g. `/api` for same-origin)

## Step 7: Deploy to Kubernetes

1. **Create namespace:**
   ```bash
   kubectl apply -f namespace.yaml
   ```

2. **Create secrets:**
   ```bash
   kubectl apply -f secrets.yaml
   ```

3. **Create configmap:**
   ```bash
   kubectl apply -f configmap.yaml
   ```

4. **Deploy MongoDB:**
   ```bash
   kubectl apply -f mongodb.yaml
   ```

5. **Wait for MongoDB to be ready:**
   ```bash
   kubectl wait --for=condition=ready pod -l app=mongodb -n student-counsellor --timeout=300s
   ```

6. **Deploy backend:**
   ```bash
   kubectl apply -f backend-deploy.yaml  # or backend.yaml if you replaced placeholders
   ```

7. **Deploy frontend:**
   ```bash
   kubectl apply -f frontend-deploy.yaml  # or frontend.yaml if you replaced placeholders
   ```

8. **Deploy ingress:**
   ```bash
   kubectl apply -f ingress.yaml
   ```

9. **Deploy network policies:**
   ```bash
   kubectl apply -f network-policy.yaml
   ```

## Step 8: Get the Application URL

1. **Wait for ingress to be ready:**
   ```bash
   kubectl get ingress -n student-counsellor
   ```

2. **Get the ALB URL:**
   ```bash
   kubectl get ingress student-counsellor-ingress -n student-counsellor -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
   ```

3. **Open in browser:**
   - The URL will be something like: `k8s-studentc-xxxxx-xxxxx.us-east-1.elb.amazonaws.com`
   - **Note:** For HTTPS, you need to add an ACM certificate ARN to `ingress.yaml` (see below)

## Step 9: Seed the Database

1. **Get a backend pod:**
   ```bash
   kubectl get pods -n student-counsellor -l app=backend
   ```

2. **Run seed script:**
   ```bash
   kubectl exec -it <backend-pod-name> -n student-counsellor -- python -m app.seed_data
   ```

## Step 10: Configure HTTPS (Optional)

1. **Request an ACM certificate:**
   ```bash
   aws acm request-certificate \
     --domain-name yourdomain.com \
     --validation-method DNS \
     --region <region>
   ```

2. **Update ingress.yaml:**
   - Uncomment and set `alb.ingress.kubernetes.io/certificate-arn: <cert-arn>`

3. **Apply:**
   ```bash
   kubectl apply -f ingress.yaml
   ```

## Network Policy for ALB

The existing `network-policy.yaml` restricts backend ingress to frontend pods and ingress-nginx. With ALB, traffic comes from the VPC. You have two options:

**Option A: Add VPC CIDR to backend policy** (recommended)

Add this to `network-policy.yaml` in the `backend-network-policy` ingress section:

```yaml
- from:
    - ipBlock:
        cidr: <vpc-cidr>  # e.g. 10.0.0.0/16 (get from: terraform output vpc_cidr)
  ports:
    - protocol: TCP
      port: 8000
```

**Option B: Temporarily relax the policy** (for testing)

Comment out the backend ingress restrictions in `network-policy.yaml`.

## Troubleshooting

### "Cannot connect to cluster"
- Verify `kubectl` is configured: `kubectl get nodes`
- Check AWS credentials: `aws sts get-caller-identity`

### "ImagePullBackOff"
- Verify ECR login: `aws ecr get-login-password ...`
- Check image exists: `aws ecr describe-images --repository-name student-counsellor-backend`
- Verify image URL in deployment matches ECR URL

### "LoadBalancer not created"
- Check AWS Load Balancer Controller logs: `kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller`
- Verify IAM role ARN is correct in Helm install
- Check subnets have correct tags (Terraform sets these automatically)

### "MongoDB not starting"
- Check PVC: `kubectl get pvc -n student-counsellor`
- Check storage class: `kubectl get storageclass`
- EKS uses `gp2` by default; ensure it exists

### "Backend cannot connect to MongoDB"
- Verify MongoDB service: `kubectl get svc -n student-counsellor`
- Check network policy allows backend -> MongoDB
- Verify `MONGODB_URL` in secrets matches service name

## Cost Estimation

- **EKS Control Plane**: ~$73/month
- **EC2 Nodes** (2x t3.medium): ~$60/month
- **NAT Gateway** (3x): ~$135/month (or ~$45/month if `single_nat_gateway = true`)
- **ALB**: ~$20/month + data transfer
- **EBS Volumes** (MongoDB): ~$10/month
- **ECR**: Storage + transfer (minimal)

**Total**: ~$300/month (or ~$210/month with single NAT gateway)

## Cleanup

To destroy all resources:

```bash
cd terraform
terraform destroy
```

**Warning:** This will delete the EKS cluster, VPC, and all data. Ensure you have backups.

## Multi-Tenant Considerations

### Current Setup (Recommended)

The default setup uses **application-level isolation** where all tenants share the same Kubernetes resources:

- ✅ **Single namespace** (`student-counsellor`) for all tenants
- ✅ **Shared pods** (backend/frontend) handle requests from all tenants
- ✅ **MongoDB** supports multiple isolation strategies (row-level, collection-per-tenant, database-per-tenant)
- ✅ **Network policies** provide pod-to-pod security
- ✅ **Horizontal Pod Autoscaler (HPA)** scales based on aggregate load

**This is the most cost-effective approach** and works well for most SaaS deployments.

### Optional: Enhanced Multi-Tenant Isolation

If you need stronger isolation, consider:

1. **Resource Quotas per Tenant** (optional):
   ```yaml
   # k8s/resource-quota.yaml (example)
   apiVersion: v1
   kind: ResourceQuota
   metadata:
     name: tenant-quota
     namespace: student-counsellor
   spec:
     hard:
       requests.cpu: "4"
       requests.memory: 8Gi
       limits.cpu: "8"
       limits.memory: 16Gi
   ```

2. **Separate Namespaces per Tenant** (high isolation):
   - Create namespace per university: `tenant-<university-id>`
   - Deploy separate backend/frontend pods per tenant
   - Higher cost but maximum isolation

3. **Separate MongoDB Instances** (high-isolation mode):
   - Use `database_per_tenant` strategy
   - Each tenant gets own MongoDB database
   - Configure via `TENANT_STRATEGY=database_per_tenant`
   - **⚠️ Also requires separate log groups per tenant** (see `EKS_LOGGING_MULTI_TENANT.md` Option 3)

4. **Network Policies per Tenant**:
   - Restrict pod-to-pod communication per tenant
   - More complex but provides network-level isolation

### Scaling for Multiple Tenants

The EKS cluster automatically scales to handle multiple tenants:

- **HPA** (Horizontal Pod Autoscaler): Already configured in `backend.yaml` and `frontend.yaml`
  - Scales backend pods from 2-10 based on CPU/memory
  - Scales frontend pods from 2-10 based on CPU/memory
- **Cluster Autoscaler** (optional): Add to auto-scale EKS node group
- **MongoDB**: Single StatefulSet handles all tenants (or separate per tenant in high-isolation)

### Monitoring Multi-Tenant Workloads

- **CloudWatch**: Monitor aggregate metrics (CPU, memory, request count)
- **Application Logs**: Include `institution_id` in logs to track per-tenant usage
  - **Low Isolation**: All tenant logs in same stream (filter by `institution_id`)
  - **High Isolation**: **MUST use separate log groups per tenant** (matches database-per-tenant strategy)
  - See **[EKS_LOGGING_MULTI_TENANT.md](EKS_LOGGING_MULTI_TENANT.md)** for log separation strategies
- **Custom Metrics**: Track requests per tenant for billing/analytics

## Next Steps

- Set up CI/CD (GitHub Actions, GitLab CI) to build and push images
- Use AWS Secrets Manager for secrets instead of Kubernetes secrets
- Consider AWS DocumentDB for MongoDB (managed, HA)
- Set up monitoring (CloudWatch, Prometheus)
- Configure Cluster Autoscaler for automatic node scaling
- Add backup strategy for MongoDB
- Implement tenant-level metrics and billing (optional)

## Additional Resources

- [EKS User Guide](https://docs.aws.amazon.com/eks/latest/userguide/)
- [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)
- [Terraform AWS EKS Module](https://registry.terraform.io/modules/terraform-aws-modules/eks/aws)
