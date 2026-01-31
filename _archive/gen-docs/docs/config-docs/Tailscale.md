# Tailscale

## Important Notes

- You must generate an Ephemeral auth key in the Tailscale admin console, you can find [instructions here](https://tailscale.com/kb/1111/ephemeral-nodes/#step-1-generate-an-ephemeral-auth-key).
  - If you must manually confirm new nodes on your Tailnet, you must confirm it within a couple minutes unless you set the key to automatically approve new nodes. Otherwise it will create a new node on your Tailnet every couple minutes.

- Tailscale auth keys are only able to be valid for up to 90 days.
