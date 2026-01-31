# Cloudflare DDNS

Below is how to configure DDNS (Dynamic DNS) for Cloudflare.

## Requirements

- A Cloudflare account and Cloudflare configured as your domains DNS servers
- API keys for your account with the correct permissions
  - Requires `Zone.DNS:Edit` permissions for the correct zone

## Enabling

In `inventory/group_vars/all/cloudflare_ddns.yml`:

- `cloudflare_api_token` : the API token of the Cloudflare account
- `cloudflare_ddns_enabled` : `yes` or `no` to enable/disable Cloudflare DDNS (default: `no`)
- `cloudflare_ddns_domain` : the domain name of the Cloudflare zone (e.g. `example.com`), this will default to the `hms_docker_domain` defined in the `main.yml` file
- `cloudflare_ddns_subdomain` : the subdomain record (e.g. `overseerr` would be created as `overseerr.example.com`) (default: `overseerr`)
- `cloudflare_ddns_proxied` : `'true'` or `'false'` to enable/disable proxying the traffic through Cloudflare (default: `'true'`)
  - NOTE: This value must be in quotes
- `cloudflare_ddns_delete_record_on_stop` : If the record should be deleted when the container stops (default: `"false"`)
  - NOTE: This value must be in quotes
- `cloudflare_ddns_create_ipv6_aaaa_record` : Creates a `AAAA` record for IPv6 (default: `no`)
