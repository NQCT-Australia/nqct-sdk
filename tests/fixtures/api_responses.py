"""Sanitized API response fixtures (no real secrets)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

NOW = datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc)
USER_ID = UUID("11111111-1111-1111-1111-111111111111")
FUNCTION_ID = UUID("22222222-2222-2222-2222-222222222222")
JOB_ID = UUID("33333333-3333-3333-3333-333333333333")

BACKEND_ITEM = {
    "id": "qiskit-aer-local",
    "name": "Qiskit Aer Local",
    "provider": "qiskit",
    "type": "simulator",
    "status": "online",
    "qubits": 32,
    "max_shots": 1_000_000,
    "connectivity": None,
    "gates": ["h", "cx"],
    "noise_model": None,
    "topology": None,
    "region": None,
    "max_duration_hours": None,
    "calibration_date": None,
    "backend_metadata": None,
    "api_endpoint_url": None,
    "created_at": NOW.isoformat(),
    "updated_at": NOW.isoformat(),
}

BACKEND_LIST = {
    "items": [BACKEND_ITEM],
    "total": 1,
    "skip": 0,
    "limit": 100,
}

QUEUE_STATUS = {
    "backend_id": "qiskit-aer-local",
    "queue_depth": 2,
    "queued": 2,
    "running": 0,
    "estimated_wait_time_seconds": 10.0,
    "oldest_queued_wait_time_seconds": 5.0,
}

FUNCTION_ITEM = {
    "id": str(FUNCTION_ID),
    "name": "demo-vqe",
    "display_name": "Demo VQE",
    "description": "Example function",
    "sdk_type": "qiskit",
    "handler_function": "run",
    "version": "1.0.0",
    "is_public": False,
    "author_id": str(USER_ID),
    "author_username": "researcher",
    "author_full_name": "Research User",
    "status": "ready",
    "code_storage_path": "functions/demo/code.py",
    "created_at": NOW.isoformat(),
    "updated_at": NOW.isoformat(),
}

FUNCTION_LIST = {
    "items": [FUNCTION_ITEM],
    "total": 1,
    "skip": 0,
    "limit": 100,
}

JOB_ITEM = {
    "id": str(JOB_ID),
    "user_id": str(USER_ID),
    "user_username": "researcher",
    "user_full_name": "Research User",
    "user_email": "user@example.com",
    "function_id": str(FUNCTION_ID),
    "function_name": "demo-vqe",
    "source": "nqct_functions",
    "backend_id": "qiskit-aer-local",
    "status": "queued",
    "priority": 5,
    "shots": 1024,
    "qubits": 4,
    "circuit_depth": None,
    "parameters": {"layers": 2},
    "results": None,
    "error_message": None,
    "submit_time": NOW.isoformat(),
    "start_time": None,
    "end_time": None,
    "execution_time_seconds": None,
    "queue_position": 1,
    "estimated_wait_time_seconds": 5.0,
    "booking_bypass": False,
    "celery_task_id": "task-abc",
    "created_at": NOW.isoformat(),
    "updated_at": NOW.isoformat(),
}

JOB_DONE = {
    **JOB_ITEM,
    "status": "done",
    "queue_position": None,
    "results": {"counts": {"00": 512, "11": 512}},
    "execution_time_seconds": 1.5,
    "end_time": NOW.isoformat(),
}

JOB_LIST = {
    "items": [JOB_ITEM],
    "total": 1,
    "skip": 0,
    "limit": 100,
}

INVOKE_RESPONSE = {
    "job_id": str(JOB_ID),
    "status": "queued",
    "queue_position": 1,
    "booking_bypass": False,
    "message": "Job queued successfully",
}

JOB_SUBMIT_RESPONSE = {
    "job_id": str(JOB_ID),
    "status": "queued",
    "queue_position": 2,
    "booking_bypass": False,
    "message": "Job queued successfully. Position in queue: 2",
}

DIRECT_QASM_JOB_ITEM = {
    **JOB_ITEM,
    "function_id": None,
    "function_name": "direct_qasm",
    "source": "direct_qasm",
}

JOB_RESULTS = {
    "job_id": str(JOB_ID),
    "status": "done",
    "results": {"counts": {"00": 512, "11": 512}},
    "error_message": None,
    "execution_time_seconds": 1.5,
}

JOB_LOGS = {
    "job_id": str(JOB_ID),
    "logs": ["Job queued", "Job running", "Job completed"],
    "execution_time_seconds": 1.5,
}

FUNCTION_CODE = {
    "code": "def run(parameters):\n    return {}",
    "function_id": str(FUNCTION_ID),
    "version": "1.0.0",
}
