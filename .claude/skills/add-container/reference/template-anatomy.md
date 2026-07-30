# Container template anatomy

The canonical skeleton for `roles/hmsdocker/templates/containers/<key>.yml.j2`. Replace
every `<key>`, `<uiport>`, `<hostport>` below.

```jinja
services:
  <key>:
    image: <registry>/<image>:latest
    container_name: <key>
    restart: ${RESTART_POLICY}
    security_opt:
      - no-new-privileges:true
    logging:
      options:
        max-size: "12m"
        max-file: "5"
      driver: json-file
    networks:
      - proxy_net
    {% if '<key>' in expose_ports_enabled_containers %}
    ports:
      - <hostport>:<uiport>
    {% endif %}
    environment:
      - PUID=${PUID}
      - PGID=${PGID}
      - TZ=${TIMEZONE}
    volumes:
      - ${HMSD_APPS_PATH}/<key>/config:/config
      - ${HMSD_MOUNT_PATH}:/data
    {% if '<key>' in traefik_enabled_containers or '<key>' in homepage_enabled_containers %}
    labels:
      {% if '<key>' in traefik_enabled_containers %}
      - traefik.enable=true
      - traefik.http.services.<key>-${COMPOSE_PROJECT}.loadbalancer.server.port=<uiport>
      - traefik.http.routers.<key>-${COMPOSE_PROJECT}.rule=Host(`{{ hms_docker_container_map['<key>']['proxy_host_rule'] | default('<key>') }}.${HMSD_DOMAIN}`)
      - traefik.http.routers.<key>-${COMPOSE_PROJECT}.middlewares={{ 'external' if '<key>' in expose_public_enabled_containers else 'internal' }}-{{ 'secured' if traefik_security_hardening else 'ipallowlist' }}@file{{ ',authentik-proxy-${COMPOSE_PROJECT}-<key>-midware@docker' if '<key>' in authentik_enabled_containers }}
      {% endif %}
      {% if '<key>' in homepage_enabled_containers %}
      - homepage.group=<group>
      - homepage.name=<Display Name>
      - homepage.icon=<key>.png
      - homepage.href=http://{{ hms_docker_container_map['<key>']['proxy_host_rule'] | default('<key>') }}.${HMSD_DOMAIN}
      - homepage.description=<short description>
      - homepage.widget.type=<homepage widget type>
      - homepage.widget.url=http://<key>:<uiport>
      - homepage.widget.key=${<KEY>_KEY:-apikeyapikeyapikey}
        {% if '<key>' in homepage_stats_enabled_containers %}
      - homepage.showStats=true
        {% endif %}
      {% endif %}
    {% endif %}
    healthcheck:
      test: curl -f http://127.0.0.1:<uiport>/ || exit 1
      interval: 5s
      timeout: 2s
      retries: 3
      start_period: 30s
```

## Block by block

### `image`

Pin the registry. `lscr.io/linuxserver/*` images support `PUID`/`PGID`; most others do not
— check before adding those env vars.

### `restart`, `security_opt`, `logging`

Boilerplate on essentially every service — `security_opt: no-new-privileges:true` is active
on 55 of the 57 templates.

**Not every image tolerates it.** Anything that escalates privileges at runtime will break:
tdarr cannot create a library with it on, and fileflows' Dockermods need `sudo` to install
ffmpeg. Symptoms are runtime, not startup — the container comes up healthy and then a
specific feature silently fails, so it is worth checking the upstream image's docs for
`sudo`/`setuid` use before assuming it is fine.

When it has to go, **comment it out in place with the reason** rather than deleting it —
that is the convention in both affected templates, and it stops the next person from
re-adding it:

```yaml
    restart: ${RESTART_POLICY}
    # Cannot enable security_opt:no-new-privileges, if enabled then you cannot create a library
    #security_opt:
    #  - no-new-privileges:true
    logging:
```

Removing it from a shipped container is a user-visible behaviour change: `6f93080` (tdarr)
bumped `hmsd_current_version` and added a release-note line for exactly this.

### `networks` — required

- `proxy_net` — required for Traefik to reach the container. Attachable.
- `download_net` — add for download-adjacent apps (autobrr, flaresolverr, qbittorrent,
  deluge). Non-attachable bridge.
- A service can declare its own private network in the same file — see `n8n.yml.j2`, which
  appends a top-level `networks: n8n_net:` block.

Both `proxy_net` and `download_net` are defined in
`roles/hmsdocker/templates/docker-compose.yml.j2` — do not redefine them.

### `environment`

`PUID`/`PGID`/`TZ` is the common trio. If the image has no PUID support, drop them and use
`user: ${PUID}:${PGID}` at the service level instead (autobrr, n8n).

Env values can be computed from Ansible vars — beszel builds its `APP_URL` from
`traefik_ssl_enabled`, the map's `proxy_host_rule`, and `expose_ports_enabled_containers`.

Compose interpolation defaults work and are used for optional secrets:
`${BESZEL_TOKEN:-}`, `${CAPTCHA_SOLVER:-none}`.

### `volumes`

- Config: `${HMSD_APPS_PATH}/<key>/config:/config`. Requires `directory: true` in the map,
  which is what creates the dir.
- Media: `${HMSD_MOUNT_PATH}:/data` — only if the service touches media.
- Docker socket: `/var/run/docker.sock:/var/run/docker.sock` (dockhand, portainer); add
  `:ro` when read-only suffices.

### `ports` — always gated

```jinja
    {% if '<key>' in expose_ports_enabled_containers %}
    ports:
      - <hostport>:<uiport>
    {% endif %}
```

Never emit an unguarded `ports:`. Annotate optional/UDP ports inline the way jellyfin does
(`- 7359:7359/udp #optional`).

### `labels` — the whole block is gated

The outer `{% if ... in traefik_enabled_containers or ... in homepage_enabled_containers %}`
prevents emitting an empty `labels:` key when both are off.

The middlewares label resolves to one of four file-provider middlewares —
`internal-ipallowlist@file`, `internal-secured@file`, `external-ipallowlist@file`,
`external-secured@file` — defined in
`roles/hmsdocker/templates/traefik/hmsd_traefik_middlewares.yml.j2`, plus the optional
Authentik forward-auth suffix. Copy the line verbatim and change only the service key.

Homepage groups already in use, with usage counts: `Managers` (12 — the *arr stack, the
seerr family, checkrr, librariarr, pinchflat, tubearchivist), `Infrastructure` (12),
`Media` (9 — media servers plus analytics/transcoding), `Downloads` (7), and
`Managers - 4K` (2, used only inside the sonarr/radarr 4k blocks). Pick an existing one and
match the string exactly: `homepage_services.yaml` ships empty, so Homepage builds every
group from these labels and a near-miss silently creates a new one-service group.

Widget types and their required credentials come from
[the Homepage widget docs](https://gethomepage.dev/widgets/) — if the app has no widget,
omit the three `homepage.widget.*` lines and keep the rest.

`homepage.showStats` is conventionally nested one level deeper (8 spaces on the `{% if %}`)
in 28 of the 37 gates that guard it; the other 9 (radarr, sabnzbd, prowlarr, tdarr,
tautulli, netdata, cloudflare-tunnel, sonarr's 4k block) leave it flush at 6. It is purely
visual — `lstrip_blocks` makes both forms render identically. Use 8 in new templates.

### `healthcheck`

Near-universal. `curl -f http://127.0.0.1:<uiport>/ || exit 1` with
`interval: 5s / timeout: 2s / retries: 3 / start_period: 30s` (60s for heavy apps).

If the image is distroless or has no shell, use the exec form with a binary the image
actually ships — beszel uses `["CMD", "/beszel", "health", "--url", "http://127.0.0.1:8090"]`
and carries a comment explaining why.

Prefer a real health endpoint when the app has one: `/health` (jellyfin, flaresolverr),
`/api/healthz` (autobrr).

## Rendering semantics

`tasks/main.yml` renders these with `trim_blocks: yes` and `lstrip_blocks: yes`, so:

- Leading whitespace before `{%` is stripped — indent tags to match the surrounding file
  for readability only.
- The newline after a block tag is consumed — no blank lines leak into the output YAML.

`{{ }}` is Ansible/Jinja, evaluated at render time. `${...}` is Docker Compose
interpolation, evaluated at `docker compose up` from the generated `.env`. A `{{ }}`
expression can safely contain a `${...}` literal — that is exactly what the middlewares
label does.
