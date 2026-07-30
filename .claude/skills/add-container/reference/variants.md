# Non-standard container shapes

For anything that is not a plain web app, start from the real file listed here rather than
the generic skeleton. Paths are relative to `roles/hmsdocker/templates/containers/`.

## GPU transcoding — `jellyfin.yml.j2`

Intel QSV/VAAPI and Nvidia are separate flags; a template can support both.

```jinja
    {% if enable_intel_gpu %}
    devices:
      - /dev/dri:/dev/dri
    {% endif %}
    environment:
      - TZ=${TIMEZONE}
      - PUID=${PUID}
      - PGID=${PGID}
    {% if enable_nvidia_gpu %}
      - NVIDIA_VISIBLE_DEVICES=all
    runtime: nvidia
    {% endif %}
```

Note the Nvidia block closes the `environment:` list *and* adds a sibling `runtime:` key —
it must be the last thing in `environment:`.

Transcode scratch space, same file:

```jinja
    volumes:
      {% if not hmsdocker_transcode_tmpfs_enabled | default(false) %}
      - {{ plex_transcode_folder }}/cache:/cache
      {% endif %}
    {% if hmsdocker_transcode_tmpfs_enabled | default(false) %}
    tmpfs:
      - /cache:size={{ hmsdocker_transcode_tmpfs_size | default('4g') }},mode=1777
    {% endif %}
```

Transcoders that use a shared temp path (tdarr, fileflows, unmanic) mount
`hmsdocker_transcode_temp_path` from `defaults/main/service_misc.yml`.

## VPN download client — `qbittorrent.yml.j2`, `deluge.yml.j2`

The VPN runs *inside* the container (binhex images) — there is no `network_mode: service:`
indirection. WireGuard and OpenVPN need different capabilities:

```jinja
    {% if hmsdocker_vpn_type == 'wireguard' %}
    privileged: true
    sysctls:
      - net.ipv4.conf.all.src_valid_mark=1
    {% else %}
    cap_add:
      - NET_ADMIN
    {% endif %}
    environment:
      - VPN_ENABLED=yes
      - VPN_USER=${VPN_USER}
      - VPN_PASS=${VPN_PASS}
      - VPN_PROV={{ (hmsdocker_vpn_provider | default('', true) | lower) if (hmsdocker_vpn_provider | default('', true) | lower) in ['pia', 'airvpn', 'protonvpn', 'custom'] else 'custom' }}
      - VPN_CLIENT={{ hmsdocker_vpn_type }}
      - LAN_NETWORK={{ hms_docker_network_subnet }}
```

`tasks/main.yml` gates VPN validation on `transmission`/`deluge`/`qbittorrent` specifically
— a new VPN client would need adding there.

## Host networking — `beszel.yml.j2` (agent), `netdata.yml.j2`

`network_mode: host` replaces `networks:` entirely and makes `ports:` meaningless. A
host-networked service cannot be Traefik-routed through `proxy_net`, so it **omits the
`traefik` key** from its map entry — no entry in the map ever writes `traefik: false`,
because the derived fact filters on `selectattr('value.traefik', 'defined')` first, so an
absent key is enough. Such entries are minimal; netdata's is just `enabled`, `homepage`,
`homepage_stats`. The alternative, as with beszel, is a `traefik: true` hub on `proxy_net`
with only the agent host-networked.

## Device passthrough with a loop — `scrutiny.yml.j2`, `beszel.yml.j2` (agent)

```jinja
    devices:
    {% for device in hmsdocker_monitor_disk_devices %}
      - {{ device }}
    {% endfor %}
    cap_add:
      - SYS_RAWIO # required for S.M.A.R.T. data
      - SYS_ADMIN # required for NVMe S.M.A.R.T. data
```

`hmsdocker_monitor_disk_devices` lives in `defaults/main/service_misc.yml` and is shared —
reuse it, don't add a parallel list.

## Multiple containers in one template — `n8n.yml.j2`, `beszel.yml.j2`

One template file may define several services. Conventions:

- Sidecar names are prefixed with the primary key (`n8n-postgres`, `beszel-agent`) so
  `container_name` stays unambiguous.
- The map has **one** entry, for the primary service only.
- Private networks and named volumes get top-level blocks at the bottom of the same file:

  ```yaml
  volumes:
    n8n_data:

  networks:
    n8n_net:
      driver: bridge
      attachable: false
  ```

- Startup ordering uses `depends_on` with `condition: service_healthy`, which requires the
  dependency to define a `healthcheck`.
- Directories the sidecar needs (`db`, `db-init`) are created in
  `tasks/container_prereqs/<key>.yml`, not by the map's `directory: true`.

## No config dir, no labels — `flaresolverr.yml.j2`

A pure daemon: `download_net` only, no volumes, no labels, no Traefik. Its whole map entry
is two keys — `enabled: false` and `expose_ports: false` — everything else omitted. Still
gates `ports:` and still has a healthcheck.

## Image without PUID/PGID support — `autobrr.yml.j2`, `n8n.yml.j2`

```yaml
    user: ${PUID}:${PGID}
    environment:
      - TZ=${TIMEZONE}
```

Drop the `PUID=`/`PGID=` env vars entirely; passing both is redundant and some images
error on unknown vars.

## Homepage widget with username/password — `dockhand.yml.j2`, `beszel.yml.j2`

```yaml
      - homepage.widget.username=${DOCKHAND_USER:-dockhanduserisblank}
      - homepage.widget.password=${DOCKHAND_PASS:-dockhandpasswordisblank}
```

Beszel additionally pins `- homepage.widget.version=2`. These vars need a line in
`templates/env.j2` and a blank default in `defaults/main/homepage_api_keys.yml`
(`hmsdocker_homepage_dockhand_user:` etc.).

For a key that can be scraped from the app's own config on disk, add a `stat` + `slurp`
block plus an entry in the `api_keys` dict in `tasks/app_api_key_reader.yml` and reference
it as `{{ api_keys.<key>_key | default('') }}` in `env.j2` — that is the sonarr/sabnzbd
pattern.

## Custom Traefik middleware — `n8n.yml.j2`

n8n defines its own headers middleware chain in labels instead of using the shared
`internal-*@file` middlewares. This is an exception; do not copy it unless the app has a
specific requirement (n8n needs `SSLHost`/HSTS headers). Its labels are also unconditional,
which is why n8n has no `traefik_enabled_containers` gate — also not a pattern to copy.

## Conditional on another service — `notifiarr.yml.j2`

```jinja
    {% if 'sabnzbd' in enabled_containers %}
      - DN_SABNZBD_0_NAME=SABnzbd
      - DN_SABNZBD_0_URL=http://sabnzbd:8080
      - DN_SABNZBD_0_API_KEY=${SABNZBD_KEY}
    {% endif %}
```

Use `enabled_containers` (not the raw map) when one service needs to know whether another
is running.
