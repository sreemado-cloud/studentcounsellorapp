data "aws_caller_identity" "current" {}
data "aws_availability_zones" "available" { state = "available" }

locals {
  azs = slice(data.aws_availability_zones.available.names, 0, var.availability_zones_count)
}
