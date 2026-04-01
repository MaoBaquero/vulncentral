const base = () => (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

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
  const url = `${base()}${path.startsWith("/") ? path : `/${path}`}`;
  const res = await fetch(url, { method, headers, body: fetchBody });
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
