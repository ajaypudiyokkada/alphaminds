import AsyncStorage from "@react-native-async-storage/async-storage";

// One-time cleanup: tokens used to live in plain AsyncStorage. They now live in
// expo-secure-store (see tokens.js). Delete any leftovers; nothing is migrated,
// so a user who upgrades simply logs in again.
export async function clearLegacyTokens() {
  try {
    await AsyncStorage.multiRemove(["access_token", "refresh_token"]);
  } catch {
    // nothing to clean up
  }
}
