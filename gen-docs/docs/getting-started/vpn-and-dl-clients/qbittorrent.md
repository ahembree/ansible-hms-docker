# qBittorrent

This setup uses the container maintained here: [binhex/arch-qbittorrentvpn](https://github.com/binhex/arch-qbittorrentvpn)

Settings mentioned below should already exist in your `inventory/group_vars/all/vpn.yml` file

:::note

After updating the VPN config file, run `docker restart qbittorrent`

:::

:::warning

Authentication will be **disabled** by default for private (RFC1918) IP space:

- `10.0.0.0/8`
- `172.16.0.0/12`
- `192.168.0.0/16`

This is to allow the automatic app bootstrap to work and to reduce complexity of retrieving temporary admin password.

If you wish to have authentication, you can configure this in the WebUI settings of qBittorrent. You will also need to update the download client for qBittorrent in the Sonarr and Radarr apps

If you enabled authentication _before_ running the app bootstrap tasks, they will fail. To resolve, turn off authentication in qBittorrent, then run the bootstrap tasks and then configure the qBittorrent download client username/password in the specific apps

:::

## OpenVPN

Requires the following variables:

* `hmsdocker_vpn_type`: `openvpn`
* `hmsdocker_vpn_user`: Your VPN account/service account username
* `hmsdocker_vpn_pass`: Your VPN account/service account password

If using OpenVPN for your VPN connection, please update or place the `.ovpn` file and any other required files in the directory: `/opt/hms-docker/apps/qbittorrent/config/openvpn` (default)

This folder will not exist until the playbook is ran or the container runs

## WireGuard

Requires the following variables:

* `hmsdocker_vpn_type`: `wireguard`

If using WireGuard for your VPN connection, please update or place the `wg0.conf` file and any other required files in the directory: `/opt/hms-docker/apps/qbittorrent/config/wireguard` (default)

This folder will not exist until the playbook is ran or the container runs

## Private Internet Access (PIA)

If you are using PIA and want to use port forwarding through the VPN, see the [Container Overrides](../container-overrides.md) docs
