# GPU

Supported containers:

- Plex
- Emby
- Jellyfin
- Tdarr
- Fileflows
- Unmanic
- Dispatcharr

The variables listed below for each supported GPU type should exist in your `inventory/group_vars/all/gpu.yml` file

## Intel GPU

If you have a supported Intel processor, you can enable Intel Quick Sync Video (QSV) for use within containers.

```yaml
# inventory/group_vars/all/gpu.yml

enable_intel_gpu: true
```

## Nvidia GPU

If you have a [supported Nvidia graphics card](https://developer.nvidia.com/video-encode-decode-support-matrix), you can enable Nvidia GPU transcoding.

:::note

You must install the correct Nvidia driver for your system _before_ running this playbook with the Nvidia GPU support enabled as shown below.

This playbook does _not_ install the required driver.

:::

```yaml
# inventory/group_vars/all/gpu.yml

enable_nvidia_gpu: true
```
