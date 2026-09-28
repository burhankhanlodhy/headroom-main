# Baseline Verification Record

Recorded before any pruning or rebranding, on the untouched Horizon tree
(commit `af8ff2d`). Every later gate compares against these numbers.

## Environment

- Windows 11, Python 3.12.0, Node v24.15.0
- Rust: rustup 1.29.1, toolchain `1.95.0` (MSVC default; Visual Studio 2022 Build Tools with VC.Tools.x86.x64 installed for this machine)
- Install: `pip install -e ".[proxy]"` into `.venv` (maturin builds `horizon._core`)
- Import smoke: `import horizon; import horizon._core` -> OK (`horizon/_core.pyd`)

## Test baseline

Command: `.venv\Scripts\python.exe -m pytest tests/test_transforms tests/test_ccr.py -q`

Result: **1 failed, 414 passed, 78 skipped** (~20s)

The single failure is pre-existing and environment-dependent, NOT caused by
repository changes (it fired on the untouched baseline tree):

```
tests/test_transforms/test_kompress_compressor.py::TestKompressBackendSelection::test_onnx_session_options_read_thread_caps
assert options.enable_cpu_mem_arena is False  # got True
```

Local onnxruntime version behaves differently from the version CI pins.
Gate comparisons treat `1 failed` as the floor: gates must show **0 new
failures** relative to this set (same single failure tolerated).

## CLI smoke

`python -m horizon.cli --help` renders the command tree (usage: Manage
memories, run the optimization proxy, and analyze metrics).

---

# Gate Records (Horizon rebrand)

## Gate A — post-prune (commit b98bce3)

- `pytest tests/test_transforms tests/test_ccr.py -q`: 408 passed, 78 skipped,
  1 failed (same pre-existing ONNX env failure above). 0 new failures.
- `cargo check -p headroom-core -p headroom-py`: clean.
- `headroom` CLI imports and renders help.

## Gate B — post-rebrand (commit 9725c9d)

- `pytest tests/test_transforms tests/test_ccr.py tests/test_cli -q`:
  **1,181 passed, 84 skipped, 1 failed** (same pre-existing ONNX env failure).
  0 new failures.
- `maturin build --release -m crates/horizon-py/Cargo.toml`:
  `horizon_ai-0.39.1-cp310-abi3-win_amd64.whl`.
- Fresh venv install of the wheel with `[proxy]`: `import horizon`,
  `import horizon._core`, and `horizon --help` all OK.
- `cargo check -p horizon-core -p horizon-py`: clean.
- Grep audit (`git grep -i headroom`): only intentional keeps remain
  (CHANGELOG history note, LICENSE/NOTICE legal text, README fork lineage).
- Notable fixes made during the gate: two lazy imports of the removed
  telemetry beacon (wrap.py banner), a Windows-only drive-colon bug in the
  hook-purge path tokenizer (`context_tool_cleanup._PATH_TOKEN_SPLIT`), and
  the `HORIZON_1M_MODEL` doc guard repointed to `wiki/configuration.md`.

## Gate C — per-user keys + remote relay (commits 8a118a5..)

- `pytest tests/test_cli tests/test_keys.py tests/test_vault.py
  tests/test_forwarder.py tests/test_proxy_hardening.py tests/test_transforms
  tests/test_ccr.py -q`: **1,242 passed, 84 skipped, 1 failed** (same
  pre-existing ONNX env failure). 0 new failures.
- New in this phase: per-user API keys (SQLite store, `horizon keys` CLI,
  proxy auth gate accepting `hz_`-tagged credentials), the VPS deploy pack
  (optional Caddy TLS compose profile, DEPLOY.md), the PC-side loopback
  forwarder (`horizon forward start`) with the credential in the OS key
  store (`horizon vault set`, optional `[vault]` extra), and
  `horizon wrap claude --remote URL` which swaps the local proxy for the
  forwarder relay.
- `test_mcp_reconcile.py::test_ordinary_install_does_not_adopt_serena` was
  made hermetic (pins `resolve_horizon_command`): it silently depended on
  `horizon.exe` being on the ambient PATH and failed from a bare dev shell.
- Full-tree `pytest tests` was attempted: 10 upstream test files fail to
  COLLECT for missing optional test deps (`respx`, `opentelemetry.sdk`,
  langchain, ...). Excluding them, large never-run-here areas (gateway
  suites) show pre-existing failures unrelated to this phase; they are not
  part of the gate. The gate remains the scoped suite above.
- EDITOR HAZARD (this machine): `StrReplace` intermittently corrupts files
  under this OneDrive-synced workspace (fused lines at unrelated offsets,
  cp1252 mojibake of em-dashes). Full-file `Write` has been reliable.
  Suspect any surprise SyntaxError whose reported line looks fine in the
  Read tool; verify with `py_compile` and rewrite whole files.
