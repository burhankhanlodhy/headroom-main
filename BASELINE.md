# Baseline Verification Record

Recorded before any pruning or rebranding, on the untouched Headroom tree
(commit `af8ff2d`). Every later gate compares against these numbers.

## Environment

- Windows 11, Python 3.12.0, Node v24.15.0
- Rust: rustup 1.29.1, toolchain `1.95.0` (MSVC default; Visual Studio 2022 Build Tools with VC.Tools.x86.x64 installed for this machine)
- Install: `pip install -e ".[proxy]"` into `.venv` (maturin builds `headroom._core`)
- Import smoke: `import headroom; import headroom._core` -> OK (`headroom/_core.pyd`)

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

`python -m headroom.cli --help` renders the command tree (usage: Manage
memories, run the optimization proxy, and analyze metrics).
