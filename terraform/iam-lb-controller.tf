# IAM role for AWS Load Balancer Controller (IRSA).
# After Terraform apply, install the controller with Helm and use this role ARN
# for the service account (see EKS_TERRAFORM_DEPLOYMENT.md).

data "http" "lb_controller_iam_policy" {
  url = "https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.2/docs/install/iam_policy.json"
}

resource "aws_iam_policy" "lb_controller" {
  name        = "AWSLoadBalancerController-${var.cluster_name}"
  description = "IAM policy for AWS Load Balancer Controller"
  policy      = data.http.lb_controller_iam_policy.response_body
}

data "aws_iam_policy_document" "lb_controller_assume" {
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
      values   = ["system:serviceaccount:kube-system:aws-load-balancer-controller"]
    }
  }
}

resource "aws_iam_role" "lb_controller" {
  name               = "aws-load-balancer-controller-${var.cluster_name}"
  assume_role_policy = data.aws_iam_policy_document.lb_controller_assume.json
}

resource "aws_iam_role_policy_attachment" "lb_controller" {
  role       = aws_iam_role.lb_controller.name
  policy_arn = aws_iam_policy.lb_controller.arn
}

output "lb_controller_role_arn" {
  description = "IAM role ARN for AWS Load Balancer Controller (use with Helm serviceAccount.annotations)"
  value       = aws_iam_role.lb_controller.arn
}
