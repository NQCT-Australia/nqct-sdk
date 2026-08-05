"""Submit a QASM job via POST /jobs and wait for results."""

from __future__ import annotations

import os
import sys

from nqct import NQCTClient

BELL_QASM = """OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
bit[2] c;
h q[0];
cx q[0], q[1];
c = measure q;
"""


def main() -> int:
    backend_id = os.environ.get("NQCT_BACKEND_ID")
    if not backend_id:
        print("Set NQCT_BACKEND_ID to a connected simulator backend id.", file=sys.stderr)
        return 1

    with NQCTClient() as client:
        job = client.submit_job(
            qasm=BELL_QASM,
            backend_id=backend_id,
            shots=1024,
            source="api",
            metadata={"label": "sdk-submit-job example"},
        )
        print(f"Job {job.id} queued at position {job.queue_position}")
        finished = job.wait(timeout=3600)
        print(f"Job finished with status {finished.status}")
        if finished.status == "done":
            print(finished.result())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
