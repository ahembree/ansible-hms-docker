# Automatic App Initialization

There are tasks within this playbook that will attempt to automatically configure the connections between supported apps to reduce the amount of time it takes to get up and running.

If you are using qBittorrent and/or Deluge and create or update the password for their WebUI's, you will need to update the password for the download client(s) in the Sonarr and Radarr apps manually.

:::note

This requires DNS records to be properly configured for the following apps:

- Prowlarr

- Sonarr (including 4K instance if enabled)

- Radarr (including 4K instance if enabled)

:::

By default, the playbook will check for the various apps API keys in their config files.

If you set `hmsdocker_app_bootstrap` to `yes` in `inventory/group_vars/all/app_bootstrap.yml`, it will also attempt to connect some of the apps together to speed up initial installation process.

:::info

This will only _create_ the connections and configurations if they do not exist already, it will **not update existing connections or remove ones that are no longer used**. These connections are prefixed with `HMSD - ` and this is required to work correctly. You can modify the settings of the connection, but not the name, otherwise it will just create another.

:::

It will do the following for each service:

- Prowlarr

  - Create Indexer Proxies and Tags for the following services (if enabled)

    - FlareSolverr

    - qBittorrent

    - Transmission

    - Deluge

  - Configure the Sonarr and Radarr apps (including 4K instances if enabled)

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
