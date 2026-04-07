import { request } from "./apiClient";

export function listRoles(token) {
  return request("/api/v1/roles", { token });
}
