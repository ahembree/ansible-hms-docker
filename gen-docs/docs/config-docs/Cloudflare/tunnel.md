# Cloudflare Tunnel

## Requirements and Enabling

1. You will need to first generate a token by following the steps [here](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/remote/#1-create-a-tunnel)

    a. You can find the token here:

    ![Cloudflare Tunnel Token](../../static/img/cloudflare_tunnel_token.png)

2. Once you've generated the token, update the variables in `inventory/group_vars/all/cloudflare.yml`:

    - `cloudflare_tunnel_enabled` to `yes`
    - `cloudflare_tunnel_token` to your token

3. After the container has been started, you should now see an active Connector in your Cloudflare dashboard

4. Follow [the steps here](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/remote/#2-connect-an-application) to link containers to the tunnel, following the [container map](../../container-map.md) for the available container names and ports (use the container name as the "Service" name in the Cloudflare webgui, and append the port, e.g. `overseerr:5055`)

Example:

![Cloudflare Tunnel Example](../../static/img/cloudflare_tunnel_example.png)

## Important Notes

:::tip

The "public hostname" subdomain you use does not need to match any Traefik proxy rule as **this traffic does NOT pass through Traefik**, it goes directly from the container -> Cloudflare Tunnel via the internal Docker network.

:::

:::warning

This also means that **SSO using Authentik will not work for any container configured to go through the Tunnel** due to the authentication middleware being applied by Traefik. In order to use Authentik with a publicly accessible container, you will need to port forward.

:::
