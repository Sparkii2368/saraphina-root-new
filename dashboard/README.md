# Saraphina Telemetry Dashboard (React via CDN)

This is a minimal local dashboard that polls the API server metrics.

How to run:
1) Start the API server from the terminal: `/api enable local` then `/api start`
2) Open the dashboard: `/dashboard open`

The page fetches `http://127.0.0.1:8000/metrics/health` every 5s.

For richer dev, you can later scaffold Vite/CRA, but this works without Node.
