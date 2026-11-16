import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { getStoredTokens, login as apiLogin, logout as apiLogout } from "../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);   // { athlete_id, full_name }
  const [loading, setLoading] = useState(true);

  // Restore session on mount
  useEffect(() => {
    getStoredTokens().then(({ access }) => {
      if (access) {
        // We have a token — set a placeholder so navigator sends to app
        setUser({ restored: true });
      }
      setLoading(false);
    });
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
