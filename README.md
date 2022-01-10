# ansible-hms-docker

Ansible Playbook to setup an automated Home Media Server stack running on Docker across a variety of platforms with support for GPUs, SSL, DDNS, and more.

## Getting Started

- [Installation](#installation)
- [Content layout](#content-layout)
- [Configuration](#configuration)
- [Connecting the containers](#connecting-the-containers)
- [Only generate config files](#only-generate-config-files)

## Container List

- Plex: media server
- Sonarr: tv series management
- Radarr: movie management
- Bazarr: subtitle management
- Jackett: tracker management
- Transmission: download client with VPN and HTTP proxy
- Tautulli: analytics
- Traefik: reverse proxy (with SSL support from Let's Encrypt if configured)
- Portainer: container management GUI
- Ombi: request platform
- Watchtower: automatic container updates (if enabled)
- Cloudflare-ddns: dynamic dns (if enabled)

## Other Features

- GPU acceleration: Intel and Nvidia GPU support (if enabled) for the Plex container
  - You must install the drivers for your GPU yourself, it is not included in this playbook, but it will verify GPU acceleration is available
- Automated Docker installation
- Automatic container updates
- Dynamic DNS updates
- Wildcard SSL certificate generation
- Support for multiple network shares

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
- Minimum 4GB RAM
- Minimum 8GB free disk space
- Nvidia GPU drivers already installed (if using Nvidia GPU acceleration)
- Python 3.8 (Recommended, minimum Python 3.6)
- Ansible (minimum 2.9)
- If you plan to make Plex and/or Ombi available outside your local network, the following ports must be forwarded in your router to the IP of the server that will be running these containers:
  - Instructions for forwarding ports to the correct device is outside the scope of this project as every router/gateway has different instructions.
  - This is in no way guaranteed to be the best or most secure way to do this, and this assumes your ISP does not block these ports
  - `80/tcp` (HTTP)
  - `443/tcp` (HTTPS)
  - `32400/tcp` (Plex)

---

## WARNING

This playbook assumes that it is a fresh install of an operating system that has not been configured yet.
It should be safe to run on an existing system, BUT it may cause issues with Python since it installs Python 3.8, Docker repos, configures Nvidia GPU acceleration (if enabled), and configures network mounts (if enabled).

To ensure no conflicting changes with an existing system, you can run this playbook in "check mode" to see if any changes would be made by supplying the additional `--check` flag (outlined again below with example)

## Please note

Setting up the individual container configurations, such as for Sonarr, Radarr, Ombi, Jackett, etc. are outside the scope of this project. The purpose of this project is to ensure the necessary base containers are running.

## Content Layout

By default, the content is laid out in the following directory structure:

Generated compose file location: `/opt/hms-docker/docker-compose.yml`

Container data directory: `/opt/hms-docker/apps`

Default mount path for local share: `/opt/hms-docker/media_data/`

Media folder that contains movie and tv show folders: `<mount path>/_library`

Movie folder: `<media path>/Movies`

TV Show folder: `<media path>/TV_Shows`

---

## Installation

It is recommended to read and follow this guide entirely as there is a lot of configuration options that are required to get the system up and running to its full potential.

1. Install git and clone the repository:

   CentOS, Fedora, Alma, Rocky, Red Hat:

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

   CentOS, Fedora, Alma, Rocky, Red Hat

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

3. Edit the `vars/default.yml` file to configure settings and variables used in the playbook.

## Configuration

- Settings to configure:

  - `plex_claim_token` : (optional) your Plex claim code from https://plex.tv/claim
  - `hms_docker_domain` : the local domain name of the server to be used for proxy rules and SSL certificates (e.g. `home.local`)
  - `transmission_vpn_user` : the username of the VPN user
  - `transmission_vpn_pass` : the password of the VPN user
  - `transmission_vpn_provider` : the VPN provider (e.g. `nordvpn`, [see this page for the list of supported providers](https://haugene.github.io/docker-transmission-openvpn/supported-providers/#internal_providers))
  - `hms_docker_media_share_type` : the type of network share (`cifs`, `nfs`, `local`)

- Required settings for wildcard SSL certificate generation:

  - A supported DNS provider (e.g. Cloudflare), [you can find supported providers here along with their settings](https://doc.traefik.io/traefik/https/acme/#providers)
  - `traefik_ssl_enabled` : whether or not to generate a wildcard SSL certificate
  - `traefik_ssl_dns_provider_zone` : the zone of the DNS provider (e.g. `example.com`, this will default to the `hms_docker_domain` if not modified)
  - `traefik_ssl_dns_provider_code` : the code of the DNS provider (e.g. `cloudflare`, found at link above)
  - `traefik_ssl_dns_provider_environment_vars` : the environment variables, along with their values, of the DNS provider you're using (e.g. `"CF_DNS_API_TOKEN": "<token>"` if using `cloudflare`, found at link above)
  - `traefik_ssl_letsencrypt_email` : the email address to use for Let's Encrypt
  - `traefik_ssl_use_letsencrypt_staging_url` : whether or not to use the Let's Encrypt staging URL for initial testing (`yes` or `no`) (default: `yes`)
    - The certificate will say it is invalid, but if you check the issuer, it should come from the "Staging" server, meaning it worked successfully and you then change this value to `no` to use the production server and get a valid certificate.

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
  - `cloudflare_ddns_subdomain` : the subdomain record (e.g. `ombi` would be created as `ombi.example.com`) (default: `ombi`)
  - `cloudflare_ddns_proxied` : `'true'` or `'false'` to enable/disable proxying the traffic through Cloudflare (default: `'true'`)

- Optional settings to configure:
  - If you with to use a more advanced configuration, you can run this command to replace the standard config with the default advanced config:

  ```bash
  cp roles/hmsdocker/defaults/main.yml vars/default.yml
  ```

---

### Running the playbook

```bash
# If you're running against the local system (to check for any changes made, add `--check` to the end of the command):
ansible-playbook -i inventory --connection local hms-docker.yml

# If you wish to run it against a remote host, add the host to the `inventory` file and then run the command:
ansible-playbook -i inventory hms-docker.yml
```

Once the playbook has finished running, it may take up to a few minutes for the SSL certificate to be generated (if enabled).

If you do not already have a "wildcard" DNS record setup for the domain you used on your LOCAL DNS server (such as `*.home.local`), create this record to point to the IP address of the server. If you enabled Cloudflare DDNS, an "ombi" public A record will be created.

You can also create individual A records for each container listed in the table below.

If the above DNS requirements are met, you can then access the containers by using the following URLs (substituting `{{ domain }}` for the domain you used):

Plex: `https://plex.{{ domain }}`

Sonarr: `https://sonarr.{{ domain }}`

Radarr: `https://radarr.{{ domain }}`

Bazarr: `https://bazarr.{{ domain }}`

Ombi: `https://ombi.{{ domain }}`

Jackett: `https://jackett.{{ domain }}`

Transmission: `https://transmission.{{ domain }}`

Tautulli: `https://tautulli.{{ domain }}`

Traefik: `https://traefik.{{ domain }}`

Adminer: `http://adminer.{{ domain }}`

## Connecting the Containers

When connecting Jackett to Sonarr and Radarr and etc, you can use the name of the container (e.g. `jackett` or `radarr`) and then defining the container port to connect to (e.g. `jackett:9117` or `radarr:7878`).

If you choose to expose the container ports on the host (by setting `container_expose_ports: yes` in the `vars/default.yml` file), see below for which ports are mapped to which container on the host.

| Service Name       | Container Name       | Host Port (if enabled) | Container Port | Accessible via Traefik |
| ------------------ | -------------------- | ---------------------- | -------------- | ---------------------- |
| Plex               | `plex`               | `32400`                | `32400`        | &#9745;                |
| Sonarr             | `sonarr`             | `8989`                 | `8989`         | &#9745;                |
| Radarr             | `radarr`             | `7878`                 | `7878`         | &#9745;                |
| Jackett            | `jackett`            | `9117`                 | `9117`         | &#9745;                |
| Ombi               | `ombi`               | `3579`                 | `3579`         | &#9745;                |
| Transmission       | `transmission`       | `9091`                 | `9091`         | &#9745;                |
| Transmission Proxy | `transmission-proxy` | `8081`                 | `8080`         | &#9744;                |
| Portainer          | `portainer`          | `9000`                 | `9000`         | &#9745;                |
| Bazarr             | `bazarr`             | `6767`                 | `6767`         | &#9745;                |
| Tautulli           | `tautulli`           | `8181`                 | `8181`         | &#9745;                |
| Adminer            | `adminer`            | `8082`                 | `8080`         | &#9745;                |
| Traefik            | `traefik`            | `8080`                 | `8080`         | &#9745;                |
| MySQL (if enabled) | `ombi_mysql`         | `3306` (if enabled)    | `3306`         | &#9744;                |


## Only generate config files

If you only want to generate the config files for docker-compose and Traefik, you can run the following command:

```bash
ansible-playbook -i inventory --connection local generate-configs.yml
```

By default, it will output these configs into `/opt/hms-docker/`
