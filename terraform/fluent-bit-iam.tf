# IAM role for Fluent Bit (for high-isolation log routing)
# Only needed when using SAAS_ISOLATION_LEVEL=high

data "aws_iam_policy_document" "fluent_bit_assume" {
  statement {
    sid     = "AssumeRoleWithWebIdentity"
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [module.eks.oidc_provider_arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${module.eks.oidc_provider}:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "${module.eks.oidc_provider}:sub"
      values   = ["system:serviceaccount:student-counsellor:fluent-bit"]
    }
  }
}

resource "aws_iam_role" "fluent_bit" {
  count              = var.enable_high_isolation_logging ? 1 : 0
  name               = "fluent-bit-${var.cluster_name}"
  assume_role_policy = data.aws_iam_policy_document.fluent_bit_assume.json
}

# IAM policy for Fluent Bit to write to CloudWatch Logs
resource "aws_iam_policy" "fluent_bit" {
  count       = var.enable_high_isolation_logging ? 1 : 0
  name        = "FluentBitCloudWatch-${var.cluster_name}"
  description = "IAM policy for Fluent Bit to write to CloudWatch Logs"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = [
          "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/eks/${var.cluster_name}/tenant-*",
          "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/eks/${var.cluster_name}/tenant-*:*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "fluent_bit" {
  count      = var.enable_high_isolation_logging ? 1 : 0
  role       = aws_iam_role.fluent_bit[0].name
  policy_arn = aws_iam_policy.fluent_bit[0].arn
}

output "fluent_bit_role_arn" {
  description = "IAM role ARN for Fluent Bit (for high-isolation log routing)"
  value       = var.enable_high_isolation_logging ? aws_iam_role.fluent_bit[0].arn : null
}
