variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g. production, staging)"
  type        = string
  default     = "production"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "student-counsellor"
}

variable "kubernetes_version" {
  description = "Kubernetes version for the EKS cluster"
  type        = string
  default     = "1.30"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones_count" {
  description = "Number of AZs to use (2 or 3)"
  type        = number
  default     = 3
}

variable "node_instance_types" {
  description = "EC2 instance types for EKS managed node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  description = "Desired number of nodes in the node group"
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "Minimum number of nodes in the node group"
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Maximum number of nodes in the node group"
  type        = number
  default     = 5
}

variable "enable_cluster_creator_admin" {
  description = "Grant cluster creator (Terraform caller) admin access to EKS"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use a single NAT gateway to reduce cost (less HA)"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags for all resources"
  type        = map(string)
  default     = {}
}

variable "enable_high_isolation_logging" {
  description = "Enable separate log groups per tenant (required for SAAS_ISOLATION_LEVEL=high)"
  type        = bool
  default     = false
}
