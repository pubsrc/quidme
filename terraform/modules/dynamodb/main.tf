locals {
  users_table              = "${var.project_name}-users"
  user_identities_table    = "${var.project_name}-user-identities"
  stripe_accounts_table    = "${var.project_name}-stripe-accounts"
  payment_links_table      = "${var.project_name}-payment-links"
  subscription_links_table = "${var.project_name}-subscription-links"
  subscriptions_table      = "${var.project_name}-subscriptions"
  transactions_table       = "${var.project_name}-transactions"
}

resource "aws_dynamodb_table" "users" {
  name         = local.users_table
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  tags = var.tags
}

resource "aws_dynamodb_table" "user_identities" {
  name         = local.user_identities_table
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "identity_id"

  attribute {
    name = "identity_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  global_secondary_index {
    name = "user_id_index"
    key_schema {
      attribute_name = "user_id"
      key_type       = "HASH"
    }
    projection_type = "ALL"
  }

  tags = var.tags
}

resource "aws_dynamodb_table" "user_accounts" {
  name         = local.stripe_accounts_table
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "stripe_account_id"
    type = "S"
  }

  global_secondary_index {
    name = "stripe_account_id_index"
    key_schema {
      attribute_name = "stripe_account_id"
      key_type       = "HASH"
    }
    projection_type = "ALL"
  }

  tags = var.tags
}

resource "aws_dynamodb_table" "payment_links" {
  name         = local.payment_links_table
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "link_id"

  attribute {
    name = "link_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "expires_at"
    type = "N"
  }

  global_secondary_index {
    name = "user_id_index"
    key_schema {
      attribute_name = "user_id"
      key_type       = "HASH"
    }
    projection_type = "ALL"
  }

  global_secondary_index {
    name = "status_expires_at_index"
    key_schema {
      attribute_name = "status"
      key_type       = "HASH"
    }
    key_schema {
      attribute_name = "expires_at"
      key_type       = "RANGE"
    }
    projection_type = "ALL"
  }

  tags = var.tags
}

resource "aws_dynamodb_table" "transactions" {
  name         = local.transactions_table
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "date_transaction_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "date_transaction_id"
    type = "S"
  }

  tags = var.tags
}

resource "aws_dynamodb_table" "subscription_links" {
  name         = local.subscription_links_table
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "subscription_id"

  attribute {
    name = "subscription_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "expires_at"
    type = "N"
  }

  global_secondary_index {
    name = "user_id_index"
    key_schema {
      attribute_name = "user_id"
      key_type       = "HASH"
    }
    projection_type = "ALL"
  }

  global_secondary_index {
    name = "status_expires_at_index"
    key_schema {
      attribute_name = "status"
      key_type       = "HASH"
    }
    key_schema {
      attribute_name = "expires_at"
      key_type       = "RANGE"
    }
    projection_type = "ALL"
  }

  tags = var.tags
}

resource "aws_dynamodb_table" "subscriptions" {
  name         = local.subscriptions_table
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "created_at_key"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "created_at_key"
    type = "S"
  }

  attribute {
    name = "subscription_id"
    type = "S"
  }

  global_secondary_index {
    name = "subscription_id_index"
    key_schema {
      attribute_name = "subscription_id"
      key_type       = "HASH"
    }
    projection_type = "ALL"
  }

  tags = var.tags
}
