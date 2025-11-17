# Lightway VPN

A small, self-hosted WireGuard configuration manager and UI for creating and managing peers and server configs. The repository contains a Python-based backend and a TypeScript/Vite frontend, plus helpers and templates for generating WireGuard configuration files.

This README gives quick start steps for both Docker-based deployment and local development, plus a short walkthrough of the repository layout and configuration points you will likely need to change.

## Prerequisites

- Docker & Docker Compose (for the easiest deployment)
- Wireguard tools for clients (check how to install it in your devices)

## Quickstart (Docker)

1. Clone the repo and change into the project folder:

```bash
git clone https://github.com/wharton-SP/ligthway-VPN.git
cd ligthway-VPN
```

> Optionnal but important

Change IP address to use in project
```python
python3 ip.py
```

2. Build and run the full stack (backend + frontend) with Docker Compose:

```bash
docker compose up --build
```

To run detached:

```bash
docker compose up -d --build
```

To stop the services:

```bash
docker compose down
```

If you already built images and want to start existing containers:

```bash
docker compose start
```


## Common tasks

- Change IP address used by project: run the provided script at the repo root:

```bash
python3 ip.py
```

- Recreate containers (when making container/build changes):

```bash
docker compose up -d --build --remove-orphans
```

## Project layout (short)

- `backend/` - Python backend (Flask/FastAPI-style app files, services, routes). Key files:
	- `backend/app.py`, `backend/wsgi.py` - app entrypoints
	- `backend/requirements.txt` - Python deps
	- `backend/routes/` - HTTP routes for peers, server, wireguard
	- `backend/services/` - business logic and wireguard interaction

- `frontend/` - Vite + React/TypeScript app
	- `frontend/src/` - source code
	- `frontend/package.json`, `pnpm-lock.yaml` - frontend package metadata

- `wireguard-config/` - examples, generated WireGuard config files, keys and templates
	- `templates/` - `peer.conf`, `server.conf` templates used by the service

- `template/` - helper templates and example files used for scaffolding

## Configuration notes

- Environment variables and settings are located in `backend/config/settings.py`. Review and adjust before production.
- WireGuard templates and generated configs live under `wireguard-config/`. Be careful with private keys — do not commit secrets to public repositories.

## Adding a peer / regenerating configs

1. Use the backend UI or API endpoint (check `backend/routes/peers.py`) to create a new peer.
2. The backend services (`backend/services/wireguard_service.py`) will use templates in `wireguard-config/templates` to generate peer/server `.conf` files.

If you prefer a manual flow, inspect `wireguard-config/` for example peer configs and the `templates/` folder for template structure.

## Troubleshooting

- If Docker Compose fails, run with `--verbose` or check logs:

```bash
docker compose logs -f
```

## Contributing

Contributions are welcome. Suggested workflow:

1. Fork the repo
2. Create a feature branch
3. Add tests for new behavior when possible
4. Open a PR with a clear description of changes

If you add sensitive keys or real WireGuard configs for testing, exclude them from commits and add them to `.gitignore`.


## Contact

If you need help or want to report issues, open an issue in the repository.
