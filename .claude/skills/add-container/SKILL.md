---
name: add-container
description: Add a new container/service to the ansible-hms-docker stack — container_map entry, compose Jinja template, Traefik/Authentik/Homepage wiring, prereq/postreq tasks, env vars, docs and CI. Use when asked to add, wire up, or onboard a service (e.g. "add byparr", "add <app> to the stack"), or when creating/editing a file under roles/hmsdocker/templates/containers/.
---

# Adding a container to hms-docker

Two files are always required. Everything else is conditional, and **adding conditional
files that nothing consumes is the most common failure mode here** — see
[Anti-patterns](#anti-patterns).

| | File |
|-|-|
| Required | `roles/hmsdocker/defaults/main/container_map.yml` — the map entry |
| Required | `roles/hmsdocker/templates/containers/<key>.yml.j2` — the compose fragment |

There is **no** edit to `docker-compose.yml.j2`, no Traefik dynamic-config entry, and no
task-file registration. The map is filtered into derived facts in
[tasks/main.yml](../../../roles/hmsdocker/tasks/main.yml) (lines 6–143), the render task
loops those facts (lines 292–303), and the top-level compose builds its `include:` list
from `compose_files_created.results`.

## 1. Gather inputs

Before writing anything, know:

- **service key** — lowercase, hyphens ok. This one string is the map key, the compose
  service name, `container_name`, and the template filename. They must all match.
- **image** — full ref including registry (`lscr.io/linuxserver/…`, `ghcr.io/…`).
- **container UI port** — the port the app listens on *inside* the container.
- **config dir?** — does it need `${HMSD_APPS_PATH}/<key>/config`?
- **media access?** — does it need `${HMSD_MOUNT_PATH}:/data`?
- **Traefik?** — anything with a web UI: yes. Daemons with no UI (flaresolverr,
  watchtower, cloudflare-ddns): no.
- **Homepage widget?** — check [the Homepage widget docs](https://gethomepage.dev/widgets/)
  for whether the app has a widget type and what credential it takes (`key`, or
  `username`/`password`).
- **secrets/tunables** — anything the user must supply.

If the image or port is not known, ask the user rather than guessing. A wrong port
silently produces a 502 through Traefik.

## 2. Pick a host port that does not collide

75 host ports are already claimed. Enumerate them — the `"?` is load-bearing, five mappings
are quoted (cleanuparr, cross-seed, fileflows, n8n, tracearr) and a regex without it
silently misses ports 2468, 3002, 5678, 11011 and 19200:

```bash
grep -rhoE '^\s+- "?[0-9]+:[0-9]+' roles/hmsdocker/templates/containers/ | tr -d '" -' | sort -t: -k1 -n
```

Convention: keep the **container** port on the right and shift the **host** port left-side
when it collides — `8080:8080` is taken, so scrutiny uses `8087:8080`, dockhand uses
`3003:3000`, beszel uses `8091:8090`.

## 3. Map entry — `defaults/main/container_map.yml`

Key meanings are documented in that file's own header (lines 3–13). Rules:

- **Insert alphabetically by key.** Read the two entries that will surround yours *before*
  editing, and confirm afterwards that neither was clobbered. Getting this wrong is a
  recorded regression (see [Anti-patterns](#anti-patterns)).
- Keys **within** an entry are also alphabetical.
- **`enabled: false`** for anything new. Never ship a service on by default.
- Emit only the keys that apply:
  - `directory` — omit for containers with no config dir (watchtower, tailscale, netdata,
    flaresolverr, cloudflare-*).
  - `homepage` / `homepage_stats` — omit when there is no Homepage integration.
  - `authentik_provider_type` — only when the service genuinely uses OAuth2. Default is
    `proxy` and is left implicit on almost every entry.
- `proxy_host_rule` is the subdomain. Usually equals the key; shorten when the key is long
  (`speedtest-tracker` → `speedtest`, `tinymediamanager` → `tmm`).

Standard shape:

```yaml
  <key>:
    authentik: false
    directory: true
    enabled: false
    expose_ports: false
    expose_to_public: false
    homepage: true
    homepage_stats: false
    proxy_host_rule: <key>
    traefik: true
```

## 4. Compose template — `templates/containers/<key>.yml.j2`

Read [reference/template-anatomy.md](reference/template-anatomy.md) for the annotated
skeleton, and [reference/variants.md](reference/variants.md) when the service is not a
plain web app (GPU, VPN, host networking, sidecar DB, no config dir, no PUID support).

The best in-repo model to copy is
[scrutiny.yml.j2](../../../roles/hmsdocker/templates/containers/scrutiny.yml.j2) — it has
port gating, the full label block, a device loop, and a healthcheck.

Non-negotiables:

- **A map key with no matching template file fails the play.** Always create both.
- **Gate on the derived list facts, never the raw map.** The real names are
  `enabled_containers`, `expose_ports_enabled_containers`, `traefik_enabled_containers`,
  `homepage_enabled_containers`, `homepage_stats_enabled_containers`,
  `expose_public_enabled_containers`, `authentik_enabled_containers`.
- **`${...}` is a shell var from the `.env`**, rendered by
  [env.j2](../../../roles/hmsdocker/templates/env.j2) — `HMSD_APPS_PATH`, `HMSD_MOUNT_PATH`,
  `HMSD_DOMAIN`, `PUID`, `PGID`, `TIMEZONE`, `RESTART_POLICY`, `COMPOSE_PROJECT`. Ansible
  vars use `{{ }}`. Do not confuse them.
- Rendering sets `trim_blocks: yes` + `lstrip_blocks: yes`, so `{% %}` indentation is
  cosmetic — match the surrounding file (most use 4 spaces, nested stats block uses 8).
- The four Traefik label lines are near-verbatim boilerplate. Every router and service name
  carries the `-${COMPOSE_PROJECT}` suffix.
- **`security_opt: no-new-privileges:true` is the default but is not universal.** Images
  that escalate privileges at runtime break under it (tdarr, fileflows). When it must go,
  comment the block out in place with the reason — see
  [reference/template-anatomy.md](reference/template-anatomy.md).
- **Authentik needs no block in the template.** It is only the conditional
  `,authentik-proxy-${COMPOSE_PROJECT}-<key>-midware@docker` suffix on the middlewares
  label. Outposts are generated by `tasks/container_prereqs/authentik.yml` looping
  `authentik_proxy_enabled_containers`.

## 5. Conditional wiring — add only when the service needs it

| File | Add **only if** |
|-|-|
| `tasks/container_prereqs/<key>.yml` | dirs/files/keys must exist before the container starts. Model: [n8n.yml](../../../roles/hmsdocker/tasks/container_prereqs/n8n.yml) |
| `tasks/container_postreqs/<key>.yml` | config must be patched after first start. Model: [sabnzbd.yml](../../../roles/hmsdocker/tasks/container_postreqs/sabnzbd.yml) |
| `tasks/app_inits/<key>.yml` | the app is bootstrapped over its API (arr-style only) |
| `templates/env.j2` | the template already references a `${VAR}` that does not exist yet |
| `defaults/main/service_misc.yml` | a user-tunable var the template actually consumes |
| `defaults/main/homepage_api_keys.yml` | a Homepage widget needs a user-supplied credential |
| `tasks/app_api_key_reader.yml` | the key can be scraped from the app's own config file on disk |
| `handlers/main.yml` | some task genuinely `notify:`s a restart |

Prereq/postreq/app_init files are **auto-discovered by filename** — `fileglob` over the
directory, intersected with `enabled_containers`. Dropping the file in is the whole
wiring step; there is no list to register it in.

Order matters for env vars: add the `${VAR}` reference in the template **first**, then the
line in `env.j2`, then the default in `service_misc.yml` or `homepage_api_keys.yml`. Never
the reverse — that is how orphan vars get committed.

Homepage credential styles:

- API key: `- homepage.widget.key=${<KEY>:-apikeyapikeyapikey}`
- user/pass: `- homepage.widget.username=${X_USER:-}` / `.password=${X_PASS:-}`
  (see dockhand, beszel)

## 6. Docs, version, CI

- **`docs-astro/src/content/docs/docs/container-list.mdx`** — two edits:
  1. A bullet under the right `##` category (Media Servers / Media Management Systems /
     Download Clients / Analytics-Dashboards / Networking / Misc), format
     `- [Name](upstream-url): short description <Badge text="New" variant="success"/>`.
  2. A row appended to the `### Map` table: Service Name, Enabled by Default, Container
     Name, Host Port (if enabled), Container Port, Accessible via Traefik, Homepage
     Integration — using `&#9745;` for checked and `&#9744;` for unchecked.
- **`docs-astro/src/content/docs/docs/release-notes/v<major>.<minor>.md`** — add a
  `## v<version>` section at the top of the file. The header must match
  `hmsd_current_version` exactly; the release workflow extracts everything between it and
  the next `## `.
- **`hms-docker.yml`** — bump `hmsd_current_version` (3-part semver). Tell the user this
  cuts a GitHub Release when merged to master.
- **`.github/extra-vars.yml`** — add an entry to the duplicated CI container map so the
  deployment test exercises the service. It is JSON-ish with unquoted scalar values and a
  different key order from the real map:

  ```json
      "<key>": {
        "enabled": true,
        "proxy_host_rule": <key>,
        "directory": true,
        "traefik": true,
        "authentik": false,
        "authentik_provider_type": proxy,
        "expose_to_public": false,
        "homepage": true,
        "homepage_stats": false
      },
  ```

  `enabled: true` here is correct and intentional — it is the opposite of the real map.
  If the service is enabled in CI and Traefik-routed, also add its subdomain to the
  `/etc/hosts` line in `.github/workflows/run-playbook.yml`.

Do **not** touch `README.md` unless the service adds a headline capability.

## 7. Verify (static — nothing mutates the host)

```bash
# map keys and template filenames correspond 1:1 — 57 and 57. Any output is a real break;
# there are no benign exceptions. authentik is not one (it has both a map entry and
# authentik.yml.j2, it is just rendered outside the generic loop), and neither are the 4k
# instances (sonarr-4k/radarr-4k are extra compose services *inside* sonarr.yml.j2 and
# radarr.yml.j2, never their own map key or template file).
diff <(grep -oP '^  \K[a-z0-9-]+(?=:)' roles/hmsdocker/defaults/main/container_map.yml | sort) \
     <(ls roles/hmsdocker/templates/containers/ | sed 's/\.yml\.j2$//' | sort)

# duplicate host ports. The known-benign baseline is 443, 5055, 8096, 8266, 8920 —
# traefik's own repeat (443 tcp + udp), overseerr/seerr, jellyfin/emby, tdarr's own repeat,
# jellyfin/emby. Anything else is your collision.
grep -rhoE '^\s+- "?[0-9]+:[0-9]+' roles/hmsdocker/templates/containers/ | tr -d '" -' \
  | cut -d: -f1 | sort -n | uniq -d

# every derived-list fact the new template references must be a real one
grep -oE 'in [a-z_]+_containers' roles/hmsdocker/templates/containers/<key>.yml.j2 | sort -u

# the map entry parses and looks right
./bin/yq '.hms_docker_container_map.<key>' roles/hmsdocker/defaults/main/container_map.yml
```

Then read the two `container_map.yml` entries adjacent to the new one and confirm they are
intact.

`make check` (Ansible dry-run) will catch Jinja syntax errors but needs a populated
`inventory/group_vars/all/` and installs galaxy requirements — offer it, let the user
decide. `make apply` mutates the host; never run it unprompted.

## Anti-patterns

Every item below is a real correction from commit `b241ceb` ("fix: claudes mistakes"),
which reverted most of an agent-authored service addition:

- **A restart handler nothing notifies.** Do not add to `handlers/main.yml` unless a task
  you also wrote has `notify: Restart <key>`.
- **A `service_misc.yml` var the template never reads.** Same for `env.j2` lines.
- **`enabled: true` in `container_map.yml`.** New services ship disabled. Only
  `.github/extra-vars.yml` gets `enabled: true`.
- **An alphabetical insert that overwrites the neighbouring entry.** The librariarr add
  rewrote the adjacent `lidarr` block's key and `proxy_host_rule`.
- **Editing `README.md`** for a service that is not a headline feature.
