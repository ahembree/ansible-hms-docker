# Configuring DNS

:::tip

It is recommended to use an internal DNS server (such as a Pi-hole or AdGuard Home) to serve these DNS requests. This is because creating public DNS records would reveal your internal network IPs.

Very small risk but one that should be mentioned.

:::

The domain used is defined in the variable `hms_docker_domain` in `inventory/group_vars/all/main.yml`

## Accessing the Containers

If you do not already have a "wildcard" DNS record (`*.example.com`) setup for the domain you used on your LOCAL DNS server (such as `*.home.local`), create this `A` record to point to the IP address of the server.

:::note

If you enabled Cloudflare DDNS, an `overseerr` public `A` record will be created automatically that points to your networks public IP.

* This default `A` record can be changed in the `cloudflare_ddns_subdomain` variable located in `inventory/group_vars/all/cloudflare.yml`.

Unless port `80` and `443` are port forwarded on the router to your host, accessing this public address from outside your main network will not work.

:::

You can also create individual `A` records for each container listed in the [Container Map](../container-map.md), or have 1 `A` record with multiple `CNAME` records pointed to the `A` record. This will allow you to change 1 DNS record if the IP were to ever change, instead of having to change many individual records.

If the appropriate DNS records exist (you can test by running `nslookup <domain>`, or optionally `nslookup <domain> <DNS server IP>` to query a specific DNS server), you can then access the containers from your network by going to `<name>.<domain>` where `<name>` is the container name and `<domain>` is the domain you used for the variable `hms_docker_domain` in the `proxy_host_rule` value.

You can also change the name/subdomain of each application within the `hms_docker_container_map`.
