output "stripe_secret_name" {
  value = aws_secretsmanager_secret.stripe_secret.name
}

output "google_oauth_secret_name" {
  value = aws_secretsmanager_secret.google_oauth.name
}

output "cloudflaire_api_token_secret_name" {
  value = aws_secretsmanager_secret.cloudflaire_api_token.name
}
