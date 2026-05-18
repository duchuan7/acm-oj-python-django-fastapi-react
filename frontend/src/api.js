const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export function getToken() {
  try {
    return localStorage.getItem("acmoj_token");
  } catch {
    return null;
  }
}

export function setToken(token) {
  try {
    if (token) {
      localStorage.setItem("acmoj_token", token);
    } else {
      localStorage.removeItem("acmoj_token");
    }
  } catch {
    // Ignore storage errors in restricted in-app browsers.
  }
}

export async function request(path, options = {}) {
  const headers = {
    "Content-Type": "application/json; charset=utf-8",
    Accept: "application/json",
    ...(options.headers || {}),
  };
  const token = getToken();
  if (token) {
    headers.Authorization = `Token ${token}`;
  }
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json().catch(() => ({})) : {};
  if (!response.ok) {
    const message = data.detail || data.non_field_errors?.join("; ") || JSON.stringify(data) || `HTTP ${response.status}`;
    throw new Error(message);
  }
  if (!contentType.includes("application/json")) {
    throw new Error("API did not return JSON. Please check the frontend proxy configuration.");
  }
  return data;
}
