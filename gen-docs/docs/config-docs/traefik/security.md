# Security

## How the containers are protected

There is an allowlist configured within Traefik that only allows private IPs (RFC1918) to access all of the containers via Traefik. However if you choose to route a container through [Cloudflare Tunnel](../Cloudflare/tunnel.md) (recommended so you don't have to port forward), then it is no longer being routed through Traefik.

This is controlled on a per-container basis in the `inventory/group_vars/all/container_map.yml` file as the `expose_to_public` variable for each container. If you set this to `yes`, it will allow all IPs (`0.0.0.0/0`) to access them.

## SSO

To configure SSO (Single Sign-On) for certain containers, see the [Authentik docs](../Authentik.md)

## TLS Versions

`traefik_security_hardening`: This will disable TLS1.0 and TLS1.1 and use TLS1.2 as the new minimum.

