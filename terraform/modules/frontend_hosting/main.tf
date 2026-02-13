data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  bucket_name       = lower("${var.project_name}-${var.environment}-frontend-${data.aws_caller_identity.current.account_id}-${data.aws_region.current.name}")
  use_custom_domain = length(var.domain_aliases) > 0

  files = fileset(var.frontend_build_dir, "**")

  content_types = {
    css         = "text/css"
    gif         = "image/gif"
    html        = "text/html"
    ico         = "image/x-icon"
    jpg         = "image/jpeg"
    jpeg        = "image/jpeg"
    js          = "application/javascript"
    json        = "application/json"
    map         = "application/json"
    png         = "image/png"
    svg         = "image/svg+xml"
    txt         = "text/plain"
    webmanifest = "application/manifest+json"
    woff        = "font/woff"
    woff2       = "font/woff2"
    xml         = "application/xml"
  }
}

resource "aws_s3_bucket" "frontend" {
  bucket = local.bucket_name
  tags   = var.tags
}

resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${var.project_name}-${var.environment}-frontend-oac"
  description                       = "CloudFront access control for frontend bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "${var.project_name} ${var.environment} frontend"
  default_root_object = "index.html"
  aliases             = var.domain_aliases

  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "s3-frontend"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "s3-frontend"

    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = !local.use_custom_domain
    acm_certificate_arn            = local.use_custom_domain ? var.acm_certificate_arn : null
    ssl_support_method             = local.use_custom_domain ? "sni-only" : null
    minimum_protocol_version       = local.use_custom_domain ? "TLSv1.2_2021" : "TLSv1"
  }

  tags = var.tags

  lifecycle {
    precondition {
      condition     = !local.use_custom_domain || trimspace(var.acm_certificate_arn) != ""
      error_message = "acm_certificate_arn must be set when domain_aliases is not empty."
    }
  }
}

data "aws_iam_policy_document" "frontend_bucket_policy" {
  statement {
    sid     = "AllowCloudFrontServicePrincipalReadOnly"
    effect  = "Allow"
    actions = ["s3:GetObject"]

    resources = ["${aws_s3_bucket.frontend.arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.frontend.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  policy = data.aws_iam_policy_document.frontend_bucket_policy.json
}

resource "aws_s3_object" "frontend_assets" {
  for_each = {
    for file in local.files :
    file => file
    if !endswith(file, "/")
  }

  bucket = aws_s3_bucket.frontend.id
  key    = each.value
  source = "${var.frontend_build_dir}/${each.value}"
  etag   = filemd5("${var.frontend_build_dir}/${each.value}")

  content_type = lookup(
    local.content_types,
    lower(element(reverse(split(".", each.value)), 0)),
    "application/octet-stream"
  )
}
