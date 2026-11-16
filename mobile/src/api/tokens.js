import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";

const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

// expo-secure-store has no web implementation. Web is dev-only here, so fall
// back to sessionStorage there (cleared when the tab closes).
const isWeb = Platform.OS === "web";

async function getItem(key) {
  if (isWeb) return globalThis.sessionStorage?.getItem(key) ?? null;
  return SecureStore.getItemAsync(key);
}

async function setItem(key, value) {
  if (isWeb) return globalThis.sessionStorage?.setItem(key, value);
  return SecureStore.setItemAsync(key, value);
}

async function removeItem(key) {
  if (isWeb) return globalThis.sessionStorage?.removeItem(key);
  return SecureStore.deleteItemAsync(key);
}

export const getAccessToken = () => getItem(ACCESS_KEY);
export const getRefreshToken = () => getItem(REFRESH_KEY);

export async function setTokens({ access, refresh }) {
  if (access) await setItem(ACCESS_KEY, access);
  if (refresh) await setItem(REFRESH_KEY, refresh);
}

export async function clearTokens() {
  await Promise.all([removeItem(ACCESS_KEY), removeItem(REFRESH_KEY)]);
}
