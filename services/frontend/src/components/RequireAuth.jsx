import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function RequireAuth({ children }) {
  const { token, loading, user } = useAuth();
  const loc = useLocation();

  if (loading) {
    return (
      <div className="vc-loading">
        <p>Cargando sesión…</p>
      </div>
    );
  }
  if (!token || !user) {
    return <Navigate to="/login" state={{ from: loc }} replace />;
  }
  return children;
}
