# crepe

`crepe` is an internal Microsoft Teams communication analysis and channel migration planning MVP. It extracts Teams data from Microsoft Graph, normalizes it into flat datasets, segments conversations, computes communication graphs, clusters conversation themes, and proposes a future Teams channel taxonomy. It also ships a Vue-based admin explorer for graph-first investigation.

## Architecture

- `backend/` contains the Python pipeline, FastAPI app, SQLite run registry, and tests.
- `frontend/` contains the Vue 3 + TypeScript admin explorer using `force-graph` and `echarts`.
- `data/` stores run artifacts under `raw`, `normalized`, `processed`, and `reports`.

The pipeline is snapshot-based. Each run gets a unique `run_id`, persists raw Graph payloads, and produces deterministic derived outputs that the API and UI read back later.

## Security and data handling

- This project can process sensitive internal communication content.
- The pipeline is configured to persist metadata only (`sender`, `receiver`, `entities`, `sentiment`).
- Message body content is intentionally excluded from normalized/processed/reported artifacts.
- Strict privacy mode (`CREPE_PRIVACY_FAIL_ON_CONTENT=1`) blocks processing if content-bearing keys are detected.
- Do not commit real tenant data from `data/`.
- Do not commit `.env` or any credential-bearing files.
- See [SECURITY.md](./SECURITY.md) for vulnerability reporting.
- See [PRIVACY.md](./PRIVACY.md) and [COMPLIANCE.md](./COMPLIANCE.md) for policy statements.

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

Or put the same values in `/Users/thanhdang/Documents/shrimpl/crepe/.env` and use the launcher below.

## Install (recommended)

macOS/Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/alg0s/crepe/main/install.sh | bash
```

Windows (PowerShell):

```powershell
iwr https://raw.githubusercontent.com/alg0s/crepe/main/install.ps1 -UseBasicParsing | iex
```

## Quick start (recommended)

Use one entrypoint and choose CLI or web:

```bash
crepe web                   # start API + frontend
crepe status                # show service + job status
crepe run all               # real Teams run
crepe run demo              # demo run without Graph
crepe pause                 # pause current running job
crepe cancel                # cancel current active job
crepe resume                # resume latest paused job
crepe stop                  # stop web services
```

Only one active job (running/paused) is allowed at a time.

Open the UI at `http://127.0.0.1:5173`, go to `Setup`, enter credentials, then run from `Runs`.
Credentials entered in Setup are saved automatically to the managed secure local file (`~/.config/crepe/.env` on macOS/Linux, `%APPDATA%/crepe/.env` on Windows).
By default, launcher runtime data is stored at `~/.config/crepe/data` (or `%APPDATA%/crepe/data` on Windows), not the repository `data/` folder.
Runtime SQLite job log file:
- macOS/Linux: `~/.config/crepe/data/crepe.sqlite3`
- Windows: `%APPDATA%/crepe/data/crepe.sqlite3`

If you are running directly from this repository without installer-managed PATH:

```bash
./run-crepe.sh web
./run-crepe.sh run demo
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

Backend test categories:

```bash
cd /Users/thanhdang/Documents/shrimpl/crepe/backend
PYTHONPATH=. pytest -m unit
PYTHONPATH=. pytest -m integration
PYTHONPATH=. pytest -m regression
```

Frontend tests:

```bash
cd /Users/thanhdang/Documents/shrimpl/crepe/frontend
npm test
```

## CI

GitHub Actions runs:

- backend test suite (`pytest`)
- frontend test suite (`vitest`)
- frontend production build (`vite build`)

Workflow path: `.github/workflows/ci.yml`

## Assumptions and limitations

- Authentication is app-only via `MS_TENANT_ID`, `MS_CLIENT_ID`, and `MS_CLIENT_SECRET`.
- The tool is internal-only and stores communication metadata only (no message body persistence).
- The recommendation engine is heuristic. It proposes merges, splits, and new channels, but it does not mutate Teams.
- Channel message extraction uses thread roots and replies; chat segmentation is based on inactivity gaps.
- Sentiment scoring is metadata-driven (importance and reaction signals), not text NLP.
- Some Microsoft Graph endpoints remain permission-sensitive even with tenant admin consent. The extractor surfaces those failures explicitly.
