---
sidebar_position: 2
---

# Installation Steps

:::warning[Warning]

This playbook assumes that it is a fresh install of an operating system that has not been configured yet.

To ensure no conflicting changes with an existing system, you can run this playbook in "check mode" to see what, if any, changes would be made by running `sudo make check`

:::

## Installation

:::tip

You can skip the Ansible install in step 1 if you already have Ansible installed to a "control node" (a system that can SSH into the target host).

If this is your case, see [Remote Host](#remote-host)

:::

### Local Host

If installing to the same system you will clone/download this repo to, proceed to [Install Steps](#install-steps)

### Remote Host

#### Requirements

- Ability to SSH into remote host
- Sudo privileges on remote host

If installing to a remote host (a different system than where Ansible is installed), you will need to modify your `inventory/hosts.yml` file to specify the remote host:

```yaml
all:
  hosts:
    hmsdockerhost:
      ansible_host: 192.168.1.2 # The IP address of the target host you want to install to
      # Uncomment and modify the following if you have a specific user you use for Ansible:
      #ansible_user: ansibleuser
      #ansible_ssh_private_key_file: /path/to/key/file
      #ansible_ssh_pass: foo #leave as-is if key does not have a password
      # You can also specify host-specific variables here:
      #hms_docker_domain: secondary.example.com
```

### Install Steps

1. Install Ansible for your system by following the instructions available here: https://docs.ansible.com/ansible/latest/installation_guide/installation_distros.html

2. Install requirements and clone the repository:

   Ubuntu:

   ```bash
   sudo apt install git make python3-pip -y
   ```

   ```bash
   # Clone the repository and then go into the folder
   git clone https://github.com/ahembree/ansible-hms-docker.git
   cd ansible-hms-docker/
   ```

3. Proceed to [configuration](#configuration-files)

## Configuration Files

:::tip

All configuration files are stored in `inventory/group_vars/all` after running the next command

:::

4. To copy the default configuration files, run `make config`

:::warning

Re-running this command will overwrite any existing files in the config directory (a reset to default configuration)

:::

---

## Container Selection

To select the containers you want to use, you will need to modify the `inventory/group_vars/all/container_map.yml` file. Within there, you will find a giant list of containers to modify in the `hms_docker_container_map` variable.

To enable a container, set its `enabled` value to `true` or `yes`.

For an example of a container map entry and the description of what each setting does, check the [Container Map](../container-map.md) docs

---

There is a small number of containers not in this list since they do not need config directories and are not routed through Traefik.

Current list of containers not in the container map config file:

- Cloudflare DDNS (see the [Cloudflare DDNS](../config-docs/Cloudflare/ddns.md) page)

---

## Service Configuration

All configuration options are in a (hopefully) aptly-named `.yml` file.

:::tip

All configuration files are stored in `inventory/group_vars/all`

Any variable can be removed from _your_ config file if not being used, it will use the default already defined in the file, this can help reduce the number of variables and narrow it down to only ones you know have changed.

:::

:::note

Any future containers variables will need to be added to your config file manually, if you chose to change from the default values.

The default variable files are found in `roles/hmsdocker/defaults/main/`

For adding a newly supported container, see [Updating](./updating.md#new-containers)

:::

### Required Settings

#### General

In `inventory/group_vars/all/main.yml`:

- `hms_docker_domain` : the local domain name of the server to be used for proxy rules and (if enabled) SSL certificates (e.g. `home.local`)
- `hms_docker_media_share_type` : the type of network share (`cifs`, `nfs`, `local`)
  - See [the NAS setup page](./network-shares/NAS.md) if using `nfs` or `cifs`
  - `nfs` if using an NFS share/mount
  - `cifs` if using Samba or a Windows file share
  - `local` if using a local drive/directory on the same system

- `hms_docker_mount_path` : This is where the media and download folders will be "mounted". Recommended to change if using a network share and/or other drive in the system.

#### Plex (if enabled)

In `inventory/group_vars/all/plex.yml`:

- `plex_claim_token` : your Plex claim code from [Plex's website](https://plex.tv/claim)

#### VPN and Download Client (if enabled)

In `inventory/group_vars/all/vpn.yml`:

- `hmsdocker_vpn_provider` : the VPN provider code (e.g. `NORDVPN`, [see this page for the list of supported providers](https://haugene.github.io/docker-transmission-openvpn/supported-providers/#internal_providers))
- `hmsdocker_vpn_user` : the username of the VPN user
- `hmsdocker_vpn_pass` : the password of the VPN user

For more info, see the [VPN and Download Client](../category/vpn-and-download-clients) docs

#### SSL

If you want a SSL/TLS certificate for Traefik, see the **[SSL Certificates](docs/config-docs/traefik/ssl.md)** docs.

#### Network Storage

If you have your media content stored on a NAS that will be connected via NFS or CIFS, please follow the directions in [the NAS readme](docs/getting-started/network-shares/NAS.md) (after updating your `hms_docker_media_share_type` to the correct value as outlined above in [General](#general))

## Running the playbook

You can run the playbook using the following commands:

```bash
# Run in "Check mode" to see changes before they are made
sudo make check

# Apply changes
sudo make apply
```

### Debug mode

There is a debug mode you can control from a variable in `hms-docker.yml`

:::warning

Debug mode will also potentially output "secrets" (passwords, API keys) when enabled

:::

## Next Steps

Check out [Configuring DNS](./dns-setup.md) on how to setup the DNS records on a (recommended) internal DNS server.

This will allow you to access the containers by going to `https://<container>.<domain>` in a browser and serve the SSL certificate, if enabled.

If you already have DNS enabled and want to get up and running quicker, check out the [Automatic App Initialization](./app-bootstrap.md).

If you are receiving a `404` or `502` error when attempting to access the service, this is either because the container is not running, failing to start, or still starting. To troubleshoot, run `docker logs -f <container name>` and check the container logs.

Or, if you have Portainer enabled, you can also check the container logs there.
