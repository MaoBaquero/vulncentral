import { useCallback, useEffect, useState } from "react";
import { UC_PROJECTS } from "../rbac";
import { useAuth } from "../context/AuthContext";
import * as api from "../services/projects";

export default function ProjectsPage() {
  const { token, user, can } = useAuth();
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const [modal, setModal] = useState(null);

  const load = useCallback(async () => {
    setError("");
    try {
      const data = await api.listProjects(token);
      setRows(data);
    } catch (e) {
      setError(e.message);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  async function onDelete(id) {
    if (!window.confirm("¿Eliminar este proyecto?")) return;
    try {
      await api.deleteProject(token, id);
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div>
      <div className="vc-page-head">
        <h1>Proyectos</h1>
        {can(UC_PROJECTS, "c") && (
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
              <th>Usuario ID</th>
              <th>Nombre</th>
              <th>Descripción</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.id}>
                <td>{p.id}</td>
                <td>{p.user_id}</td>
                <td>{p.name}</td>
                <td className="vc-ellipsis">{p.description || "—"}</td>
                <td className="vc-table__actions">
                  {can(UC_PROJECTS, "r") && (
                    <button type="button" className="vc-btn vc-btn--small" onClick={() => setModal({ mode: "view", row: p })}>
                      Ver
                    </button>
                  )}
                  {can(UC_PROJECTS, "u") && (
                    <button type="button" className="vc-btn vc-btn--small" onClick={() => setModal({ mode: "edit", row: p })}>
                      Editar
                    </button>
                  )}
                  {can(UC_PROJECTS, "d") && (
                    <button type="button" className="vc-btn vc-btn--small vc-btn--danger" onClick={() => onDelete(p.id)}>
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
        <ProjectModal
          token={token}
          defaultUserId={user?.id}
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

function ProjectModal({ token, defaultUserId, modal, onClose, onSaved }) {
  const { mode, row } = modal;
  const [userId, setUserId] = useState(String(row?.user_id ?? defaultUserId ?? ""));
  const [name, setName] = useState(row?.name || "");
  const [description, setDescription] = useState(row?.description || "");
  const [err, setErr] = useState("");

  async function submit(e) {
    e.preventDefault();
    setErr("");
    try {
      if (mode === "create") {
        await api.createProject(token, {
          user_id: Number(userId),
          name,
          description: description || null,
        });
      } else if (mode === "edit") {
        await api.updateProject(token, row.id, {
          user_id: Number(userId),
          name,
          description: description || null,
        });
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
          <h2>Proyecto #{row.id}</h2>
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
        <h2>{mode === "create" ? "Nuevo proyecto" : `Editar proyecto #${row.id}`}</h2>
        {err && <div className="vc-banner vc-banner--error">{err}</div>}
        <form onSubmit={submit} className="vc-form">
          <label className="vc-field">
            <span>Usuario propietario (ID)</span>
            <input value={userId} onChange={(e) => setUserId(e.target.value)} required />
          </label>
          <label className="vc-field">
            <span>Nombre</span>
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </label>
          <label className="vc-field">
            <span>Descripción</span>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
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
