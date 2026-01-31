# NAS

If you have more than 1 share you need to mount, see the **[Additional NAS docs](./additional-nas.md)** after doing this configuration.

The main mount point is defined in `hms_docker_mount_path` in file `inventory/group_vars/all/main.yml`

The main NAS share type is defined in `hms_docker_media_share_type` in file `inventory/group_vars/all/main.yml`

## NFS Shares

### NFS Requirements

Required settings for the `hms_docker_media_share_type` of `nfs`:

In `inventory/group_vars/all/nas_nfs.yml`

- `nas_client_remote_nfs_path` : the path to the network share (e.g. `nas.example.com:/share`)
- `nas_client_nfs_opts` : the options for the network share (Google can help you find the correct options)

## CIFS Shares

:::warning

The CIFS credentials will be stored in plaintext within the `hms_docker_data_path` folder, but will be owned by `root:root` with `0600` permissions, so only those with root or sudo access can read

:::

### CIFS Requirements

Required settings for the `hms_docker_media_share_type` of `cifs`:

In `inventory/group_vars/all/nas_cifs.yml`

- `nas_client_remote_cifs_path` : the path to the network share (e.g. `//nas.example.com/share`)
- `nas_client_cifs_username` : the username of the network share
- `nas_client_cifs_password` : the password of the network share
- `nas_client_cifs_opts` : the options for the network share (Google can help you find the correct options)
