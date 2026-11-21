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
| `make install-reqs` | Installs galaxy roles + the `community.docker`, `community.general`, `ansible.posix` and `ansible.utils` collections. Auto-run by `check`/`apply`/`lint`. |
| `make update` | `git pull`s the **currently checked-out branch**, then (via `make migrate-config`, re-invoked so the freshly pulled Makefile runs) renames deprecated variables in `inventory/group_vars/all/*.yml` with [migrations/apply_renames.py](migrations/apply_renames.py) (keys and `{{ }}` references, from the `renames` list of [migrations/variable_renames.yml](migrations/variable_renames.yml), after saving a copy to `inventory/backups/`) and merges new services/keys from the local `roles/hmsdocker/defaults/main/container_map.yml` (uses a vendored `yq` in `./bin/`). |
| `make switch-develop` / `make switch-stable` | Check out `develop` / `master` (git carries non-conflicting local edits over), then run `make update`. `make branch` shows the current branch. |
| `make lint` | Runs `ansible-lint` with the rules in [.ansible-lint](.ansible-lint) (must pass, CI runs it). Needs `ansible-lint` installed. |
| `make verify-containers` | Runs `.github/workflows/scripts/check_containers.py` to validate exposed ports (used in CI). |
| `make manager` | Interactive Python settings editor (`settings_manager.py` in a venv). |

There is no separate test runner; CI in [.github/workflows/run-playbook.yml](.github/workflows/run-playbook.yml) is `make lint`, then `make check` followed by `make apply` followed by `make verify-containers`. It also checks that the variable migrations do not touch the current defaults. Lint config is [.ansible-lint](.ansible-lint).

## Architecture

### Entry point and flow

[hms-docker.yml](hms-docker.yml) is the only playbook. Order of operations:

1. **pre_tasks** — `import_role: hmsdocker, tasks_from: preflight` validates all required vars and feature flags BEFORE any host mutation. Then optionally imports the `gpu` role.
2. **roles** — `galaxy-roles/geerlingguy.docker` installs/configures Docker. Daemon settings (`docker_daemon_options`) are merged from a base dict and a Nvidia-runtime dict when `hmsdocker_enable_nvidia_gpu` is true.
3. **tasks** — GPU CUDA-container validation, optional `unifi_dns` role, then the main `hmsdocker` role.

Inventory is [inventory/hosts.yml](inventory/hosts.yml) (bare: just localhost with `ansible_connection: local`). User config lives in `inventory/group_vars/all/` and is gitignored — populated by `make config`.

### The main role: `roles/hmsdocker/`

- **defaults/main/** — split across many files by concern (`main.yml`, `container_map.yml`, `traefik.yml`, `sso.yml` (Authentik, Tinyauth, Pocket ID), `vpn.yml`, `plex.yml`, `cloudflare.yml`, `nas*.yml`, `gpu.yml`, `tailscale.yml`, `app_bootstrap.yml`, `homepage_api_keys.yml`, `hmsd_advanced.yml`, `container_settings.yml`). When adding a default, place it in the file matching its subsystem.
- **tasks/main.yml** — versioning checks, then builds derived facts (`hmsdocker_enabled_containers`, `hmsdocker_traefik_enabled_containers`, `hmsdocker_authentik_enabled_containers`, `hmsdocker_traefik_enabled_subdomains`) from `hmsdocker_container_map`. The map is filtered once into `hmsdocker_containers_with` (enabled containers per map setting), which the other facts are built from.
- **tasks/preflight.yml** + **tasks/compat_shim.yml** — preflight imports the compat shim, then runs feature-gated asserts. Soft warnings are appended to `hmsdocker_preflight_warnings` and printed at the end.
- **tasks/container_prereqs/**, **tasks/container_postreqs/**, **tasks/app_inits/** — per-service setup split into pre-start (mounts, networks, volumes), post-start (settling, handler triggers), and app initialization (API key retrieval, indexer/download-client wiring). Sonarr, Radarr and Lidarr share `tasks/app_inits/shared/arr_instance.yml`; their own files only set its `hmsdocker_arr_*` variables per instance.
- **tasks/nas/share.yml** — mounts one media share. Included once for the primary share and once per additional path.
- **tasks/app_api_key_reader.yml** — introspects running containers to extract API keys, then writes them back to config for downstream apps. CI runs the playbook twice partly to exercise this.
- **templates/** — `docker-compose.yml.j2`, `env.j2`, plus subtrees `traefik/`, `authentik/`, `container_configs/`, `containers/`, `socket_proxy/` and `macros/` (`labels.j2`: the Traefik and Homepage label blocks every container template uses; `arr.j2`: the Sonarr/Radarr compose service, regular and 4K).
- **handlers/main.yml** — restart handlers for Traefik and the arr-stack/VPN/etc. Service restarts are deferred and only fire when tasks notify them.

### The container map (canonical service toggle)

`hmsdocker_container_map` (defined in `roles/hmsdocker/defaults/main/container_map.yml`) is a single dict with ~40+ services. Each entry has keys like `enabled`, `directory`, `traefik`, `authentik`, `authentik_provider_type`, `expose_ports`, `expose_to_public`, `homepage`, `homepage_stats`, `proxy_host_rule`.

Service enablement is **two-stage** — gating happens at task time, not in the top-level template:

1. `tasks/main.yml` filters the map into derived list facts: `hmsdocker_enabled_containers` (services where `.enabled == true`), `hmsdocker_traefik_enabled_containers`, `hmsdocker_authentik_enabled_containers`, `hmsdocker_homepage_enabled_containers`, `hmsdocker_expose_ports_enabled_containers`, etc.
2. A task loops `hmsdocker_enabled_containers` and renders `templates/containers/{name}.yml.j2` → one `{name}.yml` file per service into the compose dir (registered as `hmsdocker_compose_files_created`).
3. The top-level [docker-compose.yml.j2](roles/hmsdocker/templates/docker-compose.yml.j2) is tiny (~18 lines) — it emits an `include:` list referencing `hmsdocker_compose_files_created.results` (Authentik is special-cased).
4. Per-service templates (e.g. `containers/jellyfin.yml.j2`) then gate feature blocks against the **derived lists**, not the raw map: `{% if 'jellyfin' in hmsdocker_traefik_enabled_containers %}`, etc. The Traefik and Homepage labels inside those blocks are written by `labels.traefik(...)` / `labels.homepage(...)` from `templates/macros/labels.j2`, not by hand.

Adding a service = adding a map entry in `container_map.yml` + a `templates/containers/{name}.yml.j2` fragment. No edit to the top-level compose template is needed.

### Variable rename / compatibility shim

The `renames` list in [migrations/variable_renames.yml](migrations/variable_renames.yml) is the **single source of truth** for deprecated variable names. It feeds two paths:

1. **Runtime** — `tasks/compat_shim.yml` aliases old names to new ones in-memory using a `varnames` lookup, skips null/empty values, runs `no_log: true`, and emits one warning that lists the old names still in use (plus one per variable set under both names).
2. **On-disk** — `make update` / `make migrate-config` run [migrations/apply_renames.py](migrations/apply_renames.py) (standard library only), which renames the top-level keys in `inventory/group_vars/all/*.yml` and the references to them inside `{{ }}`, leaving everything else as it is. It first copies the files to `inventory/backups/<timestamp>/`.

When renaming a variable, **always** add a `- { old: ..., new: ... }` line to `renames` rather than hand-editing the shim or update script, and point the `new` of any earlier entry for that variable at the final name. The file also has a frozen `variable_renames` list: Makefiles up to v1.20 keep running their own `make update` recipe after `git pull` and rename those keys with `sed` without fixing references, so nothing may be added to it. For the same Makefiles, the docs workflows publish the container map at `hmsdocker.dev/configs/` under its old key `hms_docker_container_map`.

**Naming:** every variable the `hmsdocker` role defines (defaults, vars, `set_fact`, `register`, task `vars`, loop variables) and the play-level variables in `hms-docker.yml` start with `hmsdocker_`; the `gpu` and `unifi_dns` roles use their own role name. `ansible-lint` (`var-naming[no-role-prefix]`) enforces it. Variables that belong to another role (e.g. `docker_daemon_options` for `geerlingguy.docker`) keep that role's names.

### Versioning

`hmsdocker_current_version` in `hms-docker.yml` (a **quoted** 3-part semver — unquoted values like `1.20` parse as the YAML float `1.2` and break the semver comparison; a runtime assert in `tasks/versioning.yml` enforces the format) is compared at runtime against the on-disk version file at `{{ hmsdocker_data_path }}/.hmsd-version`. The on-disk value is normalized before comparison (releases 1.4–1.9 wrote 2-part versions). Mismatches trigger migration logic in `tasks/versioning.yml`; the version file itself is written at the end of `tasks/main.yml` so a failed run re-prompts on retry. Bump this when shipping a breaking change that needs a migration.

### Branching model

- **`master`** = released code only. It is the default branch, so `git clone` and `make update` give users the latest release. It only moves when a release is cut (or a hotfix lands).
- **`develop`** = integration branch. All feature/fix PRs target `develop`.
- [.github/workflows/pr-target-guard.yml](.github/workflows/pr-target-guard.yml) fails PRs into `master` unless the source is `develop` or `hotfix/*` (same repo). It is a CI check because GitHub branch protection/rulesets cannot restrict a PR's source branch; it only enforces once marked as a required status check on `master`. Keeping `master` as the default branch (so clones get released code) means new PRs default to `master`, and this check is what turns that into a hard stop.
- [.github/workflows/pr-retarget-develop.yml](.github/workflows/pr-retarget-develop.yml) runs on `pull_request_target` when a PR is opened/reopened against `master` and, unless the source is `develop` or `hotfix/*` (same repo), switches its base to `develop` and comments. It never checks out PR code. The guard still fails the initial run; that stale check is harmless once the PR targets `develop`.
- Hotfix: branch `hotfix/<topic>` off `master`, PR it to `master` (with a patch bump + notes). [.github/workflows/sync-develop.yml](.github/workflows/sync-develop.yml) then opens a `master` → `develop` PR if `develop` is missing the change.
- Merge `develop` → `master` with a **merge commit**, never squash, so the branches don't diverge.

**Cutting a release:**

Feature/fix PRs into `develop` **do not bump** `hmsdocker_current_version`. They add their release notes as bullets under a `## Unreleased` section at the top of the newest release-notes file; the release workflow ignores that header.

1. On a branch off `develop`, bump `hmsdocker_current_version` in [hms-docker.yml](hms-docker.yml), keeping it quoted, and PR it into `develop`.
2. Rename `## Unreleased` to `## v<version>` (moving it into a new minor-series file on a minor bump), or add the section if none exists, in the release-notes file for that minor series, e.g. `docs-astro/src/content/docs/docs/release-notes/v1.18.md`. The header must be exactly `## v<version>` (matching the new version) — the release workflow extracts everything between it and the next `## ` heading as the GitHub Release body.
3. Open a PR from `develop` to `master` and merge it with a merge commit. [.github/workflows/release.yml](.github/workflows/release.yml) triggers on pushes to `master` that touch `hms-docker.yml`: it reads the version, tags it, and creates the GitHub Release from the extracted notes. Releases are not cut from feature branches or from `develop`.

### Supporting roles

- **roles/gpu/** — verifies Nvidia drivers + runtime by running a CUDA container. Imported as a pre_task when `hmsdocker_enable_nvidia_gpu: true`. Does NOT install drivers.
- **roles/unifi_dns/** — optional Unifi Dream Machine DNS record management. Imported mid-playbook when `unifi_dns_enabled: true` so records exist before they're used.

## Conventions

- **No mocked tests** — there is no test framework here beyond CI running the real playbook on real Ubuntu runners. "Testing" a change means `make check` locally, ideally followed by `make apply` against a throwaway host.
- **Lint must pass.** `make lint` runs in CI. Prefer fixing a finding; where the fix would change behaviour, add `# noqa: <rule>` with a comment that says why (see the `mode`-less `file` tasks on the media share).
- **Don't break upgrades.** Renames go through `migrations/variable_renames.yml`. Removed variables stay tombstoned there until users have had a chance to migrate.
- **Preflight is the gate.** New required variables should be asserted in `tasks/preflight.yml`, feature-gated so optional subsystems don't fail.
- **Handlers, not inline restarts.** Service restarts go through `handlers/main.yml` and are notified by tasks — don't run `docker restart` inline.
- **Docs** live in `docs-astro/` (Astro site published to https://hmsdocker.dev via [.github/workflows/deploy-docs.yml](.github/workflows/deploy-docs.yml)). User-facing behavioral changes should update both the playbook and the relevant docs page.
