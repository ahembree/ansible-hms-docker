# qBittorrent

This setup uses the container maintained here: [binhex/arch-qbittorrentvpn](https://github.com/binhex/arch-qbittorrentvpn)

Settings mentioned below should already exist in your `inventory/group_vars/all/vpn.yml` file

:::note

After updating the VPN config file, run `docker restart qbittorrent`

:::

## OpenVPN

Requires the following variables:

* `hmsdocker_vpn_type`: `openvpn`
* `hmsdocker_vpn_provider`: see [the official docs page](https://haugene.github.io/docker-transmission-openvpn/supported-providers/)
* `hmsdocker_vpn_user`: Your VPN account/service account username
* `hmsdocker_vpn_pass`: Your VPN account/service account password

If using OpenVPN for your VPN connection, please update or place the `.ovpn` file and any other required files in the directory: `/opt/hmsdocker/apps/qbittorrent/config/openvpn` (default)

This folder will not exist until the playbook is ran or the container runs

## WireGuard

Requires the following variables:

* `hmsdocker_vpn_type`: `wireguard`

If using WireGuard for your VPN connection, please update or place the `wg0.conf` file and any other required files in the directory: `/opt/hmsdocker/apps/qbittorrent/config/wireguard` (default)

This folder will not exist until the playbook is ran or the container runs
