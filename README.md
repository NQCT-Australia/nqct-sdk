# nqct-sdk — Python client for NQCT Cloud

Python SDK for [NQCT Cloud](https://github.com/NQCT-Australia/nqct-cloud). Use it from notebooks, scripts, and CI to submit OpenQASM 3, monitor jobs, discover backends, and run circuits against the same REST API as the web dashboard. Deployed quantum functions remain available via `function.invoke()`.

**Status:** Phase 1 (MVP) + `submit_job`. See [CHANGELOG](CHANGELOG.md).

**Product spec (authoritative contract):** [nqct-cloud](https://github.com/NQCT-Australia/nqct-cloud/blob/main/references/specs/14-python-sdk.md) `references/specs/14-python-sdk.md`


| Environment          | URL                                                                                                            |
| -------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Production API**   | `https://api.nqct.org/api/v1` ([docs](https://api.nqct.org/docs), UI [cloud.nqct.org](https://cloud.nqct.org)) |
| Local (`nqct start`) | `http://localhost:8000/api/v1`                                                                                 |




## Installation

```bash
pip install nqct   # PyPI — will be available after first 0.1.0 release

# Local development (sibling clone) — uses uv
cd nqct-sdk
uv sync --extra dev
```



## Quick start

```python
from nqct import NQCTClient

# One-time setup (writes ~/.nqct/credentials.json, mode 0600)
NQCTClient.save_account(
    url="https://api.nqct.org/api/v1",  # or http://localhost:8000/api/v1
    api_key="nqct_your_key_here",
)

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

# Deployed functions: client.function(fn_id).invoke(...) also returns a Job

client.close()
```

Or use environment variables (recommended for CI):

```bash
export NQCT_URL=https://api.nqct.org/api/v1
export NQCT_API_KEY=nqct_...
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
3. Point the SDK at `http://localhost:8000/api/v1`

Integration tests (local or production):

```bash
export NQCT_URL=https://api.nqct.org/api/v1   # or http://localhost:8000/api/v1
export NQCT_API_KEY=nqct_...
uv run pytest -m integration
```



### Jupyter notebook

Walk through direct QASM submit interactively:

```bash
uv sync --extra notebook
export NQCT_URL=https://api.nqct.org/api/v1
export NQCT_API_KEY=nqct_...
uv run jupyter lab examples/sdk_walkthrough.ipynb
```

The notebook covers auth, backends, direct QASM submit, and job monitoring.

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
  invoke_function.py
  submit_job.py
  sdk_walkthrough.ipynb
```



## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management (no manual `venv` required).

```bash
uv sync --extra dev
uv run pre-commit install
uv run ruff check nqct tests
uv run mypy nqct
uv run pytest tests/unit
```



## Related repositories


| Repo                                                       | Role                                      |
| ---------------------------------------------------------- | ----------------------------------------- |
| [nqct-cloud](https://github.com/NQCT-Australia/nqct-cloud) | Platform API, context files, Unit 14 spec |
| **nqct-sdk** (this repo)                                   | `pip install nqct`                        |


