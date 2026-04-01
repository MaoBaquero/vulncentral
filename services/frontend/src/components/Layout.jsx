import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  UC_LOGS,
  UC_PROJECTS,
  UC_SCANS,
  UC_USERS,
  UC_VULNS,
} from "../rbac";
import { useAuth } from "../context/AuthContext";

const linkClass = ({ isActive }) =>
  `vc-nav__link${isActive ? " vc-nav__link--active" : ""}`;

export default function Layout() {
  const { user, logout, can } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="vc-layout">
      <aside className="vc-sidebar">
        <div className="vc-sidebar__brand">VulnCentral</div>
        <nav className="vc-nav">
          <NavLink to="/" end className={linkClass}>
            Inicio
          </NavLink>
          {can(UC_USERS, "r") && (
            <NavLink to="/users" className={linkClass}>
              Usuarios
            </NavLink>
          )}
          {can(UC_PROJECTS, "r") && (
            <NavLink to="/projects" className={linkClass}>
              Proyectos
            </NavLink>
          )}
          {can(UC_SCANS, "r") && (
            <NavLink to="/scans" className={linkClass}>
              Escaneos
            </NavLink>
          )}
          {can(UC_VULNS, "r") && (
            <NavLink to="/vulnerabilities" className={linkClass}>
              Vulnerabilidades
            </NavLink>
          )}
          {can(UC_LOGS, "r") && (
            <NavLink to="/logs" className={linkClass}>
              Logs
            </NavLink>
          )}
          {can(UC_PROJECTS, "c") && can(UC_SCANS, "c") && (
            <NavLink to="/flow/nuevo" className={linkClass}>
              Nuevo flujo
            </NavLink>
          )}
        </nav>
      </aside>
      <div className="vc-main">
        <header className="vc-header">
          <span className="vc-header__user">
            {user?.name} ({user?.email})
          </span>
          <button
            type="button"
            className="vc-btn vc-btn--ghost"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            Cerrar sesión
          </button>
        </header>
        <div className="vc-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
