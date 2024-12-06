# Homepage

## Using Homepage

Homepage is able to integrate directly with Docker, allowing it to "auto-discover" the running containers/services.

Homepage can also integrate with a very large number of the containers in this project, so setting up the connection is very easy.

You just need to define the services API key in the `inventory/group_vars/all/homepage_api_keys.yml` file. These can be found in the applications setting page.

It is also _highly_ recommended to ensure the permissions and ownership of this file is locked down. You can do this by running:

```bash
chmod 0600 inventory/group_vars/all/homepage_api_keys.yml
```

```bash
chown $(whoami):$(whoami) inventory/group_vars/all/homepage_api_keys.yml
```
