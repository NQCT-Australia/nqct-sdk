# nqct-sdk — Python client for NQCT Cloud

Python SDK for [NQCT Cloud](https://github.com/NQCT-Australia/nqct-cloud). Use it from notebooks, scripts, and CI to submit OpenQASM 3, monitor jobs, discover backends, and run circuits against the same REST API as the web dashboard.

**Status:** Phase 1 (MVP) + `submit_job`. See [CHANGELOG](CHANGELOG.md).

**Product spec (authoritative contract):** [nqct-cloud](https://github.com/NQCT-Australia/nqct-cloud/blob/main/references/specs/14-python-sdk.md) `references/specs/14-python-sdk.md`


| Environment          | URL                                                                                                            |
| -------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Production API**   | `https://api.nqct.org/api/v1` ([docs](https://api.nqct.org/docs), UI [cloud.nqct.org](https://cloud.nqct.org)) |
| Local (`nqct start`) | `http://localhost:8000/api/v1`                                                                                 |




## Installation

Clone this repo, then install with **uv** (recommended) or **pip**.

### With uv (recommended)

Install [uv](https://docs.astral.sh/uv/) if you do not have it:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

Then sync the project (creates `.venv` and installs deps):

```bash
cd nqct-sdk
uv sync --extra dev
```

Run commands with `uv run …` (e.g. `uv run pytest tests/unit`).

### Without uv (pip + venv)

```bash
cd nqct-sdk
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Then run tools directly: `pytest tests/unit`, `ruff check nqct tests`, `mypy nqct`.

### From PyPI (not yet available)

```bash
pip install nqct   # will be available after the first PyPI release
```


## Quick start

```python
from nqct import NQCTClient

# One-time setup (writes ~/.nqct/credentials.json, mode 0600)
# URL defaults to https://api.nqct.org/api/v1
NQCTClient.save_account(api_key="nqct_your_key_here")

client = NQCTClient()

# Discover backends
for backend in client.backends(status="online"):
    print(backend.name, backend.id)

# Submit OpenQASM 3 (POST /jobs) and wait for results
job = client.submit_job(
    qasm='OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[2] q;\nbit[2] c;\nh q[0];\ncx q[0], q[1];\nc = measure q;',
    backend_id="qiskit-aer-local",
    shots=1024,
    source="api",
)
job.wait(timeout=3600)
print(job.result())

client.close()
```

Or pass the key directly (no disk write):

```python
client = NQCTClient(api_key="nqct_your_key_here")
```

For local `nqct start`, override the URL:

```python
NQCTClient.save_account(
    api_key="nqct_your_key_here",
    url="http://localhost:8000/api/v1",
)
```

Or use environment variables (recommended for CI):

```bash
export NQCT_API_KEY=nqct_...
# optional — defaults to https://api.nqct.org/api/v1
# export NQCT_URL=http://localhost:8000/api/v1
```

```python
from nqct import Client

with Client() as client:
    print(client.me())
```

Aliases: `Client` and `Runtime` are the same class as `NQCTClient`.

## Local development with nqct-cloud

Clone both repositories side by side:

```
~/Projects/
  nqct-cloud/      # platform — start with `nqct start`
  nqct-sdk/        # this repo
```

1. Start the platform from `nqct-cloud`: `nqct start`
2. Create an API key in the web UI profile page
3. Override the SDK URL (production is the default):

```python
NQCTClient.save_account(api_key="nqct_...", url="http://localhost:8000/api/v1")
```

Integration tests (local or production):

```bash
export NQCT_API_KEY=nqct_...
# optional for production (already the default); required for local:
# export NQCT_URL=http://localhost:8000/api/v1
uv run pytest -m integration          # or: pytest -m integration  (with venv active)
```

### Jupyter notebook

Walk through direct QASM submit interactively:

```bash
# uv
uv sync --extra notebook
uv run jupyter lab examples/sdk_walkthrough.ipynb

# pip (venv active)
pip install -e ".[notebook]"
jupyter lab examples/sdk_walkthrough.ipynb
```

Open the notebook, replace `API_KEY` in the first code cell, then run all. The notebook covers auth, backends, direct QASM submit, and job monitoring.

## Repository layout

```
nqct/
  client.py              # NQCTClient facade
  http/session.py        # httpx + error mapping
  auth/credentials.py
  models/                # Backend, Job, Function, ExecutionConfig
  resources/             # REST managers
  execution/polling.py   # job.wait()
  exceptions.py
tests/unit/
tests/integration/
examples/
  submit_job.py
  sdk_walkthrough.ipynb
```



## Development

Preferred: [uv](https://docs.astral.sh/uv/) (see [Installation](#installation) for install steps). Pip + venv works the same after `pip install -e ".[dev]"`.

```bash
# uv
uv sync --extra dev
uv run pre-commit install
uv run ruff check nqct tests
uv run mypy nqct
uv run pytest tests/unit

# pip (venv active)
pre-commit install
ruff check nqct tests
mypy nqct
pytest tests/unit
```



## Related repositories


| Repo                                                       | Role                                      |
| ---------------------------------------------------------- | ----------------------------------------- |
| [nqct-cloud](https://github.com/NQCT-Australia/nqct-cloud) | Platform API, context files, Unit 14 spec |
| **nqct-sdk** (this repo)                                   | `pip install nqct`                        |


