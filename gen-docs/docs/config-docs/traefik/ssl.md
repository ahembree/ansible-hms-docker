# SSL Certificate

## Generating Wildcard SSL Certificate

A wildcard certificate (`*.example.com`) will be the default. To change this, see [Changing SSL Certificate SANs](#changing-ssl-certificate-sans). Note that an individual certificate for each container will not be generated due to [Let's Encrypts rate limit of 5 exact hostnames every 7 days](https://letsencrypt.org/docs/rate-limits/#new-certificates-per-exact-set-of-hostnames).

:::note

This has only been tested using Cloudflare, so ymmv. This page is just to reference supported providers, their required `Provider Code` and `Environment Variables`. Do not follow any additional configuration links within that page, you only need the provider code and environment variables.

:::

## Requirements

- A supported DNS provider (e.g. Cloudflare), [you can find supported providers **here** along with their settings](https://doc.traefik.io/traefik/https/acme/#providers)
- A valid Top-Level Domain (TLD), such as `.com` or `.net`, that Let's Encrypt is able to issue certificates for
- API keys for the DNS provider with the correct permissions

:::tip

The default configuration already has the correct Environment Variables for Cloudflare.

If also using Cloudflare, set the API key in `cloudflare_api_token` in `inventory/group_vars/all/cloudflare.yml`

:::

## Configuration

Settings mentioned below should already exist in your `inventory/group_vars/all/traefik.yml`:

- `traefik_ssl_enabled` : whether or not to generate a wildcard SSL certificate
- `traefik_ssl_dns_provider_zone` : the zone of the DNS provider (e.g. `example.com`, this will default to the `hms_docker_domain` if not modified)
- `traefik_ssl_dns_provider_code` : the "Provider Code" of the DNS provider (e.g. `cloudflare`, found at link above)
- `traefik_ssl_dns_provider_environment_vars` : the "Environment Variables", along with their values, of the DNS provider you're using (e.g. `"CF_DNS_API_TOKEN": "<token>"` if using `cloudflare`, found at link above)
- `traefik_ssl_letsencrypt_email` : the email address to use for Let's Encrypt
- `traefik_ssl_use_letsencrypt_staging_url` : whether or not to use the Let's Encrypt staging URL for initial testing (`yes` or `no`) (default: `yes`)
  - Recommended to use if setting up for the first time so you do not encounter [Rate-Limiting from Let's Encrypt](https://letsencrypt.org/docs/rate-limits/)
  - The certificate will say it is invalid within a browser, but if you check the issuer, it should come from the "Staging" server, meaning it worked successfully and you then change this value to `no` to use the production server and get a valid certificate.

:::tip

Once the playbook has finished running, it may take up to a few minutes for the SSL certificate to be generated.

To view debug logs, set `traefik_log_level` to `DEBUG` and then re-run the playbook and run `docker logs traefik -f`. This can show you the status of the certificate generation request.

:::

## Changing SSL Certificate SANs

To change/add the SANs used for the certificate, in `inventory/group_vars/all/traefik.yml` modify the `traefik_ssl_sans` variable.

By default, it will generate a wildcard certificate for the domain set in `hms_docker_domain`

```yaml
traefik_ssl_sans: [
  '*.{{ hms_docker_domain }}',
  '*.dev.{{ hms_docker_domain }}'
]
```
