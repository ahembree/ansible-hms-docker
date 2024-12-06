# Updating

To easily update from this git repo _**and**_ update your custom variable names (due to deprecating/renaming variables) if you are on a previous release, run:

```bash
make update
```

Previous variable names will still work for at least a year after the change and will be noted as such within the default configs. Please update to resolve.

Please see the [Release Notes](../category/release-notes) if you are updating from a previous version.

## New Containers

When a new container is added, you will need to manually add the new container to your [Container Map](../container-map.md) file, it will look something like this:

```yaml
...
  newcontainername:
    enabled: yes
    proxy_host_rule: new-container-name
    directory: yes
    traefik: yes
    authentik: no
    authentik_provider_type: proxy
    expose_to_public: no
    homepage: yes
    homepage_stats: no
...
```

:::note

If the key (such as `newcontainername:`) does not match an available container, an error may be thrown.

:::
