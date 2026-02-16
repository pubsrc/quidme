data "aws_region" "current" {}

locals {
  tags = {
    Environment = "prod"
    ManagedBy   = "terraform"
    Project     = var.project_name
  }

  callback_urls_value = length(var.callback_urls_default) > 0 ? var.callback_urls_default : [
    var.payme_base_url_default,
  ]
  logout_urls_value = length(var.logout_urls_default) > 0 ? var.logout_urls_default : [
    var.payme_base_url_default,
  ]

  frontend_manage_certificate = length(var.frontend_domain_aliases) > 0 && trimspace(var.frontend_acm_certificate_arn) == ""
  frontend_certificate_arn    = local.frontend_manage_certificate ? aws_acm_certificate_validation.frontend[0].certificate_arn : var.frontend_acm_certificate_arn
  api_manage_certificate      = trimspace(var.api_acm_certificate_arn) == ""
  api_certificate_arn         = local.api_manage_certificate ? aws_acm_certificate_validation.api[0].certificate_arn : var.api_acm_certificate_arn
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = var.lambda_source_dir
  output_path = "${path.module}/.tmp/${var.project_name}.zip"
}

module "dynamodb" {
  source       = "../../modules/dynamodb"
  project_name = var.project_name
  tags         = local.tags
}

module "secrets" {
  source = "../../modules/secrets"

  stripe_secret_name                = "${var.project_name}-stripe-api-key"
  stripe_secret_placeholder         = var.stripe_secret_placeholder
  stripe_webhook_secret_name        = "${var.project_name}-stripe-webhook-secret"
  stripe_webhook_secret_placeholder = var.stripe_webhook_secret_placeholder
  google_oauth_secret_name          = "${var.project_name}-google-oauth-pi-key"
  google_client_id_placeholder      = var.google_client_id_placeholder
  google_client_secret_placeholder  = var.google_client_secret_placeholder
  tags                              = local.tags
}

module "ssm" {
  source = "../../modules/ssm_parameters"

  service_fee_bps_name  = "${var.parameter_prefix}/service_fee_bps"
  service_fee_bps_value = var.service_fee_bps_default

  service_fee_fixed_name  = "${var.parameter_prefix}/service_fee_fixed"
  service_fee_fixed_value = var.service_fee_fixed_default

  payme_base_url_name  = "${var.parameter_prefix}/payme_base_url"
  payme_base_url_value = var.payme_base_url_default

  account_refresh_url_name  = "${var.parameter_prefix}/account_refresh_url"
  account_refresh_url_value = var.account_refresh_url_default

  account_return_url_name  = "${var.parameter_prefix}/account_return_url"
  account_return_url_value = var.account_return_url_default

  cognito_domain_prefix_name  = "${var.parameter_prefix}/cognito_domain_prefix"
  cognito_domain_prefix_value = var.cognito_domain_prefix_default

  callback_urls_name  = "${var.parameter_prefix}/callback_urls"
  callback_urls_value = local.callback_urls_value

  logout_urls_name  = "${var.parameter_prefix}/logout_urls"
  logout_urls_value = local.logout_urls_value

  expiry_schedule_name  = "${var.parameter_prefix}/expiry_schedule"
  expiry_schedule_value = var.expiry_schedule_default

  cors_allowed_origins_name  = "${var.parameter_prefix}/cors_allowed_origins"
  cors_allowed_origins_value = var.cors_allowed_origins_default

  tags = local.tags
}

data "aws_secretsmanager_secret_version" "stripe" {
  secret_id  = module.secrets.stripe_secret_name
  depends_on = [module.secrets]
}

data "aws_secretsmanager_secret_version" "stripe_webhook" {
  secret_id  = module.secrets.stripe_webhook_secret_name
  depends_on = [module.secrets]
}

data "aws_secretsmanager_secret_version" "google_oauth" {
  secret_id  = module.secrets.google_oauth_secret_name
  depends_on = [module.secrets]
}

data "aws_ssm_parameter" "service_fee_bps" {
  name       = module.ssm.service_fee_bps_name
  depends_on = [module.ssm]
}

data "aws_ssm_parameter" "service_fee_fixed" {
  name       = module.ssm.service_fee_fixed_name
  depends_on = [module.ssm]
}

data "aws_ssm_parameter" "payme_base_url" {
  name       = module.ssm.payme_base_url_name
  depends_on = [module.ssm]
}

data "aws_ssm_parameter" "account_refresh_url" {
  name       = module.ssm.account_refresh_url_name
  depends_on = [module.ssm]
}

data "aws_ssm_parameter" "account_return_url" {
  name       = module.ssm.account_return_url_name
  depends_on = [module.ssm]
}

data "aws_ssm_parameter" "cognito_domain_prefix" {
  name       = module.ssm.cognito_domain_prefix_name
  depends_on = [module.ssm]
}

data "aws_ssm_parameter" "callback_urls" {
  name       = module.ssm.callback_urls_name
  depends_on = [module.ssm]
}

data "aws_ssm_parameter" "logout_urls" {
  name       = module.ssm.logout_urls_name
  depends_on = [module.ssm]
}

data "aws_ssm_parameter" "expiry_schedule" {
  name       = module.ssm.expiry_schedule_name
  depends_on = [module.ssm]
}

data "aws_ssm_parameter" "cors_allowed_origins" {
  name       = module.ssm.cors_allowed_origins_name
  depends_on = [module.ssm]
}

module "cognito" {
  source               = "../../modules/cognito"
  user_pool_name       = "${var.project_name}-users"
  app_client_name      = "${var.project_name}-app"
  domain_prefix        = data.aws_ssm_parameter.cognito_domain_prefix.value
  google_client_id     = jsondecode(data.aws_secretsmanager_secret_version.google_oauth.secret_string).client_id
  google_client_secret = jsondecode(data.aws_secretsmanager_secret_version.google_oauth.secret_string).client_secret
  callback_urls        = split(",", data.aws_ssm_parameter.callback_urls.value)
  logout_urls          = split(",", data.aws_ssm_parameter.logout_urls.value)
  tags                 = local.tags
}

module "iam_lambda" {
  source       = "../../modules/iam_lambda"
  project_name = var.project_name
  dynamodb_table_arns = [
    module.dynamodb.users_table_arn,
    module.dynamodb.user_identities_table_arn,
    module.dynamodb.payment_links_table_arn,
    module.dynamodb.subscription_links_table_arn,
  ]
  dynamodb_index_arns = [
    "${module.dynamodb.user_identities_table_arn}/index/*",
    "${module.dynamodb.payment_links_table_arn}/index/*",
    "${module.dynamodb.subscription_links_table_arn}/index/*",
  ]
  tags = local.tags
}

locals {
  common_env = {
    STRIPE_SECRET                = data.aws_secretsmanager_secret_version.stripe.secret_string
    STRIPE_WEBHOOK_SECRET        = data.aws_secretsmanager_secret_version.stripe_webhook.secret_string
    SERVICE_FEE_BPS              = data.aws_ssm_parameter.service_fee_bps.value
    SERVICE_FEE_FIXED            = data.aws_ssm_parameter.service_fee_fixed.value
    COGNITO_REGION               = var.aws_region
    COGNITO_USER_POOL_ID         = module.cognito.user_pool_id
    COGNITO_APP_CLIENT_ID        = module.cognito.app_client_id
    PAYME_BASE_URL               = data.aws_ssm_parameter.payme_base_url.value
    PAYME_ACCOUNT_REFRESH_URL    = data.aws_ssm_parameter.account_refresh_url.value
    PAYME_ACCOUNT_RETURN_URL     = data.aws_ssm_parameter.account_return_url.value
    DEFAULT_COUNTRY              = "GB"
    DDB_TABLE_USERS              = module.dynamodb.users_table_name
    DDB_TABLE_USER_IDENTITIES    = module.dynamodb.user_identities_table_name
    DDB_TABLE_STRIPE_ACCOUNTS    = module.dynamodb.user_accounts_table_name
    DDB_TABLE_PAYMENT_LINKS      = module.dynamodb.payment_links_table_name
    DDB_TABLE_SUBSCRIPTION_LINKS = module.dynamodb.subscription_links_table_name
    DDB_TABLE_TRANSACTIONS       = module.dynamodb.transactions_table_name
    PAYME_ENV                    = "prod"
    CORS_ALLOWED_ORIGINS         = data.aws_ssm_parameter.cors_allowed_origins.value
  }
}

module "api_lambda" {
  source                = "../../modules/lambda"
  function_name         = "${var.project_name}-api"
  handler               = "payme.handlers.api.handler"
  role_arn              = module.iam_lambda.role_arn
  filename              = data.archive_file.lambda_zip.output_path
  source_code_hash      = data.archive_file.lambda_zip.output_base64sha256
  timeout               = 30
  memory_size           = 512
  environment_variables = local.common_env
  tags                  = local.tags
}

module "expire_lambda" {
  source                = "../../modules/lambda"
  function_name         = "${var.project_name}-expire-links"
  handler               = "payme.handlers.expire_links.handler"
  role_arn              = module.iam_lambda.role_arn
  filename              = data.archive_file.lambda_zip.output_path
  source_code_hash      = data.archive_file.lambda_zip.output_base64sha256
  timeout               = 30
  memory_size           = 256
  environment_variables = local.common_env
  tags                  = local.tags
}

module "api_gateway" {
  source                = "../../modules/api_gateway"
  project_name          = var.project_name
  lambda_invoke_arn     = module.api_lambda.invoke_arn
  lambda_function_name  = module.api_lambda.lambda_function_name
  cognito_user_pool_id  = module.cognito.user_pool_id
  cognito_app_client_id = module.cognito.app_client_id
  region                = var.aws_region
  cors_allowed_origins  = var.cors_allowed_origins_default
  tags                  = local.tags
}

module "expire_schedule" {
  source               = "../../modules/eventbridge"
  rule_name            = "${var.project_name}-expire-links"
  schedule_expression  = data.aws_ssm_parameter.expiry_schedule.value
  lambda_arn           = module.expire_lambda.lambda_function_arn
  lambda_function_name = module.expire_lambda.lambda_function_name
  tags                 = local.tags
}

module "frontend_hosting" {
  source              = "../../modules/frontend_hosting"
  project_name        = var.project_name
  environment         = "prod"
  domain_aliases      = var.frontend_domain_aliases
  acm_certificate_arn = local.frontend_certificate_arn
  tags                = local.tags
}

# Cloudflare DNS (prod) for frontend + API custom domain + ACM validation.
data "cloudflare_zone" "zone" {
  count = trimspace(var.cloudflare_zone_name) != "" ? 1 : 0
  filter {
    name = var.cloudflare_zone_name
  }
}

locals {
  cloudflare_zone_id = trimspace(var.cloudflare_zone_name) != "" ? data.cloudflare_zone.zone[0].id : ""
}

resource "aws_acm_certificate" "api" {
  count             = local.api_manage_certificate ? 1 : 0
  domain_name       = var.api_domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_acm_certificate_validation" "api" {
  count           = local.api_manage_certificate ? 1 : 0
  certificate_arn = aws_acm_certificate.api[0].arn

  validation_record_fqdns = [
    for dvo in aws_acm_certificate.api[0].domain_validation_options : dvo.resource_record_name
  ]

  depends_on = [cloudflare_dns_record.api_cert_validation]
}

resource "aws_apigatewayv2_domain_name" "api" {
  domain_name = var.api_domain_name

  domain_name_configuration {
    certificate_arn = local.api_certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}

resource "aws_apigatewayv2_api_mapping" "api" {
  api_id      = module.api_gateway.api_id
  domain_name = aws_apigatewayv2_domain_name.api.id
  stage       = "$default"
}

resource "aws_acm_certificate" "frontend" {
  count                     = local.frontend_manage_certificate ? 1 : 0
  provider                  = aws.us_east_1
  domain_name               = var.frontend_domain_aliases[0]
  subject_alternative_names = slice(var.frontend_domain_aliases, 1, length(var.frontend_domain_aliases))
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_acm_certificate_validation" "frontend" {
  count           = local.frontend_manage_certificate ? 1 : 0
  provider        = aws.us_east_1
  certificate_arn = aws_acm_certificate.frontend[0].arn

  validation_record_fqdns = [
    for dvo in aws_acm_certificate.frontend[0].domain_validation_options : dvo.resource_record_name
  ]

  depends_on = [cloudflare_dns_record.frontend_cert_validation]
}

module "dns_cloudflare" {
  count   = trimspace(var.cloudflare_zone_name) != "" ? 1 : 0
  source  = "../../modules/dns_cloudflare"
  zone_id = local.cloudflare_zone_id
  records = merge(
    length(var.frontend_domain_aliases) > 0 ? {
      frontend_root = {
        type    = "CNAME"
        name    = var.frontend_domain_aliases[0]
        content = module.frontend_hosting.cloudfront_domain_name
        proxied = false
        ttl     = 1
      }
    } : {},
    length(var.frontend_domain_aliases) > 1 ? {
      frontend_www = {
        type    = "CNAME"
        name    = var.frontend_domain_aliases[1]
        content = var.frontend_domain_aliases[0]
        proxied = false
        ttl     = 1
      }
    } : {},
    trimspace(var.api_domain_name) != "" ? {
      api_root = {
        type    = "CNAME"
        name    = var.api_domain_name
        content = aws_apigatewayv2_domain_name.api.domain_name_configuration[0].target_domain_name
        proxied = false
        ttl     = 1
      }
    } : {},
  )
}

resource "cloudflare_dns_record" "api_cert_validation" {
  for_each = trimspace(var.cloudflare_zone_name) != "" && local.api_manage_certificate ? {
    for dvo in aws_acm_certificate.api[0].domain_validation_options :
    dvo.resource_record_name => dvo
  } : {}

  zone_id = local.cloudflare_zone_id
  type    = each.value.resource_record_type
  name    = trimsuffix(each.value.resource_record_name, ".")
  content = each.value.resource_record_value
  ttl     = 1
  proxied = false
}

resource "cloudflare_dns_record" "frontend_cert_validation" {
  for_each = trimspace(var.cloudflare_zone_name) != "" && local.frontend_manage_certificate ? {
    for dvo in aws_acm_certificate.frontend[0].domain_validation_options :
    dvo.resource_record_name => dvo
  } : {}

  zone_id = local.cloudflare_zone_id
  type    = each.value.resource_record_type
  name    = trimsuffix(each.value.resource_record_name, ".")
  content = each.value.resource_record_value
  ttl     = 1
  proxied = false
}
