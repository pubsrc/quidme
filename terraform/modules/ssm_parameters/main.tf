resource "aws_ssm_parameter" "service_fee_bps" {
  name  = var.service_fee_bps_name
  type  = "String"
  value = tostring(var.service_fee_bps_value)
  tags  = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "service_fee_fixed" {
  name  = var.service_fee_fixed_name
  type  = "String"
  value = tostring(var.service_fee_fixed_value)
  tags  = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "payme_base_url" {
  name  = var.payme_base_url_name
  type  = "String"
  value = var.payme_base_url_value
  tags  = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "account_refresh_url" {
  name  = var.account_refresh_url_name
  type  = "String"
  value = var.account_refresh_url_value
  tags  = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "account_return_url" {
  name  = var.account_return_url_name
  type  = "String"
  value = var.account_return_url_value
  tags  = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "cognito_domain_prefix" {
  name  = var.cognito_domain_prefix_name
  type  = "String"
  value = var.cognito_domain_prefix_value
  tags  = var.tags
}

resource "aws_ssm_parameter" "callback_urls" {
  name  = var.callback_urls_name
  type  = "StringList"
  value = join(",", var.callback_urls_value)
  tags  = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "logout_urls" {
  name  = var.logout_urls_name
  type  = "StringList"
  value = join(",", var.logout_urls_value)
  tags  = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "expiry_schedule" {
  name  = var.expiry_schedule_name
  type  = "String"
  value = var.expiry_schedule_value
  tags  = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "cors_allowed_origins" {
  name  = var.cors_allowed_origins_name
  type  = "StringList"
  value = join(",", var.cors_allowed_origins_value)
  tags  = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "vite_api_base_url" {
  name  = var.vite_api_base_url_name
  type  = "String"
  value = var.vite_api_base_url_value
  tags  = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "vite_cognito_user_pool_id" {
  name  = var.vite_cognito_user_pool_id_name
  type  = "String"
  value = var.vite_cognito_user_pool_id_value
  tags  = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "vite_cognito_user_pool_client_id" {
  name  = var.vite_cognito_user_pool_client_id_name
  type  = "String"
  value = var.vite_cognito_user_pool_client_id_value
  tags  = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "vite_cognito_region" {
  name  = var.vite_cognito_region_name
  type  = "String"
  value = var.vite_cognito_region_value
  tags  = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "vite_cognito_oauth_domain" {
  name  = var.vite_cognito_oauth_domain_name
  type  = "String"
  value = var.vite_cognito_oauth_domain_value
  tags  = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "vite_oauth_redirect_sign_in" {
  name  = var.vite_oauth_redirect_sign_in_name
  type  = "String"
  value = var.vite_oauth_redirect_sign_in_value
  tags  = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "vite_oauth_redirect_sign_out" {
  name  = var.vite_oauth_redirect_sign_out_name
  type  = "String"
  value = var.vite_oauth_redirect_sign_out_value
  tags  = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}
