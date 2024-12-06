---
sidebar_position: 1
slug: /
---

# Introduction

ansible-hms-docker helps setup a home media server automation pipeline using many containers.

The idea was to go from a fresh OS install to a fully running media server after only installing Ansible and configuring variables.

Setting up the individual container configurations, such as for Sonarr, Radarr, Overseerr, Prowlarr, etc. are outside the scope of this project. The purpose of this project is to ensure the necessary base containers are running with the appropriate configs. There is a basic outline of how to connect the containers together in the [Container Connections](./Examples/container-connections.md) doc.

## Features

- Automatic Docker installation
- Automatic container/service updates
- Wildcard SSL certificate generation
- Dynamic DNS updates with Cloudflare
- GPU acceleration for media transcoding
  - Intel and Nvidia GPU support
  - You must install the drivers for your Nvidia GPU yourself, it is not included in this playbook, but it will verify GPU acceleration is available
- Support for multiple network shares
- Single Sign-On with Authentik
- Support for separate 4K instances of Sonarr and Radarr
- Automated dashboard configuration in [Homepage](https://gethomepage.dev/)
- Custom scripts
  - Advanced monitoring script(s) for Uptime-Kuma to detect if media is actually accessible by the Plex container
  - Convert Traefik certificate file to a Plex-supported certificate file (PKCS12)

## Contributing

Pull requests are always welcome!

If you have suggestions for containers to add or any other improvements, please submit a [Discussion Post](https://github.com/ahembree/ansible-hms-docker/discussions)
