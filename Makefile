# Horizon Rust build targets.

SHELL := /bin/bash
CARGO ?= cargo
MATURIN ?= maturin
PYTHON ?= python3

.PHONY: help test bench build-wheel verify-rust-core fmt fmt-check clippy clean ci-precheck ci-precheck-rust ci-precheck-python install-git-hooks

help:
	@echo "Horizon Rust targets:"
	@echo "  make test               - cargo test --workspace"
	@echo "  make bench              - cargo bench --workspace"
	@echo "  make build-wheel        - release wheel for horizon-py"
	@echo "  make verify-rust-core   - build + install + import-verify horizon._core"
	@echo "  make fmt                - cargo fmt --all"
	@echo "  make fmt-check          - cargo fmt --all -- --check"
	@echo "  make clippy             - cargo clippy --workspace -- -D warnings"
	@echo "  make clean              - cargo clean"
	@echo ""
	@echo "Local verification (run before committing):"
	@echo "  make ci-precheck        - rust + python gates"
	@echo "  make ci-precheck-rust   - cargo fmt --check + clippy + test"
	@echo "  make ci-precheck-python - compressor-affected python tests"
	@echo "  make install-git-hooks  - install pre-commit hooks"

test:
	$(CARGO) test --workspace

bench:
	$(CARGO) bench --workspace

build-wheel:
	$(MATURIN) build --release -m crates/horizon-py/Cargo.toml

# Build + install + import-verify the extension in one shot. Run this any
# time you suspect Python silently lost its Rust core.
verify-rust-core:
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "error: activate a venv first (e.g. source .venv/bin/activate)"; \
		exit 1; \
	fi
	bash scripts/build_rust_extension.sh

fmt:
	$(CARGO) fmt --all

fmt-check:
	$(CARGO) fmt --all -- --check

clippy lint:
	$(CARGO) clippy --workspace -- -D warnings

clean:
	$(CARGO) clean

# ─── Local verification gate ───────────────────────────────────────────────

ci-precheck: ci-precheck-rust ci-precheck-python
	@echo ""
	@echo "ci-precheck PASSED."

ci-precheck-rust:
	@echo "── ci-precheck-rust ────────────────────────────────────────────"
	$(CARGO) fmt --all -- --check
	$(CARGO) clippy --workspace -- -D warnings
	$(CARGO) test --workspace

# Compressor-affected test files expected green on every change. Builds the
# Rust extension first because most of these tests instantiate SmartCrusher,
# which hard-imports horizon._core.
ci-precheck-python:
	@echo "── ci-precheck-python ─────────────────────────────────────────"
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "error: activate a venv first (e.g. source .venv/bin/activate)"; \
		exit 1; \
	fi
	bash scripts/build_rust_extension.sh
	$(PYTHON) -m pytest -q \
		tests/test_transforms/test_smart_crusher_bugs.py \
		tests/test_transforms/test_smart_crusher_rust_parity.py \
		tests/test_transforms/test_diff_compressor.py \
		tests/test_transforms/test_diff_compressor_rust_parity.py \
		tests/test_relevance.py \
		tests/test_relevance_extra.py \
		tests/test_ccr.py \
		tests/test_acceptance.py \
		tests/test_critical_fixes.py \
		tests/test_quality_retention.py \
		tests/test_toin_integration.py

install-git-hooks:
	@scripts/install-git-hooks.sh
