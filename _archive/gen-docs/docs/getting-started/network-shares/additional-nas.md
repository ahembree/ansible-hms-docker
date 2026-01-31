# Additional NAS Mounts

If you have more than 1 network share you want to mount, set `nas_client_use_additional_paths` in `inventory/group_vars/all/nas_additional.yml` to `yes`

## List of Variables

Use the below variables to create a list of mappings in the `nas_client_remote_additional_paths` variable in `inventory/group_vars/all/nas_additional.yml`.

Confused? See the [Example below](#example), a version of it already exists in `inventory/group_vars/all/nas_additional.yml` so just modify that.

### Local Folder

- `name`: Friendly name of the path
- `local_mount_path`: Local path to the folder
- `create_library_folders`: If the library folder structure should be created (default: `false`)
- `type`: Type of path, valid: `local`

### NFS Share Variables

- `name`: Friendly name of the path
- `remote_path`: Remote path to the folder
- `local_mount_path`: Local path to where it will be mounted
- `create_library_folders`: If the library folder structure should be created (default: `false`)
- `type`: Type of path, valid: `nfs`
- `nfs_opts`: NFS options, default: `defaults`

### CIFS Share Variables

- `name`: Friendly name of the path
- `remote_path`: Remote path to the folder
- `local_mount_path`: Local path to where it will be mounted
- `create_library_folders`: If the library folder structure should be created (default: `false`)
- `type`: Type of path, valid: `cifs`
- `cifs_username`: CIFS username, default: `""`
- `cifs_password`: CIFS password, default: `""`
- `cifs_opts`: CIFS options, default: `rw,soft`

## Example

Below is an example configuration that defines both an NFS mount (the first) and a CIFS mount (the second) that also uses the default mounting location defined in the variable `hms_docker_mount_path` in file `inventory/group_vars/all/main.yml`

```yaml
nas_client_remote_additional_paths:
  [
    {
      name: "Media 4K",
      remote_path: "192.168.1.5:/Media_4K",
      local_mount_path: "{{ hms_docker_mount_path }}/Media_4k",
      create_library_folders: true,
      type: nfs,
      nfs_opts: "rw,defaults"
    },
    {
      name: "Media NAS 3",
      remote_path: "//nas.example.com/media_3",
      local_mount_path: "{{ hms_docker_mount_path }}_custom_path_3",
      create_library_folders: false,
      type: cifs,
      cifs_username: "insecureusername",
      cifs_password: "veryinsecurepassword",
      cifs_opts: "rw,soft",
    },
  ]
```
