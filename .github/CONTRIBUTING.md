# Contributing

Thank you for helping improve OpenSign Darija. Start with the [README](../README.md),
[architecture](../docs/architecture/overview.md), and [research roadmap](../docs/research/roadmap.md).
Choose a focused issue or propose a small improvement before starting large changes.

## Setup and workflow

1. Clone the repository and enter it: `git clone <repository-url> && cd OpenSigne-Darija`.
2. Use Python 3.12, Node.js 22, npm and Docker Compose; follow the
   [local setup](../docs/operations/local-development.md) and
   [model asset instructions](../docs/operations/model-assets.md). Protected datasets
   and model binaries are not included in a fresh clone.
   Run `make install PYTHON=python3.12` and, for ML work,
   `make ml-install PYTHON=python3.12`.
3. Create a descriptive branch, for example `fix/camera-cleanup` or
   `docs/model-limitations`. Make small commits with clear imperative summaries.
4. Run relevant checks (`make test`, `make test-e2e`, and `make compose-check` as
   applicable); report skipped checks and their reasons in the pull request.
5. Open a pull request explaining the problem, change, verification, and risks. Ask for
   review and address feedback; update documentation when behavior or setup changes.

Follow the existing language style and run `make lint`. Add focused tests for meaningful
behavior changes; do not present mocks as evidence of model accuracy. Preserve API
contracts, the separation of browser, API and inference, and the distinction between
recognition and the optional contribution workflow.

## Research and data

Read the [dataset documentation](../docs/datasets/README.md) and [model card](../docs/model-cards/mosl-isolated-sign-v1.md)
before working on ML. Preserve source data, provenance, checksums, and evaluation
splits. Document changes to preprocessing, labels, and model evaluation; avoid leakage
and never claim signer independence without evidence. Do not publish videos, weights,
personal information, or secrets without verified rights and authorization. Contribution
collection stays closed until the [readiness requirements](../docs/contributions/README.md)
are satisfied. Report vulnerabilities through the [security policy](SECURITY.md).
