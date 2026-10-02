//! ContextShrink control-plane API (the same endpoints the web dashboard uses).

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

/// Public dashboard origin. `CONTEXTSHRINK_APP_URL` overrides it for testing.
pub fn app_url() -> String {
    std::env::var("CONTEXTSHRINK_APP_URL")
        .unwrap_or_else(|_| "https://app.contextshrink.com".into())
        .trim_end_matches('/')
        .to_string()
}

fn api_url(path: &str) -> String {
    format!("{}/api{}", app_url(), path)
}

/// Hosted proxy the local forwarder relays to: its own hostname (the Pi 5
/// Cloudflare Tunnel), separate from the dashboard origin.
/// `CONTEXTSHRINK_PROXY_URL` overrides it for testing.
pub fn proxy_url() -> String {
    std::env::var("CONTEXTSHRINK_PROXY_URL")
        .unwrap_or_else(|_| "https://proxy.contextshrink.com".into())
        .trim_end_matches('/')
        .to_string()
}

#[derive(Debug)]
pub enum ApiError {
    /// Session missing, expired or revoked.
    Unauthorized,
    Message(String),
}

impl ApiError {
    pub fn text(&self) -> String {
        match self {
            ApiError::Unauthorized => "Your session has expired. Please sign in again.".into(),
            ApiError::Message(m) => m.clone(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub id: String,
    pub name: String,
    pub email: String,
    #[serde(default)]
    pub plan: Option<String>,
    #[serde(default)]
    pub subscription_status: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct DeviceKey {
    pub id: String,
    pub key: String,
}

pub struct Api {
    http: reqwest::Client,
}

impl Api {
    pub fn new() -> Self {
        let http = reqwest::Client::builder()
            .user_agent(concat!("ContextShrinkDesktop/", env!("CARGO_PKG_VERSION")))
            .timeout(std::time::Duration::from_secs(20))
            .build()
            .expect("HTTP client");
        Api { http }
    }

    async fn send(&self, req: reqwest::RequestBuilder) -> Result<Value, ApiError> {
        let resp = req.send().await.map_err(|_| {
            ApiError::Message("Cannot reach ContextShrink. Check your internet connection.".into())
        })?;
        let status = resp.status();
        if status == reqwest::StatusCode::UNAUTHORIZED {
            return Err(ApiError::Unauthorized);
        }
        let body: Value = resp.json().await.unwrap_or(Value::Null);
        if !status.is_success() {
            let detail = body
                .get("detail")
                .and_then(Value::as_str)
                .map(str::to_string)
                .unwrap_or_else(|| format!("Request failed ({status})"));
            return Err(ApiError::Message(detail));
        }
        Ok(body)
    }

    /// Returns the session token and the user.
    pub async fn login(&self, email: &str, password: &str) -> Result<(String, User), ApiError> {
        let body = self
            .send(
                self.http
                    .post(api_url("/auth/login"))
                    .json(&json!({ "email": email, "password": password })),
            )
            .await
            .map_err(|e| match e {
                ApiError::Unauthorized => ApiError::Message("Incorrect email or password.".into()),
                other => other,
            })?;
        let token = body["token"].as_str().unwrap_or_default().to_string();
        let user = serde_json::from_value(body["user"].clone())
            .map_err(|_| ApiError::Message("Unexpected login response".into()))?;
        Ok((token, user))
    }

    pub async fn me(&self, token: &str) -> Result<User, ApiError> {
        let body = self
            .send(self.http.get(api_url("/auth/me")).bearer_auth(token))
            .await?;
        serde_json::from_value(body).map_err(|_| ApiError::Message("Unexpected account response".into()))
    }

    /// Plan, savings this cycle, Free cap and any unpaid fee.
    pub async fn billing_estimate(&self, token: &str) -> Result<Value, ApiError> {
        self.send(self.http.get(api_url("/billing/estimate")).bearer_auth(token))
            .await
    }

    /// Creates a proxy key for this device, named after the computer.
    pub async fn create_device_key(&self, token: &str, name: &str) -> Result<DeviceKey, ApiError> {
        let body = self
            .send(
                self.http
                    .post(api_url("/keys"))
                    .bearer_auth(token)
                    .json(&json!({ "name": name, "scopes": ["proxy:messages", "proxy:responses"] })),
            )
            .await?;
        serde_json::from_value(body).map_err(|_| ApiError::Message("Unexpected key response".into()))
    }

    /// True while the key exists on the account and has not been revoked
    /// (e.g. from the dashboard's API Keys page).
    pub async fn key_is_active(&self, token: &str, key_id: &str) -> Result<bool, ApiError> {
        let body = self
            .send(self.http.get(api_url("/keys")).bearer_auth(token))
            .await?;
        Ok(body.as_array().is_some_and(|keys| {
            keys.iter()
                .any(|k| k["id"].as_str() == Some(key_id) && k["revoked_at"].is_null())
        }))
    }

    pub async fn revoke_key(&self, token: &str, key_id: &str) -> Result<(), ApiError> {
        self.send(
            self.http
                .delete(api_url(&format!("/keys/{key_id}")))
                .bearer_auth(token),
        )
        .await
        .map(|_| ())
    }

    pub async fn logout(&self, token: &str) {
        let _ = self
            .http
            .post(api_url("/auth/logout"))
            .bearer_auth(token)
            .send()
            .await;
    }
}
