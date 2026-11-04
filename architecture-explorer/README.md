# ATLAS Architecture Explorer

**Live demo** · [Open the ATLAS Architecture Explorer](https://fullscipts.github.io/ATLAS/)

A self-hosted copy of the interactive ride-hailing reference design. It serves the architecture map, the component catalog, the deployment view and the folder tree. The ride, driver and learning flows are illustrative. The server runs the explorer alone. It has no dependencies on FastAPI, PostgreSQL, Kafka, or trained models.

## Run the ride-hailing application

The starter includes the passenger and driver apps, FastAPI services, PostgreSQL and Kafka configuration, trained model commands, and an end-to-end smoke test. [Starter README](starter/README.md) · [Implementation guide](https://fullscipts.github.io/ATLAS/build.html)

[Final handover and runbook](starter/docs/FINAL_HANDOVER.md) · [UML blueprint and exact class/function inventory](starter/docs/UML_BLUEPRINT.md)

## Run from Git

Install a supported Node.js LTS release and Git on the server. The explorer uses Node.js built-ins and needs no npm install or build step.

Clone the public deployment branch. The explorer is in its own directory within the ATLAS research repository.

```bash
git clone --branch architecture-explorer --single-branch https://github.com/FUllSCIPTS/ATLAS.git atlas-architecture-explorer
cd atlas-architecture-explorer/architecture-explorer
node server.mjs
```

The source repository is public. Access to a running deployment is controlled by your server.

## Access privately

The app listens on the server's loopback address, `127.0.0.1:8080`. From your workstation, open an SSH tunnel and visit [http://127.0.0.1:8080/](http://127.0.0.1:8080/).

```bash
ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:8080:127.0.0.1:8080 YOUR_USER@YOUR_SERVER
```

Port 8080 needs no inbound firewall rule. SSH controls remote access. Other processes and users on the server can reach its loopback interface, so use a server you trust. If you add an HTTPS reverse proxy, require authentication for every explorer route before exposing it. On a port conflict, set `PORT` for the service and update the tunnel's destination port.

## Install as a Linux service

Clone or move the checkout to `/opt/atlas-architecture-explorer`. Keep the files readable by the service and writable only by the deployment user. Install Node.js on the system path available to systemd.

```bash
cd /opt/atlas-architecture-explorer/architecture-explorer
sudo install -m 0644 deploy/atlas-explorer.service /etc/systemd/system/atlas-explorer.service
sudo systemctl daemon-reload
sudo systemctl enable --now atlas-explorer
curl -fsS http://127.0.0.1:8080/healthz
```

Expected health response is `ok`. View service logs with `sudo journalctl -u atlas-explorer -n 50`.

To update from GitHub, run `git pull --ff-only` as the deployment user and restart the service with `sudo systemctl restart atlas-explorer`. Run the health check again after the restart. To roll back, check out the previous known-good commit with `git checkout --detach COMMIT_SHA` and restart. Return to the `architecture-explorer` branch before pulling again.
