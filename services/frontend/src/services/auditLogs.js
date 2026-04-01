import { request } from "./apiClient";

export function listAuditLogs(token, skip = 0, limit = 50) {
  const q = new URLSearchParams({ skip: String(skip), limit: String(limit) });
  return request(`/api/v1/audit-logs?${q}`, { token });
}
