import { getApiBaseUrl } from "./apiBaseUrl.js";

/**
 * @param {string} path
 * @param {{ method?: string, body?: unknown, token?: string | null, formBody?: string }} opts
 */
export async function request(path, opts = {}) {
  const { method = "GET", body, token, formBody } = opts;
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  let fetchBody;
  if (formBody !== undefined) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    fetchBody = formBody;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    fetchBody = JSON.stringify(body);
  }
  const base = await getApiBaseUrl();
  const url = `${base}${path.startsWith("/") ? path : `/${path}`}`;
  let res;
  try {
    res = await fetch(url, { method, headers, body: fetchBody });
  } catch (e) {
    const name = e?.name || "";
    const msg = e?.message || "";
    const isNetwork =
      msg === "Failed to fetch" || name === "TypeError" || name === "AbortError";
    const hint =
      "Comprueba que el API esté en marcha, VITE_API_BASE_URL / VC_API_BASE_URL en el contenedor frontend (config.json), CORS_ORIGINS y la consola/red del navegador (F12). Ver docs/diagnostico-ingesta-trivy-carga.md.";
    const out = isNetwork ? `Failed to fetch. ${hint}` : msg || "Error de red";
    const err = new Error(out);
    err.code = "network_error";
    err.cause = e;
    throw err;
  }
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text };
  }
  if (!res.ok) {
    const msg = data?.error?.message || data?.raw || res.statusText;
    const code = data?.error?.code || "http_error";
    const err = new Error(msg);
    err.code = code;
    err.status = res.status;
    throw err;
  }
  return data;
}
