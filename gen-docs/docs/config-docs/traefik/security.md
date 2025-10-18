# Security

## How the containers are protected

There is an allowlist configured within Traefik that only allows private IPs (RFC1918) to access all of the containers via Traefik. However if you choose to route a container through [Cloudflare Tunnel](../Cloudflare/tunnel.md) (recommended so you don't have to port forward), then it is no longer being routed through Traefik and thus not subject to any Traefik allowlists.

This is controlled on a per-container basis in the `inventory/group_vars/all/container_map.yml` file as the `expose_to_public` variable for each container. If you set this to `yes`, it will allow all IPs (`0.0.0.0/0`) to access them.

## SSO

To configure SSO (Single Sign-On) for certain containers, see the [Authentik docs](../Authentik.md)

## Security Hardening

There is a `traefik_security_hardening` variable that will do the following if enabled:

- Enforce HTTPS only requests
- Enforce Traefik dashboard over secure connection
- Disable port `8080` access to Traefik
  - This will also disable Homepage integration with Traefik
- Only allows requests to services/Hosts with Traefik enabled
- Disable TLS1.0 and TLS1.1 and use TLS1.2 as the new minimum
- Add security headers for the following:
  - `X-Frame-Options: DENY` : [[Mozilla Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Frame-Options)] Denies iFrame embedding
  - `X-Content-Type-Options: nosniff` : [[Mozilla Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Content-Type-Options)] Blocks a request if the request destination is of type style and the MIME type is not text/css, or of type script and the MIME type is not a [JavaScript MIME type](https://html.spec.whatwg.org/multipage/infrastructure.html#javascript-mime-type)

## Middlewares

The following middlwares are available:

- `internal-ipallowlist`: Allows only RFC1918 private address space and any other IPs/ranges defined in the `traefik_subnet_allow_list` variable
- `external-ipallowlist`: Allows all traffic from `0.0.0.0/0`
- `internal-secured`: Applies the `internal-ipallowlist`, `https-only`, and `secure-headers` middlewares
- `external-secured`: Applies the `externa-ipallowlist`, `https-only`, and `secure-headers` middlewares
- `https-only`: Configures permanent redirection to HTTPS
- `secure-headers`: Applies headers to prevent iFrame embedding, blocks requests if MIME types do not match certain criteria, and only allows Host headers for applications that are enabled within this project
- `error-pages`: Not security related, but it renders pretty error pages
