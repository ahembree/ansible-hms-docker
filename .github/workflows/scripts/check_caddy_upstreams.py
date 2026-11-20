#!/usr/bin/env python3
"""Checks that Caddy routes every container the same way its Traefik labels do.

Caddy is configured from `hmsdocker_caddy_upstreams` in roles/hmsdocker/vars/main.yml instead of container labels.
This compares each template's Traefik service port and scheme (and the container that carries the labels) with
that table, so a container added with Traefik labels but without a Caddy upstream (or with a different port)
fails CI.
"""
import glob
import os
import re
import sys

import yaml

ROLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'roles', 'hmsdocker')


def template_routes() -> dict:
    """Returns {container map key: {'host', 'port', 'scheme'}} from the Traefik labels of each template."""
    routes = {}
    for path in sorted(glob.glob(os.path.join(ROLE, 'templates', 'containers', '*.yml.j2'))):
        key = os.path.basename(path)[:-len('.yml.j2')]
        service = None
        container_names = {}
        for line in open(path):
            match = re.match(r'^  ([a-z0-9_-]+):\s*$', line)
            if match:
                service = match.group(1)
            match = re.match(r'^\s+container_name:\s*(\S+)', line)
            if match and service:
                container_names[service] = match.group(1)
            if service is None or service.endswith('-4k'):
                continue
            match = re.search(r'traefik\.http\.services\.[^.]+\.loadbalancer\.server\.port=(\d+)', line)
            if match:
                routes.setdefault(key, {'scheme': 'http'}).update({'port': int(match.group(1)), 'service': service})
            match = re.search(r'traefik\.http\.services\.[^.]+\.loadbalancer\.server\.scheme=(\w+)', line)
            if match:
                routes.setdefault(key, {})['scheme'] = match.group(1)
        if key in routes:
            routes[key]['host'] = container_names.get(routes[key]['service'], routes[key]['service'])
    return routes


def main() -> int:
    upstreams = yaml.safe_load(open(os.path.join(ROLE, 'vars', 'main.yml')))['hmsdocker_caddy_upstreams']
    errors = []
    for key, route in template_routes().items():
        upstream = upstreams.get(key)
        if upstream is None:
            errors.append(f'{key}: has Traefik labels but no entry in hmsdocker_caddy_upstreams')
            continue
        expected = {
            'host': upstream.get('host', key),
            'port': upstream.get('port'),
            'scheme': upstream.get('scheme', 'http'),
        }
        for field, value in expected.items():
            if route[field] != value:
                errors.append(f'{key}: Traefik uses {field} {route[field]!r}, hmsdocker_caddy_upstreams has {value!r}')
    for key in upstreams:
        if key not in template_routes():
            errors.append(f'{key}: is in hmsdocker_caddy_upstreams but its template has no Traefik service labels')
    for error in errors:
        print(f'ERROR: {error}')
    if errors:
        return 1
    print(f'OK: {len(upstreams)} Caddy upstreams match the Traefik labels')
    return 0


if __name__ == '__main__':
    sys.exit(main())
