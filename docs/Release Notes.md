# Release Notes

Note that any update to a new version might need to be done manually using a `make update` since some variables may now be deprecated/renamed.

## Version 1.4

New containers:

* Maintainerr
* Unpackerr
* Lidarr
* Autobrr
* Speedtest-Tracker
* Recyclarr
* tinyMediaManager
* PASTA
* Netdata

I now realize while writing these notes that version 0.2 was merged into 1.3 without a new Tag release, whoops...

## Version 1.3

No changes other than number, I didn't realize there were already "Tags" for Releases on GitHub so this just aligned them.

## Verison 0.2

Major changes to file paths inside and outside containers to standardize on one path for all apps in order to support hard links

* No more multiple volumes per container for data, all data (including multiple NAS paths) is now under 1 `/data` folder in each container

To update Plex config (source: https://support.plex.tv/articles/201154537-move-media-content-to-a-new-location/):

* Go to Settings -> Library -> Disable "Empty trash automatically after every scan"

* Apply playbook

* Add new Movie and TV paths to the appropriate Plex library

* Scan for library changes

* Once scan is finished and media is available, remove the old path from the library config

To update Arr app configs:

* Add the new root folder

* Mass edit the content and change the root path to the new one, select "No, I'll move the files myself" when prompted

* Edit your lists to also change the root paths

Remove NAS Transmission download path toggle

Remove custom Transmission download path

Remove usenet app optional volume mounts

---

## Version 0.1

Initial versioning implementation, no changes other than writing a new `.hmsd-version` file that will be read on every playbook run.

If your version is behind the current version, you will be prompted to continue so you are aware of any changes that may be made. It is highly recommened to always read through any changes.
