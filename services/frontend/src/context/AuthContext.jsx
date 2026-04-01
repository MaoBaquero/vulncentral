import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import * as authApi from "../services/auth";

const TOKEN_KEY = "vc_access_token";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setTokenState] = useState(() => sessionStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(!!sessionStorage.getItem(TOKEN_KEY));

  useEffect(() => {
    if (!token) {
      setUser(null);
      setLoading(false);
      return undefined;
    }
    let cancelled = false;
    setLoading(true);
    authApi
      .fetchMe(token)
      .then((me) => {
        if (!cancelled) setUser(me);
      })
      .catch(() => {
        if (!cancelled) {
          sessionStorage.removeItem(TOKEN_KEY);
          setTokenState(null);
          setUser(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  const setToken = useCallback((t) => {
    if (t) sessionStorage.setItem(TOKEN_KEY, t);
    else sessionStorage.removeItem(TOKEN_KEY);
    setTokenState(t);
  }, []);

  const login = useCallback(async (email, password) => {
    const r = await authApi.login(email, password);
    setToken(r.access_token);
  }, [setToken]);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, [setToken]);

  const can = useCallback(
    (useCase, action) => {
      if (!user?.permissions) return false;
      const row = user.permissions.find((p) => p.use_case === useCase);
      return row ? !!row[action] : false;
    },
    [user],
  );

  const value = useMemo(
    () => ({
      token,
      user,
      loading,
      login,
      logout,
      setToken,
      can,
    }),
    [token, user, loading, login, logout, setToken, can],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth fuera de AuthProvider");
  return ctx;
}
