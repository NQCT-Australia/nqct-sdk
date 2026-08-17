# NQCT Python SDK

[![Documentation](https://img.shields.io/badge/Documentation-blue)](https://nqct.github.io/nqct-sdk/)

Python interface for the **National Quantum Computing Testbed (NQCT)**.

The NQCT Python SDK lets researchers and developers work with NQCT programmatically from Python, Jupyter notebooks, scripts, and automated workflows. Use it to discover available quantum computing resources, submit work, monitor jobs, and retrieve results.

The SDK provides programmatic access to the same NQCT environment available through the [NQCT Cloud portal](https://cloud.nqct.org) (see [Developer documentation](docs/README.md)).

> **NQCT is an evolving platform.** We welcome feedback, bug reports, feature requests, and complaints. See [Feedback and support](#feedback-and-support) below.

---

## Getting started

The easiest way to get started is through the example Jupyter notebooks in this repository.

They are designed to take you from your first connection to NQCT through progressively more advanced workflows.

**New to the SDK? Start here:**

1. Get an NQCT account and API key.
2. Install the Python SDK.
3. Open the **Getting Started** notebook.
4. Follow the examples and adapt them to your own work.
5. Explore the other notebooks as you become familiar with the platform.

See [Examples and notebooks](#examples-and-notebooks).

---

## Installation

Install the SDK using Python's package manager:

```bash
pip install nqct
```

> **Note:** The package will be published to PyPI as the project reaches its public release. Until then, see the repository documentation for the current installation method.

You will also need an **NQCT API key** to access the platform.

API keys are managed through your NQCT account.

---

## Feedback and support

NQCT is an active research and development platform, and **user feedback is an important part of its development**.

If you encounter a problem, have a feature request, disagree with how something works, or simply have feedback about your experience, please open an issue on GitHub.

**GitHub Issues are also the preferred forum for discussion and feedback.**

[Open an issue or join the discussion](https://github.com/NQCT-Australia/nqct-sdk/issues).

---

## Related resources

| Resource                                                            | Description           |
| ------------------------------------------------------------------- | --------------------- |
| [NQCT Cloud](https://cloud.nqct.org)                                | NQCT web portal       |
| [NQCT Python SDK](https://github.com/NQCT-Australia/nqct-sdk)       | This repository       |
| [NQCT Cloud platform](https://github.com/NQCT-Australia/nqct-cloud) | NQCT platform and API |
| [NQCT API documentation](https://api.nqct.org/docs)                 | API reference         |

---

## Project status

The NQCT Python SDK is under active development.

Current functionality and interfaces may evolve as the NQCT platform develops. See the [CHANGELOG](CHANGELOG.md) for significant changes between releases.

For the latest information about supported capabilities, see the example notebooks and current technical documentation.
