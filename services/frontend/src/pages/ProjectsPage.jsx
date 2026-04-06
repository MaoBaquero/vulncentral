import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { UC_PROJECTS, UC_SCANS } from "../rbac";
import { useAuth } from "../context/AuthContext";
import * as api from "../services/projects";

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

function IconScan() {
  return (
    <svg className="vc-btn__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
      <circle cx="12" cy="13" r="4" />
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

export default function ProjectsPage() {
  const navigate = useNavigate();
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
              <th>Propietario</th>
              <th>Nombre</th>
              <th>Descripción</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.id}>
                <td>{p.owner_name ?? "—"}</td>
                <td>{p.name}</td>
                <td className="vc-ellipsis">{p.description || "—"}</td>
                <td className="vc-table__actions">
                  {can(UC_PROJECTS, "r") && (
                    <button type="button" className="vc-btn vc-btn--small" onClick={() => setModal({ mode: "view", row: p })}>
                      <span className="vc-btn__inner">
                        <IconEye />
                        Ver
                      </span>
                    </button>
                  )}
                  {can(UC_PROJECTS, "u") && (
                    <button type="button" className="vc-btn vc-btn--small" onClick={() => setModal({ mode: "edit", row: p })}>
                      <span className="vc-btn__inner">
                        <IconPencil />
                        Editar
                      </span>
                    </button>
                  )}
                  {can(UC_PROJECTS, "d") && (
                    <button type="button" className="vc-btn vc-btn--small vc-btn--danger" onClick={() => onDelete(p.id)}>
                      <span className="vc-btn__inner">
                        <IconTrash />
                        Eliminar
                      </span>
                    </button>
                  )}
                  {can(UC_SCANS, "r") && (
                    <button
                      type="button"
                      className="vc-btn vc-btn--small"
                      onClick={() => navigate("/scans", { state: { projectId: p.id } })}
                    >
                      <span className="vc-btn__inner">
                        <IconScan />
                        Escaneos
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
        <div className="vc-modal" role="dialog" onClick={(e) => e.stopPropagation()} aria-labelledby="project-view-title">
          <h2 id="project-view-title">Proyecto #{row.id}</h2>
          <div className="vc-form">
            <label className="vc-field">
              <span>ID</span>
              <input value={String(row.id)} readOnly className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>Propietario</span>
              <input value={row.owner_name ?? "—"} readOnly className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>Nombre</span>
              <input value={row.name} readOnly className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>Descripción</span>
              <textarea value={row.description || ""} readOnly rows={4} className="vc-input-readonly" />
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
              Cerrar
            </button>
          </div>
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
