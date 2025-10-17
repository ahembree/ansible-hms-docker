# Other Containers and Services

## Adding other Containers to Traefik

If a container exists outside of this Compose project but on the same host, you can add them to Traefik so they can also have TLS/SSL

1. Add the `HMSD_DOMAIN` to a new or existing `.env` file that your other containers reference with the value of your domain used for this project

2. Add the `hms-docker_proxy_net` (default) network to the container along with the following required labels:

    ```yml
    services:
      mycontainer:
        image: mycontainerimage:latest
        ...
        network:
          - hms-docker_proxy_net
        labels:
          - traefik.enable=true
          - traefik.http.services.<container name>.loadbalancer.server.port=<web UI port for container>
          - traefik.http.routers.<container name>.rule=Host(`<subdomain name>.${HMSD_DOMAIN}`)
          # The following restricts it to only internal IP addresses
          - traefik.http.routers.<container name>.middlewares=internal-{{ 'secured' if traefik_security_hardening else 'ipallowlist' }}@file
    ...
    networks:
      - hms-docker_proxy_net
          external: true
    ...
    ```

    :::note

      If you changed the `project_name` in the `hmsd_advanced.yml` config file, use that `project_name` instead of `hms-docker`

    :::

3. [Add DNS records](../../getting-started/dns-setup.md) (if necessary)

4. Restart the container(s) you just added labels to

5. Check to see if it is working correctly

## Adding External Services to Traefik

You can add external services (such as services running on another host/server, like an external grafana server) to this projects Traefik config.

In `inventory/group_vars/all/traefik.yml` you _must_ set `traefik_ext_hosts_enabled` to `yes`, and add the correct items to the `traefik_ext_hosts_list` array.

:::warning

All traffic between the host that runs Traefik and the target external service will be **unencrypted**:

> Traefik will terminate the SSL connections (meaning that it will send decrypted data to the services).

**_[Source](https://doc.traefik.io/traefik/routing/routers/#general)_**.

You may be able to add additional Traefik configuration to configure certificates for HTTPS or bypass certificate checking, but that is outside this scope.

:::
