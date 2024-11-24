# Authentik

:::warning

In order to use Authentik, you must be using SSL as outlined in this project.

:::

This Authentik installation is based on the [single application](https://goauthentik.io/docs/providers/proxy/forward_auth#single-application) proxy provider configuration.

There are no authentik proxy containers defined in the `docker-compose.yml` file. This is because authentik will auto-detect the Docker socket and be able to start/stop its own proxy containers by using the configurations below.

Authentik is able to be controlled on a per-container basis, but requires a bit of configuration as outlined below.

## Important Note

:::warning

If you are using [Cloudflare Tunnel](./Cloudflare/tunnel.md) **AND** you have disabled port forwarding to 80/443, you **MUST** create a new "public hostname" in Tunnel in order for SSO to work since the SSO server needs to be publicly accessible. If your Tunnel is online and working, follow [step 4 when setting up Tunnel](./Cloudflare/tunnel.md) and configure it for the `authentik-server:9001` container.

However, any containers configured to be accessible through the Cloudflare Tunnel **will not** be protected by Authentik if accessed via the Tunnel. This is mainly for the use case of not having to port forward while still having Authentik protect services routed through Traefik.

:::

## Enabling Authentik on Individual Containers

1. Enable the `authentik` container either in the container map or within the `authentik.yml` config file

2. Enable `authentik` for the containers you want in the `hms_docker_container_map` variable available in the `inventory/group_vars/all/container_map.yml` file.

3. Run the playbook as normal

4. Once all containers are started, go to `https://authentik.< domain >/if/flow/initial-setup/` to create the initial user and password to continue Authentik setup

5. Configure an Application Provider within Authentik

    a. Login

    b. Go to the Admin panel

    c. Expand `Applications` on the left

    d. Click `Providers`

    e. Create a new `Proxy Provider`

    f. Give it the same name as the application (such as Sonarr)

    g. Select `Forward auth (single application)`

    h. Set the `External host` to the URL of the application (such as `sonarr.< domain >`)

    i. Click finish

6. Configure an Application

    a. Do a-c (above in step 4) again

    b. Click `Applications`

    c. Create a new Application with its name, slug (lowercase name for it), and select the provider created for the application

    d. Click `Create` and now you should have Authentik in front of the application!

7. Configure an Application Outpost

    a. Do a-c above in step 5 again

    b. Click `Outposts`

    c. Give it a name, the `type` is `Proxy` and integration should be the `Local Docker connection`

    d. Select the application to associate it to

    :::tip

    **IMPORTANT**: copy the content of the file for the container generated in: `< hms_docker_apps_path >/authentik/outposts/authentik-< container_name >-output.yml` (so by default: `/opt/hms-docker/apps/authentik/outposts/...`) to your clipboard

    - If a configuration does not exist for the container you want, ensure you've enabled Authentik and have enabled `authentik` for that specific container in the `container_map.yml` config file

    :::

    f. Replace the configuration in the Authentik webpage with this generated configuration, otherwise stuff will not work correctly.

    g. Once you click create, it will automatically create a new `authentik-proxy` container that will handle authentication.

    h. Note: it may take some time to setup the proxy, be patient

    :::note

    This `authentik-proxy` container (and also any associated networks) will **not** be deleted if the Compose stack is removed since the container is not defined in the Compose file.

    :::

8. Troubleshooting

    a. Using the Traefik and Portainer dashboards help a LOT during the troubleshooting process

    b. If you're getting a `404 not found` error, this is likely due to the `authentik-proxy` containers not working, running, or not being configured correctly. Check Portainer. If you just configured a new application output, wait a couple more minutes.

    c. If you're getting a `500` server error, this is possibly due to having duplicate Traefik routes for the same host rules, check Traefik logs and/or Portainer logs for the correct `authentik-proxy` container.

## How the Authentik secret keys are stored

There are 2 files created when enabling Authentik, `.authentik.key` and `.authentik.pgpass` within the project directory. These files store the Authentik secret key and Authentik postgres database password respectively. For security, these files are owned by `root:root` with mode `0600` so no one other than the root user can read/modify them.

These values are stored in these files for persistence since they are generated randomly upon first launch and are required for Authentik to work correctly. If these values are changed or lost, Authentik will no longer work and will need to be reset to defaults.

Since the `.env` file will be continually updated with new values and these 2 randomly generated values need to remain persistent, Ansible will read/`slurp` these 2 files created and retrieve the values, ensuring the values within the `.env` are the same each time during every playbook run.

To ensure these key and pgpass files are not changed by Ansible, `force: no` is set on the template resource that creates these files.
