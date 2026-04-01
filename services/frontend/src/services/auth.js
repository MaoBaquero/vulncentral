import { request } from "./apiClient";

export function login(username, password) {
  const formBody = new URLSearchParams({ username, password }).toString();
  return request("/auth/login", { method: "POST", formBody });
}

export function fetchMe(token) {
  return request("/auth/me", { token });
}
