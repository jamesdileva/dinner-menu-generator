// Shared frontend API client (created during the §4.1 modularization).
// `apiFetch` throws on non-2xx so callers can centralise error handling.

export const MEALS_PER_PAGE = 20;

export async function apiFetch(path, opts = {}) {
  const res = await fetch(path, opts);

  if (!res.ok) {
    let message;
    try {
      message = (await res.json()).error;
    } catch {
      message = `${res.status} ${res.statusText}`;
    }
    throw new Error(message || "Request failed");
  }

  return res.json();
}
