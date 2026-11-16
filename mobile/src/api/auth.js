import client from "./client";
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "./tokens";

export async function login(username, password) {
  const { data } = await client.post("/auth/login/", { username, password });
  await setTokens({ access: data.access, refresh: data.refresh });
  return data;
}

export async function logout() {
  try {
    const refresh = await getRefreshToken();
    if (refresh) {
      await client.post("/auth/logout/", { refresh });
    }
  } catch {
    // best-effort
  } finally {
    await clearTokens();
  }
}

export async function forgotPassword(email) {
  const { data } = await client.post("/auth/forgot-password/", { email });
  return data;
}

export async function getStoredTokens() {
  const access = await getAccessToken();
  const refresh = await getRefreshToken();
  return { access, refresh };
}
