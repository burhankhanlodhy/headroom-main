//! ContextShrink desktop launcher.
//!
//! Sign in, get a per-device proxy key (created through the API and kept in
//! Windows Credential Manager), keep a loopback forwarder running, and launch
//! the user's installed coding tools through the ContextShrink proxy.

mod api;
mod client;
mod secrets;

use std::path::PathBuf;
use std::process::Child;
use std::sync::Mutex;

use api::{Api, ApiError, User};
use client::Client;
use serde::Serialize;
use serde_json::Value;
use tauri::{AppHandle, Manager, RunEvent, State};

struct AppState {
    api: Api,
    client: Client,
    forwarder: Mutex<Option<Child>>,
}

#[derive(Serialize)]
struct Session {
    user: User,
    device: String,
    dashboard_url: String,
}

fn device_name() -> String {
    let host = std::env::var("COMPUTERNAME").unwrap_or_else(|_| "Windows PC".into());
    format!("Desktop: {host}")
}

/// Makes sure this device has a working proxy key, creating one if needed.
async fn ensure_device_key(state: &AppState, token: &str) -> Result<(), String> {
    if let Some(id) = secrets::device_key_id() {
        let active = state.api.key_is_active(token, &id).await.map_err(|e| e.text())?;
        if active && state.client.has_key() {
            return Ok(());
        }
    }
    let key = state
        .api
        .create_device_key(token, &device_name())
        .await
        .map_err(|e| e.text())?;
    if let Err(e) = state.client.store_key(&key.key) {
        // Never leave an unusable key active on the account.
        let _ = state.api.revoke_key(token, &key.id).await;
        return Err(e);
    }
    secrets::set_device_key_id(&key.id)
}

fn ensure_forwarder(state: &AppState) -> Result<(), String> {
    let mut slot = state.forwarder.lock().unwrap();
    let running = match slot.as_mut() {
        Some(child) => matches!(child.try_wait(), Ok(None)),
        None => false,
    };
    if running && Client::forwarder_listening() {
        return Ok(());
    }
    if let Some(mut old) = slot.take() {
        let _ = old.kill();
    }
    *slot = Some(state.client.start_forwarder(&api::proxy_url())?);
    drop(slot);
    if Client::wait_for_forwarder() {
        Ok(())
    } else {
        Err("The ContextShrink forwarder did not start. Restart the app and try again.".into())
    }
}

fn stop_forwarder(state: &AppState) {
    if let Some(mut child) = state.forwarder.lock().unwrap().take() {
        let _ = child.kill();
        let _ = child.wait();
    }
}

async fn open_session(state: &AppState, token: &str, user: User) -> Result<Session, String> {
    if !state.client.available() {
        return Err("The ContextShrink client is missing. Reinstall the app.".into());
    }
    ensure_device_key(state, token).await?;
    ensure_forwarder(state)?;
    Ok(Session {
        user,
        device: device_name(),
        dashboard_url: api::app_url(),
    })
}

/// Restores a saved session on startup; `None` means "show sign-in".
#[tauri::command]
async fn restore_session(state: State<'_, AppState>) -> Result<Option<Session>, String> {
    let Some(token) = secrets::session() else {
        return Ok(None);
    };
    match state.api.me(&token).await {
        Ok(user) => open_session(&state, &token, user).await.map(Some),
        Err(ApiError::Unauthorized) => {
            secrets::clear_all();
            state.client.clear_key();
            Ok(None)
        }
        Err(e) => Err(e.text()),
    }
}

#[tauri::command]
async fn login(
    state: State<'_, AppState>,
    email: String,
    password: String,
) -> Result<Session, String> {
    let (token, user) = state
        .api
        .login(email.trim(), &password)
        .await
        .map_err(|e| e.text())?;
    secrets::set_session(&token)?;
    // Fresh plan details (login returns only identity).
    let user = state.api.me(&token).await.unwrap_or(user);
    open_session(&state, &token, user).await
}

#[tauri::command]
async fn logout(state: State<'_, AppState>) -> Result<(), String> {
    stop_forwarder(&state);
    if let Some(token) = secrets::session() {
        if let Some(id) = secrets::device_key_id() {
            let _ = state.api.revoke_key(&token, &id).await;
        }
        state.api.logout(&token).await;
    }
    state.client.clear_key();
    secrets::clear_all();
    Ok(())
}

/// Plan, savings, Free cap and unpaid-fee details for the header.
#[tauri::command]
async fn account_summary(state: State<'_, AppState>) -> Result<Value, String> {
    let token = secrets::session().ok_or("Not signed in")?;
    let user = state.api.me(&token).await.map_err(|e| e.text())?;
    let estimate = state
        .api
        .billing_estimate(&token)
        .await
        .map_err(|e| e.text())?;
    Ok(serde_json::json!({ "user": user, "estimate": estimate }))
}

#[tauri::command]
fn list_tools() -> Vec<client::ToolInfo> {
    client::tools()
}

#[tauri::command]
fn forwarder_running() -> bool {
    Client::forwarder_listening()
}

#[tauri::command]
async fn launch_tool(
    state: State<'_, AppState>,
    tool: String,
    folder: String,
) -> Result<(), String> {
    let spec = client::TOOLS
        .iter()
        .find(|t| t.id == tool)
        .ok_or("Unknown tool")?;
    if which::which(spec.command).is_err() {
        return Err(format!("{} is not installed on this computer.", spec.name));
    }
    ensure_forwarder(&state)?;
    state.client.launch(spec, &PathBuf::from(folder))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            // Tauri can return verbatim `\\?\C:\...` paths, which cmd.exe cannot
            // run ("The system cannot find the path specified"); use plain ones.
            let exe = dunce::simplified(&app.path().resource_dir()?)
                .join("horizon")
                .join("horizon.exe");
            let data_dir = dunce::simplified(&app.path().app_local_data_dir()?).to_path_buf();
            app.manage(AppState {
                api: Api::new(),
                client: Client::new(exe, data_dir),
                forwarder: Mutex::new(None),
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            restore_session,
            login,
            logout,
            account_summary,
            list_tools,
            forwarder_running,
            launch_tool
        ])
        .build(tauri::generate_context!())
        .expect("error while building the ContextShrink app");

    app.run(|handle: &AppHandle, event| {
        if let RunEvent::Exit = event {
            stop_forwarder(&handle.state::<AppState>());
        }
    });
}
