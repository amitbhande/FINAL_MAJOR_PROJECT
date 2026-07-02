/**
 * API base for FastAPI backend.
 * - Recommended local dev: `NEXT_PUBLIC_API_BASE=/api/backend` (see next.config.js rewrites → :8000).
 * - Or direct: `NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000` (requires working CORS on backend).
 */
function joinUrl(base: string, path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  const b = base.replace(/\/$/, "");
  return `${b}${p}`;
}

export function getApiBase(): string {
  const raw = (
    process.env.NEXT_PUBLIC_API_BASE || "/api/backend"
  ).trim();

  if (raw.startsWith("http://") || raw.startsWith("https://")) {
    return raw.replace(/\/$/, "");
  }

  const pathBase = raw.startsWith("/") ? raw : `/${raw}`;

  if (typeof window !== "undefined") {
    return pathBase.replace(/\/$/, "");
  }

  // Server Components: use absolute URL to this Next app so rewrites run.
  const origin = (
    process.env.NEXT_PUBLIC_APP_ORIGIN || "http://127.0.0.1:3000"
  ).replace(/\/$/, "");
  return `${origin}${pathBase.replace(/\/$/, "")}`;
}

export const API_BASE = getApiBase();

export async function apiGet<T>(path: string): Promise<T> {
  const r = await fetch(joinUrl(getApiBase(), path), { cache: "no-store" });
  if (!r.ok) throw new Error(await r.text());
  return (await r.json()) as T;
}

export async function apiPostForm<T>(
  path: string,
  form: FormData
): Promise<T> {
  const r = await fetch(joinUrl(getApiBase(), path), {
    method: "POST",
    body: form,
  });
  if (!r.ok) throw new Error(await r.text());
  return (await r.json()) as T;
}

export async function apiPostJson<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(joinUrl(getApiBase(), path), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await r.text());
  return (await r.json()) as T;
}
