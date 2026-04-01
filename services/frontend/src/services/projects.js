import { request } from "./apiClient";

export function listProjects(token) {
  return request("/api/v1/projects", { token });
}

export function getProject(token, id) {
  return request(`/api/v1/projects/${id}`, { token });
}

export function createProject(token, body) {
  return request("/api/v1/projects", { method: "POST", body, token });
}

export function updateProject(token, id, body) {
  return request(`/api/v1/projects/${id}`, { method: "PATCH", body, token });
}

export function deleteProject(token, id) {
  return request(`/api/v1/projects/${id}`, { method: "DELETE", token });
}
