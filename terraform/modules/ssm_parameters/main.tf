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
