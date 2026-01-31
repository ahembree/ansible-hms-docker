---
sidebar_position: 6
---
# Container Overrides

:::warning

This section is meant for those that are familiar with writing/modifying Docker Compose files

:::

If you want to specify custom container Compose settings or only change certain values (without having to modify the Compose files) and persist your own custom settings (such as environment variables), you can create a `docker-compose.override.yml` file located at `/opt/hms-docker/docker-compose.override.yml` with only the settings you want to override or merge.

Documentation on how to do this can be found here: [Merge | Docker Docs](https://docs.docker.com/compose/how-tos/multiple-compose-files/merge/)

Here is a basic example of this file (assuming Sonarr, Radarr, and Plex are enabled) that will _not_ override any settings:

```yaml
# /opt/hms-docker/docker-compose.override.yml
services:
  sonarr:
  radarr:
  plex:
  ...
```

:::warning

Only enabled containers must be specified in this file

If a container is not enabled but is specified in this override file, it will fail to validate and throw an error

To resolve, remove the invalid item from the override file

:::

If you want to check the final Compose configuration after modification of the override file, you can run (may need `sudo`):

```bash
docker compose config
```

## Private Internet Access (PIA)

The Deluge and qBittorrent containers have native support for the VPN provider Private Internet Access (PIA).

These containers also support port forwarding through PIA, but this means you will only be able to connect to endpoints that support port forwarding.

For more information on this port fowarding feature, see Question 15 (Q15) here: [Binhex Documentation](https://github.com/binhex/documentation/blob/master/docker/faq/vpn.md)

In order to enable this port forwarding, you will need to add the following to the "override" file specified above (`/opt/hms-docker/docker-compose.override.yml`):

```yaml
services:
  qbittorrent:
    environment:
      - VPN_PROV=pia
      - STRICT_PORT_FORWARDING=yes
  deluge:
    environment:
      - VPN_PROV=pia
      - STRICT_PORT_FORWARDING=yes
```
