# Backrest

Backrest is available to perform backups. Configuring Backrest and the required repository is outside the scope of this project as there are way too many different configurations.

In general:

1. Have a backup destination
2. Configure a "Repository" to point to that destination
    a. :::warning

      BE SURE TO CREATE A BACKUP OF YOUR ENCRYPTION KEY SOMEWHERE SAFE SINCE THIS IS REQUIRED FOR RESTORE

      :::
3. Configure a "Plan" to perform the backups from `/opt/hms-docker` (mounted in the container as read-only by default) to the configured Repository

Some repositories may require rclone configuration, which is also outside the scope of this project.

The intent of the initial implementation is to backup the container configs and _not_ the media data, unless your media data lives in the default data path (`/opt/hms-docker`). If you'd like support for backing up media as well, please submit a [Discussion Post](https://github.com/ahembree/ansible-hms-docker/discussions).

## Inclusion and Exclusion Configs

The following was used to decide on the paths to exclude for Plex: https://www.plexopedia.com/plex-media-server/general/migrate-plex-server/

Case-Sensitive Excludes:

```bash
**/apps/plex/config/Library/Application Support/Plex Media Server/Crash Reports/** # Plex crash reports
**/apps/plex/config/Library/Application Support/Plex Media Server/Diagnostics/** # Plex Diagnostics
**/apps/plex/config/Library/Application Support/Plex Media Server/Updates/** # Plex updates
**/MediaCover/** # The poster and artwork files for the Arr apps. If excluded, you will need to manually click "Update All" within the Arr apps
```

Case-_Insensitive_ Excludes:

```text
"**/cache/**"
"**/tmp/**"
"**/logs/**"
"**/transcode_temp/**"
"*.log"
"*.tmp"
"*.pid"
"**/.venv/**"
```

## Restoring from backup

If a backup/snapshot has been performed, you can follow these steps to restore:

1. Enable write access for Backrest by setting `hmsdocker_backrest_allow_write` to `true` in `inventory/group_vars/all/service_misc.yml`

2. Stop all containers:

    ```bash
    cd /opt/hms-docker
    sudo docker compose down
    ```

3. Start only Traefik and Backrest:

    ```bash
    sudo docker compose up traefik backrest -d
    ```

4. Reconnect your Backrest repository that you used for backups

5. List your available snapshots by using the "run command" from within your Backrest respository:

    ```bash
    snapshots
    ```

6. Restore to the snapshot ID that you want:

    ```bash
    restore <snapshot ID> --target=/opt/hms-docker-restore
    ```

    :::note

    It will restore the full path of the files under this folder (example: `/opt/hms-docker-restore/opt/hms-docker), so folders will need to be moved after the restore has completed. This gives a little more control to the restore process.

    To avoid this, set the target to `/`, but this will overwrite any existing files

    :::

7. Wait for the restore to finish

8. Start containers again:

    ```bash
    cd /opt/hms-docker
    sudo docker compose up -d
    ```

## OneDrive

I personally only currently have experience with setting up OneDrive as a backup destination.

Since there is no native support for OneDrive through Backrest/restic, it is done through rclone.

The documentation on configuring and connecting rclone to OneDrive can be found here: https://rclone.org/onedrive/

When configuring OneDrive, make sure that the Backrest containers version of rclone (can be found using `docker run -it --rm garethgeorge/backrest rclone version`) matches the version of rclone used to generate the config
