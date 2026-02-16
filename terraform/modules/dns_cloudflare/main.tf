resource "cloudflare_dns_record" "this" {
  for_each = var.records

  zone_id = var.zone_id
  type    = upper(each.value.type)
  name    = each.value.name
  content = each.value.content
  ttl     = each.value.ttl
  proxied = each.value.proxied
}

