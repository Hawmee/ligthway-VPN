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

- frontend URL : `http://<server_ip>:5173`
- backend URL : `http://<server_ip>:5000`
- metrics URL : `http://<server_ip>:9586/metrics`
- protheus URL : `http://<server_ip>:9090`


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

---

---

# Complete API Routes Documentation - Lightway VPN

## Server Routes (Blueprint: `server`)

### Status & Configuration

| Method | Endpoint | Description | Parameters | Response |
|---------|----------|-------------|------------|---------|
| `GET` | `/` | Check backend status | - | `{ status, wireguard_config }` |
| `GET` | `/server-info` | Get detailed WireGuard server information | - | `{ server_public_key, publickey_server_exists, wg0_conf_exists, existing_peers_count, wireguard_path }` |

---

## Peers Routes (Blueprint: `peers`)

### Peer Management

| Method | Endpoint | Description | Parameters | Response |
|---------|----------|-------------|------------|---------|
| `GET` | `/peers` | List all peers with metrics | `?metrics=true/false` | `{ peers[], count, summary }` |
| `POST` | `/add-peer` | Create a new peer | Body: `{ name }` | `{ message, peer_name, ip_address, public_key, config_file, directory }` |
| `GET` | `/peer/<name>` | Get peer configuration | `?metrics=true/false` | `{ peer_name, config, [metrics, bandwidth, history] }` |
| `GET` | `/peer/<name>/metrics` | Get detailed peer metrics | `?hours=1-24` | `{ peer_name, public_key, stats, bandwidth, history }` |
| `DELETE` | `/peer/<name>` | Delete a peer | - | `{ message }` |

---

## WireGuard Routes (Blueprint: `wireguard`)

### Service Control

| Method | Endpoint | Description | Parameters | Response |
|---------|----------|-------------|------------|---------|
| `POST` | `/reload-wireguard` | Restart WireGuard container | - | `{ message }` or `{ error }` |

---

## Prometheus Metrics Routes (Blueprint: `metrics`)

### Overview

| Method | Endpoint | Description | Parameters | Response |
|---------|----------|-------------|------------|---------|
| `GET` | `/api/metrics/summary` | Get global VPN summary | - | `{ total_peers, active_peers, inactive_peers, total_sent_gb, total_received_gb, total_traffic_gb, current_bandwidth_*_mbps }` |
| `GET` | `/api/metrics/health` | Check API and Prometheus health | - | `{ api_status, prometheus_status, prometheus_url }` |

### Peer Metrics

| Method | Endpoint | Description | Parameters | Response |
|---------|----------|-------------|------------|---------|
| `GET` | `/api/metrics/peers` | Get basic metrics for all peers | - | `{ peers[], count }` |
| `GET` | `/api/metrics/peers/active` | List only active peers | - | `{ active_peers[], count }` |
| `GET` | `/api/metrics/peer/<public_key>` | Get complete stats for a peer | - | `{ public_key, interface, allowed_ips, sent_bytes, received_bytes, total_bytes, sent_mb, received_mb, total_mb, last_handshake, time_since_handshake, is_active, status }` |

### Bandwidth

| Method | Endpoint | Description | Parameters | Response |
|---------|----------|-------------|------------|---------|
| `GET` | `/api/metrics/bandwidth` | Get current bandwidth for all peers | - | `{ bandwidth[], count }` |
| `GET` | `/api/metrics/peer/<public_key>/bandwidth` | Get bandwidth for a specific peer | - | `{ public_key, sent_bytes_per_sec, recv_bytes_per_sec, total_bytes_per_sec, sent_kbps, recv_kbps, sent_mbps, recv_mbps }` |

### History

| Method | Endpoint | Description | Parameters | Response |
|---------|----------|-------------|------------|---------|
| `GET` | `/api/metrics/peer/<public_key>/history` | Get bandwidth history | `?hours=1-24` | `{ public_key, duration_hours, history[], data_points }` |

---

## Classification by Functionality

### Monitoring & Status
- `GET /` - Backend status
- `GET /server-info` - Server information
- `GET /api/metrics/summary` - Global summary
- `GET /api/metrics/health` - System health

### Peer Management
- `GET /peers` - List peers
- `POST /add-peer` - Create peer
- `GET /peer/<name>` - Peer details
- `DELETE /peer/<name>` - Delete peer

### Metrics & Analytics
- `GET /peer/<name>/metrics` - Metrics by name
- `GET /api/metrics/peers` - All peers metrics
- `GET /api/metrics/peers/active` - Active peers
- `GET /api/metrics/peer/<public_key>` - Metrics by key
- `GET /api/metrics/bandwidth` - Global bandwidth
- `GET /api/metrics/peer/<public_key>/bandwidth` - Peer bandwidth
- `GET /api/metrics/peer/<public_key>/history` - Peer history

### Administration
- `POST /reload-wireguard` - Restart WireGuard

---

## Usage Examples

### Scenario 1: Create a new peer and view its metrics
```bash
# 1. Create the peer
curl -X POST http://<server_ip>:5000/add-peer \
  -H "Content-Type: application/json" \
  -d '{"name": "laptop-alice"}'

# 2. Wait a few seconds (peer connection)

# 3. View its metrics
curl http://<server_ip>:5000/peer/laptop-alice/metrics
```

### Scenario 2: Monitoring dashboard
```bash
# Global summary
curl http://<server_ip>:5000/api/metrics/summary

# All peers with their status
curl http://<server_ip>:5000/peers

# Real-time bandwidth
curl http://<server_ip>:5000/api/metrics/bandwidth
```

### Scenario 3: Analyze a specific peer
```bash
# Config + metrics
curl http://<server_ip>:5000/peer/laptop-alice?metrics=true

# 6-hour history
curl http://<server_ip>:5000/peer/laptop-alice/metrics?hours=6
```

### Scenario 4: Maintenance
```bash
# Check health
curl http://<server_ip>:5000/api/metrics/health

# Server info
curl http://<server_ip>:5000/server-info

# Restart WireGuard if needed
curl -X POST http://<server_ip>:5000/reload-wireguard
```

---

## HTTP Response Codes

| Code | Meaning | Used for |
|------|---------|----------|
| `200` | OK | Successful request |
| `400` | Bad Request | Invalid parameters, peer already exists |
| `404` | Not Found | Peer/Config not found |
| `500` | Internal Server Error | Server error, Docker/WireGuard unreachable |

---

## Important Notes

### Difference between `/peers` and `/api/metrics/peers`
- **`/peers`**: Main route, returns complete config + enriched metrics (frontend-oriented)
- **`/api/metrics/peers`**: Dedicated metrics route, raw Prometheus data (monitoring-oriented)

### Peer Identification
- By **name** in `/peer/<name>` (config reading)
- By **public key** in `/api/metrics/peer/<public_key>` (Prometheus data)

### Query Parameters
- `?metrics=true/false`: Enable/disable metrics (default: `true` for `/peers`, `false` for `/peer/<name>`)
- `?hours=1-24`: History duration in hours (default: 1, max: 24)

### Asynchronous Threads
The following endpoints launch background tasks without blocking the response:
- `POST /add-peer` → Restarts WireGuard after creation
- `DELETE /peer/<name>` → Restarts WireGuard after deletion

---

## Routes by Priority of Use

### For a Frontend Dashboard
1. `GET /api/metrics/summary` - Overview
2. `GET /peers` - Enriched list
3. `GET /api/metrics/bandwidth` - Real-time chart
4. `GET /peer/<name>/metrics?hours=6` - Peer details

### For Monitoring (Grafana/Scripts)
1. `GET /api/metrics/health` - Healthcheck
2. `GET /api/metrics/peers/active` - Connected peers
3. `GET /api/metrics/peer/<public_key>/history` - Time series
4. `GET /api/metrics/summary` - Global KPIs

### For Administration
1. `GET /server-info` - Server state
2. `POST /add-peer` - User addition
3. `DELETE /peer/<name>` - Deletion
4. `POST /reload-wireguard` - Maintenance

---

## Response Examples

### GET /api/metrics/summary
```json
{
  "total_peers": 3,
  "active_peers": 2,
  "inactive_peers": 1,
  "total_sent_gb": 12.45,
  "total_received_gb": 3.21,
  "total_traffic_gb": 15.66,
  "current_bandwidth_sent_mbps": 2.341,
  "current_bandwidth_recv_mbps": 0.876,
  "current_bandwidth_total_mbps": 3.217
}
```

### GET /peers
```json
{
  "peers": [
    {
      "name": "laptop-john",
      "ip": "10.0.3.2",
      "metrics": {
        "status": "active",
        "is_active": true,
        "traffic": {
          "sent_mb": 98.41,
          "received_mb": 4.10,
          "total_mb": 102.51
        },
        "last_handshake": "2025-11-18T10:30:45",
        "time_since_handshake": "2m 15s"
      },
      "bandwidth": {
        "sent_kbps": 125.5,
        "recv_kbps": 45.2,
        "sent_mbps": 1.004,
        "recv_mbps": 0.361
      }
    }
  ],
  "count": 1,
  "summary": {
    "total_peers": 3,
    "active_peers": 2,
    "inactive_peers": 1
  }
}
```

### POST /add-peer
```json
{
  "message": "Peer laptop-alice created successfully",
  "peer_name": "laptop-alice",
  "ip_address": "10.0.3.5",
  "public_key": "8BGW2iCuYLoHQfgdPmfOoLfn2jPBw7/oNaUEbfjKNR0=",
  "config_file": "laptop-alice.conf",
  "directory": "laptop-alice"
}
```

### GET /peer/laptop-alice/metrics?hours=6
```json
{
  "peer_name": "laptop-alice",
  "public_key": "8BGW2iCuYLoHQfgdPmfOoLfn2jPBw7/oNaUEbfjKNR0=",
  "stats": {
    "public_key": "8BGW2iCuYLoHQfgdPmfOoLfn2jPBw7/oNaUEbfjKNR0=",
    "interface": "wg0",
    "allowed_ips": "10.0.3.5/32",
    "sent_bytes": 103198720,
    "received_bytes": 4301824,
    "total_bytes": 107500544,
    "sent_mb": 98.41,
    "received_mb": 4.10,
    "total_mb": 102.51,
    "last_handshake_timestamp": 1731925845,
    "last_handshake": "2025-11-18T10:30:45",
    "time_since_handshake": "2m 15s",
    "is_active": true,
    "status": "active"
  },
  "bandwidth": {
    "public_key": "8BGW2iCuYLoHQfgdPmfOoLfn2jPBw7/oNaUEbfjKNR0=",
    "sent_bytes_per_sec": 128256.45,
    "recv_bytes_per_sec": 46284.12,
    "total_bytes_per_sec": 174540.57,
    "sent_kbps": 125.25,
    "recv_kbps": 45.20,
    "sent_mbps": 1.004,
    "recv_mbps": 0.361
  },
  "history": {
    "duration_hours": 6,
    "data_points": 360,
    "data": [
      {
        "timestamp": 1731904245,
        "datetime": "2025-11-18T04:30:45",
        "sent_bytes_per_sec": 125840.23,
        "recv_bytes_per_sec": 44120.56,
        "sent_kbps": 122.89,
        "recv_kbps": 43.09,
        "sent_mbps": 0.983,
        "recv_mbps": 0.345
      }
    ]
  }
}
```

### GET /api/metrics/health
```json
{
  "api_status": "up",
  "prometheus_status": "up",
  "prometheus_url": "http://<server_ip>:9090"
}
```