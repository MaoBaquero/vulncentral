/** Base URL del API: primero /config.json (contenedor), si no VITE_API_BASE_URL (dev/build). */

let cached;
/** @type {Promise<string> | null} */
let inflight;

async function resolveBase() {
  try {
    const res = await fetch("/config.json", { cache: "no-store" });
    if (res.ok) {
      const data = await res.json();
      const url = String(data.apiBaseUrl ?? "").trim().replace(/\/$/, "");
      if (url) return url;
    }
  } catch {
    /* Sin config.json (p. ej. vite dev) */
  }
  return (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
}

/**
 * @returns {Promise<string>}
 */
export async function getApiBaseUrl() {
  if (cached !== undefined) return cached;
  if (!inflight) {
    inflight = resolveBase()
      .then((url) => {
        cached = url;
        return url;
      })
      .finally(() => {
        inflight = null;
      });
  }
  return inflight;
}
