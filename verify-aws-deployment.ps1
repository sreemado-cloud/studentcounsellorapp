# ============================================================================
# AWS EKS Deployment Verification Script
# ============================================================================
# This script verifies the deployment is healthy
# Run from project root: .\verify-aws-deployment.ps1
# ============================================================================

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AWS EKS Deployment Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check kubectl connection
Write-Host "[1/6] Checking cluster connection..." -ForegroundColor Yellow
try {
    $nodes = kubectl get nodes -o json | ConvertFrom-Json
    $nodeCount = $nodes.items.Count
    Write-Host "  Cluster: Connected ($nodeCount nodes)" -ForegroundColor Green
    foreach ($node in $nodes.items) {
        $nodeName = $node.metadata.name
        $nodeStatus = ($node.status.conditions | Where-Object { $_.type -eq "Ready" }).status
        $statusColor = if ($nodeStatus -eq "True") { "Green" } else { "Red" }
        Write-Host "    - $nodeName : Ready=$nodeStatus" -ForegroundColor $statusColor
    }
} catch {
    Write-Host "  ERROR: Cannot connect to cluster" -ForegroundColor Red
    Write-Host "  Run: aws eks update-kubeconfig --region <region> --name <cluster>" -ForegroundColor Gray
    exit 1
}
Write-Host ""

# Check namespace
Write-Host "[2/6] Checking namespace..." -ForegroundColor Yellow
$namespace = kubectl get namespace student-counsellor -o json 2>$null | ConvertFrom-Json
if ($namespace) {
    Write-Host "  Namespace: student-counsellor exists" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Namespace 'student-counsellor' not found" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check pods
Write-Host "[3/6] Checking pods..." -ForegroundColor Yellow
$pods = kubectl get pods -n student-counsellor -o json | ConvertFrom-Json
$podTable = @()
foreach ($pod in $pods.items) {
    $podName = $pod.metadata.name
    $podStatus = $pod.status.phase
    $containerStatuses = $pod.status.containerStatuses
    $ready = if ($containerStatuses -and $containerStatuses[0].ready) { "Yes" } else { "No" }
    $restarts = if ($containerStatuses) { $containerStatuses[0].restartCount } else { 0 }
    
    $statusColor = switch ($podStatus) {
        "Running" { "Green" }
        "Pending" { "Yellow" }
        default { "Red" }
    }
    
    Write-Host "  $podName" -ForegroundColor $statusColor
    Write-Host "    Status: $podStatus | Ready: $ready | Restarts: $restarts" -ForegroundColor Gray
}
Write-Host ""

# Check services
Write-Host "[4/6] Checking services..." -ForegroundColor Yellow
$services = kubectl get svc -n student-counsellor -o json | ConvertFrom-Json
foreach ($svc in $services.items) {
    $svcName = $svc.metadata.name
    $svcType = $svc.spec.type
    $svcPorts = ($svc.spec.ports | ForEach-Object { "$($_.port):$($_.targetPort)" }) -join ", "
    Write-Host "  $svcName ($svcType): $svcPorts" -ForegroundColor Green
}
Write-Host ""

# Check ingress/ALB
Write-Host "[5/6] Checking Ingress (ALB)..." -ForegroundColor Yellow
$ingress = kubectl get ingress student-counsellor-ingress -n student-counsellor -o json 2>$null | ConvertFrom-Json
if ($ingress) {
    $albHostname = $ingress.status.loadBalancer.ingress[0].hostname
    if ($albHostname) {
        Write-Host "  ALB Hostname: $albHostname" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Application URL: http://$albHostname" -ForegroundColor Cyan
    } else {
        Write-Host "  ALB: Provisioning (wait 2-3 minutes)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ERROR: Ingress not found" -ForegroundColor Red
}
Write-Host ""

# Check deployments
Write-Host "[6/6] Checking deployments..." -ForegroundColor Yellow
$deployments = @("backend", "frontend")
foreach ($dep in $deployments) {
    $deployment = kubectl get deployment $dep -n student-counsellor -o json 2>$null | ConvertFrom-Json
    if ($deployment) {
        $ready = $deployment.status.readyReplicas
        $desired = $deployment.spec.replicas
        $statusColor = if ($ready -eq $desired) { "Green" } else { "Yellow" }
        Write-Host "  $dep : $ready/$desired replicas ready" -ForegroundColor $statusColor
    } else {
        Write-Host "  $dep : NOT FOUND" -ForegroundColor Red
    }
}
Write-Host ""

# Health check
Write-Host "[HEALTH CHECK] Testing endpoints..." -ForegroundColor Yellow
if ($albHostname) {
    # Test frontend
    try {
        $frontendResponse = Invoke-WebRequest -Uri "http://$albHostname/" -TimeoutSec 10 -UseBasicParsing
        Write-Host "  Frontend (/): $($frontendResponse.StatusCode) OK" -ForegroundColor Green
    } catch {
        Write-Host "  Frontend (/): FAILED - $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Test backend health
    try {
        $healthResponse = Invoke-WebRequest -Uri "http://$albHostname/health" -TimeoutSec 10 -UseBasicParsing
        Write-Host "  Backend (/health): $($healthResponse.StatusCode) OK" -ForegroundColor Green
    } catch {
        Write-Host "  Backend (/health): FAILED - $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Test API
    try {
        $apiResponse = Invoke-WebRequest -Uri "http://$albHostname/api/health" -TimeoutSec 10 -UseBasicParsing
        Write-Host "  API (/api/health): $($apiResponse.StatusCode) OK" -ForegroundColor Green
    } catch {
        Write-Host "  API (/api/health): May not be defined, checking auth..." -ForegroundColor Yellow
        try {
            $authResponse = Invoke-WebRequest -Uri "http://$albHostname/api/auth/me" -TimeoutSec 10 -UseBasicParsing
        } catch {
            if ($_.Exception.Response.StatusCode -eq 401) {
                Write-Host "  API (/api/auth/me): 401 Unauthorized (API is working)" -ForegroundColor Green
            }
        }
    }
} else {
    Write-Host "  Skipping health checks - ALB not ready yet" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verification Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Gray
Write-Host "  kubectl logs -f deployment/backend -n student-counsellor   # Backend logs"
Write-Host "  kubectl logs -f deployment/frontend -n student-counsellor  # Frontend logs"
Write-Host "  kubectl describe pod <pod-name> -n student-counsellor      # Pod details"
Write-Host "  kubectl get events -n student-counsellor --sort-by='.lastTimestamp'  # Events"
Write-Host ""
