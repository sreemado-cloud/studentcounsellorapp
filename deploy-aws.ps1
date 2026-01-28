# ============================================================================
# AWS EKS Deployment Script for Student Counsellor App
# ============================================================================
# This script deploys the application to AWS EKS using Terraform
# Run from the project root: .\deploy-aws.ps1
# ============================================================================

param(
    [string]$Region = "us-east-1",
    [string]$ClusterName = "student-counsellor",
    [switch]$SkipTerraform,
    [switch]$SkipBuild,
    [switch]$SkipDeploy,
    [switch]$Destroy
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AWS EKS Deployment - Student Counsellor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ----------------------------------------------------------------------------
# Step 0: Destroy (if requested)
# ----------------------------------------------------------------------------
if ($Destroy) {
    Write-Host "[DESTROY] Destroying all AWS resources..." -ForegroundColor Red
    Set-Location "$ProjectRoot\terraform"
    
    # First delete K8s resources to avoid orphaned load balancers
    Write-Host "Deleting Kubernetes resources first..." -ForegroundColor Yellow
    kubectl delete namespace student-counsellor --ignore-not-found=true 2>$null
    
    Write-Host "Running terraform destroy..." -ForegroundColor Yellow
    terraform destroy -auto-approve
    
    Write-Host "[DESTROY] Complete!" -ForegroundColor Green
    exit 0
}

# ----------------------------------------------------------------------------
# Step 1: Check Prerequisites
# ----------------------------------------------------------------------------
Write-Host "[1/9] Checking prerequisites..." -ForegroundColor Yellow

$prerequisites = @{
    "aws" = "AWS CLI"
    "terraform" = "Terraform"
    "kubectl" = "kubectl"
    "helm" = "Helm"
    "docker" = "Docker"
}

$missing = @()
foreach ($cmd in $prerequisites.Keys) {
    if (!(Get-Command $cmd -ErrorAction SilentlyContinue)) {
        $missing += $prerequisites[$cmd]
    }
}

if ($missing.Count -gt 0) {
    Write-Host "ERROR: Missing prerequisites: $($missing -join ', ')" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install instructions:" -ForegroundColor Yellow
    Write-Host "  AWS CLI:   https://aws.amazon.com/cli/"
    Write-Host "  Terraform: https://developer.hashicorp.com/terraform/install"
    Write-Host "  kubectl:   https://kubernetes.io/docs/tasks/tools/"
    Write-Host "  Helm:      https://helm.sh/docs/intro/install/"
    Write-Host "  Docker:    https://docs.docker.com/get-docker/"
    exit 1
}

# Check AWS credentials
Write-Host "Verifying AWS credentials..." -ForegroundColor Gray
try {
    $awsIdentity = aws sts get-caller-identity --output json | ConvertFrom-Json
    $AWS_ACCOUNT_ID = $awsIdentity.Account
    Write-Host "  AWS Account: $AWS_ACCOUNT_ID" -ForegroundColor Green
} catch {
    Write-Host "ERROR: AWS credentials not configured. Run 'aws configure' first." -ForegroundColor Red
    exit 1
}

# Check Docker is running
Write-Host "Checking Docker daemon..." -ForegroundColor Gray
try {
    docker info > $null 2>&1
    Write-Host "  Docker: Running" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

Write-Host "[1/9] Prerequisites OK" -ForegroundColor Green
Write-Host ""

# ----------------------------------------------------------------------------
# Step 2: Create Terraform Configuration
# ----------------------------------------------------------------------------
Write-Host "[2/9] Configuring Terraform..." -ForegroundColor Yellow
Set-Location "$ProjectRoot\terraform"

if (!(Test-Path "terraform.tfvars")) {
    Write-Host "Creating terraform.tfvars..." -ForegroundColor Gray
    @"
aws_region = "$Region"
environment = "production"
cluster_name = "$ClusterName"

kubernetes_version = "1.30"

# VPC Configuration
vpc_cidr = "10.0.0.0/16"
availability_zones_count = 3

# EKS Node Group Configuration
node_instance_types = ["t3.medium"]
node_desired_size = 2
node_min_size = 2
node_max_size = 5

# Use single NAT gateway to reduce cost (~$90/month savings)
single_nat_gateway = true

# Grant cluster creator admin access
enable_cluster_creator_admin = true

# Additional tags
tags = {
  Project     = "student-counsellor"
  Environment = "production"
  ManagedBy   = "terraform"
}
"@ | Out-File -FilePath "terraform.tfvars" -Encoding utf8
    Write-Host "  Created terraform.tfvars" -ForegroundColor Green
} else {
    Write-Host "  terraform.tfvars already exists" -ForegroundColor Gray
}

Write-Host "[2/9] Terraform configured" -ForegroundColor Green
Write-Host ""

# ----------------------------------------------------------------------------
# Step 3: Apply Terraform (creates VPC, EKS, ECR, IAM)
# ----------------------------------------------------------------------------
if (!$SkipTerraform) {
    Write-Host "[3/9] Applying Terraform (this takes 15-20 minutes)..." -ForegroundColor Yellow
    
    Write-Host "Running terraform init..." -ForegroundColor Gray
    terraform init
    
    Write-Host "Running terraform plan..." -ForegroundColor Gray
    terraform plan -out=tfplan
    
    Write-Host ""
    Write-Host "Terraform will create the following AWS resources:" -ForegroundColor Cyan
    Write-Host "  - VPC with public/private subnets across 3 AZs"
    Write-Host "  - EKS cluster with managed node group"
    Write-Host "  - ECR repositories for backend and frontend"
    Write-Host "  - IAM roles for EKS and Load Balancer Controller"
    Write-Host ""
    
    $confirm = Read-Host "Proceed with terraform apply? (yes/no)"
    if ($confirm -ne "yes") {
        Write-Host "Aborted." -ForegroundColor Yellow
        exit 0
    }
    
    Write-Host "Applying Terraform (please wait ~15-20 min)..." -ForegroundColor Gray
    terraform apply tfplan
    
    Write-Host "[3/9] Terraform applied successfully" -ForegroundColor Green
} else {
    Write-Host "[3/9] Skipping Terraform (--SkipTerraform)" -ForegroundColor Gray
}
Write-Host ""

# ----------------------------------------------------------------------------
# Step 4: Configure kubectl
# ----------------------------------------------------------------------------
Write-Host "[4/9] Configuring kubectl..." -ForegroundColor Yellow

$kubeconfigCmd = terraform output -raw configure_kubectl
Write-Host "Running: $kubeconfigCmd" -ForegroundColor Gray
Invoke-Expression $kubeconfigCmd

Write-Host "Verifying cluster connection..." -ForegroundColor Gray
kubectl get nodes

Write-Host "[4/9] kubectl configured" -ForegroundColor Green
Write-Host ""

# ----------------------------------------------------------------------------
# Step 5: Install AWS Load Balancer Controller
# ----------------------------------------------------------------------------
Write-Host "[5/9] Installing AWS Load Balancer Controller..." -ForegroundColor Yellow

# Add Helm repo
Write-Host "Adding EKS Helm repository..." -ForegroundColor Gray
helm repo add eks https://aws.github.io/eks-charts 2>$null
helm repo update

# Get values from Terraform
$CLUSTER_NAME = terraform output -raw cluster_name
$LB_ROLE_ARN = terraform output -raw lb_controller_role_arn
$VPC_ID = terraform output -raw vpc_id

# Check if already installed
$existingRelease = helm list -n kube-system -q | Select-String "aws-load-balancer-controller"
if ($existingRelease) {
    Write-Host "  AWS Load Balancer Controller already installed, upgrading..." -ForegroundColor Gray
    helm upgrade aws-load-balancer-controller eks/aws-load-balancer-controller `
        -n kube-system `
        --set clusterName=$CLUSTER_NAME `
        --set serviceAccount.create=true `
        --set serviceAccount.name=aws-load-balancer-controller `
        --set "serviceAccount.annotations.eks\.amazonaws\.com/role-arn=$LB_ROLE_ARN" `
        --set vpcId=$VPC_ID
} else {
    Write-Host "  Installing AWS Load Balancer Controller..." -ForegroundColor Gray
    helm install aws-load-balancer-controller eks/aws-load-balancer-controller `
        -n kube-system `
        --set clusterName=$CLUSTER_NAME `
        --set serviceAccount.create=true `
        --set serviceAccount.name=aws-load-balancer-controller `
        --set "serviceAccount.annotations.eks\.amazonaws\.com/role-arn=$LB_ROLE_ARN" `
        --set vpcId=$VPC_ID
}

Write-Host "Waiting for controller to be ready..." -ForegroundColor Gray
Start-Sleep -Seconds 10
kubectl wait --for=condition=available deployment/aws-load-balancer-controller -n kube-system --timeout=120s

Write-Host "[5/9] Load Balancer Controller installed" -ForegroundColor Green
Write-Host ""

# ----------------------------------------------------------------------------
# Step 6: Build and Push Docker Images
# ----------------------------------------------------------------------------
if (!$SkipBuild) {
    Write-Host "[6/9] Building and pushing Docker images..." -ForegroundColor Yellow
    
    # Get ECR URLs
    $ECR_BACKEND = terraform output -raw ecr_backend_url
    $ECR_FRONTEND = terraform output -raw ecr_frontend_url
    
    # Login to ECR
    Write-Host "Logging in to ECR..." -ForegroundColor Gray
    aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$Region.amazonaws.com"
    
    # Build and push backend
    Write-Host "Building backend image..." -ForegroundColor Gray
    Set-Location "$ProjectRoot\backend"
    docker build -t "${ECR_BACKEND}:latest" -t "${ECR_BACKEND}:v1.0.0" .
    
    Write-Host "Pushing backend image..." -ForegroundColor Gray
    docker push "${ECR_BACKEND}:latest"
    docker push "${ECR_BACKEND}:v1.0.0"
    
    # Build and push frontend
    Write-Host "Building frontend image..." -ForegroundColor Gray
    Set-Location "$ProjectRoot\frontend"
    docker build -t "${ECR_FRONTEND}:latest" -t "${ECR_FRONTEND}:v1.0.0" .
    
    Write-Host "Pushing frontend image..." -ForegroundColor Gray
    docker push "${ECR_FRONTEND}:latest"
    docker push "${ECR_FRONTEND}:v1.0.0"
    
    Write-Host "[6/9] Docker images pushed to ECR" -ForegroundColor Green
} else {
    Write-Host "[6/9] Skipping Docker build (--SkipBuild)" -ForegroundColor Gray
}
Write-Host ""

# ----------------------------------------------------------------------------
# Step 7: Prepare Kubernetes Secrets
# ----------------------------------------------------------------------------
Write-Host "[7/9] Preparing Kubernetes secrets..." -ForegroundColor Yellow
Set-Location "$ProjectRoot\k8s"

# Generate secure secrets
$SECRET_KEY = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object {[char]$_})
$MONGO_PASSWORD = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})

Write-Host "Generated secure SECRET_KEY and MongoDB password" -ForegroundColor Gray

# Create production secrets file
@"
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: student-counsellor
type: Opaque
stringData:
  MONGODB_URL: "mongodb://admin:$MONGO_PASSWORD@mongodb-service:27017"
  SECRET_KEY: "$SECRET_KEY"
  MONGO_INITDB_ROOT_USERNAME: "admin"
  MONGO_INITDB_ROOT_PASSWORD: "$MONGO_PASSWORD"
"@ | Out-File -FilePath "secrets-production.yaml" -Encoding utf8

Write-Host "  Created secrets-production.yaml" -ForegroundColor Green
Write-Host "[7/9] Secrets prepared" -ForegroundColor Green
Write-Host ""

# ----------------------------------------------------------------------------
# Step 8: Deploy to Kubernetes
# ----------------------------------------------------------------------------
if (!$SkipDeploy) {
    Write-Host "[8/9] Deploying to Kubernetes..." -ForegroundColor Yellow
    Set-Location "$ProjectRoot\k8s"
    
    # Get ECR URLs from Terraform
    Set-Location "$ProjectRoot\terraform"
    $ECR_BACKEND = terraform output -raw ecr_backend_url
    $ECR_FRONTEND = terraform output -raw ecr_frontend_url
    $VPC_CIDR = terraform output -raw vpc_cidr
    Set-Location "$ProjectRoot\k8s"
    
    # Create namespace
    Write-Host "Creating namespace..." -ForegroundColor Gray
    kubectl apply -f namespace.yaml
    
    # Apply secrets
    Write-Host "Applying secrets..." -ForegroundColor Gray
    kubectl apply -f secrets-production.yaml
    
    # Apply configmap
    Write-Host "Applying configmap..." -ForegroundColor Gray
    kubectl apply -f configmap.yaml
    
    # Deploy MongoDB
    Write-Host "Deploying MongoDB..." -ForegroundColor Gray
    kubectl apply -f mongodb.yaml
    
    Write-Host "Waiting for MongoDB to be ready..." -ForegroundColor Gray
    kubectl wait --for=condition=ready pod -l app=mongodb -n student-counsellor --timeout=300s
    
    # Generate backend manifest with ECR URL
    Write-Host "Generating backend manifest..." -ForegroundColor Gray
    (Get-Content "backend.yaml" -Raw) `
        -replace '\$\{AWS_ACCOUNT_ID\}', $AWS_ACCOUNT_ID `
        -replace '\$\{AWS_REGION\}', $Region `
        | Out-File -FilePath "backend-deploy.yaml" -Encoding utf8
    
    # Deploy backend
    Write-Host "Deploying backend..." -ForegroundColor Gray
    kubectl apply -f backend-deploy.yaml
    
    # Generate frontend manifest with ECR URL
    Write-Host "Generating frontend manifest..." -ForegroundColor Gray
    (Get-Content "frontend.yaml" -Raw) `
        -replace '\$\{AWS_ACCOUNT_ID\}', $AWS_ACCOUNT_ID `
        -replace '\$\{AWS_REGION\}', $Region `
        | Out-File -FilePath "frontend-deploy.yaml" -Encoding utf8
    
    # Deploy frontend
    Write-Host "Deploying frontend..." -ForegroundColor Gray
    kubectl apply -f frontend-deploy.yaml
    
    # Update network policy with VPC CIDR for ALB
    Write-Host "Updating network policy for ALB..." -ForegroundColor Gray
    (Get-Content "network-policy.yaml" -Raw) `
        -replace '10\.0\.0\.0/16', $VPC_CIDR `
        | Out-File -FilePath "network-policy-deploy.yaml" -Encoding utf8
    kubectl apply -f network-policy-deploy.yaml
    
    # Deploy ingress
    Write-Host "Deploying ingress (ALB)..." -ForegroundColor Gray
    kubectl apply -f ingress.yaml
    
    Write-Host "Waiting for deployments to be ready..." -ForegroundColor Gray
    kubectl wait --for=condition=available deployment/backend -n student-counsellor --timeout=300s
    kubectl wait --for=condition=available deployment/frontend -n student-counsellor --timeout=300s
    
    Write-Host "[8/9] Kubernetes deployment complete" -ForegroundColor Green
} else {
    Write-Host "[8/9] Skipping deployment (--SkipDeploy)" -ForegroundColor Gray
}
Write-Host ""

# ----------------------------------------------------------------------------
# Step 9: Seed Database and Get URL
# ----------------------------------------------------------------------------
Write-Host "[9/9] Finalizing deployment..." -ForegroundColor Yellow

# Seed database
Write-Host "Seeding database with initial data..." -ForegroundColor Gray
$backendPod = kubectl get pods -n student-counsellor -l app=backend -o jsonpath='{.items[0].metadata.name}'
kubectl exec $backendPod -n student-counsellor -- python -m app.seed_data

# Wait for ALB to be ready
Write-Host "Waiting for ALB to be provisioned (this may take 2-3 minutes)..." -ForegroundColor Gray
Start-Sleep -Seconds 30

$maxAttempts = 20
$attempt = 0
$albUrl = ""

while ($attempt -lt $maxAttempts) {
    $attempt++
    $albUrl = kubectl get ingress student-counsellor-ingress -n student-counsellor -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>$null
    
    if ($albUrl) {
        break
    }
    
    Write-Host "  Attempt $attempt/$maxAttempts - ALB not ready yet..." -ForegroundColor Gray
    Start-Sleep -Seconds 15
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

if ($albUrl) {
    Write-Host "Application URL: http://$albUrl" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Note: DNS propagation may take a few minutes." -ForegroundColor Yellow
    Write-Host "If the URL doesn't work immediately, wait 2-3 minutes." -ForegroundColor Yellow
} else {
    Write-Host "ALB URL not yet available. Check with:" -ForegroundColor Yellow
    Write-Host "  kubectl get ingress -n student-counsellor" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Default Login Credentials:" -ForegroundColor Cyan
Write-Host "  Super Admin:  super.admin@counsellor.app / SuperAdmin123!"
Write-Host "  Admin:        admin@stateuniversity.edu / Admin123!"
Write-Host "  Counsellor:   dr.sarah.johnson@stateuniversity.edu / Counsellor123!"
Write-Host "  Student:      john.doe@stateuniversity.edu / Student123!"
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  kubectl get pods -n student-counsellor    # Check pod status"
Write-Host "  kubectl logs -f deployment/backend -n student-counsellor  # Backend logs"
Write-Host "  kubectl logs -f deployment/frontend -n student-counsellor # Frontend logs"
Write-Host ""
Write-Host "To destroy all resources:" -ForegroundColor Yellow
Write-Host "  .\deploy-aws.ps1 -Destroy"
Write-Host ""

Set-Location $ProjectRoot
