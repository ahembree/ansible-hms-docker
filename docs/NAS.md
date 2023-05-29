# NAS

## CIFS Shares

Required settings for the `hms_docker_media_share_type` of `cifs`:

In `vars/custom/nas_cifs.yml`

- `nas_client_remote_cifs_path` : the path to the network share (e.g. `//nas.example.com/share`)
- `nas_client_cifs_username` : the username of the network share
- `nas_client_cifs_password` : the password of the network share
- `nas_client_cifs_opts` : the options for the network share (Google can help you find the correct options)

## NFS Shares/Mounts

Required settings for the `hms_docker_media_share_type` of `nfs`:

In `vars/custom/nas_nfs.yml`

- `nas_client_remote_nfs_path` : the path to the network share (e.g. `nas.example.com:/share`)
- `nas_client_nfs_opts` : the options for the network share (Google can help you find the correct options)
