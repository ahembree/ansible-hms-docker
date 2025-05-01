# Configuring DNS

:::tip

It is recommended to use an internal DNS server (such as a Pi-hole or AdGuard Home) to serve requests that point to an internal private IP address ([RFC1918](https://en.wikipedia.org/wiki/Private_network)). Creating public DNS records that resolve to internal IPs would reveal your internal network IP space, but not allow anyone outside of the same network to access it.

Very small risk but one that should be mentioned.

:::

The domain used is defined in the variable `hms_docker_domain` in `inventory/group_vars/all/main.yml`

## Accessing the Containers

### Internally

If you do not already have a "wildcard" DNS record (`*.example.com`) setup for the domain you used on your LOCAL DNS server, create this `A` record to point to the private IP address of the server.

You can also create individual `A` records for each container listed in the [Container Map](../container-map.md), or have 1 `A` record with multiple `CNAME` records pointed to the `A` record. This will allow you to change 1 DNS record if the IP were to ever change, instead of having to change many individual records.

If the appropriate DNS records exist (you can test by running `nslookup <domain>`, or optionally `nslookup <domain> <DNS server IP>` to query a specific DNS server), you can then access the containers from your network by going to `<name>.<domain>` where `<name>` is the `proxy_host_rule` value (from the container map config file) and `<domain>` is the domain you used for the variable `hms_docker_domain`.

You can also change the name/subdomain of each application within the `hms_docker_container_map` in the containers `proxy_host_rule` value.

### Externally

If you enabled Cloudflare DDNS, an `overseerr` public `A` record will be created automatically that points to your networks _public_ IP.

- This default `A` record can be changed in the `cloudflare_ddns_subdomain` variable located in `inventory/group_vars/all/cloudflare.yml`.

:::note

The below only applies if you are NOT using a [Cloudflare Tunnel](../config-docs/Cloudflare/tunnel.md):

Although this DNS record is created automatically, you will need to set the `expose_to_public` value to `yes` for the `overseerr` container in the [Container Map](../container-map.md) config file if you want Overseerr to be public

:::

Unless port `80` and `443` are port forwarded on the router to your host, accessing this public address from outside your main network will not work.

To grant public access to other containers, you will need to:

- Create a public DNS record for it that is either:

  a.) `A` record that points to the public IP

  b.) `CNAME` record that points to the `<cloudflare_ddns_subdomain>.<domain>` (eg. `overseerr.example.com`)

- Set the `expose_to_public` value to `yes` for the specific container in the [Container Map](../container-map.md)

- OR use a [Cloudflare Tunnel](../config-docs/Cloudflare/tunnel.md)
