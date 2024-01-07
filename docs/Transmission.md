# Transmission

All settings mentioned below should already exist in your `vars/custom/transmission.yml` file

## Using a different VPN location or type

For supported providers, you can change the server location and/or type.

1. Make sure `transmission_vpn_provider` is set to your correct provider

    a. You can find supported providers at [the official docs page](https://haugene.github.io/docker-transmission-openvpn/supported-providers/)

2. Find your VPN providers folder in [this github repo](https://github.com/haugene/vpn-configs-contrib/tree/main/openvpn)

3. Find the correct VPN config you want to use, and use this as the value for `transmission_ovpn_config_file`, and remove the `.ovpn` from the end

For example, if you wanted to use the US Chicago server for mullvad:

```yml
transmission_vpn_provider: MULLVAD
...
transmission_ovpn_config_file: us_chi
```

## Using a local OpenVPN config file

1. Change `transmission_vpn_provider` to `custom`

2. Change `transmission_ovpn_config_file` to the `.ovpn` file name, and remove the `.ovpn` from the end

3. Change `transmission_ovpn_config_local_path` to the folder path where the above file is stored

    a. If needed by your provider/server, make sure certificate files and any others are also in the same folder

For example, if you had a custom file named `test-vpn.ovpn` located in `/opt/hms-docker/vpn_configs` (this folder does not exist by default, just an example):

```yml
transmission_ovpn_config_file: test-vpn
transmission_ovpn_config_local_path: /opt/hms-docker/vpn_configs
```
