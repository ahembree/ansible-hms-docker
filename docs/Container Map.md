# Container Map

## Connecting the Containers to each other

When connecting Prowlarr to Sonarr and Radarr and etc, you can use the name of the container (e.g. `prowlarr` or `radarr`) and then defining the container port to connect to (e.g. `prowlarr:9696` or `radarr:7878`).

Here's an example within Prowlarr:

![Prowlarr example](./_img/container_connect_example.png)

If you choose to expose the container ports on the host (by setting `container_expose_ports: yes` in the `vars/custom/container_settings.yml` file), see below for which ports are mapped to which container on the host.

**NOTE:** Ports are _NOT_ exposed by default (with the exception of Traefik)

## Map

| Service Name                             | Enabled by Default | Container Name       | Host Port (if enabled) | Container Port    | Accessible via Traefik |
| ---------------------------------------- | ------------------ | -------------------- | ---------------------- | ----------------- | ---------------------- |
| Plex                                     | &#9745;            | `plex`               | `32400`                | `32400`           | &#9745;                |
| Sonarr                                   | &#9745;            | `sonarr`             | `8989`                 | `8989`            | &#9745;                |
| Sonarr (Separate 4K instance if enabled) | &#9745;            | `sonarr-4k`          | `8990`                 | `8989`            | &#9745;                |
| Radarr                                   | &#9745;            | `radarr`             | `7878`                 | `7878`            | &#9745;                |
| Radarr (Separate 4K instance if enabled) | &#9745;            | `radarr-4k`          | `7879`                 | `7878`            | &#9745;                |
| Prowlarr                                 | &#9745;            | `prowlarr`           | `9696`                 | `9696`            | &#9745;                |
| Overseerr                                | &#9745;            | `overseerr`          | `5055`                 | `5055`            | &#9745;                |
| Requestrr                                | &#9745;            | `requestrr`          | `4545`                 | `4545`            | &#9745;                |
| Transmission UI Proxy                    | &#9745;            | `transmission-proxy` | `8081`                 | `8080`            | &#9745;                |
| Transmission (HTTP Proxy)                | &#9745;            | `transmission`       | `8888`                 | `8888`            | &#9744;                |
| Transmission (RPC)                       | &#9745;            | `transmission`       | `9091`                 | `9091`            | &#9744;                |
| Portainer                                | &#9745;            | `portainer`          | `9000`                 | `9000`            | &#9745;                |
| Bazarr                                   | &#9745;            | `bazarr`             | `6767`                 | `6767`            | &#9745;                |
| Tautulli                                 | &#9745;            | `tautulli`           | `8181`                 | `8181`            | &#9745;                |
| Traefik                                  | &#9745;            | `traefik`            | `80`, `8080`, `443`    | `80`, `8080`, `443`| &#9745;               |
| Nzbget                                   | &#9744;            | `nzbget`             | `6789`                 | `6789`            | &#9745;                |
| Sabnzb                                   | &#9744;            | `sabnzb`             | `8082`                 | `8080`            | &#9745;                |
| Authentik                                | &#9744;            | `authentik-server`   | `9001` and `9443`      | `9000` and `9443` | &#9745;                |
| Tdarr                                    | &#9744;            | `tdarr`              | `8265` and `8266`      | `8265` and `8266` | &#9745;                |
| HomePage                                 | &#9744;            | `homepage`           | `3000`                 | `3000`            | &#9745;                |
| Flaresolverr                             | &#9744;            | `flaresolverr`       | `8191`                 | `8191`            | &#9744;                |
| Uptime Kuma                              | &#9744;            | `uptime-kuma`        | `3001`                 | `3001`            | &#9745;                |
| Heimdall                                 | &#9744;            | `heimdall`           | `8000` and `8443`      | `80` and `443`    | &#9745;                |
| Readarr                                  | &#9744;            | `readarr`            | `8787`                 | `8787`            | &#9745;                |
| Kavita                                   | &#9744;            | `kavita`             | `5000`                 | `5000`            | &#9745;                |
| Calibre                                  | &#9744;            | `calibre`            | `8083`, `8182`, `8084` | `8080`, `8181`, `8081`| &#9745;            |
| Jellyfin                                 | &#9744;            | `jellyfin`           | `8096`, `8920`, `7359`, `1900` | `8096`, `8920`, `7359`, `1900` | &#9745;            |
| Emby                                     | &#9744;            | `emby`               | `8096`, `8920`         | `8096`, `8920`    | &#9745;                |
| Maintainerr                              | &#9744;            | `maintainerr`        | `6246`                 | `6246`            | &#9745;                |
| Lidarr                                   | &#9744;            | `lidarr`             | `8686`                 | `8686`            | &#9745;                |
| Autobrr                                  | &#9744;            | `autobrr`            | `7474`                 | `7474`            | &#9745;                |
| Notifiarr                                | &#9744;            | `notifiarr`          | `5454`                 | `5454`            | &#9745;                |
| Speedtest-Tracker                        | &#9744;            | `speedtest`          | `8090`, `8444`         | `8080`, `8443`    | &#9745;                |
| tinyMediaManager                         | &#9744;            | `tmm`                | `5900`, `4000`         | `5900`, `4000`    | &#9745;                |
| PASTA                                    | &#9744;            | `pasta`              | `8085`                 | `80`              | &#9745;                |

If both Jellyfin and Emby are enabled, then Emby will be available on ports `8097` and `8921` (if ports are being exposed for both)
