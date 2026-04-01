import { useCallback, useEffect, useState } from "react";
import { UC_USERS } from "../rbac";
import { useAuth } from "../context/AuthContext";
import * as api from "../services/users";

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
            Crear
          </button>
        )}
      </div>
      {error && <div className="vc-banner vc-banner--error">{error}</div>}
      <div className="vc-table-wrap">
        <table className="vc-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nombre</th>
              <th>Email</th>
              <th>Rol ID</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((u) => (
              <tr key={u.id}>
                <td>{u.id}</td>
                <td>{u.name}</td>
                <td>{u.email}</td>
                <td>{u.role_id ?? "—"}</td>
                <td className="vc-table__actions">
                  {can(UC_USERS, "r") && (
                    <button type="button" className="vc-btn vc-btn--small" onClick={() => setModal({ mode: "view", row: u })}>
                      Ver
                    </button>
                  )}
                  {can(UC_USERS, "u") && (
                    <button type="button" className="vc-btn vc-btn--small" onClick={() => setModal({ mode: "edit", row: u })}>
                      Editar
                    </button>
                  )}
                  {can(UC_USERS, "d") && (
                    <button type="button" className="vc-btn vc-btn--small vc-btn--danger" onClick={() => onDelete(u.id)}>
                      Eliminar
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
  const [err, setErr] = useState("");

  async function submit(e) {
    e.preventDefault();
    setErr("");
    try {
      if (mode === "create") {
        await api.createUser(token, {
          name,
          email,
          password,
          role_id: roleId === "" ? null : Number(roleId),
        });
      } else if (mode === "edit") {
        const body = { name, email, role_id: roleId === "" ? null : Number(roleId) };
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
        <div className="vc-modal" role="dialog" onClick={(e) => e.stopPropagation()}>
          <h2>Usuario #{row.id}</h2>
          <pre className="vc-pre">{JSON.stringify(row, null, 2)}</pre>
          <button type="button" className="vc-btn" onClick={onClose}>
            Cerrar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="vc-modal-backdrop" role="presentation" onClick={onClose}>
      <div className="vc-modal" role="dialog" onClick={(e) => e.stopPropagation()}>
        <h2>{mode === "create" ? "Nuevo usuario" : `Editar usuario #${row.id}`}</h2>
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
            <span>{mode === "create" ? "Contraseña" : "Contraseña (dejar vacío para no cambiar)"}</span>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required={mode === "create"} />
          </label>
          <label className="vc-field">
            <span>Rol ID (opcional, p. ej. 1 Admin, 2 Master)</span>
            <input value={roleId} onChange={(e) => setRoleId(e.target.value)} placeholder="vacío = sin rol" />
          </label>
          <div className="vc-form__actions">
            <button type="button" className="vc-btn" onClick={onClose}>
              Cancelar
            </button>
            <button type="submit" className="vc-btn vc-btn--primary">
              Guardar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
