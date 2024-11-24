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

You can skip this first Ansible install step if you already have Ansible installed to a "control node" (a system that can SSH into the target host)

:::

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

3. Proceed to [configuring the deployment](#configuration-files)

---

## Configuration Files

:::tip

All configuration files are stored in `inventory/group_vars/all` after running the next command

:::

1. To initialize the configuration files, run `make config`

:::warning

Re-running this command will overwrite any existing files in the config directory

:::

---

## Container Selection

To select the containers you want to use, you will need to modify the `inventory/group_vars/all/container_map.yml` file.

Within there, you will find a giant list of containers to modify in the `hms_docker_container_map` variable.

To enable a container, set its `enabled` value to `yes`.

There is a small number of containers not in this list since they do not need config directories and are not routed through Traefik.

Current list of containers not in the container map config file:

- Flaresolverr (controlled in `inventory/group_vars/all/cloudflare.yml` in the `flaresolverr_enabled` variable)

- Cloudflare Tunnel (controlled in `inventory/group_vars/all/cloudflare.yml` in the `cloudflare_tunnel_enabled` variable)

- Cloudflare DDNS (see the [Cloudflare DDNS](../config-docs/Cloudflare/ddns.md) page)

---

## Service Configuration

All configuration options are in a (hopefully) aptly-named `.yml` file.

:::tip

All configuration files are stored in `inventory/group_vars/all`

:::

### Required Settings

#### General

In `inventory/group_vars/all/main_custom.yml`:

- `hms_docker_domain` : the local domain name of the server to be used for proxy rules and (if enabled) SSL certificates (e.g. `home.local`)
- `hms_docker_media_share_type` : the type of network share (`cifs`, `nfs`, `local`)
  - See [the NAS setup page](./network-shares/NAS.md)
  - `nfs` if using an NFS share/mount
  - `cifs` if using Samba or a Windows file share
  - `local` if using a local directory on the same system

#### Plex

In `inventory/group_vars/all/plex.yml`:

- `plex_claim_token` : your Plex claim code from [Plex's website](https://plex.tv/claim)

#### Download Client

In `inventory/group_vars/all/transmission.yml`:

- `transmission_vpn_provider` : the VPN provider code (e.g. `NORDVPN`, [see this page for the list of supported providers](https://haugene.github.io/docker-transmission-openvpn/supported-providers/#internal_providers))
- `transmission_vpn_user` : the username of the VPN user
- `transmission_vpn_pass` : the password of the VPN user

#### SSL

If you want a SSL/TLS certificate for Traefik, see the **[SSL Certificates](docs/config-docs/traefik/ssl.md)** docs.

#### Network Storage

If you have your media content stored on a NAS that will be connected via NFS or CIFS, please follow the directions in [the NAS readme](docs/getting-started/network-shares/NAS.md) (after updating your `hms_docker_media_share_type` to the correct value as outlined above in [General](#general))

## Running the playbook

You can run the playbook using the included `Makefile` with the following commands:

```bash
# Run in "Check mode" to see changes before they are made
sudo make check

# Apply changes
sudo make apply
```

## Next Steps

Check out [the NAS Setup](docs/getting-started/network-shares/NAS.md) if you set `hms_docker_media_share_type` to `cifs` or `nfs`

Check out [Configuring DNS](./dns-setup.md) on how to setup the DNS records on a (recommended) internal DNS server.

This will allow you to access the containers by going to `https://<container>.<domain>` in a browser and serve the SSL certificate, if enabled.
