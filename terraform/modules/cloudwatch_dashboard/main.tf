locals {
  dashboard_name = "${var.project_name}-${var.environment}-operational-metrics"
}

resource "aws_cloudwatch_dashboard" "this" {
  dashboard_name = local.dashboard_name

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "Users and Verified Accounts"
          view    = "timeSeries"
          stacked = false
          stat    = "Sum"
          period  = 300
          region  = var.aws_region
          metrics = [
            [var.metrics_namespace, "Users", { label = "Users" }],
            [".", "VerifiedAccounts", { label = "Verified Accounts" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "Transactions"
          view    = "timeSeries"
          stacked = false
          stat    = "Sum"
          period  = 300
          region  = var.aws_region
          metrics = [
            [var.metrics_namespace, "Transactions", { label = "Transactions" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 7
        properties = {
          title   = "Transfers"
          view    = "timeSeries"
          stacked = false
          stat    = "Sum"
          period  = 300
          region  = var.aws_region
          metrics = [
            [var.metrics_namespace, "SuccessfulTransfers", { label = "Successful Transfers" }],
            [".", "FailedTransfers", { label = "Failed Transfers" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 7
        properties = {
          title   = "Payouts"
          view    = "timeSeries"
          stacked = false
          stat    = "Sum"
          period  = 300
          region  = var.aws_region
          metrics = [
            [var.metrics_namespace, "SuccessfulPayouts", { label = "Successful Payouts" }],
            [".", "FailedPayouts", { label = "Failed Payouts" }],
          ]
        }
      },
    ]
  })
}
