import { request } from "./apiClient";

export function listVulnerabilities(token) {
  return request("/api/v1/vulnerabilities", { token });
}

export function getVulnerability(token, id) {
  return request(`/api/v1/vulnerabilities/${id}`, { token });
}

export function createVulnerability(token, body) {
  return request("/api/v1/vulnerabilities", { method: "POST", body, token });
}

export function updateVulnerability(token, id, body) {
  return request(`/api/v1/vulnerabilities/${id}`, { method: "PATCH", body, token });
}

export function deleteVulnerability(token, id) {
  return request(`/api/v1/vulnerabilities/${id}`, { method: "DELETE", token });
}
