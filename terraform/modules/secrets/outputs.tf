output "stripe_secret_name" {
  value = aws_secretsmanager_secret.stripe_secret.name
}

output "stripe_webhook_secret_name" {
  value = aws_secretsmanager_secret.stripe_webhook_secret.name
}

output "stripe_connected_webhook_secret_name" {
  value = aws_secretsmanager_secret.stripe_connected_webhook_secret.name
}

output "google_oauth_secret_name" {
  value = aws_secretsmanager_secret.google_oauth.name
}
