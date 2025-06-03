# Automatic App Initialization

## Requirements

This requires DNS records to be properly configured for the following apps:

- Prowlarr

- Sonarr (including 4K instance if enabled)

- Radarr (including 4K instance if enabled)

- Lidarr

- Readarr

:::info

These tasks will **NOT** work in `check` mode, this is a [limitation of the Ansible URI module](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/uri_module.html#attributes)

:::

## Details

There are tasks within this playbook that will attempt to automatically configure the connections between supported apps to reduce the amount of time it takes to get up and running.

If a service is no longer used it will be removed from the app connections.

Example: If qBittorrent was enabled when the bootstrap tasks were ran but then you disable qBittorrent, it will remove the download client `HMSD - qBittorrent` if it exists in Sonar and Radarr and indexer proxy in Prowlarr if it exists whenever the playbook is ran next.

:::note

If you are using qBittorrent and/or Deluge and create or update the password for their WebUI's, you will need to update the password for the download client(s) in the Sonarr and Radarr apps manually.

:::

By default, the playbook will check for the various apps API keys in their config files.

If you set `hmsdocker_app_bootstrap` to `yes` or `true` in `inventory/group_vars/all/app_bootstrap.yml`, it will also attempt to connect some of the apps together to speed up initial installation process.

## Connections

:::info

These connections are prefixed with `HMSD - ` and this is required to work correctly. You can modify the settings of the connection, but not the name, otherwise it will just create another.

:::

It will do the following for each service:

- Prowlarr

  - Configure Indexer Proxies and Tags for the following services (if enabled)

    - FlareSolverr

    - qBittorrent

    - Transmission

    - Deluge

  - Configure the following apps:
    - Sonarr (including 4K)
    - Radarr (including 4K)
    - Lidarr
    - Readarr

- Radarr (including 4K instance if enabled)

  - Configure root folder

  - Configure download clients (if enabled):

    - Transmission

    - qBittorrent

    - Deluge

- Sonarr (including 4K instance if enabled)

  - Configure root folder

  - Configure download clients (if enabled):

    - Transmission

    - qBittorrent

    - Deluge

- Lidarr

  - Configure download clients (if enabled):

    - Transmission

    - qBittorrent

    - Deluge

- Readarr

  - Configure download clients (if enabled):

    - Transmission

    - qBittorrent

    - Deluge

:::note

FlareSolverr uses Prowlarrs `General -> Proxy` settings. If this setting is invalid, the task will fail.

:::

## Unsupported Services

### Overseerr

Overseerr is unsupported due to it requiring you to initially authenticate with Plex after the container first starts in order for its API key to work and it guides you through the setup process.
