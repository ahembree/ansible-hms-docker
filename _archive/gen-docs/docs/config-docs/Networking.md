# Networking

:::tip

Ports are _NOT_ exposed by default (with the exception of Traefik, `80/443`) on the host.

:::

The service ports (such as for Sonarr (`8989`) or Radarr (`7878`)) will be **exposed/open** on the host machine if:

* `container_expose_ports` is set to `yes` in `inventory/group_vars/all/container_settings.yml`

* Traefik is disabled entirely

* Traefik is disabled on that specific container in `inventory/group_vars/all/container_map.yml`

See the **[Container Map](../container-map.md)** for the `Host Port` value for each service as there may be overlapping default ports, meaning the default port may have changed for a service.
