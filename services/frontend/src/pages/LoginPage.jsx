import { useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { token, loading, login } = useAuth();
  const loc = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  if (!loading && token) {
    const to = loc.state?.from?.pathname || "/";
    return <Navigate to={to} replace />;
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setPending(true);
    try {
      await login(email.trim(), password);
    } catch (err) {
      setError(err.message || "No se pudo iniciar sesión");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="vc-login">
      <form className="vc-login__card" onSubmit={onSubmit}>
        <h1>VulnCentral</h1>
        <p className="vc-muted">Inicie sesión con su email y contraseña</p>
        {error && <div className="vc-banner vc-banner--error">{error}</div>}
        <label className="vc-field">
          <span>Email</span>
          <input
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label className="vc-field">
          <span>Contraseña</span>
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        <button type="submit" className="vc-btn vc-btn--primary" disabled={pending}>
          {pending ? "Entrando…" : "Entrar"}
        </button>
      </form>
    </div>
  );
}
