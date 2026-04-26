# Changelog

All notable changes to `lipa-py` are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.4] - 2026-04-26

### Added
- `callback_url` field on `SafaricomConfig` for the unified client.
- Module-level loggers (`logging.getLogger(__name__)`) on every provider client.
  Failures emit a `warning` with status code, reference, and response body before
  raising. Package init registers a `NullHandler` so the library is silent until
  the host configures logging.
- All six webhook routers and their handler-setters are now re-exported from the
  top-level `lipa_py` package (e.g. `from lipa_py import mpesa_router, set_webhook_handler`).
- Shared generic `WebhookRegistry[T]` in `lipa_py._base` powering all six routers.
- Cross-provider router contract tests (`tests/test_router_consistency.py`) covering
  async-handler validation and `/webhook` mounting.
- `[tool.pytest.ini_options]` block in `pyproject.toml` so plain `pytest` discovers
  `src/` and `tests/` without a `PYTHONPATH=src` workaround.
- This `CHANGELOG.md`.

### Changed
- The four previously bare-`global`-based routers (`airtel_money`, `tigo_pesa`,
  `safaricom`, `tips`) now use the same `WebhookRegistry` + `Depends` pattern as
  `mpesa` and `selcom`. Setter names are unchanged.
- Sync handlers passed to **any** provider's `set_*_handler` now raise `ValueError`
  immediately instead of silently hanging inside FastAPI background tasks.
- Unified Safaricom adapter now raises a clear `ValueError` if `callback_url` is
  missing, instead of silently defaulting to `https://example.com/webhook`.

## [0.1.3] - 2026-04-10

### Added
- Typed Pydantic config models per provider (`MpesaConfig`, `SelcomConfig`, etc.)
  alongside dict-based configs.
- `conversation_id` on `UnifiedPaymentRequest`.
- `service_provider_code` + `timeout` params on `MPesaClient`; `timeout` param on
  every other provider client.
- M-Pesa session token caching (eliminates a round trip on every payment).
- Top-level imports: clients, errors, schemas, and typed configs are all
  importable from `lipa_py` directly.
- Error-path coverage and routing edge-case tests (21 → 38 tests).
- PyPI Trusted Publisher GitHub Actions workflow.

### Changed
- `UnifiedPaymentClient` provider dispatch refactored from a 114-line `if/elif`
  chain into a `Dict[str, Adapter]` dispatch table.
- `Environment` dataclass deduplicated into `lipa_py._base`.

### Fixed
- `AirtelError` now exported from `airtel_money` package init.
- Airtel phone-number `int()` cast no longer crashes on a leading `+`.
- Selcom ISO-8601 timestamp no longer carries a duplicate timezone suffix.
- Selcom sandbox and production base URLs split correctly.
- Safaricom Daraja password timestamp uses UTC (was localtime).

## [0.1.2] - 2026-03-03

Initial PyPI release line. Establishes async clients for M-Pesa, Selcom,
Safaricom Daraja, Airtel Money, Tigo Pesa, and TIPS, plus a unified phone-prefix
based router and FastAPI webhook helpers.

[Unreleased]: https://github.com/PatzPaul/lipa-py/compare/v0.1.4...HEAD
[0.1.4]: https://github.com/PatzPaul/lipa-py/releases/tag/v0.1.4
[0.1.3]: https://github.com/PatzPaul/lipa-py/releases/tag/v0.1.3
[0.1.2]: https://github.com/PatzPaul/lipa-py/releases/tag/v0.1.2
