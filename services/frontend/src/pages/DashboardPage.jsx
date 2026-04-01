import { Link } from "react-router-dom";
import {
  UC_LOGS,
  UC_PROJECTS,
  UC_SCANS,
  UC_USERS,
  UC_VULNS,
} from "../rbac";
import { useAuth } from "../context/AuthContext";

export default function DashboardPage() {
  const { user, can } = useAuth();

  return (
    <div>
      <h1>Panel principal</h1>
      <p className="vc-muted">
        Rol: <strong>{user?.role_name || "—"}</strong>. Use el menú lateral o los accesos
        siguientes.
      </p>
      <ul className="vc-dash-links">
        {can(UC_USERS, "r") && (
          <li>
            <Link to="/users">Usuarios</Link>
          </li>
        )}
        {can(UC_PROJECTS, "r") && (
          <li>
            <Link to="/projects">Proyectos</Link>
          </li>
        )}
        {can(UC_SCANS, "r") && (
          <li>
            <Link to="/scans">Escaneos</Link>
          </li>
        )}
        {can(UC_VULNS, "r") && (
          <li>
            <Link to="/vulnerabilities">Vulnerabilidades</Link>
          </li>
        )}
        {can(UC_LOGS, "r") && (
          <li>
            <Link to="/logs">Logs de auditoría</Link>
          </li>
        )}
        {can(UC_PROJECTS, "c") && can(UC_SCANS, "c") && (
          <li>
            <Link to="/flow/nuevo">Nuevo flujo (proyecto → escaneo → vulnerabilidades)</Link>
          </li>
        )}
      </ul>
    </div>
  );
}
