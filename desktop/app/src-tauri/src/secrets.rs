//! App secrets in Windows Credential Manager.
//!
//! Holds the dashboard session token and the ID of this device's proxy key
//! (needed to revoke it on sign-out). The proxy key itself is stored by the
//! bundled Horizon client (`horizon vault`), which the forwarder reads.

use keyring::Entry;

const SERVICE: &str = "ContextShrink Desktop";
const SESSION: &str = "session";
const DEVICE_KEY_ID: &str = "device-key-id";

fn entry(name: &str) -> Option<Entry> {
    Entry::new(SERVICE, name).ok()
}

fn get(name: &str) -> Option<String> {
    entry(name)?.get_password().ok().filter(|v| !v.is_empty())
}

fn set(name: &str, value: &str) -> Result<(), String> {
    entry(name)
        .ok_or("Credential Manager is unavailable")?
        .set_password(value)
        .map_err(|e| format!("Could not save to Credential Manager: {e}"))
}

fn clear(name: &str) {
    if let Some(e) = entry(name) {
        let _ = e.delete_credential();
    }
}

pub fn session() -> Option<String> {
    get(SESSION)
}

pub fn set_session(token: &str) -> Result<(), String> {
    set(SESSION, token)
}

pub fn device_key_id() -> Option<String> {
    get(DEVICE_KEY_ID)
}

pub fn set_device_key_id(id: &str) -> Result<(), String> {
    set(DEVICE_KEY_ID, id)
}

pub fn clear_all() {
    clear(SESSION);
    clear(DEVICE_KEY_ID);
}
