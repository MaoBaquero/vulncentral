/**
 * Contexto de flujo Proyectos → Escaneos → Vulnerabilidades sin IDs en la URL.
 * Combina React Router location.state con sessionStorage para sobrevivir a F5.
 */

const KEY = "vc_flow_context";

function read() {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return {};
    const o = JSON.parse(raw);
    return typeof o === "object" && o !== null ? o : {};
  } catch {
    return {};
  }
}

function write(data) {
  if (!data || Object.keys(data).length === 0) {
    sessionStorage.removeItem(KEY);
    return;
  }
  sessionStorage.setItem(KEY, JSON.stringify(data));
}

export function clearFlowContext() {
  sessionStorage.removeItem(KEY);
}

/**
 * @param {unknown} routeState - location.state
 * @returns {{ projectId: number | undefined }}
 */
export function syncAndGetScansContext(routeState) {
  const prev = read();
  const r = routeState && typeof routeState === "object" ? routeState : {};
  const next = { ...prev };
  if (r.projectId != null && Number.isFinite(Number(r.projectId))) {
    next.projectId = Number(r.projectId);
    delete next.scanId;
  }
  write(next);
  const projectId = next.projectId;
  return {
    projectId: Number.isFinite(projectId) ? projectId : undefined,
  };
}

/**
 * @param {unknown} routeState - location.state
 * @returns {{ scanId: number | undefined, projectId: number | undefined }}
 */
export function syncAndGetVulnsContext(routeState) {
  const prev = read();
  const r = routeState && typeof routeState === "object" ? routeState : {};
  const next = { ...prev };
  if (r.projectId != null && Number.isFinite(Number(r.projectId))) {
    next.projectId = Number(r.projectId);
  }
  if (r.scanId != null && Number.isFinite(Number(r.scanId))) {
    next.scanId = Number(r.scanId);
  }
  write(next);
  const scanId = next.scanId;
  const projectId = next.projectId;
  return {
    scanId: Number.isFinite(scanId) ? scanId : undefined,
    projectId: Number.isFinite(projectId) ? projectId : undefined,
  };
}
