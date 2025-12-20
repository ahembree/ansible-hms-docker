---
name: Bug report
about: Create a bug report to help us improve
title: ''
labels: bug
assignees: ahembree

---

## Basics

Have you updated your local code to the latest available from the repo: yes/no

Have you ran `make update` after updating your local code: yes/no

What version of HMS-Docker are you currently using (run `cat /opt/hms-docker/.hmsd-version`), or is this a new install: 

## Operating System and Version

```bash
cat /etc/os-release
ansible --version
```

OS name and version: 

## Describe the bug

A clear and concise description of what the bug is.

## Expected behavior

A clear and concise description of what you expected to happen.

## List any applicable variables and their values

As some examples, if the issue is related to a below item then provide the variables from the mentioned file:

- Cloudflare: `cloudflare.yml`
- Authentik: `authentik.yml`
- NAS: `nas.yml` and the appropriate type (such as NFS, CIFS, or if it's an additional path)
- VPN: `vpn.yml`
- Traefik: `traefik.yml`

Please be sure to redact any sensitive information

## Additional context

Add any other context about the problem here, such as what you've already tried
