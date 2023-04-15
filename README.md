# ansible-hms-docker

Ansible Playbook to setup an automated Home Media Server stack running on Docker across a variety of platforms with support for GPUs, SSL, SSO, DDNS, and more.

## Getting Started

- [Container List](#container-list)
- [Other Features](#other-features)
- [Supported Platforms](#supported-platforms)
- [Requirements](#requirements)
- [Warnings](#warning)
- [Installation](#installation)
- [Configuration](#configuration)
- [Content layout](#content-layout)
- [Connecting the containers](#connecting-the-containers)
- [Only generate config files](#only-generate-config-files)
- [Using Cloudflare Tunnel](#using-cloudflare-tunnel)
- [Using Authentik](#using-authentik)

## Container List

- Plex: media server
- Sonarr: tv series management
- Radarr: movie management
- Bazarr: subtitle management
- Prowlarr: tracker management
- Transmission: download client with VPN and HTTP proxy
- NZBGet: download client
- Tautulli: analytics
- Traefik: reverse proxy (with SSL support from Let's Encrypt if configured)
- Portainer: container management GUI
- Overseerr: request platform
- Requestrr: chat client for requests
- Tdarr: media transcoding
- Watchtower: automatic container updates (if enabled)
- Cloudflare-ddns: dynamic dns (if enabled)
- Cloudflare Tunnel: Allows you to expose HTTP services without port-forwarding on your router, [see here](https://www.cloudflare.com/products/tunnel/) for more info
- Authentik: SSO
- Tailscale: mesh VPN

## Other Features

- GPU acceleration: Intel and Nvidia GPU support (if enabled) for the Plex container
  - You must install the drivers for your GPU yourself, it is not included in this playbook, but it will verify GPU acceleration is available
- Automated Docker installation
- Automatic container updates
- Dynamic DNS updates
- Wildcard SSL certificate generation
- Support for multiple network shares
- Single Sign-On with Authentik
- Support for separate 4K instances for Sonarr and Radarr

## Supported Platforms

- RHEL based systems (CentOS 8, Fedora, Alma Linux, Rocky Linux)
- Debian based systems (Debian 9, Ubuntu 18.04+, etc.)
- Possibly Raspberry Pi (need someone to volunteer to help development)

## Requirements

- You own a domain name and are able to modify DNS A and TXT records (if you want SSL and/or dynamic DNS)
- You use a [supported VPN provider](https://haugene.github.io/docker-transmission-openvpn/supported-providers/#internal_providers) (if Transmission is enabled)
- You use a [supported DNS provider](https://doc.traefik.io/traefik/https/acme/#providers) (if SSL is enabled)
- You have a Cloudflare account with the correct zones and API keys configured (if dynamic DNS and/or SSL is enabled)
- Slight familiarity with editing config files
- Slight familiarity with Linux (installing packages, troubleshooting, etc)
- `root` or `sudo` access
- Supported Platform
- 4 CPU Cores
- Minimum 4GB RAM (2GB additional if using Authentik)
- Minimum 8GB free disk space
- Nvidia GPU drivers already installed (if using Nvidia GPU acceleration)
- Python 3.8 (Recommended, minimum Python 3.6)
- Ansible (minimum 2.9)
- If you plan to make Plex and/or Overseerr available outside your local network, the following ports must be forwarded in your router to the IP of the server that will be running these containers:
  - Instructions for forwarding ports to the correct device is outside the scope of this project as every router/gateway has different instructions.
  - This is in no way guaranteed to be the best or most secure way to do this, and this assumes your ISP does not block these ports
  - `80/tcp` (HTTP) (Not required if using Cloudflare Tunnel)
  - `443/tcp` (HTTPS) (Not required if using Cloudflare Tunnel)
  - `32400/tcp` (Plex)

---

## WARNING

This playbook assumes that it is a fresh install of an operating system that has not been configured yet.
It should be safe to run on an existing system, BUT it may cause issues with Python since it installs Python 3.8, Docker repos, configures Nvidia GPU acceleration (if enabled), and configures network mounts (if enabled).

To ensure no conflicting changes with an existing system, you can run this playbook in "check mode" to see if any changes would be made by supplying the additional `--check` flag (outlined again below with example)

## Please note

Setting up the individual container configurations, such as for Sonarr, Radarr, Overseerr, Prowlarr, etc. are outside the scope of this project. The purpose of this project is to ensure the necessary base containers are running.

---

## Installation

It is recommended to read and follow this guide entirely as there is a lot of configuration options that are required to get the system up and running to its full potential.

1. Install git and clone the repository:

   CentOS, Fedora, Alma, Rocky, RedHat:

   ```bash
   # Install git if not already installed
   sudo yum install git -y
   ```

   Ubuntu, Debian:

   ```bash
   # Install git if not already installed
   sudo apt-get install git -y
   ```

   ```bash
   # Clone the repository and then go into the folder
   git clone https://github.com/ahembree/ansible-hms-docker.git
   cd ansible-hms-docker/
   ```

2. Install Ansible if not installed already:

   CentOS, Fedora, Alma, Rocky, RedHat

   ```bash
   sudo yum install python38
   ### (If you wish to stay on Python 3.6, run `sudo yum install python3-pip` and then `pip3 install -U pip`)
   sudo pip3 install ansible
   ```

   Ubuntu, Debian

   ```bash
   sudo apt-get install python38
   ### (If you wish to stay on Python 3.6, run `sudo apt-get install python3-pip` and then `pip3 install -U pip`)
   sudo pip3 install ansible
   ```

3. Proceed to [Configuration](#configuration)

---

## Configuration

### Content Layout

By default, the content is laid out in the following directory structure, if you wish to change the install location, you must use the [advanced configuration](#using-the-advanced-configuration)

Generated compose file location: `/opt/hms-docker/docker-compose.yml`

Container data directory: `/opt/hms-docker/apps`

Default mount path for local share (known as the `mount_path` in this readme): `/opt/hms-docker/media_data/`

Media folder that contains movie and tv show folders (known as the `media_path` in this readme): `<mount path>/_library`

Movie folder: `<media path>/Movies`

TV Show folder: `<media path>/TV_Shows`

Secrets file (where all sensitive key material is stored): `/opt/hms-docker/.env`

- This files default ownership and permissions requires you to enter the sudo/root password every time you run a `docker-compose` command within the project directory

  - If you wish to get around this (and reduce security), you can change the `secrets_env_user`, `secrets_env_group`, and `secrets_env_mode` within the [advanced configuration](#using-the-advanced-configuration) to the values you prefer, or...

  - These recommended values (if you wish to do this) will allow all users with `docker` access to read the file, and thus run `docker-compose` commands without needing to run as sudo/root, but will not allow them to modify.

    - `secrets_env_user: root`

    - `secrest_env_group: docker`

    - `secrets_env_mode: 0640`

### Using the advanced configuration

If you with to use a more advanced configuration, you can run this command to replace the standard config with the default advanced config:

  ```bash
  cp roles/hmsdocker/defaults/main.yml vars/default.yml
  ```

This is personal preference, but you may want to copy this `vars/default.yml` file to a `vars/custom.yml` file and then update the `vars_files` line in the `hms-docker.yml` file to point to your new custom file instead. (This `vars/custom.yml` file is ignored by git)

Edit the `vars/default.yml` or the `vars/custom.yml` file you just created to configure the settings and variables used in the playbook.

### General Configuration

- Required settings to configure:

  - `plex_claim_token` : (optional) your Plex claim code from [Plex's website](https://plex.tv/claim)
  - `hms_docker_domain` : the local domain name of the server to be used for proxy rules and (if supported) SSL certificates (e.g. `home.local`)
  - `transmission_vpn_provider` : the VPN provider (e.g. `nordvpn`, [see this page for the list of supported providers](https://haugene.github.io/docker-transmission-openvpn/supported-providers/#internal_providers))
  - `transmission_vpn_user` : the username of the VPN user
  - `transmission_vpn_pass` : the password of the VPN user
  - `hms_docker_media_share_type` : the type of network share (`cifs`, `nfs`, `local`)

- Required settings for wildcard SSL certificate generation:

  - A supported DNS provider (e.g. Cloudflare), [you can find supported providers here along with their settings](https://doc.traefik.io/traefik/https/acme/#providers)
    - Note: This has only been tested using Cloudflare, so ymmv. This page is just to reference supported providers, their required provider code and environment variables. Do not follow any additional configuration links within that page, you only need the provider code and environment variables.
  - A valid Top-Level Domain (TLD), such as `.com` or `.net`, that Let's Encrypt is able to issue certificates for (see [the Public Suffix List](https://publicsuffix.org/list/public_suffix_list.dat) or [the IANA Root Zone Database](https://www.iana.org/domains/root/db))
  - `traefik_ssl_enabled` : whether or not to generate a wildcard SSL certificate
  - `traefik_ssl_dns_provider_zone` : the zone of the DNS provider (e.g. `example.com`, this will default to the `hms_docker_domain` if not modified)
  - `traefik_ssl_dns_provider_code` : the "Provider Code" of the DNS provider (e.g. `cloudflare`, found at link above)
  - `traefik_ssl_dns_provider_environment_vars` : the "Environment Variables", along with their values, of the DNS provider you're using (e.g. `"CF_DNS_API_TOKEN": "<token>"` if using `cloudflare`, found at link above)
  - `traefik_ssl_letsencrypt_email` : the email address to use for Let's Encrypt
  - `traefik_ssl_use_letsencrypt_staging_url` : whether or not to use the Let's Encrypt staging URL for initial testing (`yes` or `no`) (default: `yes`)
    - Recommended to use if setting up for the first time so you do not encounter [Rate-Limiting from Let's Encrypt](https://letsencrypt.org/docs/rate-limits/)
    - The certificate will say it is invalid within a browser, but if you check the issuer, it should come from the "Staging" server, meaning it worked successfully and you then change this value to `no` to use the production server and get a valid certificate.

- Required settings for the `hms_docker_media_share_type` of `cifs`:

  - `nas_client_remote_cifs_path` : the path to the network share (e.g. `//nas.example.com/share`)
  - `nas_client_cifs_username` : the username of the network share
  - `nas_client_cifs_password` : the password of the network share
  - `nas_client_cifs_opts` : the options for the network share (Google can help you find the correct options)

- Required settings for the `hms_docker_media_share_type` of `nfs`:

  - `nas_client_remote_nfs_path` : the path to the network share (e.g. `nas.example.com:/share`)
  - `nas_client_nfs_opts` : the options for the network share (Google can help you find the correct options)

- Required settings for using Cloudflare DDNS:

  - A Cloudflare account and Cloudflare configured as your domains DNS servers
  - `cloudflare_ddns_enabled` : `yes` or `no` to enable/disable Cloudflare DDNS (default: `no`)
  - `cloudflare_api_token` : the API token of the Cloudflare account
  - `cloudflare_zone` : the domain name of the Cloudflare zone (e.g. `example.com`)
  - `cloudflare_ddns_subdomain` : the subdomain record (e.g. `overseerr` would be created as `overseerr.example.com`) (default: `overseerr`)
  - `cloudflare_ddns_proxied` : `'true'` or `'false'` to enable/disable proxying the traffic through Cloudflare (default: `'true'`)

---

### Running the playbook

If you wish to see the changes being made, you can add `--diff` to the end.

If you wish to see the changes that _would be made_ without actually making any changes, you can add `--diff --check`

```bash
# If you're running against the local system:
ansible-playbook -i inventory --connection local hms-docker.yml

# If you wish to run it against a remote host, add the host to the `inventory` file and then run the command:
ansible-playbook -i inventory hms-docker.yml
```

Once the playbook has finished running, it may take up to a few minutes for the SSL certificate to be generated (if enabled).

If you do not already have a "wildcard" DNS record (`*`) setup for the domain you used on your LOCAL DNS server (such as `*.home.local`), create this `A` record to point to the IP address of the server. If you enabled Cloudflare DDNS, an "overseerr" public A record will be created automatically.

You can also create individual A records for each container listed in the table below, or have 1 A record with multiple CNAME records pointed to the A record.

If the above DNS requirements are met, you can then access the containers by using the following URLs (substituting `{{ domain }}` for the domain you used).

You can also change the subdomain of each application within the advanced `hms_docker_container_map` setting.

Plex: `https://plex.{{ domain }}`

Sonarr: `https://sonarr.{{ domain }}`

Radarr: `https://radarr.{{ domain }}`

Bazarr: `https://bazarr.{{ domain }}`

Overseerr: `https://overseerr.{{ domain }}`

Requestrr: `https://requestrr.{{ domain }}`

Prowlarr: `https://prowlarr.{{ domain }}`

Transmission: `https://transmission.{{ domain }}`

Tautulli: `https://tautulli.{{ domain }}`

Traefik: `https://traefik.{{ domain }}`

NZBGet: `https://nzbget.{{ domain }}`

Authentik: `https://authentik.{{ domain }}`

Tdarr: `https://tdarr.{{ domain }}`

## Connecting the Containers

When connecting Prowlarr to Sonarr and Radarr and etc, you can use the name of the container (e.g. `prowlarr` or `radarr`) and then defining the container port to connect to (e.g. `prowlarr:9696` or `radarr:7878`).

If you choose to expose the container ports on the host (by setting `container_expose_ports: yes` in the `vars/default.yml` file), see below for which ports are mapped to which container on the host.

**NOTE:** Ports are _NOT_ exposed by default

| Service Name                             | Container Name       | Host Port (if enabled) | Container Port    | Accessible via Traefik |
| ---------------------------------------- | -------------------- | ---------------------- | ----------------- | ---------------------- |
| Plex                                     | `plex`               | `32400`                | `32400`           | &#9745;                |
| Sonarr                                   | `sonarr`             | `8989`                 | `8989`            | &#9745;                |
| Sonarr (Separate 4K instance if enabled) | `sonarr-4k`          | `8990`                 | `8989`            | &#9745;                |
| Radarr                                   | `radarr`             | `7878`                 | `7878`            | &#9745;                |
| Radarr (Separate 4K instance if enabled) | `radarr-4k`          | `7879`                 | `7878`            | &#9745;                |
| Prowlarr                                 | `prowlarr`           | `9696`                 | `9696`            | &#9745;                |
| Overseerr                                | `Overseerr`          | `5055`                 | `5055`            | &#9745;                |
| Requestrr                                | `Requestrr`          | `4545`                 | `4545`            | &#9745;                |
| Transmission                             | `transmission`       | `9091`                 | `9091`            | &#9745;                |
| Transmission                             | `transmission-proxy` | `8081`                 | `8080`            | &#9744;                |
| Portainer                                | `portainer`          | `9000`                 | `9000`            | &#9745;                |
| Bazarr                                   | `bazarr`             | `6767`                 | `6767`            | &#9745;                |
| Tautulli                                 | `tautulli`           | `8181`                 | `8181`            | &#9745;                |
| Traefik                                  | `traefik`            | `8080`                 | `8080`            | &#9745;                |
| NZBGet                                   | `nzbget`             | `6789`                 | `6789`            | &#9745;                |
| Authentik                                | `authentik-server`   | `9001` and `9443`      | `9000` and `9443` | &#9745;                |
| Tdarr                                    | `tdarr`              | `8265` and `8266`      | `8265` and `8266` | &#9745;                |

## Only generate config files

If you only want to generate the config files for docker-compose and Traefik, you can run the following command:

```bash
ansible-playbook -i inventory --connection local generate-configs.yml
```

By default, it will output these configs into `/opt/hms-docker/`

## Using Cloudflare Tunnel

1. You will need to first generate a token by following the steps [here](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/remote/#1-create-a-tunnel)

2. Once you've generated the token, update the variables `cloudflare_tunnel_enabled` to `yes` and `cloudflare_tunnel_token` to your token

3. After the container has been started, you should now see an active Connector in your Cloudflare dashboard

4. Follow [the steps here](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/remote/#2-connect-an-application) to link containers to the tunnel, following the [table above](#connecting-the-containers) for the available container names and ports (use the container name as the "Service" name in the Cloudflare webgui, and append the port, e.g. `overseerr:5055`)

### Important Notes

The "public hostname" you use for the container does not need to match any Traefik proxy rule as **this traffic does NOT pass through Traefik**, it goes directly from the container -> Cloudflare.

This also means that **SSO using Authentik will not work for any container configured to go through the Tunnel** due to the authentication middleware being applied by Traefik. In order to use Authentik with a publicly accessible container, you will need to port-forward.

## Using Authentik

In order to use Authentik, you must be using the [advanced configuration outlined above](#using-the-advanced-configuration) **AND** you must be using SSL as outlined in this project.

This Authentik installation is based on the [single application](https://goauthentik.io/docs/providers/proxy/forward_auth#single-application) proxy provider configuration.

There are no authentik proxy containers defined in the `docker-compose.yml` file. This is because authentik will auto-detect the Docker socket and be able to start/stop its own proxy containers by using the configurations below.

Authentik is able to be controlled on a per-container basis, but requires a bit of configuration as outlined below:

### How the Authentik secret keys are stored

There are 2 files created when enabling Authentik, `.authentik.key` and `.authentik.pgpass` within the project directory. These files store the Authentik secret key and Authentik postgres database password respectively. For security, these files are owned by `root:root` with mode `0600`.

These values are stored in these files for persistence since they are generated randomly upon first launch and are required for Authentik to work correctly. If these values are changed or lost, Authentik will no longer work and will need to be reset to defaults.

Since the `.env` file will be continually updated with new values and these 2 randomly generated values need to remain persistent, Ansible will read/`slurp` these 2 files created and retrieve the values, ensuring the values within the `.env` are the same each time during every playbook run.

To ensure these files are not changed by Ansible, `force: no` is set on the template resource that creates these files.

### Important Note

If you are using [Cloudflare Tunnel](#using-cloudflare-tunnel) **AND** you have disabled port forwarding to 80/443, you **MUST** create a new "public hostname" in Tunnel in order for SSO to work since the SSO server needs to be publicly accessible. If your tunnel is online and working, follow [step 4 when setting up Tunnel](#using-cloudflare-tunnel) and configure it for the `authentik-server` container.

1. Within the advanced variable settings (as outlined in the [advanced settings setup](#using-the-advanced-configuration)), enable the authentik container and enable authentik for the containers you want using the `hms_docker_container_map` variable

2. Run the playbook as normal

3. Once all containers are started, go to `https://authentik.{{ domain }}/if/flow/initial-setup/` to create the initial user and password to continue Authentik setup

4. **Configure an Application Provider within Authentik**

    a. Login

    b. Go to the Admin panel

    c. Expand `Applications` on the left

    d. Click `Providers`

    e. Create a new `Proxy Provider`

    f. Give it the same name as the application (such as Sonarr)

    g. Select `Forward auth (single application)`

    h. Set the `External host` to the URL of the application (such as `sonarr.{{ domain }}`)

    i. Click finish

5. **Configure an Application**

    a. Do a-c again

    b. Click `Applications`

    c. Create a new Application with its name, slug (lowercase name for it), and select the provider created for the application

    d. Click `Create` and now you should have Authentik in front of the application!

6. **Configure an Application Outpost**

    a. Do a-c above

    b. Click `Outposts`

    c. Give it a name, the `type` is `Proxy` and integration should be the `Local Docker connection`

    d. Select the application to associate it to

    e. IMPORTANT: copy the correct configuration generated in: `{{ hms_docker_apps_path }}/authentik/outposts/authentik-{{ container_name }}-output.yml` (so by default: `/opt/hms-docker/authentik/...`)

    - If a configuration does not exist for the container you want, ensure you've enabled authentik and have enabled authentik for that specific container

    f. Replace the configuration in the authentik webpage with this generated configuration, otherwise stuff will not work correctly.

    g. Once you click create, it will automatically create a new authentik-proxy container that will handle authentication.

    h. Note: it will take some time to setup the proxy, be patient

7. **Troubleshooting**

    a. Using the Traefik and Portainer dashboards help a LOT during the troubleshooting process

    b. If you're getting a `404 not found` error, this is likely due to the `authentik-proxy` containers not working, running, or not being configured correctly. If you just configured a new application output, wait a couple more minutes.

    c. If you're getting a `500` server error, this is possibly due to having duplicate Traefik routes for the same host rules

## Using Tailscale

### Important Notes

- You must generate an Ephemeral auth key in the Tailscale admin console, you can find [instructions here](https://tailscale.com/kb/1111/ephemeral-nodes/#step-1-generate-an-ephemeral-auth-key).

- Tailscale auth keys are only able to be valid for up to 90 days.
