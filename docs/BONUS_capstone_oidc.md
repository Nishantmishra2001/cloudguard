# Bonus: Capstone me long-lived AWS access keys hatao (GitHub OIDC)

Capstone README me `AdministratorAccess` wala IAM user aur `AWS_ACCESS_KEY_ID/SECRET` GitHub Secrets me rakhne ko kaha hai. Real companies me yeh pasand nahi kiya jaata (key leak ho sakti hai). Alternative: **OIDC**. GitHub Actions har run pe temporary credentials leta hai, koi stored key nahi.

> Yeh bonus hai aur maine isko test nahi kiya. Pehle CloudGuard ke steps poore karo. Isko tab karo jab time ho.

## 1. Terraform (capstone `infra/terraform` me naya file `oidc.tf`)

```hcl
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

data "aws_iam_policy_document" "github_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:Nishantmishra2001/Devops-Capstone:ref:refs/heads/main"]
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name               = "devops-capstone-github-actions"
  assume_role_policy = data.aws_iam_policy_document.github_trust.json
}
```

Role ko sirf wahi permissions do jo pipeline ko chahiye (S3, Lambda, CloudFront, API Gateway, SNS, DynamoDB/state bucket). Pehle `AdministratorAccess` attach karke kaam chalao, phir dheere dheere kam karo.
Pehli baar yeh role tumhe apne local admin credentials se `terraform apply` karke banana padega (chicken-and-egg).

## 2. Workflow me badlav (har workflow file jo AWS use karti hai)

```yaml
permissions:
  id-token: write
  contents: read

steps:
  - uses: actions/checkout@v4
  - uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::<ACCOUNT_ID>:role/devops-capstone-github-actions
      aws-region: us-east-1
```

Ab `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` secrets hata sakte ho, aur IAM user delete kar do.

## Interview line
"Capstone me stored access keys ki jagah GitHub OIDC se short-lived credentials use kiye."
