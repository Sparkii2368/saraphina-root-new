# ULTIMATE_UPGRADE.md

Status: Implemented “Go all” bundle scaffolding

Additions
- Security: Optional AES‑GCM at rest for locations (env SARA_ENC_KEY), geofences, anomaly detection
- Intelligence: Movement forecast, risk scoring; geofence enter events
- UX: Web dashboard PWA + WebSocket live updates; metrics endpoint
- Autonomy: Risk‑aware recovery step ordering; plugin extension points
- Plugins: Base/registry + sample discovery/telemetry plugins
- DevOps: Load and chaos test scripts

Quick start
- CLI (natural language OK):
  - python saraphina_cli.py "/locate test-device-001 simulate from 37.775 -122.419"
  - python saraphina_cli.py "/track test-device-001 every 1 for 5 seconds from 37.775 -122.419 simulate"
  - python saraphina_cli.py "/lost workflow start test-device-001 --simulate"
- Dashboard (requires fastapi, uvicorn):
  - python -c "import sys;from saraphina.web_dashboard import create_app;import uvicorn;uvicorn.run(create_app(),host='127.0.0.1',port=8000)"
  - Open http://127.0.0.1:8000/dashboard

Security (optional)
- Set encryption key: set SARA_ENC_KEY to passphrase or 64‑hex bytes
- cryptography recommended for AES‑GCM

Load/Chaos
- python scripts/load_test.py 50 100
- python scripts/chaos.py chaos-device-001
