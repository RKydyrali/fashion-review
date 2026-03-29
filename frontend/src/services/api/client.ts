import { API_BASE_URL } from "@/config/env";
import { useAuthStore } from "@/state/auth-store";

import type { AuthSession, LocaleCode } from "./types";

type RequestOptions = RequestInit & {
  auth?: boolean;
  locale?: LocaleCode;
};

let refreshPromise: Promise<void> | null = null;
const LOCAL_MEDIA_HOSTS = new Set(["127.0.0.1", "localhost", "10.0.2.2"]);

function createConnectionError() {
  return new Error(`Cannot connect to AVISHU API at ${API_BASE_URL}. Start the backend server or update EXPO_PUBLIC_API_URL.`);
}

function formatErrorPayload(payload: string) {
  try {
    const parsed = JSON.parse(payload) as { detail?: unknown; message?: unknown };
    if (typeof parsed.detail === "string" && parsed.detail.trim()) {
      return parsed.detail;
    }
    if (Array.isArray(parsed.detail)) {
      const validationMessage = parsed.detail
        .map((item) => {
          if (!item || typeof item !== "object") {
            return null;
          }
          const entry = item as { msg?: unknown; loc?: unknown };
          const msg = typeof entry.msg === "string" ? entry.msg : null;
          const loc = Array.isArray(entry.loc) ? entry.loc.filter((part) => typeof part === "string" || typeof part === "number").join(".") : null;
          if (!msg) {
            return null;
          }
          return loc ? `${loc}: ${msg}` : msg;
        })
        .filter(Boolean)
        .join("\n");
      if (validationMessage) {
        return validationMessage;
      }
    }
    if (typeof parsed.message === "string" && parsed.message.trim()) {
      return parsed.message;
    }
  } catch {
    return payload;
  }
  return payload;
}

function resolveMediaUrl(value: string) {
  const assetBase = `${API_BASE_URL.replace(/\/+$/, "")}/`;

  if (!value.startsWith("/media/")) {
    if (!value.startsWith("media/")) {
      try {
        const parsed = new URL(value);
        if (!LOCAL_MEDIA_HOSTS.has(parsed.hostname) || !parsed.pathname.startsWith("/media/")) {
          return value;
        }
        return new URL(`${parsed.pathname}${parsed.search}`, assetBase).toString();
      } catch {
        return value;
      }
    }

    return new URL(`/${value}`, assetBase).toString();
  }

  return new URL(value, assetBase).toString();
}

function normalizeApiPayload<T>(value: T): T {
  if (typeof value === "string") {
    return resolveMediaUrl(value) as T;
  }
  if (Array.isArray(value)) {
    return value.map((item) => normalizeApiPayload(item)) as T;
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, entry]) => [key, normalizeApiPayload(entry)])
    ) as T;
  }
  return value;
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = await response.text();
    let message = payload || `Request failed with ${response.status}`;

    if (payload) {
      message = formatErrorPayload(payload) || message;
    }

    throw new Error(message);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return normalizeApiPayload((await response.json()) as T);
}

async function refreshSession() {
  const { refreshToken, setSession, clearSession } = useAuthStore.getState();
  if (!refreshToken) {
    await clearSession();
    throw new Error("Missing refresh token");
  }
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ refresh_token: refreshToken })
    });
  } catch {
    throw createConnectionError();
  }
  if (!response.ok) {
    await clearSession();
    throw new Error("Unable to refresh session");
  }
  const session = (await response.json()) as AuthSession;
  await setSession(session);
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { accessToken, locale } = useAuthStore.getState();
  const headers = new Headers(options.headers);
  headers.set("Accept-Language", options.locale ?? locale);
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (options.auth !== false && accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const request = async () =>
    fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers
    });

  let response: Response;
  try {
    response = await request();
  } catch {
    throw createConnectionError();
  }
  if (response.status === 401 && options.auth !== false && useAuthStore.getState().refreshToken) {
    refreshPromise ??= refreshSession().finally(() => {
      refreshPromise = null;
    });
    await refreshPromise;
    return apiFetch(path, options);
  }
  return parseResponse<T>(response);
}
