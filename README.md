# ansible-hms-docker

[![Deployment Tests](https://github.com/ahembree/ansible-hms-docker/actions/workflows/run-playbook.yml/badge.svg)](https://github.com/ahembree/ansible-hms-docker/actions/workflows/run-playbook.yml)

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
- [Using Cloudflare Tunnel](./docs/Cloudflare.md/#cloudflare-tunnel)
- [Using Authentik](./docs/Authentik.md)
- [Adding External Services to Traefik](./docs/Traefik.md/#adding-external-services-to-traefik)

## Container List

- Plex: media server
- Sonarr: tv series management
- Radarr: movie management
- Bazarr: subtitle management
- Prowlarr: tracker management
- Transmission: download client with VPN and HTTP proxy
- NZBGet: download client
- Sabnzbd: download client
- Tautulli: analytics
- Traefik: reverse proxy (with SSL support from Let's Encrypt if configured)
- Portainer: container management GUI
- Overseerr: request platform
- Requestrr: chat client for requests
- Tdarr: media transcoding
- Homepage: dashboarding / homepage
- Heimdall: dashboarding / homepage
- Watchtower: automatic container updates (if enabled)
- Cloudflare-ddns: dynamic dns (if enabled)
- Cloudflare Tunnel: Allows you to expose HTTP services without port-forwarding on your router, [see here](https://www.cloudflare.com/products/tunnel/) for more info
- Authentik: SSO
- Tailscale: mesh VPN
- Flaresolverr: CAPTCHA solving
- Uptime Kuma: service status monitoring

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
- Script to convert a Traefik certificate file to a Plex-supported certificate file (PKCS12)
- Automated dashboard configuration in Homepage
- Custom advanced monitoring script(s)

## Supported Platforms

Currently only Ubuntu 22.04+ is actively supported and is used for GitHub Actions testing.

RHEL based systems (CentOS 8, Fedora, Alma Linux, Rocky Linux) may work, but are no longer being tested against.

## Requirements

- `root` or `sudo` access
- [Supported Platform](#supported-platforms)
- 4 CPU Cores
- Minimum 4GB RAM (2GB additional if using Authentik)
- Minimum 8GB free disk space
- You own a domain name and are able to modify DNS A and TXT records (if you want SSL and/or dynamic DNS)
- You use a [supported VPN provider](https://haugene.github.io/docker-transmission-openvpn/supported-providers/#internal_providers) (if Transmission is enabled)
- You use a [supported DNS provider](https://doc.traefik.io/traefik/https/acme/#providers) (if SSL is enabled)
- You have a Cloudflare account with the correct DNS zones and API keys configured (if dynamic DNS and/or SSL is enabled)
- Familiarity with editing config files
- Familiarity with Linux (installing packages, troubleshooting, etc)
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

To ensure no conflicting changes with an existing system, you can run this playbook in "check mode" to see if any changes would be made by running `make check`

## Scope of the Project

Setting up the individual container configurations, such as for Sonarr, Radarr, Overseerr, Prowlarr, etc. are outside the scope of this project. The purpose of this project is to ensure the necessary base containers are running with the appropriate configs.

---

## Installation

It is recommended to read and follow this guide entirely as there is a lot of configuration options that are required to get the system up and running to its full potential.

1. Install requirements and clone the repository:

   Ubuntu:

   ```bash
   sudo apt update
   sudo apt install git make ansible python3-pip -y
   ```

   ```bash
   # Clone the repository and then go into the folder
   git clone https://github.com/ahembree/ansible-hms-docker.git
   cd ansible-hms-docker/
   ```

2. Proceed to [Configuration](#configuration)

---

## Configuration

Copy the base configurations to the `vars/custom` directory by running:

```bash
make basic
```

You can also quickly copy the advanced configurations by running:

```bash
make advanced
```

NOTE: Re-running these commands will overwrite any existing files in the `vars/custom` directory

If you wish to add a user(s) to the `docker` group so they can run `docker` commands without using `sudo`, you can uncomment and modify the lines in `vars/default/docker.yml`, or just run (as a user with sudo/root access) `sudo usermod -aG docker <username>`

## Content Layout

By default, the content is laid out in the following directory structure, if you wish to change the install location, you must use the advanced configuration

Generated compose file location: `/opt/hms-docker/docker-compose.yml`

Container data directory: `/opt/hms-docker/apps`

Default mount path for local share (known as the `mount_path` in this readme): `/opt/hms-docker/media_data/`

Media folder that contains movie and tv show folders (known as the `media_path` in this readme): `<mount_path>/_library`

Movie folder: `<media_path>/Movies`

TV Show folder: `<media_path>/TV_Shows`

Secrets file (where sensitive key material is stored, other than the ansible variable files in `vars/custom`): `/opt/hms-docker/.env`

- This files default ownership and permissions requires you to enter the sudo/root password every time you run a `docker-compose` command within the project directory

  - If you wish to get around this (and reduce security), you can change the `secrets_env_user`, `secrets_env_group`, and `secrets_env_mode` within the advanced configuration files to the values you prefer, or...

  - These recommended values (if you wish to do this) will allow all users with `docker` access to read the file, and thus run `docker-compose` commands without needing to run as sudo/root, but will not allow them to modify.

    - `secrets_env_user: root`

    - `secrets_env_group: docker`

    - `secrets_env_mode: 0640`

## General Configuration

All configuration options are in a (hopefully) aptly-named `.yml` file. Once you copied the config you want (by running `make basic` or `make advanced`), these config files are now in `vars/custom`

- Required settings to configure:

  - In `vars/custom/plex.yml`
    - `plex_claim_token` : your Plex claim code from [Plex's website](https://plex.tv/claim)
  
  - In `vars/custom/main_custom.yml`
    - `hms_docker_domain` : the local domain name of the server to be used for proxy rules and (if supported) SSL certificates (e.g. `home.local`)
    - `hms_docker_media_share_type` : the type of network share (`cifs`, `nfs`, `local`)
      - `nfs` if using an NFS share/mount
      - `cifs` if using Samba or a Windows file share
      - `local` if using a local directory on the same system
  
  - In `vars/custom/transmission.yml`
    - `transmission_vpn_provider` : the VPN provider (e.g. `nordvpn`, [see this page for the list of supported providers](https://haugene.github.io/docker-transmission-openvpn/supported-providers/#internal_providers))
    - `transmission_vpn_user` : the username of the VPN user
    - `transmission_vpn_pass` : the password of the VPN user

- Required settings for wildcard SSL certificate generation:

  - A supported DNS provider (e.g. Cloudflare), [you can find supported providers here along with their settings](https://doc.traefik.io/traefik/https/acme/#providers)
    - Note: This has only been tested using Cloudflare, so ymmv. This page is just to reference supported providers, their required provider code and environment variables. Do not follow any additional configuration links within that page, you only need the provider code and environment variables.
  - A valid Top-Level Domain (TLD), such as `.com` or `.net`, that Let's Encrypt is able to issue certificates for (see [the Public Suffix List](https://publicsuffix.org/list/public_suffix_list.dat) or [the IANA Root Zone Database](https://www.iana.org/domains/root/db))
  - In `vars/custom/traefik.yml`
    - `traefik_ssl_enabled` : whether or not to generate a wildcard SSL certificate
    - `traefik_ssl_dns_provider_zone` : the zone of the DNS provider (e.g. `example.com`, this will default to the `hms_docker_domain` if not modified)
    - `traefik_ssl_dns_provider_code` : the "Provider Code" of the DNS provider (e.g. `cloudflare`, found at link above)
    - `traefik_ssl_dns_provider_environment_vars` : the "Environment Variables", along with their values, of the DNS provider you're using (e.g. `"CF_DNS_API_TOKEN": "<token>"` if using `cloudflare`, found at link above)
    - `traefik_ssl_letsencrypt_email` : the email address to use for Let's Encrypt
    - `traefik_ssl_use_letsencrypt_staging_url` : whether or not to use the Let's Encrypt staging URL for initial testing (`yes` or `no`) (default: `yes`)
      - Recommended to use if setting up for the first time so you do not encounter [Rate-Limiting from Let's Encrypt](https://letsencrypt.org/docs/rate-limits/)
      - The certificate will say it is invalid within a browser, but if you check the issuer, it should come from the "Staging" server, meaning it worked successfully and you then change this value to `no` to use the production server and get a valid certificate.

If you have your media content stored on a NAS that will be connected via NFS or CIFS, please follow the directions in [the NAS readme](./docs/NAS.md) (after updating your `hms_docker_media_share_type` to the correct value as outlined above)

---

## Running the playbook

You can run the playbook using the included `Makefile` with the following commands:

```bash
# Check mode
make check

# Apply changes
make apply
```

Once the playbook has finished running, it may take up to a few minutes for the SSL certificate to be generated (if enabled).

## Accessing the Containers

If you do not already have a "wildcard" DNS record (`*`) setup for the domain you used on your LOCAL DNS server (such as `*.home.local`), create this `A` record to point to the IP address of the server. If you enabled Cloudflare DDNS, an "overseerr" public A record will be created automatically.

You can also create individual `A` records for each container listed in the [container map](./docs/Container%20Map.md/#map), or have 1 `A` record with multiple `CNAME` records pointed to the `A` record.

If the above DNS requirements are met, you can then access the containers by using the following URLs (substituting `< domain >` for the domain you used).

You can also change the subdomain of each application within the advanced `hms_docker_container_map` setting.

Plex: `https://plex.< domain >`

Sonarr: `https://sonarr.< domain >`

Radarr: `https://radarr.< domain >`

Bazarr: `https://bazarr.< domain >`

Overseerr: `https://overseerr.< domain >`

Requestrr: `https://requestrr.< domain >`

Prowlarr: `https://prowlarr.< domain >`

Transmission: `https://transmission.< domain >`

Tautulli: `https://tautulli.< domain >`

Traefik: `https://traefik.< domain >`

NZBGet: `https://nzbget.< domain >`

Authentik: `https://authentik.< domain >`

Tdarr: `https://tdarr.< domain >`

Homepage: `https://homepage.< domain >`

Uptime Kuma: `https://uptime-kuma.< domain >`
