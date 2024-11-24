# Cloudflare DDNS

Below is how to configure DDNS (Dynamic DNS) for Cloudflare.

## Requirements

- A Cloudflare account and Cloudflare configured as your domains DNS servers
- API keys for your account with the correct permissions

## Enabling

In `inventory/group_vars/all/cloudflare_ddns.yml`:

- `cloudflare_ddns_enabled` : `yes` or `no` to enable/disable Cloudflare DDNS (default: `no`)
- `cloudflare_api_token` : the API token of the Cloudflare account
- `cloudflare_zone` : the domain name of the Cloudflare zone (e.g. `example.com`)
- `cloudflare_ddns_subdomain` : the subdomain record (e.g. `overseerr` would be created as `overseerr.example.com`) (default: `overseerr`)
- `cloudflare_ddns_proxied` : `'true'` or `'false'` to enable/disable proxying the traffic through Cloudflare (default: `'true'`)
  - NOTE: This value must be in quotes
