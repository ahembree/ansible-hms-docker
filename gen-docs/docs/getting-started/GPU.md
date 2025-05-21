# GPU

Supported containers:

- Plex
- Emby
- Jellyfin
- Tdarr

The variables listed below for each supported GPU type should exist in your `inventory/group_vars/all/gpu.yml` file

## Tdarr

You can also control Tdarr GPU support individually in the `inventory/group_vars/all/service_misc.yml` file. By default, it will use the values defined in the above mentioned file.

```yaml
tdarr_enable_nvidia_gpu: true
tdarr_enable_intel_gpu: true
```

## Intel GPU

If you have a supported Intel processor, you can enable Intel Quick Sync Video for use within containers.

```yaml
# inventory/group_vars/all/gpu.yml

enable_intel_gpu: true # or yes
```

## Nvidia GPU

If you have a [supported Nvidia graphics card](https://developer.nvidia.com/video-encode-and-decode-gpu-support-matrix-new), you can enable Nvidia GPU transcoding.

:::note

You must install the correct Nvidia driver for your system _before_ running this playbook with the Nvidia GPU support enabled as shown below.

This playbook does _not_ install the required driver.

:::

```yaml
# inventory/group_vars/all/gpu.yml

enable_nvidia_gpu: true # or yes
```
