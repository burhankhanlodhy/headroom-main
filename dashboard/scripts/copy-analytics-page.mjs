// Ship the Advanced Analytics page with the dashboard build.
//
// The page lives in the Horizon package (horizon/dashboard/templates/
// account_dashboard.html) and is fully static. Copying it to dist/dashboard/
// lets the web tier serve it directly at /dashboard, calling the control-plane
// API cross-origin instead of relaying through the proxy host.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = resolve(here, "../../horizon/dashboard/templates/account_dashboard.html");
const target = resolve(here, "../dist/dashboard/index.html");
const apiUrl = (process.env.VITE_API_URL || "https://api.contextshrink.com").replace(/\/+$/, "");

if (!/^https?:\/\//.test(apiUrl)) {
  throw new Error(`VITE_API_URL must be an absolute http(s) URL, got: ${apiUrl}`);
}

const html = readFileSync(source, "utf8");
const meta = `<meta name="contextshrink-api" content="${apiUrl}" />`;
if (!html.includes("<head>")) throw new Error("analytics page has no <head>");
const out = html.replace("<head>", `<head>\n    ${meta}`);

mkdirSync(dirname(target), { recursive: true });
writeFileSync(target, out);
console.log(`analytics page -> ${target} (API ${apiUrl})`);
