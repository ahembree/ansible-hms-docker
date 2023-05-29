# Traefik

## Adding External Services to Traefik

You can add external services (such as services running on another host/server, like an external grafana server) to this projects Traefik config.

You _must_ be using the Advanced Config, set `traefik_ext_hosts_enabled` to `yes`, and add the correct items to the `traefik_ext_hosts_list` array.

**NOTE**: All traffic between the host that runs Traefik and the target external service will be **unencrypted**. [Source](https://doc.traefik.io/traefik/routing/routers/#general)
