# Arr-Scripts

This project has support for automatically adding in the [Arr-Scripts](https://github.com/RandomNinjaAtk/arr-scripts) for supported containers.

## Enabling

To enable, set `hmsdocker_svc_misc_arr_scripts_enabled` in `inventory/group_vars/all/service_misc.yml` to `true`. It will update the Compose files for the appropriate containers, there is currently no support for managing it on a per-container basis.

At the time of implementation, this list is:

- Radarr
- Sonarr
- Lidarr
- SABnzbd

:::note

Container startup time will take longer after enabling

:::

After the container(s) start up normally again, you can edit the `/opt/hms-docker/apps/<app name>/config/extended.conf` to configure the settings for the Arr-Scripts.

If configuring a script that requires a URL, such as `plexUrl` or `tdarrUrl`, use the Container Name, such as `plex` or `tdarr`, as specified in the [Container Map](../container-map.md)

## Updating

Follow the steps available at the [Arr-Scripts](https://github.com/RandomNinjaAtk/arr-scripts) GitHub page for the appropriate container.

## Removing

To remove, set `hmsdocker_svc_misc_arr_scripts_enabled` to `false` and follow the steps available at the [Arr-Scripts](https://github.com/RandomNinjaAtk/arr-scripts) GitHub page.

In general, it involves the following steps:

1. Delete the `/opt/hms-docker/apps/<app name>/config/extended.conf` file
2. Delete the `/opt/hms-docker/apps/<app name>/config/extended` directory
3. Remove any app customizations manually
