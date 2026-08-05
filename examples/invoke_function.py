#!/usr/bin/env python3
"""Example: discover backends and invoke a deployed function.

Requires ``nqct start`` in sibling ``nqct-cloud`` and credentials via env or save_account.
"""

from __future__ import annotations

import sys

from nqct import NQCTClient


def main() -> int:
    with NQCTClient() as client:
        backends = client.backends(status="online")
        if not backends:
            print("No online backends found.", file=sys.stderr)
            return 1
        backend = client.least_busy()
        print(f"Using backend {backend.name} ({backend.id})")

        functions = client.functions(status="ready", limit=5)
        if not functions:
            print("No ready functions found — deploy one in the NQCT UI first.", file=sys.stderr)
            return 1

        fn = functions[0]
        print(f"Invoking function {fn.name} ({fn.id})")
        job = fn.invoke(backend_id=backend.id, shots=1024)
        print(f"Job {job.id} queued at position {job.queue_position}")

        finished = job.wait(timeout=3600)
        print(f"Job finished with status {finished.status}")
        if finished.status == "done":
            print(finished.result())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
