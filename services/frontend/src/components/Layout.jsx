import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import logoHorizontal from "../assets/LogoVC-horizontal.png";
import { UC_LOGS, UC_PROJECTS, UC_SCANS, UC_USERS } from "../rbac";
import { useAuth } from "../context/AuthContext";

const linkClass = ({ isActive }) =>
  `vc-nav__link${isActive ? " vc-nav__link--active" : ""}`;

function IconHome() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </svg>
  );
}

function IconUsers() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}

function IconFolder() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
    </svg>
  );
}

function IconLogs() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  );
}

function IconFlow() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="16" />
      <line x1="8" y1="12" x2="16" y2="12" />
    </svg>
  );
}

export default function Layout() {
  const { user, logout, can } = useAuth();
  const navigate = useNavigate();
  const [aboutOpen, setAboutOpen] = useState(false);

  return (
    <div className="vc-layout">
      <aside className="vc-sidebar">
        <div className="vc-sidebar__brand">
          <img src={logoHorizontal} alt="VulnCentral" className="vc-sidebar__brand-img" />
        </div>
        <nav className="vc-nav">
          <NavLink to="/" end className={linkClass}>
            <span className="vc-nav__link-icon">
              <IconHome />
            </span>
            Inicio
          </NavLink>
          {can(UC_USERS, "r") && (
            <NavLink to="/users" className={linkClass}>
              <span className="vc-nav__link-icon">
                <IconUsers />
              </span>
              Usuarios
            </NavLink>
          )}
          {can(UC_PROJECTS, "r") && (
            <NavLink to="/projects" className={linkClass}>
              <span className="vc-nav__link-icon">
                <IconFolder />
              </span>
              Proyectos
            </NavLink>
          )}
          {can(UC_LOGS, "r") && (
            <NavLink to="/logs" className={linkClass}>
              <span className="vc-nav__link-icon">
                <IconLogs />
              </span>
              Logs
            </NavLink>
          )}

{/*  

          {can(UC_PROJECTS, "c") && can(UC_SCANS, "c") && (
            <NavLink to="/flow/nuevo" className={linkClass}>
              <span className="vc-nav__link-icon">
                <IconFlow />
              </span>
              Nuevo flujo
            </NavLink>
          )}

*/}

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

      <div className="vc-app-footer" role="contentinfo">
        <span>VulnCentral v 0.0.0 Alpha</span>
        <span aria-hidden="true"> | </span>
        <span>Seguridad Entornos Cloud DevOps</span>
        <span aria-hidden="true"> | </span>
        <button
          type="button"
          className="vc-app-footer__about"
          aria-haspopup="dialog"
          aria-expanded={aboutOpen}
          onClick={() => setAboutOpen(true)}
        >
          Acerca de
        </button>
      </div>

      {aboutOpen && (
        <div
          className="vc-modal-backdrop"
          role="presentation"
          onClick={() => setAboutOpen(false)}
        >
          <div
            className="vc-modal vc-modal--wide"
            role="dialog"
            aria-labelledby="about-title"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 id="about-title">Acerca de</h2>
            <p>Fundación Universitaria UNIMINUTO</p>
            <strong><p>Especialización en Ciberseguridad</p></strong>
            <p>
              <strong>Materia:</strong>
            </p>
            <p className="vc-about-modal__indent">Seguridad Entornos Cloud DevOps</p>
            <p>
              <strong>Autores:</strong>
            </p>
            <ul>
              <li>Estefania Naranjo Novoa</li>
              <li>Ronald David Argel Ochoa</li>
              <li>Oscar Javier Buitrago Guiot</li>
              <li>Mauricio Baquero Soto</li>
            </ul>
            <div className="vc-form__actions">
              <button type="button" className="vc-btn" onClick={() => setAboutOpen(false)}>
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
