# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `source="pulse_designer"` on `submit_job` / `JobsManager.submit` (POST /jobs allowlist).
- Hardware `execution_config` helpers: `qubit_mapping`, `gate_substitutions`, `readout_mapping`, `pulse_calibration_id`.
- Pydantic models `ExecutionConfig`, `QubitMappingEntry`, and related types in `nqct.models`.
- `Job.program`, `Job.execution_config`, and `Job.metadata` fields aligned with production `JobResponse`.

### Changed

- `examples/sdk_walkthrough.ipynb` centers on direct QASM submit; function invoke section removed for now.
- README documents production API `https://api.nqct.org/api/v1` alongside local `nqct start`.
- README quick start leads with `submit_job`.
- `build_execution_config()` now constructs and validates `ExecutionConfig`/`SimulatorExecutionConfig`/`HardwareExecutionConfig` (via Pydantic) instead of hand-building dicts; invalid `qubit_mapping` entries or unknown fields now raise `pydantic.ValidationError`. `qubit_mapping` accepts `dict` or `QubitMappingEntry` items.
- `examples/sdk_walkthrough.ipynb` submit cell catches `JobFailedError`/`JobTimeoutError` around `job.wait()` and prints status + logs instead of raising; `NOTEBOOK_API_KEY`/`NOTEBOOK_URL` now default to `None` so env/`~/.nqct` credentials resolve without editing the cell.

### Fixed

- `SimulatorExecutionConfig`/`HardwareExecutionConfig` now reject unknown fields (`extra="forbid"`), matching `QubitMappingEntry`.
- Package version in `pyproject.toml` aligned with changelog (`0.2.0`).

## [0.2.0] - 2026-07-08

### Added

- `JobsManager.submit()` / `NQCTClient.submit_job()` — `POST /jobs` with OpenQASM 3, `execution_config`, and `source` (`direct_qasm` | `api`).
- `Job.booking_bypass` and `Job.source` fields aligned with Unit 07 program-centric jobs API.
- `client.jobs(source=...)` filter parameter.
- Example `examples/submit_job.py`.

### Changed

- Managed-backend circuit execution on the platform is async (`POST /circuits/submit`); use `submit_job()` instead of a sync `run_circuit()` helper (planned Phase 2).

## [0.1.0] - 2026-07-03

### Added

- Phase 1 MVP: credentials save/load, env discovery, `BackendsManager`, `JobsManager`, `FunctionsManager`.
- Resource models `Backend`, `Job`, `Function` with `job.wait()`, `job.result()`, `job.cancel()`, `function.invoke()`.
- `client.backends()`, `client.backend()`, `client.least_busy()`, `client.jobs()`, `client.job()`, `client.functions()`, `client.function()`.
- Unit tests with `respx` fixtures; integration test suite (`pytest -m integration`).
- Example script `examples/invoke_function.py`.
- [uv](https://docs.astral.sh/uv/) for local development and CI.

### Changed

- Renamed repository from `nqct-runtime` to `nqct-sdk` (GitHub URLs, docs, Cursor rules).
- Bumped version to `0.1.0` (Phase 1 MVP).

## [0.0.1] - 2026-07-01

### Added

- Phase 0 bootstrap: `NQCTClient`, `HTTPSession`, credentials file helpers, exception hierarchy.
- Public aliases `Client` and `Runtime`.
- Unit tests, ruff, mypy, pytest, pre-commit, GitHub Actions CI.

[Unreleased]: https://github.com/NQCT-Australia/nqct-sdk/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/NQCT-Australia/nqct-sdk/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/NQCT-Australia/nqct-sdk/releases/tag/v0.1.0
[0.0.1]: https://github.com/NQCT-Australia/nqct-sdk/releases/tag/v0.0.1
