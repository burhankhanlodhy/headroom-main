# Changelog

All notable changes to Horizon are documented here.

## [0.39.1] — Horizon rebrand baseline

Forked from Headroom 0.39.1 and rebranded to Horizon.

### Changed
- Full rebrand: package `headroom` -> `horizon` (`horizon-ai` on the
  packaging level), crates `headroom-core`/`headroom-py` ->
  `horizon-core`/`horizon-py`, extension module `headroom._core` ->
  `horizon._core`, CLI command `headroom` -> `horizon`, environment
  variables `HEADROOM_*` -> `HORIZON_*`, state directory `~/.headroom` ->
  `~/.horizon`, wire-level names (`x-headroom-*` headers ->
  `x-horizon-*`, `headroom_retrieve` -> `horizon_retrieve`).

### Removed
- `plugins/`, `sdk/`, `docs/` site, `benchmarks/`, `e2e/`, `examples/`,
  `sbom/`, `REALIGNMENT/`, `.github/` CI, beacon upload telemetry and the
  update-check phone-home, the `headroom-proxy`/`headroom-parity`/
  `headroom-simulators` Rust crates, and the `toin_publish` CLI (its TOML
  consumer was the removed Rust proxy).
- Local TOIN learning, the local telemetry collector and toggles are kept.
