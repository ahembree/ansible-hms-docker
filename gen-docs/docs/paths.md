# File/Directory Layout

By default, the content is in the following directory structure, if you wish to change the install location, you must change the `hms_docker_data_path` variable in `inventory/group_vars/all/hmsd_advanced.yml`

Generated compose file location: `/opt/hms-docker/docker-compose.yml`

Container data directory: `/opt/hms-docker/apps/<container>`

Default mount path for local share (known as the `mount_path` in this readme): `/opt/hms-docker/media_data/`

Media folder that contains movie and tv show folders (known as the `media_path` in this readme): `<mount_path>/_library`

Movie folder: `<media_path>/Movies`

TV Show folder: `<media_path>/TV_Shows`

Secrets file (where sensitive key material is stored, other than the ansible variable files in `inventory/group_vars/all`): `/opt/hms-docker/.env`

- This files default ownership and permissions requires you to enter the sudo/root password every time you run a `docker compose` command within the project directory

  - If you wish to get around this (and reduce security), you can change the `secrets_env_user`, `secrets_env_group`, and `secrets_env_mode` within the `inventory/group_vars/all/hmsd_advanced.yml` file

  - These recommended values (if you wish to do this) will allow all users with `docker` access to read the file, and thus run `docker compose` commands without needing to run as sudo/root, but will not allow them to modify.

    - `secrets_env_user: root`

    - `secrets_env_group: docker`

    - `secrets_env_mode: 0640`

## File Paths

As of release [Version 0.2](release-notes/v0.2.md), file paths were changed in order to support [hardlinks and instant/atomic-moves](https://trash-guides.info/Hardlinks/Hardlinks-and-Instant-Moves/).

Application configs (Sonarr, Radarr, Plex, etc.) are stored in `/opt/hms-docker/apps/<app name>/config` by default.

Network drives will be mounted to a folder within the path specified in the `hms_docker_mount_path` variable in `inventory/group_vars/all/main.yml`. The parent directory of all the mounted folders (`hms_docker_mount_path`) is what is mounted to the required containers on `/data`.

Hard links are supported as long as the downloads folder and media content folder are on the same filesystem. This means if you have another NAS network share connected that is on a different underlying file system (like a different physical NAS) that you want to put media content on, you must change the download client to download files to that NAS share folder within the container.

---

If you were running the playbook before versioning was implemented (August 2024) and then update your local code with the new code in the repo, you will be prompted multiple times with warnings. It is highly recommended to read these warnings and understand any changes being made as you will likely have to update the paths inside the apps (Sonarr, Radarr, etc) to point to the new directory locations.
