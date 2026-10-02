"""npm's extensionless sh shims are not runnable on Windows (WinError 193)."""

from __future__ import annotations

import pytest

from horizon.cli import wrap


@pytest.mark.parametrize("tool", ["codex", "opencode"])
def test_windows_prefers_cmd_over_bare_sh_shim(monkeypatch, tool) -> None:
    found = {
        tool: rf"C:\npm\{tool}",  # POSIX sh shim: WinError 193 if launched
        f"{tool}.cmd": rf"C:\npm\{tool}.cmd",
    }
    monkeypatch.setattr(wrap.os, "name", "nt")
    monkeypatch.setattr(wrap.shutil, "which", lambda name: found.get(name))
    assert wrap._resolve_windows_launcher(tool) == rf"C:\npm\{tool}.cmd"


def test_windows_prefers_exe_then_falls_back_to_bare_name(monkeypatch) -> None:
    monkeypatch.setattr(wrap.os, "name", "nt")
    monkeypatch.setattr(
        wrap.shutil, "which", lambda name: {"codex.exe": "C:/bin/codex.exe"}.get(name)
    )
    assert wrap._resolve_windows_launcher("codex") == "C:/bin/codex.exe"
    monkeypatch.setattr(wrap.shutil, "which", lambda name: "/x/codex" if name == "codex" else None)
    assert wrap._resolve_windows_launcher("codex") == "/x/codex"


def test_non_windows_uses_plain_lookup(monkeypatch) -> None:
    monkeypatch.setattr(wrap.os, "name", "posix")
    monkeypatch.setattr(wrap.shutil, "which", lambda name: f"/usr/local/bin/{name}")
    assert wrap._resolve_windows_launcher("codex") == "/usr/local/bin/codex"
