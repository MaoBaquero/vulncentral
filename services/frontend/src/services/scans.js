import { request } from "./apiClient";

export function listScans(token) {
  return request("/api/v1/scans", { token });
}

export function getScan(token, id) {
  return request(`/api/v1/scans/${id}`, { token });
}

export function createScan(token, body) {
  return request("/api/v1/scans", { method: "POST", body, token });
}

export function updateScan(token, id, body) {
  return request(`/api/v1/scans/${id}`, { method: "PATCH", body, token });
}

export function deleteScan(token, id) {
  return request(`/api/v1/scans/${id}`, { method: "DELETE", token });
}

/** @param {string} jsonString - cuerpo JSON Trivy */
export function uploadTrivyReport(token, scanId, jsonString) {
  const body = JSON.parse(jsonString);
  return request(`/api/v1/scans/${scanId}/trivy-report`, {
    method: "POST",
    body,
    token,
  });
}
