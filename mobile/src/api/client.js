import axios from "axios";
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "./tokens";

export const BASE_URL = process.env.EXPO_PUBLIC_API_URL;

const client = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

// ── Auth-failure event (client.js -> AuthContext) ──────────────────────────
let authFailureHandler = null;
export function setAuthFailureHandler(fn) {
  authFailureHandler = fn;
}

// Endpoints that must never trigger a token refresh (prevents refresh loops).
const AUTH_PATHS = ["/auth/login/", "/auth/refresh/", "/auth/logout/", "/auth/forgot-password/"];
const isAuthEndpoint = (url = "") => AUTH_PATHS.some((p) => url.includes(p));

// Attach access token to every non-auth request
client.interceptors.request.use(async (config) => {
  if (isAuthEndpoint(config.url)) return config;
  const token = await getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Single-flight refresh ──────────────────────────────────────────────────
// All requests that hit 401 at the same time await the same promise, so only
// one /auth/refresh/ call is made; the rest retry once it resolves.
let refreshPromise = null;

function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const refresh = await getRefreshToken();
      if (!refresh) {
        const err = new Error("No refresh token");
        err.isAuthFailure = true;
        throw err;
      }
      try {
        const { data } = await client.post("/auth/refresh/", { refresh });
        // Backend rotates the refresh token: store the new one too.
        await setTokens({ access: data.access, refresh: data.refresh });
        return data.access;
      } catch (e) {
        // Only a rejected token is an auth failure; a network error is not.
        if (e.response) e.isAuthFailure = true;
        throw e;
      }
    })().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status !== 401 || !original || original._retry || isAuthEndpoint(original.url)) {
      return Promise.reject(error);
    }
    original._retry = true;
    try {
      const access = await refreshAccessToken();
      original.headers.Authorization = `Bearer ${access}`;
      return client(original);
    } catch (refreshError) {
      if (refreshError.isAuthFailure) {
        await clearTokens();
        authFailureHandler?.();
      }
      return Promise.reject(error);
    }
  }
);

export default client;
