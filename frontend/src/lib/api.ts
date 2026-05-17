"use client";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiRequest(
  endpoint: string,
  method: string = "GET",
  body?: any,
  token?: string | null
) {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Something went wrong");
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const api = {
  get: (endpoint: string, token?: string | null) => apiRequest(`/api${endpoint}`, "GET", undefined, token),
  post: (endpoint: string, body: any, token?: string | null) => apiRequest(`/api${endpoint}`, "POST", body, token),
  put: (endpoint: string, body: any, token?: string | null) => apiRequest(`/api${endpoint}`, "PUT", body, token),
  delete: (endpoint: string, token?: string | null) => apiRequest(`/api${endpoint}`, "DELETE", undefined, token),
};
