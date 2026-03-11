# crepe

`crepe` is an internal Microsoft Teams communication analysis and channel migration planning MVP. It extracts Teams data from Microsoft Graph, normalizes it into flat datasets, segments conversations, computes communication graphs, clusters conversation themes, and proposes a future Teams channel taxonomy. It also ships a Vue-based admin explorer for graph-first investigation.

## Architecture

- `backend/` contains the Python pipeline, FastAPI app, SQLite run registry, and tests.
- `frontend/` contains the Vue 3 + TypeScript admin explorer using `force-graph` and `echarts`.
- `data/` stores run artifacts under `raw`, `normalized`, `processed`, and `reports`.

The pipeline is snapshot-based. Each run gets a unique `run_id`, persists raw Graph payloads, and produces deterministic derived outputs that the API and UI read back later.

## Repository layout

```text
crepe/
  backend/
  frontend/
  data/
  README.md
  requirements.txt
  .env.example
```

## Backend setup

```bash
cd /Users/thanhdang/Documents/shrimpl/crepe
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set credentials:

```bash
export MS_TENANT_ID="..."
export MS_CLIENT_ID="..."
export MS_CLIENT_SECRET="..."
```

## Exact run commands

Run the full pipeline:

```bash
cd /Users/thanhdang/Documents/shrimpl/crepe/backend
PYTHONPATH=. python3 -m crepe.cli all
```

Generate a local demo dataset and derived outputs without Microsoft Graph:

```bash
cd /Users/thanhdang/Documents/shrimpl/crepe/backend
PYTHONPATH=. python3 -m crepe.cli demo --run-id demo-run
```

Run individual stages:

```bash
cd /Users/thanhdang/Documents/shrimpl/crepe/backend
PYTHONPATH=. python3 -m crepe.cli extract --run-id demo-run
PYTHONPATH=. python3 -m crepe.cli normalize --run-id demo-run
PYTHONPATH=. python3 -m crepe.cli analyze --run-id demo-run
PYTHONPATH=. python3 -m crepe.cli suggest --run-id demo-run
```

Run the API server:

```bash
cd /Users/thanhdang/Documents/shrimpl/crepe/backend
PYTHONPATH=. uvicorn crepe.api.app:create_app --factory --reload
```

## Frontend setup

```bash
cd /Users/thanhdang/Documents/shrimpl/crepe/frontend
npm install
npm run dev
```

The frontend expects the API at `http://127.0.0.1:8000` by default. Override with `VITE_API_BASE`.

## Required outputs

Each run produces:

- `data/raw/<run_id>/*`
- `data/normalized/<run_id>/*`
- `data/processed/<run_id>/*`
- `data/reports/<run_id>/summary.md`
- `graph_edges.csv`
- `graph_nodes.csv`
- `graph_metrics.csv`
- `conversations.csv`
- `conversation_clusters.csv`
- `cluster_summary.csv`
- `proposed_channels.csv`
- `taxonomy.md`

## Tests

Backend tests:

```bash
cd /Users/thanhdang/Documents/shrimpl/crepe/backend
PYTHONPATH=. pytest
```

Frontend tests:

```bash
cd /Users/thanhdang/Documents/shrimpl/crepe/frontend
npm test
```

## Assumptions and limitations

- Authentication is app-only via `MS_TENANT_ID`, `MS_CLIENT_ID`, and `MS_CLIENT_SECRET`.
- The tool is internal-only and stores full message content in local artifacts and the admin UI.
- The recommendation engine is heuristic. It proposes merges, splits, and new channels, but it does not mutate Teams.
- Channel message extraction uses thread roots and replies; chat segmentation is based on inactivity gaps.
- Some Microsoft Graph endpoints remain permission-sensitive even with tenant admin consent. The extractor surfaces those failures explicitly.
