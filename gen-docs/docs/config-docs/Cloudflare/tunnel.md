# Cloudflare Tunnel

## Requirements and Enabling

1. You will need to first generate a token by following the steps [here](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/remote/#1-create-a-tunnel)

    a. You can find the token here:

    ![Cloudflare Tunnel Token](../../static/img/cloudflare_tunnel_token.png)

2. Once you've generated the token, update the `cloudflare_tunnel_token` variable in `inventory/group_vars/all/cloudflare.yml` with the newly generated token

3. Enable the container in `inventory/group_vars/all/container_map.yml`

4. After the container has been started, you should now see an active Connector in your Cloudflare dashboard

5. Follow [the steps here](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/remote/#2-connect-an-application) to link containers to the tunnel, following the [container map](../../container-map.md) for the available container names and ports (use the container name as the "Service" name in the Cloudflare webgui, and append the port, e.g. `overseerr:5055`)

:::warning

Traffic does NOT pass through Traefik first for this request flow, so no security controls from Traefik will be applied, such as the IP Allowlist controls since the request is seen as coming from the Tunnel container, which falls into the RFC1918 private address space

I am not responsible for any misconfigurations that may insecurely expose your applications. It is your responsibility to understand and accept the risks and implement security controls where possible.

:::

Example:

![Cloudflare Tunnel Example](../../static/img/cloudflare_tunnel_example.png)

## Important Notes

:::tip

The "public hostname" subdomain you use does not need to match any Traefik proxy rule as **this traffic does NOT pass through Traefik**, it goes directly from the container -> Cloudflare Tunnel via the internal Docker network.

:::

:::warning

This also means that **SSO using Authentik will not work for any container individually configured to go through the Tunnel** by default due to the authentication middleware being applied _by_ Traefik.

In order to use Authentik with a container through the Tunnel, you will need to port forward or see below for more information

:::

## Using Authentik through Cloudflare Tunnel

See the [Authentik docs for this project](../Authentik.md#authentik-through-cloudflare-tunnel)
