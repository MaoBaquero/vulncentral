import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { clearFlowContext, syncAndGetScansContext } from "../flowContext";
import { UC_SCANS, UC_VULNS } from "../rbac";
import { useAuth } from "../context/AuthContext";
import * as api from "../services/scans";

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

function IconArrowLeft() {
  return (
    <svg className="vc-btn__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <line x1="19" y1="12" x2="5" y2="12" />
      <polyline points="12 19 5 12 12 5" />
    </svg>
  );
}

export default function ScansPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { token, can } = useAuth();
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const [modal, setModal] = useState(null);
  const [flowProjectId, setFlowProjectId] = useState(undefined);

  const routeKey = `${location.key}-${JSON.stringify(location.state ?? null)}`;
  useEffect(() => {
    const { projectId } = syncAndGetScansContext(location.state);
    setFlowProjectId(projectId);
  }, [routeKey, location.state]);

  const load = useCallback(async () => {
    setError("");
    try {
      const data = await api.listScans(token);
      setRows(data);
    } catch (e) {
      setError(e.message);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  const filteredRows = useMemo(() => {
    if (flowProjectId == null) return rows;
    return rows.filter((s) => s.project_id === flowProjectId);
  }, [rows, flowProjectId]);

  async function onDelete(id) {
    if (!window.confirm("¿Eliminar este escaneo?")) return;
    try {
      await api.deleteScan(token, id);
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  function goBackToProjects() {
    clearFlowContext();
    navigate("/projects");
  }

  return (
    <div>
      <div className="vc-page-head">
        <h1>Escaneos</h1>
        <div className="vc-page-head__actions">
          {can(UC_SCANS, "c") && (
            <button
              type="button"
              className="vc-btn vc-btn--primary"
              onClick={() =>
                setModal({
                  mode: "create",
                  defaultProjectId: flowProjectId,
                  projectIdReadOnly: flowProjectId != null,
                })
              }
            >
              <span className="vc-btn__inner">
                <IconPlus />
                Crear
              </span>
            </button>
          )}
        </div>
      </div>
      
      {/* 
      {flowProjectId != null && (
        <p className="vc-muted">Filtrado por proyecto (contexto de navegación, no visible en la URL).</p>
      )}
      */}

      {error && <div className="vc-banner vc-banner--error">{error}</div>}
      <div className="vc-table-wrap">
        <table className="vc-table">
          <thead>
            <tr>
              <th>Proyecto</th>
              <th>Herramienta</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((s) => (
              <tr key={s.id}>
                <td>{s.project_name ?? "—"}</td>
                <td>{s.tool}</td>
                <td>{s.status}</td>
                <td className="vc-table__actions">
                  {can(UC_SCANS, "r") && (
                    <button type="button" className="vc-btn vc-btn--small" onClick={() => setModal({ mode: "view", row: s })}>
                      <span className="vc-btn__inner">
                        <IconEye />
                        Ver
                      </span>
                    </button>
                  )}
                  {can(UC_SCANS, "u") && (
                    <button type="button" className="vc-btn vc-btn--small" onClick={() => setModal({ mode: "edit", row: s })}>
                      <span className="vc-btn__inner">
                        <IconPencil />
                        Editar
                      </span>
                    </button>
                  )}
                  {can(UC_SCANS, "d") && (
                    <button type="button" className="vc-btn vc-btn--small vc-btn--danger" onClick={() => onDelete(s.id)}>
                      <span className="vc-btn__inner">
                        <IconTrash />
                        Eliminar
                      </span>
                    </button>
                  )}
                  {can(UC_VULNS, "r") && (
                    <button
                      type="button"
                      className="vc-btn vc-btn--small"
                      onClick={() =>
                        navigate("/vulnerabilities", {
                          state: { scanId: s.id, projectId: s.project_id },
                        })
                      }
                    >
                      <span className="vc-btn__inner">
                        <IconScan />
                        Vulnerabilidades
                      </span>
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="vc-page-footer-back">
        <button type="button" className="vc-btn" onClick={goBackToProjects}>
          <span className="vc-btn__inner">
            <IconArrowLeft />
            Atrás
          </span>
        </button>
      </div>
      {modal && (
        <ScanModal
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

function ScanModal({ token, modal, onClose, onSaved }) {
  const { mode, row, defaultProjectId, projectIdReadOnly } = modal;
  const [projectId, setProjectId] = useState(String(row?.project_id ?? defaultProjectId ?? ""));
  const [tool, setTool] = useState(row?.tool || "trivy");
  const [status, setStatus] = useState(row?.status || "pending");
  const [err, setErr] = useState("");

  const readOnlyProject = mode === "create" && projectIdReadOnly;

  async function submit(e) {
    e.preventDefault();
    setErr("");
    try {
      if (mode === "create") {
        await api.createScan(token, {
          project_id: Number(projectId),
          tool,
          status,
        });
      } else if (mode === "edit") {
        await api.updateScan(token, row.id, {
          project_id: Number(projectId),
          tool,
          status,
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
        <div className="vc-modal" role="dialog" onClick={(e) => e.stopPropagation()} aria-labelledby="scan-view-title">
          <h2 id="scan-view-title">Escaneo #{row.id}</h2>
          <div className="vc-form">
            <label className="vc-field">
              <span>ID</span>
              <input value={String(row.id)} readOnly className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>Proyecto</span>
              <input value={row.project_name ?? "—"} readOnly className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>Proyecto (ID interno)</span>
              <input value={String(row.project_id)} readOnly className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>Herramienta</span>
              <input value={row.tool} readOnly className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>Estado</span>
              <input value={row.status} readOnly className="vc-input-readonly" />
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
        <h2>{mode === "create" ? "Nuevo escaneo" : `Editar escaneo #${row.id}`}</h2>
        {err && <div className="vc-banner vc-banner--error">{err}</div>}
        <form onSubmit={submit} className="vc-form">
          <label className="vc-field">
            <span>Proyecto ID</span>
            <input
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              required
              readOnly={readOnlyProject}
              disabled={readOnlyProject}
            />
          </label>
          <label className="vc-field">
            <span>Herramienta</span>
            <input value={tool} onChange={(e) => setTool(e.target.value)} required />
          </label>
          <label className="vc-field">
            <span>Estado</span>
            <input value={status} onChange={(e) => setStatus(e.target.value)} required />
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
