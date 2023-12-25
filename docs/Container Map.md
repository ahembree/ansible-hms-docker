# Container Map

## Connecting the Containers to each other

When connecting Prowlarr to Sonarr and Radarr and etc, you can use the name of the container (e.g. `prowlarr` or `radarr`) and then defining the container port to connect to (e.g. `prowlarr:9696` or `radarr:7878`).

Here's an example within Prowlarr:

![Prowlarr example](./_img/container_connect_example.png)

If you choose to expose the container ports on the host (by setting `container_expose_ports: yes` in the `vars/custom/container_settings.yml` file), see below for which ports are mapped to which container on the host.

**NOTE:** Ports are _NOT_ exposed by default (with the exception of Traefik)

## Map

| Service Name                             | Container Name       | Host Port (if enabled) | Container Port    | Accessible via Traefik |
| ---------------------------------------- | -------------------- | ---------------------- | ----------------- | ---------------------- |
| Plex                                     | `plex`               | `32400`                | `32400`           | &#9745;                |
| Sonarr                                   | `sonarr`             | `8989`                 | `8989`            | &#9745;                |
| Sonarr (Separate 4K instance if enabled) | `sonarr-4k`          | `8990`                 | `8989`            | &#9745;                |
| Radarr                                   | `radarr`             | `7878`                 | `7878`            | &#9745;                |
| Radarr (Separate 4K instance if enabled) | `radarr-4k`          | `7879`                 | `7878`            | &#9745;                |
| Prowlarr                                 | `prowlarr`           | `9696`                 | `9696`            | &#9745;                |
| Overseerr                                | `Overseerr`          | `5055`                 | `5055`            | &#9745;                |
| Requestrr                                | `Requestrr`          | `4545`                 | `4545`            | &#9745;                |
| Transmission UI Proxy                    | `transmission-proxy` | `8081`                 | `8080`            | &#9745;                |
| Transmission (HTTP Proxy)                | `transmission`       | `8888`                 | `8888`            | &#9744;                |
| Transmission (RPC)                       | `transmission`       | `9091`                 | `9091`            | &#9744;                |
| Portainer                                | `portainer`          | `9000`                 | `9000`            | &#9745;                |
| Bazarr                                   | `bazarr`             | `6767`                 | `6767`            | &#9745;                |
| Tautulli                                 | `tautulli`           | `8181`                 | `8181`            | &#9745;                |
| Traefik                                  | `traefik`            | `80`, `8080`, `443`    | `80`, `8080`, `443`| &#9745;                |
| Nzbget                                   | `nzbget`             | `6789`                 | `6789`            | &#9745;                |
| Sabnzb                                   | `sabnzb`             | `8082`                 | `8080`            | &#9745;                |
| Authentik                                | `authentik-server`   | `9001` and `9443`      | `9000` and `9443` | &#9745;                |
| Tdarr                                    | `tdarr`              | `8265` and `8266`      | `8265` and `8266` | &#9745;                |
| HomePage                                 | `homepage`           | `3000`                 | `3000`            | &#9745;                |
| Flaresolverr                             | `flaresolverr`       | `8191`                 | `8191`            | &#9744;                |
| Uptime Kuma                              | `uptime-kuma`        | `3001`                 | `3001`            | &#9745;                |
| Heimdall                                 | `heimdall`           | `8000` and `8443`      | `80` and `443`    | &#9745;                |
