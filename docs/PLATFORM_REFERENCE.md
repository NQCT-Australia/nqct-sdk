# Platform reference

The SDK talks to the NQCT Cloud REST API (`/api/v1`).

| Resource | URL |
|----------|-----|
| Production API base | `https://api.nqct.org/api/v1` |
| Web portal | https://cloud.nqct.org |
| Local API (after `nqct start`) | `http://localhost:8000/api/v1` |

Override the SDK base URL with `NQCT_URL` or `NQCTClient(url=...)` when not using production.
