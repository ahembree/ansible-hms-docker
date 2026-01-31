# Connecting the Containers

## HTTP Proxy for Arr Services

Transmission, qBittorrent, and Deluge all have a HTTP proxy that will route requests through the VPN connection.

You can configure other apps to connect to these containers proxy services by using `transmission:8888`, `qbittorrent:8118`, or `deluge:8118`, depending on which you are using.

![Proxy Example](../static/img/proxy_example.png)

## Connecting the Containers to each other

When connecting containers together such as Prowlarr to Sonarr and Radarr or Sonarr/Radarr to Overseerr etc, you can use the name of the container (e.g. `prowlarr` or `radarr`) and then defining the container port to connect to (e.g. `prowlarr:9696` or `radarr:7878`).

For the names and port of each container to use, get the `Container Name` and `Container Port` values from the **[Container Map](../container-map)**.

Here's an example within Prowlarr:

![Prowlarr example](../static/img/container_connect_example.png)
