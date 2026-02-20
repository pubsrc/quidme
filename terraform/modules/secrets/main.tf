resource "aws_secretsmanager_secret" "stripe_secret" {
  name                    = var.stripe_secret_name
  recovery_window_in_days = var.recovery_window_in_days
  tags                    = var.tags
}

resource "aws_secretsmanager_secret_version" "stripe_secret" {
  secret_id     = aws_secretsmanager_secret.stripe_secret.id
  secret_string = var.stripe_secret_placeholder

  lifecycle {
    ignore_changes = [secret_string]
  }
}

resource "aws_secretsmanager_secret" "stripe_webhook_secret" {
  name                    = var.stripe_webhook_secret_name
  recovery_window_in_days = var.recovery_window_in_days
  tags                    = var.tags
}

resource "aws_secretsmanager_secret_version" "stripe_webhook_secret" {
  secret_id     = aws_secretsmanager_secret.stripe_webhook_secret.id
  secret_string = var.stripe_webhook_secret_placeholder

  lifecycle {
    ignore_changes = [secret_string]
  }
}

resource "aws_secretsmanager_secret" "stripe_connected_webhook_secret" {
  name                    = var.stripe_connected_webhook_secret_name
  recovery_window_in_days = var.recovery_window_in_days
  tags                    = var.tags
}

resource "aws_secretsmanager_secret_version" "stripe_connected_webhook_secret" {
  secret_id     = aws_secretsmanager_secret.stripe_connected_webhook_secret.id
  secret_string = var.stripe_connected_webhook_secret_placeholder

  lifecycle {
    ignore_changes = [secret_string]
  }
}

resource "aws_secretsmanager_secret" "google_oauth" {
  name                    = var.google_oauth_secret_name
  recovery_window_in_days = var.recovery_window_in_days
  tags                    = var.tags
}

resource "aws_secretsmanager_secret_version" "google_oauth" {
  secret_id = aws_secretsmanager_secret.google_oauth.id
  secret_string = jsonencode({
    client_id     = var.google_client_id_placeholder
    client_secret = var.google_client_secret_placeholder
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}
