//! The bundled Horizon client (`horizon.exe`, a frozen build of the Horizon CLI).
//!
//! It stores the device key (`vault`), runs the loopback forwarder that adds
//! the key to every request and relays it to the hosted proxy, and wraps the
//! user's own tools so they talk to that forwarder.

use std::io::Write;
use std::net::{SocketAddr, TcpStream};
use std::os::windows::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::time::Duration;

use serde::Serialize;

const CREATE_NO_WINDOW: u32 = 0x0800_0000;
const CREATE_NEW_CONSOLE: u32 = 0x0000_0010;

/// Loopback port of the forwarder (kept clear of a local proxy's 8787).
pub const FORWARDER_PORT: u16 = 18788;

/// A tool the launcher can wrap. Tools are never shipped with the app; they
/// must already be installed on the user's machine.
pub struct Tool {
    pub id: &'static str,
    pub name: &'static str,
    pub description: &'static str,
    /// Executable looked up on PATH to decide whether the tool is installed.
    pub command: &'static str,
    pub install_url: &'static str,
    pub wrap: &'static [&'static str],
    pub unwrap: &'static [&'static str],
}

// Serena (code memory) needs a local Python and the retrieve MCP needs proxy
// routes the hosted gateway does not expose, so both stay off for remote use.
pub const TOOLS: &[Tool] = &[
    Tool {
        id: "claude",
        name: "Claude Code",
        description: "Anthropic's agentic coding tool for the terminal",
        command: "claude",
        install_url: "https://docs.anthropic.com/en/docs/claude-code/setup",
        // Writes the base URL to the project's .claude/settings.local.json for
        // the session; unwrap restores it. --keep-mcp: the app registers no
        // MCP servers, so unwrap must not remove the user's own `horizon` or
        // code-memory registrations.
        wrap: &["wrap", "claude", "--no-proxy", "--no-mcp", "--code-memory", "none"],
        unwrap: &["unwrap", "claude", "--no-stop-proxy", "--keep-mcp"],
    },
    Tool {
        id: "opencode",
        name: "OpenCode",
        description: "Open-source AI coding agent for the terminal",
        command: "opencode",
        install_url: "https://opencode.ai/download",
        wrap: &["wrap", "opencode", "--no-proxy", "--no-mcp", "--no-serena"],
        unwrap: &["unwrap", "opencode", "--no-stop-proxy"],
    },
];

#[derive(Serialize)]
pub struct ToolInfo {
    pub id: &'static str,
    pub name: &'static str,
    pub description: &'static str,
    pub installed: bool,
    pub install_url: &'static str,
}

pub fn tools() -> Vec<ToolInfo> {
    TOOLS
        .iter()
        .map(|t| ToolInfo {
            id: t.id,
            name: t.name,
            description: t.description,
            installed: which::which(t.command).is_ok(),
            install_url: t.install_url,
        })
        .collect()
}

pub struct Client {
    exe: PathBuf,
    data_dir: PathBuf,
}

impl Client {
    pub fn new(exe: PathBuf, data_dir: PathBuf) -> Self {
        Client { exe, data_dir }
    }

    fn command(&self) -> Command {
        let mut cmd = Command::new(&self.exe);
        cmd.creation_flags(CREATE_NO_WINDOW);
        cmd
    }

    pub fn available(&self) -> bool {
        self.exe.is_file()
    }

    /// Hands the key over on stdin so it never appears in a command line.
    pub fn store_key(&self, key: &str) -> Result<(), String> {
        let mut child = self
            .command()
            .args(["vault", "set", "--stdin"])
            .stdin(Stdio::piped())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|e| format!("Could not start the ContextShrink client: {e}"))?;
        child
            .stdin
            .take()
            .ok_or("Client stdin unavailable")?
            .write_all(format!("{key}\n").as_bytes())
            .map_err(|e| e.to_string())?;
        let status = child.wait().map_err(|e| e.to_string())?;
        if status.success() {
            Ok(())
        } else {
            Err("Could not save the device key to Windows Credential Manager".into())
        }
    }

    pub fn has_key(&self) -> bool {
        // Output is discarded: only the exit status matters.
        self.command()
            .args(["vault", "get"])
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status()
            .map(|s| s.success())
            .unwrap_or(false)
    }

    pub fn clear_key(&self) {
        let _ = self
            .command()
            .args(["vault", "clear"])
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();
    }

    pub fn start_forwarder(&self, remote: &str) -> Result<Child, String> {
        std::fs::create_dir_all(&self.data_dir).map_err(|e| e.to_string())?;
        // One log for both streams: uvicorn writes request lines to stdout and
        // startup/errors to stderr.
        let log = std::fs::File::create(self.data_dir.join("forwarder.log")).ok();
        let mut cmd = self.command();
        cmd.args(["forward", "start", "--remote", remote, "--port"])
            .arg(FORWARDER_PORT.to_string())
            .stdin(Stdio::null());
        match log.as_ref().and_then(|f| Some((f.try_clone().ok()?, f.try_clone().ok()?))) {
            Some((out, err)) => cmd.stdout(out).stderr(err),
            None => cmd.stdout(Stdio::null()).stderr(Stdio::null()),
        };
        cmd.spawn()
            .map_err(|e| format!("Could not start the ContextShrink forwarder: {e}"))
    }

    pub fn wait_for_forwarder() -> bool {
        let addr = SocketAddr::from(([127, 0, 0, 1], FORWARDER_PORT));
        (0..40).any(|_| {
            if TcpStream::connect_timeout(&addr, Duration::from_millis(250)).is_ok() {
                return true;
            }
            std::thread::sleep(Duration::from_millis(250));
            false
        })
    }

    pub fn forwarder_listening() -> bool {
        let addr = SocketAddr::from(([127, 0, 0, 1], FORWARDER_PORT));
        TcpStream::connect_timeout(&addr, Duration::from_millis(300)).is_ok()
    }

    /// Opens a console window in `folder` running the wrapped tool, and
    /// restores the tool's own config when it exits.
    pub fn launch(&self, tool: &Tool, folder: &Path) -> Result<(), String> {
        if !folder.is_dir() {
            return Err("Choose an existing project folder".into());
        }
        let port = FORWARDER_PORT.to_string();
        let quote = |args: &[&str]| args.join(" ");
        let script = format!(
            "@echo off\r\n\
             title ContextShrink - {name}\r\n\
             echo Starting {name} through ContextShrink...\r\n\
             \"%CS_HORIZON%\" {wrap} --port {port}\r\n\
             set CS_EXIT=%ERRORLEVEL%\r\n\
             \"%CS_HORIZON%\" {unwrap} --port {port} >nul 2>&1\r\n\
             if not \"%CS_EXIT%\"==\"0\" (echo. & echo {name} exited with an error. & pause)\r\n",
            name = tool.name,
            wrap = quote(tool.wrap),
            unwrap = quote(tool.unwrap),
        );
        std::fs::create_dir_all(&self.data_dir).map_err(|e| e.to_string())?;
        let path = self.data_dir.join(format!("launch-{}.cmd", tool.id));
        std::fs::write(&path, script).map_err(|e| e.to_string())?;
        Command::new("cmd")
            .arg("/c")
            .arg(&path)
            .current_dir(folder)
            .env("CS_HORIZON", &self.exe)
            .creation_flags(CREATE_NEW_CONSOLE)
            .spawn()
            .map(|_| ())
            .map_err(|e| format!("Could not open a terminal for {}: {e}", tool.name))
    }
}
