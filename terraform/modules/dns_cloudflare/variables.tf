variable "zone_id" {
  type = string
}

variable "records" {
  description = "Map of DNS records to create/update in Cloudflare."
  type = map(object({
    type    = string
    name    = string
    content = string
    ttl     = optional(number, 1)   # 1 = Auto in Cloudflare
    proxied = optional(bool, false) # DNS-only by default (recommended with CloudFront/API Gateway)
  }))
  default = {}
}

