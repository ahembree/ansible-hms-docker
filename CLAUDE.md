# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Ansible playbook that deploys a Docker-based home media server stack (Plex, Sonarr/Radarr/Prowlarr/Bazarr, Transmission + optional VPN, Traefik + Let's Encrypt, Authentik SSO, Homepage, Cloudflare DDNS, optional Tailscale/Unifi DNS) onto a single Linux host. Connection is `local` — the playbook configures the machine it runs on. Tested on Ubuntu 22.04/24.04 in CI.

## Common commands

All day-to-day workflows go through the [Makefile](Makefile):

| Command | Purpose |
|-|-|
| `make config` | Copies role defaults (`roles/hmsdocker/defaults/main/*.yml`) into `inventory/group_vars/all/` for user customization. Prompts before overwriting. |
| `make check` | Dry run with `--diff --check`. |
| `make apply` | Live apply with `--diff`. |
| `make install-reqs` | Installs galaxy roles + `community.docker` / `community.general` collections. Auto-run by `check`/`apply`. |
| `make update` | `git pull`, then rewrites deprecated variable names in `inventory/group_vars/all/*.yml` from [migrations/variable_renames.yml](migrations/variable_renames.yml), then merges new services/keys from the remote `container_map.yml` (uses a vendored `yq` in `./bin/`). |
| `make verify-containers` | Runs `.github/workflows/scripts/check_containers.py` to validate exposed ports (used in CI). |
| `make manager` | Interactive Python settings editor (`settings_manager.py` in a venv). |

There is no separate test/lint runner; CI in [.github/workflows/run-playbook.yml](.github/workflows/run-playbook.yml) is essentially `make check` followed by `make apply` followed by `make verify-containers`. Lint config is [.ansible-lint](.ansible-lint).

## Architecture

### Entry point and flow

[hms-docker.yml](hms-docker.yml) is the only playbook. Order of operations:

1. **pre_tasks** — `import_role: hmsdocker, tasks_from: preflight` validates all required vars and feature flags BEFORE any host mutation. Then optionally imports the `gpu` role.
2. **roles** — `galaxy-roles/geerlingguy.docker` installs/configures Docker. Daemon settings (`docker_daemon_options`) are merged from a base dict and a Nvidia-runtime dict when `enable_nvidia_gpu` is true.
3. **tasks** — GPU CUDA-container validation, optional `unifi_dns` role, then the main `hmsdocker` role.

Inventory is [inventory/hosts.yml](inventory/hosts.yml) (bare: just localhost with `ansible_connection: local`). User config lives in `inventory/group_vars/all/` and is gitignored — populated by `make config`.

### The main role: `roles/hmsdocker/`

- **defaults/main/** — split across many files by concern (`main.yml`, `container_map.yml`, `traefik.yml`, `authentik.yml`, `vpn.yml`, `plex.yml`, `cloudflare.yml`, `nas*.yml`, `gpu.yml`, `tailscale.yml`, `app_bootstrap.yml`, `homepage_api_keys.yml`, `hmsd_advanced.yml`, `container_settings.yml`). When adding a default, place it in the file matching its subsystem.
- **tasks/main.yml** — versioning checks, then builds derived facts (`enabled_containers`, `traefik_enabled_containers`, `authentik_enabled_containers`, `traefik_enabled_subdomains`) by filtering `hms_docker_container_map`.
- **tasks/preflight.yml** + **tasks/compat_shim.yml** — preflight imports the compat shim, then runs feature-gated asserts. Soft warnings are appended to `hmsdocker_preflight_warnings` and printed at the end.
- **tasks/container_prereqs/**, **tasks/container_postreqs/**, **tasks/app_inits/** — per-service setup split into pre-start (mounts, networks, volumes), post-start (settling, handler triggers), and app initialization (API key retrieval, indexer/download-client wiring).
- **tasks/app_api_key_reader.yml** — introspects running containers to extract API keys, then writes them back to config for downstream apps. CI runs the playbook twice partly to exercise this.
- **templates/** — `docker-compose.yml.j2`, `env.j2`, plus subtrees `traefik/`, `authentik/`, `container_configs/`, `containers/`.
- **handlers/main.yml** — restart handlers for Traefik and the arr-stack/VPN/etc. Service restarts are deferred and only fire when tasks notify them.

### The container map (canonical service toggle)

`hms_docker_container_map` (defined in `roles/hmsdocker/defaults/main/container_map.yml`) is a single dict with ~40+ services. Each entry has keys like `enabled`, `directory`, `traefik`, `authentik`, `authentik_provider_type`, `expose_ports`, `expose_to_public`, `homepage`, `homepage_stats`, `proxy_host_rule`.

Service enablement is **two-stage** — gating happens at task time, not in the top-level template:

1. `tasks/main.yml` filters the map into derived list facts: `enabled_containers` (services where `.enabled == true`), `traefik_enabled_containers`, `authentik_enabled_containers`, `homepage_enabled_containers`, `expose_ports_enabled_containers`, etc.
2. A task loops `enabled_containers` and renders `templates/containers/{name}.yml.j2` → one `{name}.yml` file per service into the compose dir (registered as `compose_files_created`).
3. The top-level [docker-compose.yml.j2](roles/hmsdocker/templates/docker-compose.yml.j2) is tiny (~18 lines) — it emits an `include:` list referencing `compose_files_created.results` (Authentik is special-cased).
4. Per-service templates (e.g. `containers/jellyfin.yml.j2`) then gate feature blocks against the **derived lists**, not the raw map: `{% if 'jellyfin' in traefik_enabled_containers %}`, etc.

Adding a service = adding a map entry in `container_map.yml` + a `templates/containers/{name}.yml.j2` fragment. No edit to the top-level compose template is needed.

### Variable rename / compatibility shim

[migrations/variable_renames.yml](migrations/variable_renames.yml) is the **single source of truth** for deprecated variable names. It feeds two paths:

1. **Runtime** — `tasks/compat_shim.yml` aliases old names to new ones in-memory using a `varnames` lookup, skips null/empty values, runs `no_log: true`, and emits a single warning telling the user to migrate.
2. **On-disk** — `make update` reads the same file via `yq` and rewrites `inventory/group_vars/all/*.yml` with anchored `sed` (preserves YAML formatting).

When renaming a variable, **always** add an entry to `migrations/variable_renames.yml` rather than hand-editing the shim or update script. Naming convention is shifting from `hms_docker_*` to `hmsdocker_*` — both still appear; don't bulk-rename without a migration entry.

### Versioning

`hmsd_current_version` in `hms-docker.yml` (currently `1.18.2`, 3-part semver — Ansible's version comparison needs it that way) is compared at runtime against the on-disk version file at `{{ hms_docker_data_path }}/.hmsd-version`. Mismatches trigger migration logic in `tasks/versioning.yml`. Bump this when shipping a breaking change that needs a migration.

### Supporting roles

- **roles/gpu/** — verifies Nvidia drivers + runtime by running a CUDA container. Imported as a pre_task when `enable_nvidia_gpu: true`. Does NOT install drivers.
- **roles/unifi_dns/** — optional Unifi Dream Machine DNS record management. Imported mid-playbook when `unifi_dns_enabled: true` so records exist before they're used.

## Conventions

- **No mocked tests** — there is no test framework here beyond CI running the real playbook on real Ubuntu runners. "Testing" a change means `make check` locally, ideally followed by `make apply` against a throwaway host.
- **Don't break upgrades.** Renames go through `migrations/variable_renames.yml`. Removed variables stay tombstoned there until users have had a chance to migrate.
- **Preflight is the gate.** New required variables should be asserted in `tasks/preflight.yml`, feature-gated so optional subsystems don't fail.
- **Handlers, not inline restarts.** Service restarts go through `handlers/main.yml` and are notified by tasks — don't run `docker restart` inline.
- **Docs** live in `docs-astro/` (Astro site published to https://hmsdocker.dev via [.github/workflows/deploy-docs.yml](.github/workflows/deploy-docs.yml)). User-facing behavioral changes should update both the playbook and the relevant docs page.
