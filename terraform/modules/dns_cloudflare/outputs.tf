output "record_ids" {
  value = { for k, v in cloudflare_dns_record.this : k => v.id }
}

