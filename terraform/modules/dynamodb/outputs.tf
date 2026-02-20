output "users_table_name" {
  value = aws_dynamodb_table.users.name
}

output "user_identities_table_name" {
  value = aws_dynamodb_table.user_identities.name
}

output "user_accounts_table_name" {
  value = aws_dynamodb_table.user_accounts.name
}

output "payment_links_table_name" {
  value = aws_dynamodb_table.payment_links.name
}

output "subscription_links_table_name" {
  value = aws_dynamodb_table.subscription_links.name
}

output "subscriptions_table_name" {
  value = aws_dynamodb_table.subscriptions.name
}

output "transactions_table_name" {
  value = aws_dynamodb_table.transactions.name
}

output "users_table_arn" {
  value = aws_dynamodb_table.users.arn
}

output "user_identities_table_arn" {
  value = aws_dynamodb_table.user_identities.arn
}

output "user_accounts_table_arn" {
  value = aws_dynamodb_table.user_accounts.arn
}

output "payment_links_table_arn" {
  value = aws_dynamodb_table.payment_links.arn
}

output "subscription_links_table_arn" {
  value = aws_dynamodb_table.subscription_links.arn
}

output "subscriptions_table_arn" {
  value = aws_dynamodb_table.subscriptions.arn
}

output "transactions_table_arn" {
  value = aws_dynamodb_table.transactions.arn
}
