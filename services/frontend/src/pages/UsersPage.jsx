import { useCallback, useEffect, useState } from "react";
import { UC_USERS } from "../rbac";
import { useAuth } from "../context/AuthContext";
import * as rolesApi from "../services/roles";
import * as api from "../services/users";

function formatDateTime(value) {
  if (value == null || value === "") return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return String(value);
  }
}

function IconEye() {
  return (
    <svg className="vc-btn__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function IconPencil() {
  return (
    <svg className="vc-btn__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
  );
}

function IconTrash() {
  return (
    <svg className="vc-btn__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    </svg>
  );
}

function IconPlus() {
  return (
    <svg className="vc-btn__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  );
}

function IconX() {
  return (
    <svg className="vc-btn__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

function IconCheck() {
  return (
    <svg className="vc-btn__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

export default function UsersPage() {
  const { token, can } = useAuth();
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const [modal, setModal] = useState(null);

  const load = useCallback(async () => {
    setError("");
    try {
      const data = await api.listUsers(token);
      setRows(data);
    } catch (e) {
      setError(e.message);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  async function onDelete(id) {
    if (!window.confirm("¿Eliminar este usuario?")) return;
    try {
      await api.deleteUser(token, id);
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div>
      <div className="vc-page-head">
        <h1>Usuarios</h1>
        {can(UC_USERS, "c") && (
          <button type="button" className="vc-btn vc-btn--primary" onClick={() => setModal({ mode: "create" })}>
            <span className="vc-btn__inner">
              <IconPlus />
              Crear
            </span>
          </button>
        )}
      </div>
      {error && <div className="vc-banner vc-banner--error">{error}</div>}
      <div className="vc-table-wrap">
        <table className="vc-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Email</th>
              <th>Rol</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((u) => (
              <tr key={u.id}>
                <td>{u.name}</td>
                <td>{u.email}</td>
                <td>{u.role_name ?? "—"}</td>
                <td className="vc-table__actions">
                  {can(UC_USERS, "r") && (
                    <button type="button" className="vc-btn vc-btn--small" onClick={() => setModal({ mode: "view", row: u })}>
                      <span className="vc-btn__inner">
                        <IconEye />
                        Ver
                      </span>
                    </button>
                  )}
                  {can(UC_USERS, "u") && (
                    <button type="button" className="vc-btn vc-btn--small" onClick={() => setModal({ mode: "edit", row: u })}>
                      <span className="vc-btn__inner">
                        <IconPencil />
                        Editar
                      </span>
                    </button>
                  )}
                  {can(UC_USERS, "d") && (
                    <button type="button" className="vc-btn vc-btn--small vc-btn--danger" onClick={() => onDelete(u.id)}>
                      <span className="vc-btn__inner">
                        <IconTrash />
                        Eliminar
                      </span>
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {modal && (
        <UserModal
          token={token}
          modal={modal}
          onClose={() => setModal(null)}
          onSaved={() => {
            setModal(null);
            load();
          }}
        />
      )}
    </div>
  );
}

function UserModal({ token, modal, onClose, onSaved }) {
  const { mode, row } = modal;
  const [name, setName] = useState(row?.name || "");
  const [email, setEmail] = useState(row?.email || "");
  const [password, setPassword] = useState("");
  const [roleId, setRoleId] = useState(row?.role_id != null ? String(row.role_id) : "");
  const [roles, setRoles] = useState([]);
  const [rolesLoading, setRolesLoading] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    setName(row?.name || "");
    setEmail(row?.email || "");
    setPassword("");
    setRoleId(row?.role_id != null ? String(row.role_id) : "");
    setErr("");
  }, [mode, row]);

  useEffect(() => {
    if (mode === "view") return;
    let cancelled = false;
    setRolesLoading(true);
    (async () => {
      try {
        const data = await rolesApi.listRoles(token);
        if (!cancelled) {
          setRoles(data);
          setErr("");
        }
      } catch (e) {
        if (!cancelled) setErr(e.message);
      } finally {
        if (!cancelled) setRolesLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, mode]);

  async function submit(e) {
    e.preventDefault();
    setErr("");
    const rid = Number(roleId);
    if (!Number.isFinite(rid)) {
      setErr("Seleccione un rol.");
      return;
    }
    try {
      if (mode === "create") {
        await api.createUser(token, {
          name,
          email,
          password,
          role_id: rid,
        });
      } else if (mode === "edit") {
        const body = { name, email, role_id: rid };
        if (password.trim()) body.password = password;
        await api.updateUser(token, row.id, body);
      }
      onSaved();
    } catch (e) {
      setErr(e.message);
    }
  }

  if (mode === "view") {
    return (
      <div className="vc-modal-backdrop" role="presentation" onClick={onClose}>
        <div className="vc-modal" role="dialog" onClick={(e) => e.stopPropagation()} aria-labelledby="user-view-title">
          <h2 id="user-view-title">Usuario</h2>
          <div className="vc-form">
            <label className="vc-field">
              <span>Nombre</span>
              <input value={row.name} readOnly className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>Email</span>
              <input value={row.email} readOnly className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>Rol</span>
              <input value={row.role_name ?? "—"} readOnly className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>Creado</span>
              <input value={formatDateTime(row.created_at)} readOnly className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>Actualizado</span>
              <input value={formatDateTime(row.updated_at)} readOnly className="vc-input-readonly" />
            </label>
          </div>
          <div className="vc-form__actions">
            <button type="button" className="vc-btn" onClick={onClose}>
              <span className="vc-btn__inner">
                <IconX />
                Cerrar
              </span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="vc-modal-backdrop" role="presentation" onClick={onClose}>
      <div className="vc-modal" role="dialog" onClick={(e) => e.stopPropagation()}>
        <h2>{mode === "create" ? "Nuevo usuario" : "Editar usuario"}</h2>
        {err && <div className="vc-banner vc-banner--error">{err}</div>}
        <form onSubmit={submit} className="vc-form">
          <label className="vc-field">
            <span>Nombre</span>
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </label>
          <label className="vc-field">
            <span>Email</span>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>
          <label className="vc-field">
            <span>
              {mode === "create" ? "Contraseña" : "Contraseña (dejar vacío para no cambiar)"}
            </span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required={mode === "create"}
              autoComplete="new-password"
            />
          </label>
          <label className="vc-field">
            <span>Rol</span>
            <select
              value={roleId}
              onChange={(e) => setRoleId(e.target.value)}
              required
              disabled={rolesLoading}
            >
              <option value="" disabled>
                {rolesLoading ? "Cargando roles…" : "Seleccione un rol"}
              </option>
              {roles.map((r) => (
                <option key={r.id} value={String(r.id)}>
                  {r.name}
                </option>
              ))}
            </select>
          </label>
          <div className="vc-form__actions">
            <button type="button" className="vc-btn" onClick={onClose}>
              <span className="vc-btn__inner">
                <IconX />
                Cancelar
              </span>
            </button>
            <button type="submit" className="vc-btn vc-btn--primary" disabled={rolesLoading || roles.length === 0}>
              <span className="vc-btn__inner">
                <IconCheck />
                Guardar
              </span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
