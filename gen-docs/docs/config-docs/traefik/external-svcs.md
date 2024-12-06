# External Services

## Adding External Services to Traefik

You can add external services (such as services running on another host/server, like an external grafana server) to this projects Traefik config.

You _must_ set `traefik_ext_hosts_enabled` to `yes`, and add the correct items to the `traefik_ext_hosts_list` array.

:::warning

All traffic between the host that runs Traefik and the target external service will be **unencrypted**. **_[Source](https://doc.traefik.io/traefik/routing/routers/#general)_**.

You may be able to add additional Traefik configuration to configure certificates for HTTPS or bypass certificate checking, but that is outside this scope.

:::

