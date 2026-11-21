# Container template anatomy

The canonical skeleton for `roles/hmsdocker/templates/containers/<key>.yml.j2`. Replace
every `<key>`, `<uiport>`, `<hostport>` below.

```jinja
{% import 'macros/labels.j2' as labels with context %}
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
    {% if '<key>' in hmsdocker_expose_ports_enabled_containers %}
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
    {% if '<key>' in hmsdocker_traefik_enabled_containers or '<key>' in hmsdocker_homepage_enabled_containers %}
    labels:
      {% if '<key>' in hmsdocker_traefik_enabled_containers %}
      {{ labels.traefik('<key>', <uiport>) | indent(6) }}
      {% endif %}
      {% if '<key>' in hmsdocker_homepage_enabled_containers %}
      {{ labels.homepage('<key>', '<group>', '<Display Name>', '<short description>', widget={'type': '<homepage widget type>', 'url': 'http://<key>:<uiport>', 'key': '${<KEY>_KEY:-apikeyapikeyapikey}'}) | indent(6) }}
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
bumped `hmsdocker_current_version` and added a release-note line for exactly this. Today that
is a bullet under `## Unreleased` in the newest release-notes file, with no version bump
(the version is bumped only when a release is cut).

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
`hmsdocker_ssl_enabled`, the map's `proxy_host_rule`, and `hmsdocker_expose_ports_enabled_containers`.

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
    {% if '<key>' in hmsdocker_expose_ports_enabled_containers %}
    ports:
      - <hostport>:<uiport>
    {% endif %}
```

Never emit an unguarded `ports:`. Annotate optional/UDP ports inline the way jellyfin does
(`- 7359:7359/udp #optional`).

### `labels` — the whole block is gated

The outer `{% if ... in hmsdocker_traefik_enabled_containers or ... in hmsdocker_homepage_enabled_containers %}`
prevents emitting an empty `labels:` key when both are off.

The label lines themselves come from two macros in
`roles/hmsdocker/templates/macros/labels.j2`, imported on the first line of the template.
Call them at the indentation of the labels and pass the same width to `indent`:

- `labels.traefik('<key>', <uiport>)` writes the four Traefik labels (enable, service port,
  `Host` rule, middlewares). The middlewares label resolves to one of four file-provider
  middlewares (`internal-ipallowlist@file`, `internal-secured@file`,
  `external-ipallowlist@file`, `external-secured@file`, defined in
  `roles/hmsdocker/templates/traefik/hmsd_traefik_middlewares.yml.j2`) plus the optional
  Authentik and Tinyauth forward-auth suffixes. Options: `router=` (router name differs from
  the key), `host_default=` (fallback subdomain differs from the router name), `suffix=`,
  `scheme='https'` (the app only answers HTTPS), `authentik=false`, `tinyauth=false`.
- `labels.homepage('<key>', '<group>', '<Display Name>', '<short description>', ...)` writes
  the Homepage labels. Options: `icon=` (default `<key>.png`), `href='https'` or `href=none`,
  `host_default=`, `suffix=`, `widget={...}` (written as `homepage.widget.*` in the order
  given), `stats=` (`true`: `showStats` when `homepage_stats` is on, `'always'`, or `false`).

Labels a macro does not cover (extra Traefik middlewares, a second router) are written as
plain lines next to the macro call, see `n8n.yml.j2`, `traefik.yml.j2` and
`transmission.yml.j2`. A widget value that needs a Jinja expression cannot go through the
macro either, see `netdata.yml.j2`, `prowlarr.yml.j2` and `uptimekuma.yml.j2`.

Homepage groups already in use, with usage counts: `Managers` (12 — the *arr stack, the
seerr family, checkrr, librariarr, pinchflat, tubearchivist), `Infrastructure` (12),
`Media` (9 — media servers plus analytics/transcoding), `Downloads` (7), and
`Managers - 4K` (2, used only inside the sonarr/radarr 4k blocks). Pick an existing one and
match the string exactly: `homepage_services.yaml` ships empty, so Homepage builds every
group from these labels and a near-miss silently creates a new one-service group.

Widget types and their required credentials come from
[the Homepage widget docs](https://gethomepage.dev/widgets/). If the app has no widget,
leave out the `widget=` argument.


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
