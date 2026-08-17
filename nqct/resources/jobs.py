"""Job resource manager — ``GET /jobs`` and ``POST /jobs``."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from nqct.httpss.session import HTTPSession
from nqct.models.execution import (
    ExecutionConfig,
    HardwareExecutionConfig,
    QubitMappingEntry,
    QubitMappingLike,
    SimulatorExecutionConfig,
)
from nqct.models.job import Job, job_from_api

JobSubmitSource = Literal["direct_qasm", "api", "pulse_designer"]

QubitMapping = list[QubitMappingLike]


def build_execution_config(
    *,
    optimization_level: int = 1,
    fake_backend_name: str | None = None,
    custom_noise_model: dict[str, Any] | None = None,
    qubit_mapping: QubitMapping | None = None,
    gate_substitutions: dict[str, Any] | None = None,
    acquisition_type: str | None = None,
    averaging: str | None = None,
    shot_repeat: int | None = None,
    readout_mapping: dict[str, Any] | None = None,
    pulse_calibration_id: str | None = None,
) -> dict[str, Any]:
    """Build and validate the ``execution_config`` v1 envelope for ``POST /jobs``.

    Constructs :class:`~nqct.models.execution.ExecutionConfig` (and its nested
    simulator/hardware models) from the given kwargs, so malformed values
    (e.g. an invalid ``qubit_mapping`` entry) raise ``pydantic.ValidationError``
    before a request is ever sent. ``qubit_mapping`` entries may be plain
    dicts or already-built :class:`QubitMappingEntry` instances.

    Returns a JSON-safe dict with empty optional fields omitted — ``hardware``
    stays ``{}`` when no hardware kwargs are set, matching the pre-validation
    envelope shape.
    """
    coerced_mapping: list[QubitMappingEntry] | None = None
    if qubit_mapping is not None:
        coerced_mapping = [
            entry
            if isinstance(entry, QubitMappingEntry)
            else QubitMappingEntry.model_validate(entry)
            for entry in qubit_mapping
        ]

    config = ExecutionConfig(
        simulator=SimulatorExecutionConfig(
            optimization_level=optimization_level,
            fake_backend_name=fake_backend_name,
            custom_noise_model=custom_noise_model,
        ),
        hardware=HardwareExecutionConfig.model_validate(
            {
                "qubit_mapping": coerced_mapping,
                "gate_substitutions": gate_substitutions,
                "acquisition_type": acquisition_type,
                "averaging": averaging,
                "shot_repeat": shot_repeat,
                "readout_mapping": readout_mapping,
                "pulse_calibration_id": pulse_calibration_id,
            }
        ),
    )
    return config.model_dump(exclude_none=True)


class JobsManager:
    """List, fetch, and submit jobs."""

    def __init__(self, http: HTTPSession) -> None:
        self._http = http

    def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
        function_id: str | None = None,
        backend_id: str | None = None,
        source: str | None = None,
        user_id: UUID | str | None = None,
    ) -> list[Job]:
        """``GET /jobs`` — list jobs with optional filters (admin may filter by user)."""
        params: dict[str, Any] = {"skip": skip, "limit": limit}
        if status is not None:
            params["status"] = status
        if function_id is not None:
            params["function_id"] = function_id
        if backend_id is not None:
            params["backend_id"] = backend_id
        if source is not None:
            params["source"] = source
        if user_id is not None:
            params["user_id"] = str(user_id)

        response = self._http.get("/jobs", params=params)
        payload = response.json()
        items = payload.get("items", payload) if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            return []
        return [job_from_api(item, self._http) for item in items]

    def get(self, job_id: UUID | str) -> Job:
        """``GET /jobs/{id}`` — fetch a single job."""
        response = self._http.get(f"/jobs/{job_id}")
        return job_from_api(response.json(), self._http)

    def submit(
        self,
        *,
        qasm: str,
        backend_id: str,
        shots: int = 1024,
        priority: int = 5,
        source: JobSubmitSource = "direct_qasm",
        execution_config: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        fake_backend_name: str | None = None,
        optimization_level: int = 1,
        custom_noise_model: dict[str, Any] | None = None,
        qubit_mapping: QubitMapping | None = None,
        gate_substitutions: dict[str, Any] | None = None,
        acquisition_type: str | None = None,
        averaging: str | None = None,
        shot_repeat: int | None = None,
        readout_mapping: dict[str, Any] | None = None,
        pulse_calibration_id: str | None = None,
    ) -> Job:
        """``POST /jobs`` — enqueue OpenQASM 3 on a managed backend.

        Returns a refreshed ``Job`` (``GET /jobs/{id}``) including queue metadata.
        Use ``source="api"`` for automation clients that distinguish SDK submits.
        Use ``source="pulse_designer"`` when submitting regenerated OpenPulse QASM
        for hardware execution. If ``execution_config`` is passed explicitly, it is
        sent as-is and the ``fake_backend_name``/``optimization_level``/
        ``custom_noise_model``/``qubit_mapping``/``gate_substitutions``/
        ``acquisition_type``/``averaging``/``shot_repeat``/``readout_mapping``/
        ``pulse_calibration_id`` kwargs are ignored.
        """
        if execution_config is None:
            execution_config = build_execution_config(
                optimization_level=optimization_level,
                fake_backend_name=fake_backend_name,
                custom_noise_model=custom_noise_model,
                qubit_mapping=qubit_mapping,
                gate_substitutions=gate_substitutions,
                acquisition_type=acquisition_type,
                averaging=averaging,
                shot_repeat=shot_repeat,
                readout_mapping=readout_mapping,
                pulse_calibration_id=pulse_calibration_id,
            )

        body: dict[str, Any] = {
            "backend_id": backend_id,
            "shots": shots,
            "priority": priority,
            "source": source,
            "program": {"format": "openqasm3", "content": qasm},
            "execution_config": execution_config,
            "metadata": metadata or {},
        }
        response = self._http.post("/jobs", json=body)
        payload = response.json()
        job_id = payload.get("job_id")
        if not job_id:
            raise ValueError("POST /jobs response missing job_id")
        return self.get(job_id)
