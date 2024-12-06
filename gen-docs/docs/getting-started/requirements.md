---
sidebar_position: 1
---

# Requirements

## Supported Platforms

Currently only Ubuntu 22.04 LTS is actively supported and is used for GitHub Actions testing.

Ubuntu 24.04 LTS may work, please submit a [GitHub Issue](https://github.com/ahembree/ansible-hms-docker/issues) if you encounter any.

I've confirmed this repo also works on a Raspberry Pi 5 with 8GB RAM, but have not tested against other ARM-based systems (Apple Silicon, NAS systems, etc).

RHEL based systems (CentOS 8, Fedora, Alma Linux, Rocky Linux) may work, but are no longer being tested against and are not officially supported.

## Hardware

- Minimum 4 CPU Cores
- Minimum 4GB RAM (2GB additional if using Authentik)
- Minimum 8GB free disk space

## Software / Services

- [Supported Platform](#supported-platforms)
- `root` or `sudo` access
- [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/installation_distros.html)
- You own a domain name and are able to modify DNS `A` and `TXT` records (if you want SSL and/or dynamic DNS)
  - (Preferred) Have an internal DNS server that can resolve some or all of your domain name/zone.
- You use a [supported VPN provider](https://haugene.github.io/docker-transmission-openvpn/supported-providers/#internal_providers) (if Transmission is enabled)
- You use a [supported DNS provider](https://doc.traefik.io/traefik/https/acme/#providers) (if SSL is enabled)
- You have a Cloudflare account with the correct DNS zones and API keys configured (if Tunnel or dynamic DNS and/or SSL is enabled)
- Nvidia GPU drivers already installed (if using Nvidia GPU acceleration)

## Network

If you plan to make Plex and/or Overseerr available outside your local network, the following ports must be forwarded in your router to the IP of the server that will be running these containers.

Instructions for forwarding ports to the correct device is outside the scope of this project as every router/gateway has different instructions.

This is in no way guaranteed to be the best or most secure way to do this, and this assumes your ISP does not block these ports.

Ports required to port forward:

- `32400/tcp` (Plex)
- `80/tcp` (HTTP) (Not required if using Cloudflare Tunnel)
- `443/tcp` (HTTPS) (Not required if using Cloudflare Tunnel)

## Technical Skills

- Familiarity with editing config files (mainly YAML format)
- Familiarity with Linux (installing packages, troubleshooting, etc)
- Familiarity with Docker/containers (debugging, starting/stopping, getting a shell/CLI)
