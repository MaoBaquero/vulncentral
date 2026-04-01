import { request } from "./apiClient";

export function listUsers(token) {
  return request("/api/v1/users", { token });
}

export function getUser(token, id) {
  return request(`/api/v1/users/${id}`, { token });
}

export function createUser(token, body) {
  return request("/api/v1/users", { method: "POST", body, token });
}

export function updateUser(token, id, body) {
  return request(`/api/v1/users/${id}`, { method: "PATCH", body, token });
}

export function deleteUser(token, id) {
  return request(`/api/v1/users/${id}`, { method: "DELETE", token });
}
