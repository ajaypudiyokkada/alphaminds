import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { getStoredTokens, login as apiLogin, logout as apiLogout } from "../api/auth";
import { getMe } from "../api/athlete";
import { setAuthFailureHandler } from "../api/client";
import { clearLegacyTokens } from "../api/legacyStorage";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);   // { athlete_id, full_name }
  const [loading, setLoading] = useState(true);

  // client.js tells us when a refresh fails: tokens are already cleared, so
  // dropping the user sends the navigator back to Login.
  useEffect(() => {
    setAuthFailureHandler(() => setUser(null));
    return () => setAuthFailureHandler(null);
  }, []);

  // Restore session on mount: if we hold a token, load the athlete from the API.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      await clearLegacyTokens();
      const { access, refresh } = await getStoredTokens();
      if (access || refresh) {
        try {
          // client.js refreshes transparently on 401 and fires the auth-failure
          // handler (-> user null -> Login) if that refresh is rejected.
          const me = await getMe();
          if (!cancelled) setUser({ athlete_id: me.id, full_name: me.full_name });
        } catch (e) {
          // 401 after refresh: the handler already reset the user. Anything else
          // (e.g. offline) keeps the tokens; screens show their own retry state.
          if (!cancelled && e.response?.status !== 401) setUser({ restored: true });
        }
      }
      if (!cancelled) setLoading(false);
    })();
    return () => { cancelled = true; };
  }, []);

  const login = useCallback(async (username, password) => {
    const data = await apiLogin(username, password);
    setUser({ athlete_id: data.athlete_id, full_name: data.full_name });
    return data;
  }, []);

  const logout = useCallback(async () => {
    await apiLogout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
