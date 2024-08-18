# File Paths

As of release version 0.2, file paths were changed in order to support [hardlinks and instant/atomic-moves](https://trash-guides.info/Hardlinks/Hardlinks-and-Instant-Moves/).

Application configs (Sonarr, Radarr, Plex, etc.) are stored in `/opt/hms-docker/apps/<app name>/config` by default.

Network drives will be mounted to a folder within the path specified in the `hms_docker_mount_path` variable in `inventory/group_vars/all/main_custom.yml`. The parent directory of all the mounted folders (`hms_docker_mount_path`) is what is mounted to the required containers on `/data`.

Hard links are supported as long as the downloads folder and media content folder are on the same filesystem. This means if you have another NAS network share connected that is on a different underlying file system (like a different physical NAS) that you want to put media content on, you must change the download client to download files to that NAS share folder within the container.

---

If you were running the playbook before versioning was implemented (August 2024) and then update your local code with the new code in the repo, you will be prompted multiple times with warnings. It is highly recommended to read these warnings and understand any changes being made as you will likely have to update the paths inside the apps (Sonarr, Radarr, etc) to point to the new directory locations.

For a full list of all paths changed, please see [the release notes doc](./Release%20Notes.md)
