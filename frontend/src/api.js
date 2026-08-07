// Shared frontend API client (created during the §4.1 modularization).
// `apiFetch` throws on non-2xx so callers can centralise error handling.

export const MEALS_PER_PAGE = 20;

// audit §8.3 / §5.22 — every request carries a custom header so the backend can verify it
// is same-origin (CSRF defense for this no-cookie JSON API).
export async function apiFetch(path, opts = {}) {
  const headers = new Headers(opts.headers || {});
  headers.set("X-Requested-With", "XMLHttpRequest");

  const res = await fetch(path, { ...opts, headers });

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
