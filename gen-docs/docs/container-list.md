---
sidebar_position: 2
---

# Container List

Below is a list of all currently implemented containers.

Have one you want to add? Submit an [Issue](https://github.com/ahembree/ansible-hms-docker/issues) or [Pull Request](https://github.com/ahembree/ansible-hms-docker/pulls)!

## Media Servers

- [Plex](https://docs.linuxserver.io/images/docker-plex/)
- [Jellyfin](https://docs.linuxserver.io/images/docker-jellyfin/)
- [Emby](https://docs.linuxserver.io/images/docker-emby/)

## Media Management Systems

- [Sonarr](https://github.com/Sonarr/Sonarr): tv series management
- [Radarr](https://github.com/Radarr/Radarr): movie management
- [Lidarr](https://github.com/Lidarr/Lidarr): music management
- [Overseerr](https://github.com/sct/overseerr): request platform
- [Jellyseerr](https://github.com/Fallenbagel/jellyseerr): request platform with Jellyfin and Emby support
- [Prowlarr](https://github.com/Prowlarr/Prowlarr): tracker management
- [Bazarr](https://github.com/morpheus65535/bazarr): subtitle management
- [Requestrr](https://github.com/thomst08/requestrr): chat client for requests
- [Calibre](https://github.com/linuxserver/docker-calibre): ebook management
- [Tdarr](https://github.com/HaveAGitGat/Tdarr): media transcoding
- [Maintainerr](https://github.com/Maintainerr/Maintainerr): media management
- [tinyMediaManager](https://gitlab.com/tinyMediaManager/tinyMediaManager): media management
- [Tube Archivist](https://github.com/tubearchivist/tubearchivist): YouTube media management
- [Pinchflat](https://github.com/kieraneglin/pinchflat): YouTube media management
- [Huntarr](https://github.com/plexguide/Huntarr.io): finds missing and upgrades media items
- [Cleanuparr](https://github.com/Cleanuparr/Cleanuparr): cleanup of unwanted or blocked files
- [Fileflows](https://fileflows.com/): media transcoding
- [Unmanic](https://github.com/Unmanic/unmanic): media transcoding
- [Dispatcharr](https://github.com/Dispatcharr/Dispatcharr): IPTV manager

## Download Clients

- [Transmission](https://github.com/haugene/docker-transmission-openvpn): download client with VPN and HTTP proxy
- [NZBGet](https://docs.linuxserver.io/images/docker-nzbget/): download client
- [Sabnzbd](https://docs.linuxserver.io/images/docker-sabnzbd/): download client
- [qBittorrent](https://github.com/binhex/arch-qbittorrentvpn/): download client with VPN and HTTP proxy
- [Deluge](https://github.com/binhex/arch-delugevpn/): download client with VPN and HTTP proxy

## Analytics / Dashboards

- [Tracearr](https://github.com/connorgallopo/Tracearr): real-time monitoring and analytics
- [Tautulli](https://github.com/Tautulli/Tautulli): analytics
- [Homepage](https://github.com/gethomepage/homepage): dashboarding / homepage
- [Heimdall](https://github.com/linuxserver/Heimdall): dashboarding / homepage

## Networking

- [Traefik](https://hub.docker.com/_/traefik): reverse proxy (with SSL support from Let's Encrypt if configured)
- [Tailscale](https://hub.docker.com/r/tailscale/tailscale): mesh VPN
- [Cloudflare-DDNS](https://hub.docker.com/r/oznu/cloudflare-ddns/): dynamic dns (if enabled)
- [Cloudflare Tunnel](https://hub.docker.com/r/cloudflare/cloudflared): Allows you to expose HTTP services without port-forwarding on your router, [see here](https://www.cloudflare.com/products/tunnel/) for more info

## Misc

- [Portainer](https://hub.docker.com/r/portainer/portainer): container management GUI
- [Watchtower](https://github.com/containrrr/watchtower): automatic container updates
- [Authentik](https://github.com/goauthentik/authentik): SSO (Single Sign-On), requires TLS/SSL with Traefik
- [Flaresolverr](https://github.com/FlareSolverr/FlareSolverr): CAPTCHA solving
- [Uptime Kuma](https://github.com/louislam/uptime-kuma): service status monitoring
- [Kavita](https://hub.docker.com/r/kizaing/kavita): digital library
- [Unpackerr](https://github.com/Unpackerr/unpackerr): download decompression
- [Autobrr](https://github.com/autobrr/autobrr): torrent automation
- [Notifiarr](https://github.com/Notifiarr/notifiarr): notification system
- [Speedtest-Tracker](https://github.com/alexjustesen/speedtest-tracker): notification system
- [Recyclarr](https://github.com/recyclarr/recyclarr): auto-sync for [TRaSH guides](https://trash-guides.info/)
- [PASTA](https://github.com/cglatot/pasta): audio and subtitle management
- [Netdata](https://github.com/netdata/netdata): observability
- [Wizarr](https://github.com/wizarrrr/wizarr): media server invite management
- [Checkrr](https://github.com/aetaric/checkrr): checks for corrupt media
- [Backrest](https://github.com/garethgeorge/backrest): backup system with rclone support
- [Error-pages](https://github.com/tarampampam/error-pages): Error pages for Traefik

## Adding New Containers

If you'd like to have a container added, please submit a Discussion post or a Pull Request!

If wanting to submit a pull request, the following Compose file settings are typically used across all containers. The below is an example Jinja2 template, which is how all of the container `.yml` files are generated

A list of the locations where items will need to be updated:

- This documentation
- `roles/hmsdocker/defaults/main/container_map.yml`
- `roles/hmsdocker/templates/containers` will store the compose template file (example below) with the naming format of `<container name>.yml.j2`
- Any additional container-specific configuration in `roles/hmsdocker/defaults/main/service_misc.yml`
- Any API keys/secrets in `roles/hmsdocker/templates/env.j2`
  - If API keys need to be read from a file to auto-populate the `.env`, there is a task file in `roles/hmsdocker/tasks/app_api_key_reader.yml` that retrieves the keys from the file
  - The task that generates the `.env` file in `roles/hmsdocker/tasks/main.yml` will also need to be updated to use the newly retrieved key
- If any tasks/prerequisits need to be ran _before_ the container starts, create a `<container name>.yml` Ansible task file in `roles/hmsdocker/tasks/container_prereqs`
- If any tasks need to be ran _after_ the container starts, create a `<container name>.yml` Ansible task file in `roles/hmsdocker/tasks/container_postreqs`
- If the container needs to be restarted after any config changes, create a new handler task in `roles/hmsdocker/handlers/main.yml`

```yml
services:
  <container name>:
    image: <container image>
    container_name: <container name>
    restart: ${RESTART_POLICY}
    logging:
      options:
        max-size: "12m"
        max-file: "5"
      driver: json-file
    # Depends on the network access it needs, proxy_net is required for Traefik
    networks:
      - proxy_net
    {% if '<container name>' in expose_ports_enabled_containers %}
    # Check the container map to see if any existing containers will cause an overlap
    # If so, this port will need to be changed to no longer overlap
    ports:
      - <container UI port>:<container UI port>
    {% endif %}
    environment:
      - PUID=${PUID}
      - PGID=${PGID}
      - TZ=${TIMEZONE}
    volumes:
      - ${HMSD_APPS_PATH}/<container name>/config:/config
      # If the container needs access to your media data, add the below
      - ${HMSD_MOUNT_PATH}:/data
    {% if '<container name>' in traefik_enabled_containers or '<container name>' in homepage_enabled_containers %}
    labels:
      {% if '<container name>' in traefik_enabled_containers %}
      - traefik.enable=true
      - traefik.http.services.<container name>-${COMPOSE_PROJECT}.loadbalancer.server.port=<container UI port>
      - traefik.http.routers.<container name>-${COMPOSE_PROJECT}.rule=Host(`{{ hms_docker_container_map['<container name>']['proxy_host_rule'] | default('<container name>') }}.${HMSD_DOMAIN}`)
      - traefik.http.routers.<container name>-${COMPOSE_PROJECT}.middlewares={{ 'external' if '<container name>' in expose_public_enabled_containers else 'internal' }}-{{ 'secured' if traefik_security_hardening else 'ipallowlist' }}@file{{ ',authentik-proxy-${COMPOSE_PROJECT}-<container name>-midware@docker' if '<container name>' in authentik_enabled_containers }}
      {% endif %}
      # Below is only for Homepage
      {% if '<container name>' in homepage_enabled_containers %}
      - homepage.group=<Homepage group name>
      - homepage.name=<container name>
      - homepage.icon=<container name>.png
      - homepage.href=http://{{ hms_docker_container_map['<container name>']['proxy_host_rule'] | default('<container name>') }}.${HMSD_DOMAIN}
      - homepage.description=<homepage description>
      # If the container supports a widget, there is an additional task that runs to "slurp" the API key from a file automatically (if supported) in `tasks/app_api_key_reader.yml` that is then inserted into the `.env` file template
      - homepage.widget.type=<container name>
      - homepage.widget.url=http://<container name>:<container UI port>
      - homepage.widget.key=${<CONTAINER NAME>_KEY:-apikeyapikeyapikey}
        {% if hmsdocker_homepage_stats_enabled_<container name> %}
      - homepage.showStats=true
        {% endif %}
      {% endif %}
    {% endif %}
```
