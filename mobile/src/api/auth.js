import AsyncStorage from "@react-native-async-storage/async-storage";
import axios from "axios";
import { BASE_URL } from "./client";

export async function login(username, password) {
  const { data } = await axios.post(`${BASE_URL}/auth/login/`, { username, password });
  await AsyncStorage.setItem("access_token", data.access);
  await AsyncStorage.setItem("refresh_token", data.refresh);
  return data;
}

export async function logout() {
  const refresh = await AsyncStorage.getItem("refresh_token");
  try {
    if (refresh) {
      const token = await AsyncStorage.getItem("access_token");
      await axios.post(
        `${BASE_URL}/auth/logout/`,
        { refresh },
        { headers: { Authorization: `Bearer ${token}` } }
      );
    }
  } catch {
    // best-effort
  } finally {
    await AsyncStorage.multiRemove(["access_token", "refresh_token"]);
  }
}

export async function forgotPassword(email) {
  const { data } = await axios.post(`${BASE_URL}/auth/forgot-password/`, { email });
  return data;
}

export async function getStoredTokens() {
  const access = await AsyncStorage.getItem("access_token");
  const refresh = await AsyncStorage.getItem("refresh_token");
  return { access, refresh };
}
