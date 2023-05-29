# Homepage

## Using Homepage

Homepage is able to integrate directly with Docker, allowing it to "auto-discover" the running containers/services.

Homepage can also integrate with a very large number of the containers in this project, so setting up the connection is very easy.

You just need to define the services API key in the `vars/custom/homepage_api_keys.yml` file.

It is also _highly_ recommended to ensure the permissions and ownership of this file is locked down. You can do this by running:

- `chmod 0600 vars/custom/homepage_api_keys.yml`
- `chown $(whoami):$(whoami) vars/custom/homepage_api_keys.yml`
