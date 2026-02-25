#!/bin/bash

################################################################################
# Terraform CI/CD AWS Setup Script
#
# Sets up AWS infrastructure for Terraform CI/CD:
# - OIDC Identity Provider for GitHub Actions
# - IAM Roles with appropriate permissions (ACM, Lambda, CloudWatch Logs, EC2, ECS, etc.)
# - S3 Buckets for Terraform state storage
# - DynamoDB Tables for Terraform state locking
#
# Prerequisites:
# - AWS CLI installed and configured
# - AWS SSO profiles configured in ~/.aws/config for each account
# - Permissions to create IAM, S3, and DynamoDB resources
#
# Usage:
#   # Use default SSO profile names (globode-tools, globode-dev, globode-prod)
#   ./scripts/setup-terraform-cicd-aws.sh
#
#   # Or specify custom profile names via environment variables
#   TOOLS_AWS_PROFILE=my-tools-profile DEV_AWS_PROFILE=my-dev-profile ./scripts/setup-terraform-cicd-aws.sh
################################################################################

set -euo pipefail

################################################################################
# CONFIGURATION
################################################################################




# AWS Account IDs
readonly TOOLS_ACCOUNT_ID="998510721721"
readonly DEV_ACCOUNT_ID="347026173710"
readonly PROD_ACCOUNT_ID="278820798396"

# AWS Region
readonly AWS_REGION="eu-west-2"

# Project/repo naming (must be explicitly set to avoid accidental deploys).
# Set these via environment variables before running, for example:
#   PROJECT_NAME=payme GITHUB_REPO=payme GITHUB_ORG=pubsrc ./scripts/setup-terraform-cicd-aws.sh
readonly PROJECT_NAME="payme"

# GitHub repository (must be explicit)
readonly GITHUB_ORG="pubsrc"
readonly GITHUB_REPO="quidme"

: "${PROJECT_NAME:?Missing PROJECT_NAME. Set explicitly to the target project name.}"
: "${GITHUB_REPO:?Missing GITHUB_REPO. Set explicitly to the target GitHub repo.}"
: "${GITHUB_ORG:?Missing GITHUB_ORG. Set explicitly to the target GitHub org.}"

# OIDC Configuration
readonly OIDC_PROVIDER_URL="token.actions.githubusercontent.com"
readonly OIDC_AUDIENCE="sts.amazonaws.com"

# AWS Profile Names (defaults to globode-* profiles, can be overridden via env vars)
readonly TOOLS_AWS_PROFILE="${TOOLS_AWS_PROFILE:-globode-tools}"
readonly DEV_AWS_PROFILE="${DEV_AWS_PROFILE:-globode-dev}"
readonly PROD_AWS_PROFILE="${PROD_AWS_PROFILE:-globode-prod}"

# Login to SSO profiles
aws sso login --profile "$TOOLS_AWS_PROFILE"
aws sso login --profile "$DEV_AWS_PROFILE"
aws sso login --profile "$PROD_AWS_PROFILE"

# Resource Names
readonly TOOLS_IAM_ROLE_NAME="${TOOLS_IAM_ROLE_NAME:-github-actions-terraform-${PROJECT_NAME}-tools}"
readonly DEV_IAM_ROLE_NAME="${DEV_IAM_ROLE_NAME:-github-actions-terraform-${PROJECT_NAME}-dev}"
readonly PROD_IAM_ROLE_NAME="${PROD_IAM_ROLE_NAME:-github-actions-terraform-${PROJECT_NAME}-prod}"

readonly TOOLS_STATE_BUCKET="${TOOLS_STATE_BUCKET:-${PROJECT_NAME}-terraform-state-tools-${TOOLS_ACCOUNT_ID}}"
readonly DEV_STATE_BUCKET="${DEV_STATE_BUCKET:-${PROJECT_NAME}-terraform-state-dev-${DEV_ACCOUNT_ID}}"
readonly PROD_STATE_BUCKET="${PROD_STATE_BUCKET:-${PROJECT_NAME}-terraform-state-prod-${PROD_ACCOUNT_ID}}"

readonly TOOLS_LOCK_TABLE="${TOOLS_LOCK_TABLE:-${PROJECT_NAME}-terraform-lock-tools}"
readonly DEV_LOCK_TABLE="${DEV_LOCK_TABLE:-${PROJECT_NAME}-terraform-lock-dev}"
readonly PROD_LOCK_TABLE="${PROD_LOCK_TABLE:-${PROJECT_NAME}-terraform-lock-prod}"

################################################################################
# HELPER FUNCTIONS
################################################################################

# Get AWS CLI command for specific account
get_aws_cmd() {
    local account_type=$1
    local cmd=$2
    
    # Convert account_type to uppercase for variable name (bash 3+ compatible)
    local profile_var
    case "$account_type" in
        tools) profile_var="TOOLS_AWS_PROFILE" ;;
        dev) profile_var="DEV_AWS_PROFILE" ;;
        prod) profile_var="PROD_AWS_PROFILE" ;;
        *) profile_var="" ;;
    esac
    
    local profile="${!profile_var}"
    
    if [ -n "$profile" ]; then
        echo "aws --profile $profile --region $AWS_REGION $cmd"
    else
        echo "aws --region $AWS_REGION $cmd"
    fi
}

# Check if resource exists
resource_exists() {
    local account_type=$1
    local resource_type=$2
    local resource_name=$3
    
    local aws_cmd=$(get_aws_cmd "$account_type" "")
    
    case $resource_type in
        "oidc")
            eval "$aws_cmd iam list-open-id-connect-providers" 2>/dev/null | grep -q "$OIDC_PROVIDER_URL" && return 0 || return 1
            ;;
        "role")
            eval "$aws_cmd iam get-role --role-name \"$resource_name\"" >/dev/null 2>&1 && return 0 || return 1
            ;;
        "bucket")
            eval "$aws_cmd s3api head-bucket --bucket \"$resource_name\"" >/dev/null 2>&1 && return 0 || return 1
            ;;
        "table")
            eval "$aws_cmd dynamodb describe-table --table-name \"$resource_name\"" >/dev/null 2>&1 && return 0 || return 1
            ;;
    esac
}

################################################################################
# CREATE OIDC IDENTITY PROVIDER
################################################################################

create_oidc_provider() {
    local account_type=$1
    local account_id=$2
    
    echo ""
    echo "========================================="
    echo "OIDC Provider: $account_type account ($account_id)"
    echo "========================================="
    
    local aws_cmd=$(get_aws_cmd "$account_type" "")
    
    if resource_exists "$account_type" "oidc" ""; then
        echo "✓ OIDC provider already exists"
        return 0
    fi
    
    echo "Fetching GitHub OIDC provider thumbprint..."
    local thumbprint=$(echo | openssl s_client -servername $OIDC_PROVIDER_URL -showcerts -connect $OIDC_PROVIDER_URL:443 2>/dev/null | \
        openssl x509 -fingerprint -noout -sha1 2>/dev/null | \
        sed 's/.*Fingerprint=\(.*\)/\1/' | \
        sed 's/://g' | \
        tr '[:upper:]' '[:lower:]')
    
    if [ -z "$thumbprint" ] || [ ${#thumbprint} -ne 40 ]; then
        echo "Warning: Could not fetch thumbprint. Using known GitHub thumbprint."
        thumbprint="6938fd4d98bab03faadb97b34396831e3780aea1"
    fi
    
    echo "Creating OIDC identity provider..."
    eval "$aws_cmd iam create-open-id-connect-provider \
        --url \"https://${OIDC_PROVIDER_URL}\" \
        --client-id-list \"$OIDC_AUDIENCE\" \
        --thumbprint-list \"$thumbprint\"" \
        >/dev/null
    
    echo "✓ OIDC provider created"
}

################################################################################
# CREATE IAM ROLE WITH PERMISSIONS
################################################################################

create_iam_role() {
    local account_type=$1
    local account_id=$2
    local role_name=$3
    
    echo ""
    echo "========================================="
    echo "IAM Role: $account_type account - $role_name"
    echo "========================================="
    
    local aws_cmd=$(get_aws_cmd "$account_type" "")
    
    # Trust policy for GitHub OIDC
    local trust_policy=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${account_id}:oidc-provider/${OIDC_PROVIDER_URL}"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "${OIDC_PROVIDER_URL}:aud": "${OIDC_AUDIENCE}"
        },
        "StringLike": {
          "${OIDC_PROVIDER_URL}:sub": "repo:${GITHUB_ORG}/${GITHUB_REPO}:*"
        }
      }
    }
  ]
}
EOF
)
    
    # Permissions policy with all required actions
    local permissions_policy=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TerraformStateAccess",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketVersioning",
        "s3:GetBucketAcl",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::terraform-state-*",
        "arn:aws:s3:::${PROJECT_NAME}-terraform-state-*"
      ]
    },
    {
      "Sid": "TerraformStateObjectAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::terraform-state-*/*",
        "arn:aws:s3:::${PROJECT_NAME}-terraform-state-*/*"
      ]
    },
    {
      "Sid": "TerraformStateLock",
      "Effect": "Allow",
      "Action": [
        "dynamodb:DescribeTable",
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:${AWS_REGION}:${account_id}:table/terraform-state-lock-*",
        "arn:aws:dynamodb:${AWS_REGION}:${account_id}:table/${PROJECT_NAME}-terraform-lock-*"
      ]
    },
    {
      "Sid": "S3BucketManagement",
      "Effect": "Allow",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::${PROJECT_NAME}-frontend-*",
        "arn:aws:s3:::${PROJECT_NAME}-frontend-*/*"
      ]
    },
    {
      "Sid": "S3ObjectManagement",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:GetObjectVersion",
        "s3:DeleteObjectVersion"
      ],
      "Resource": "arn:aws:s3:::${PROJECT_NAME}-frontend-*/*"
    },
    {
      "Sid": "CloudFrontManagement",
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateDistribution",
        "cloudfront:UpdateDistribution",
        "cloudfront:DeleteDistribution",
        "cloudfront:GetDistribution",
        "cloudfront:ListDistributions",
        "cloudfront:CreateOriginAccessControl",
        "cloudfront:UpdateOriginAccessControl",
        "cloudfront:DeleteOriginAccessControl",
        "cloudfront:GetOriginAccessControl",
        "cloudfront:ListOriginAccessControls",
        "cloudfront:CreateInvalidation",
        "cloudfront:GetInvalidation",
        "cloudfront:ListInvalidations",
        "cloudfront:TagResource",
        "cloudfront:UntagResource",
        "cloudfront:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SSMParameterStore",
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:PutParameter",
        "ssm:DeleteParameter",
        "ssm:DeleteParameters",
        "ssm:AddTagsToResource",
        "ssm:RemoveTagsFromResource",
        "ssm:ListTagsForResource"
      ],
      "Resource": "arn:aws:ssm:${AWS_REGION}:${account_id}:parameter/${PROJECT_NAME}/*"
    },
    {
      "Sid": "SSMParameterStoreDescribe",
      "Effect": "Allow",
      "Action": [
        "ssm:DescribeParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "*"
    },
    {
      "Sid": "TerraformResourceManagement",
      "Effect": "Allow",
      "Action": [
        "acm:*",
        "budgets:*",
        "cognito-idp:*",
        "secretsmanager:*",
        "ec2:*",
        "ecs:*",
        "ecr:*",
        "rds:*",
        "lambda:*",
        "logs:*",
        "cloudwatch:PutDashboard",
        "cloudwatch:GetDashboard",
        "cloudwatch:DeleteDashboards",
        "cloudwatch:ListDashboards",
        "events:*",
        "s3:*",
        "elasticloadbalancing:*",
        "iam:GetRole",
        "iam:ListRoles",
        "iam:PassRole",
        "iam:GetPolicy",
        "iam:ListPolicies",
        "iam:CreatePolicy",
        "iam:DeletePolicy",
        "iam:CreatePolicyVersion",
        "iam:DeletePolicyVersion",
        "iam:GetPolicyVersion",
        "iam:ListPolicyVersions",
        "iam:SetDefaultPolicyVersion",
        "iam:TagPolicy",
        "iam:UntagPolicy",
        "iam:ListPolicyTags",
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:UpdateRole",
        "iam:UpdateAssumeRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRolePolicy",
        "iam:ListRolePolicies",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:ListAttachedRolePolicies",
        "iam:DeleteServiceLinkedRole",
        "iam:GetServiceLinkedRoleDeletionStatus",
        "iam:TagRole",
        "iam:UntagRole",
        "iam:ListRoleTags",
        "iam:GetInstanceProfile",
        "iam:ListInstanceProfiles",
        "iam:CreateInstanceProfile",
        "iam:DeleteInstanceProfile",
        "iam:AddRoleToInstanceProfile",
        "iam:RemoveRoleFromInstanceProfile",
        "iam:GetInstanceProfileTags",
        "iam:TagInstanceProfile",
        "iam:UntagInstanceProfile"
      ],
      "Resource": "*"
    }
  ]
}
EOF
)
    
    if resource_exists "$account_type" "role" "$role_name"; then
        echo "✓ IAM role already exists, updating policies..."
        
        echo "$trust_policy" | eval "$aws_cmd iam update-assume-role-policy \
            --role-name \"$role_name\" \
            --policy-document file:///dev/stdin" >/dev/null
        
        echo "$permissions_policy" | eval "$aws_cmd iam put-role-policy \
            --role-name \"$role_name\" \
            --policy-name \"TerraformOperationsPolicy\" \
            --policy-document file:///dev/stdin" >/dev/null
        
        echo "✓ Policies updated"
    else
        echo "Creating IAM role..."
        echo "$trust_policy" | eval "$aws_cmd iam create-role \
            --role-name \"$role_name\" \
            --assume-role-policy-document file:///dev/stdin \
            --description \"IAM role for GitHub Actions to run Terraform in $account_type environment\"" >/dev/null
        
        echo "Attaching permissions policy..."
        echo "$permissions_policy" | eval "$aws_cmd iam put-role-policy \
            --role-name \"$role_name\" \
            --policy-name \"TerraformOperationsPolicy\" \
            --policy-document file:///dev/stdin" >/dev/null
        
        echo "✓ IAM role created"
    fi
    
    local role_arn=$(eval "$aws_cmd iam get-role --role-name \"$role_name\" --query 'Role.Arn' --output text")
    echo "✓ Role ARN: $role_arn"
}

################################################################################
# CREATE S3 BUCKET FOR TERRAFORM STATE
################################################################################

create_s3_bucket() {
    local account_type=$1
    local account_id=$2
    local bucket_name=$3
    
    echo ""
    echo "========================================="
    echo "S3 Bucket: $account_type account - $bucket_name"
    echo "========================================="
    
    local aws_cmd=$(get_aws_cmd "$account_type" "")
    
    if resource_exists "$account_type" "bucket" "$bucket_name"; then
        echo "✓ S3 bucket already exists"
        return 0
    fi
    
    echo "Creating S3 bucket..."
    if [ "$AWS_REGION" = "us-east-1" ]; then
        eval "$aws_cmd s3api create-bucket --bucket \"$bucket_name\" --region \"$AWS_REGION\"" >/dev/null
    else
        eval "$aws_cmd s3api create-bucket \
            --bucket \"$bucket_name\" \
            --region \"$AWS_REGION\" \
            --create-bucket-configuration LocationConstraint=\"$AWS_REGION\"" >/dev/null
    fi
    
    echo "Configuring bucket..."
    eval "$aws_cmd s3api put-bucket-versioning \
        --bucket \"$bucket_name\" \
        --versioning-configuration Status=Enabled" >/dev/null
    
    eval "$aws_cmd s3api put-bucket-encryption \
        --bucket \"$bucket_name\" \
        --server-side-encryption-configuration '{\"Rules\":[{\"ApplyServerSideEncryptionByDefault\":{\"SSEAlgorithm\":\"AES256\"}}]}'" >/dev/null
    
    eval "$aws_cmd s3api put-public-access-block \
        --bucket \"$bucket_name\" \
        --public-access-block-configuration \
        \"BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true\"" >/dev/null
    
    echo "✓ S3 bucket configured"
}

################################################################################
# CREATE DYNAMODB TABLE FOR STATE LOCKING
################################################################################

create_dynamodb_table() {
    local account_type=$1
    local account_id=$2
    local table_name=$3
    
    echo ""
    echo "========================================="
    echo "DynamoDB Table: $account_type account - $table_name"
    echo "========================================="
    
    local aws_cmd=$(get_aws_cmd "$account_type" "")
    
    if resource_exists "$account_type" "table" "$table_name"; then
        echo "✓ DynamoDB table already exists"
        return 0
    fi
    
    echo "Creating DynamoDB table..."
    eval "$aws_cmd dynamodb create-table \
        --table-name \"$table_name\" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region \"$AWS_REGION\"" >/dev/null
    
    eval "$aws_cmd dynamodb wait table-exists --table-name \"$table_name\"" >/dev/null
    
    echo "✓ DynamoDB table created"
}

################################################################################
# MAIN EXECUTION
################################################################################

main() {
    echo "################################################################################"
    echo "# Terraform CI/CD AWS Setup"
    echo "################################################################################"
    echo ""
    echo "Configuration:"
    echo "  Project Name:  $PROJECT_NAME"
    echo "  Tools Account: $TOOLS_ACCOUNT_ID (profile: $TOOLS_AWS_PROFILE)"
    echo "  Dev Account:  $DEV_ACCOUNT_ID (profile: $DEV_AWS_PROFILE)"
    echo "  Prod Account: $PROD_ACCOUNT_ID (profile: $PROD_AWS_PROFILE)"
    echo "  AWS Region:   $AWS_REGION"
    echo "  GitHub Repo:  $GITHUB_ORG/$GITHUB_REPO"
    echo ""
    
    read -p "Continue with setup? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    # Setup Tools Account
    echo ""
    echo "################################################################################"
    echo "# TOOLS ACCOUNT"
    echo "################################################################################"
    create_oidc_provider "tools" "$TOOLS_ACCOUNT_ID"
    create_iam_role "tools" "$TOOLS_ACCOUNT_ID" "$TOOLS_IAM_ROLE_NAME"
    create_s3_bucket "tools" "$TOOLS_ACCOUNT_ID" "$TOOLS_STATE_BUCKET"
    create_dynamodb_table "tools" "$TOOLS_ACCOUNT_ID" "$TOOLS_LOCK_TABLE"
    
    # Setup Dev Account
    echo ""
    echo "################################################################################"
    echo "# DEV ACCOUNT"
    echo "################################################################################"
    create_oidc_provider "dev" "$DEV_ACCOUNT_ID"
    create_iam_role "dev" "$DEV_ACCOUNT_ID" "$DEV_IAM_ROLE_NAME"
    create_s3_bucket "dev" "$DEV_ACCOUNT_ID" "$DEV_STATE_BUCKET"
    create_dynamodb_table "dev" "$DEV_ACCOUNT_ID" "$DEV_LOCK_TABLE"
    
    # Setup Prod Account
    echo ""
    echo "################################################################################"
    echo "# PROD ACCOUNT"
    echo "################################################################################"
    create_oidc_provider "prod" "$PROD_ACCOUNT_ID"
    create_iam_role "prod" "$PROD_ACCOUNT_ID" "$PROD_IAM_ROLE_NAME"
    create_s3_bucket "prod" "$PROD_ACCOUNT_ID" "$PROD_STATE_BUCKET"
    create_dynamodb_table "prod" "$PROD_ACCOUNT_ID" "$PROD_LOCK_TABLE"
    
    echo ""
    echo "################################################################################"
    echo "# SETUP COMPLETE!"
    echo "################################################################################"
    echo ""
    echo "Next steps:"
    echo "1. Note the IAM Role ARNs displayed above"
    echo "2. Configure GitHub Environments: Settings > Environments"
    echo "3. Add 'AWS_ROLE_ARN' variable to each environment"
    echo "4. Test the CI/CD pipeline!"
    echo ""
}

main
