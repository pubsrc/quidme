data "aws_region" "current" {}

locals {
  tags = {
    Environment = "dev"
    ManagedBy   = "terraform"
    Project     = var.project_name
  }

  # Dev intentionally uses default AWS endpoints (no custom domains) unless you
  # explicitly configure them. This avoids DNS/provider drift during iteration.
  #
  # If you later add aliases in constants.tf, you must also provide
  # `frontend_acm_certificate_arn` for a certificate that is already validated.
  computed_payme_base_url = length(local.frontend_domain_aliases) > 0 ? "https://${local.frontend_domain_aliases[0]}" : module.frontend_hosting.frontend_url

  payme_base_url_value      = var.payme_base_url_default != "https://example.com" ? var.payme_base_url_default : local.computed_payme_base_url
  account_refresh_url_value = var.account_refresh_url_default != "https://example.com/refresh" ? var.account_refresh_url_default : "${local.payme_base_url_value}/app/profile"
  account_return_url_value  = var.account_return_url_default != "https://example.com/return" ? var.account_return_url_default : "${local.payme_base_url_value}/app/profile"

  callback_urls_value = length(var.callback_urls_default) > 0 ? var.callback_urls_default : [
    "${local.payme_base_url_value}/callback",
  ]
  logout_urls_value = length(var.logout_urls_default) > 0 ? var.logout_urls_default : [
    local.payme_base_url_value,
  ]
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

  stripe_secret_name                          = "${var.project_name}-stripe-api-key"
  stripe_secret_placeholder                   = var.stripe_secret_placeholder
  stripe_webhook_secret_name                  = "${var.project_name}-stripe-webhook-secret"
  stripe_webhook_secret_placeholder           = var.stripe_webhook_secret_placeholder
  stripe_connected_webhook_secret_name        = "${var.project_name}-stripe-connected-webhook-secret"
  stripe_connected_webhook_secret_placeholder = var.stripe_connected_webhook_secret_placeholder
  google_oauth_secret_name                    = "${var.project_name}-google-oauth-pi-key"
  google_client_id_placeholder                = var.google_client_id_placeholder
  google_client_secret_placeholder            = var.google_client_secret_placeholder
  tags                                        = local.tags
}

data "aws_secretsmanager_secret_version" "stripe" {
  secret_id  = module.secrets.stripe_secret_name
  depends_on = [module.secrets]
}

data "aws_secretsmanager_secret_version" "stripe_webhook" {
  secret_id  = module.secrets.stripe_webhook_secret_name
  depends_on = [module.secrets]
}

data "aws_secretsmanager_secret_version" "stripe_connected_webhook" {
  secret_id  = module.secrets.stripe_connected_webhook_secret_name
  depends_on = [module.secrets]
}

data "aws_secretsmanager_secret_version" "google_oauth" {
  secret_id  = module.secrets.google_oauth_secret_name
  depends_on = [module.secrets]
}

module "cognito" {
  source               = "../../modules/cognito"
  user_pool_name       = "${var.project_name}-users"
  app_client_name      = "${var.project_name}-app"
  domain_prefix        = var.cognito_domain_prefix_default
  google_client_id     = jsondecode(data.aws_secretsmanager_secret_version.google_oauth.secret_string).client_id
  google_client_secret = jsondecode(data.aws_secretsmanager_secret_version.google_oauth.secret_string).client_secret
  callback_urls        = local.callback_urls_value
  logout_urls          = local.logout_urls_value
  tags                 = local.tags
}

module "ssm" {
  source = "../../modules/ssm_parameters"

  service_fee_bps_name  = "${var.parameter_prefix}/service_fee_bps"
  service_fee_bps_value = var.service_fee_bps_default

  service_fee_fixed_name  = "${var.parameter_prefix}/service_fee_fixed"
  service_fee_fixed_value = var.service_fee_fixed_default

  payme_base_url_name  = "${var.parameter_prefix}/payme_base_url"
  payme_base_url_value = local.payme_base_url_value

  account_refresh_url_name  = "${var.parameter_prefix}/account_refresh_url"
  account_refresh_url_value = local.account_refresh_url_value

  account_return_url_name  = "${var.parameter_prefix}/account_return_url"
  account_return_url_value = local.account_return_url_value

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

  vite_api_base_url_name  = "${var.parameter_prefix}/vite_api_base_url"
  vite_api_base_url_value = trimspace(var.api_domain_name) != "" ? "https://${var.api_domain_name}" : module.api_gateway.api_endpoint

  vite_cognito_user_pool_id_name  = "${var.parameter_prefix}/vite_cognito_user_pool_id"
  vite_cognito_user_pool_id_value = module.cognito.user_pool_id

  vite_cognito_user_pool_client_id_name  = "${var.parameter_prefix}/vite_cognito_user_pool_client_id"
  vite_cognito_user_pool_client_id_value = module.cognito.app_client_id

  vite_cognito_region_name  = "${var.parameter_prefix}/vite_cognito_region"
  vite_cognito_region_value = var.aws_region

  vite_cognito_oauth_domain_name  = "${var.parameter_prefix}/vite_cognito_oauth_domain"
  vite_cognito_oauth_domain_value = "${module.cognito.domain}.auth.${var.aws_region}.amazoncognito.com"

  vite_oauth_redirect_sign_in_name  = "${var.parameter_prefix}/vite_oauth_redirect_sign_in"
  vite_oauth_redirect_sign_in_value = local.callback_urls_value[0]

  vite_oauth_redirect_sign_out_name  = "${var.parameter_prefix}/vite_oauth_redirect_sign_out"
  vite_oauth_redirect_sign_out_value = local.logout_urls_value[0]

  tags = local.tags
}

module "iam_lambda" {
  source       = "../../modules/iam_lambda"
  project_name = var.project_name
  dynamodb_table_arns = [
    module.dynamodb.users_table_arn,
    module.dynamodb.user_identities_table_arn,
    module.dynamodb.user_accounts_table_arn,
    module.dynamodb.payment_links_table_arn,
    module.dynamodb.subscription_links_table_arn,
    module.dynamodb.subscriptions_table_arn,
    module.dynamodb.transactions_table_arn,
  ]
  dynamodb_index_arns = [
    "${module.dynamodb.user_identities_table_arn}/index/*",
    "${module.dynamodb.user_accounts_table_arn}/index/*",
    "${module.dynamodb.payment_links_table_arn}/index/*",
    "${module.dynamodb.subscription_links_table_arn}/index/*",
    "${module.dynamodb.subscriptions_table_arn}/index/*",
  ]
  tags = local.tags
}

locals {
  frontend_vite_api_base_url = trimspace(var.api_domain_name) != "" ? "https://${var.api_domain_name}" : module.api_gateway.api_endpoint
  frontend_vite_oauth_domain = "${module.cognito.domain}.auth.${var.aws_region}.amazoncognito.com"

  common_env = {
    STRIPE_SECRET                   = data.aws_secretsmanager_secret_version.stripe.secret_string
    STRIPE_WEBHOOK_SECRET           = data.aws_secretsmanager_secret_version.stripe_webhook.secret_string
    STRIPE_CONNECTED_WEBHOOK_SECRET = data.aws_secretsmanager_secret_version.stripe_connected_webhook.secret_string
    SERVICE_FEE_BPS                 = tostring(var.service_fee_bps_default)
    SERVICE_FEE_FIXED               = tostring(var.service_fee_fixed_default)
    COGNITO_REGION                  = var.aws_region
    COGNITO_USER_POOL_ID            = module.cognito.user_pool_id
    COGNITO_APP_CLIENT_ID           = module.cognito.app_client_id
    PAYME_BASE_URL                  = local.payme_base_url_value
    PAYME_ACCOUNT_REFRESH_URL       = local.account_refresh_url_value
    PAYME_ACCOUNT_RETURN_URL        = local.account_return_url_value
    DEFAULT_COUNTRY                 = "GB"
    DDB_TABLE_USERS                 = module.dynamodb.users_table_name
    DDB_TABLE_USER_IDENTITIES       = module.dynamodb.user_identities_table_name
    DDB_TABLE_STRIPE_ACCOUNTS       = module.dynamodb.user_accounts_table_name
    DDB_TABLE_PAYMENT_LINKS         = module.dynamodb.payment_links_table_name
    DDB_TABLE_SUBSCRIPTION_LINKS    = module.dynamodb.subscription_links_table_name
    DDB_TABLE_SUBSCRIPTIONS         = module.dynamodb.subscriptions_table_name
    DDB_TABLE_TRANSACTIONS          = module.dynamodb.transactions_table_name
    PAYME_ENV                       = "dev"
    CORS_ALLOWED_ORIGINS            = join(",", var.cors_allowed_origins_default)
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
  schedule_expression  = var.expiry_schedule_default
  lambda_arn           = module.expire_lambda.lambda_function_arn
  lambda_function_name = module.expire_lambda.lambda_function_name
  tags                 = local.tags
}

module "frontend_hosting" {
  source              = "../../modules/frontend_hosting"
  project_name        = var.project_name
  environment         = "dev"
  domain_aliases      = local.frontend_domain_aliases
  acm_certificate_arn = var.frontend_acm_certificate_arn
  tags                = local.tags
}
