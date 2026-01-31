# Design Decisions

Below are some of the ideas behind why certain decisions were made within this project (and for me to remember why I did things this way)

## Variable Layout

The variables being stored in `inventory/group_vars/all` was decided due to [Ansible variable precedence](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable).

This layout allows someone to specify multiple hosts in the `inventory/hosts.yml` file (or other custom inventory file) each with their own specific variable settings with a "common" shared config between them. See the [Install Docs](getting-started/install.md#remote-host).

Use case: development instance with different domain and/or SSL certificate but all other settings the same

## Containers

### Gluetun

Gluetun was not implemented because adding `network_mode: "service:gluetun"` to other containers, such as qbittorrent, did not fully protect the traffic (see [this discussion post](https://github.com/ahembree/ansible-hms-docker/discussions/116#discussioncomment-12888175))
