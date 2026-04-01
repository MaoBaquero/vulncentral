import { useCallback, useEffect, useState } from "react";
import { UC_SCANS } from "../rbac";
import { useAuth } from "../context/AuthContext";
import * as api from "../services/scans";

export default function ScansPage() {
  const { token, can } = useAuth();
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const [modal, setModal] = useState(null);
  const [trivyModal, setTrivyModal] = useState(null);

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

  async function onDelete(id) {
    if (!window.confirm("¿Eliminar este escaneo?")) return;
    try {
      await api.deleteScan(token, id);
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div>
      <div className="vc-page-head">
        <h1>Escaneos</h1>
        {can(UC_SCANS, "c") && (
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
              <th>Proyecto ID</th>
              <th>Herramienta</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((s) => (
              <tr key={s.id}>
                <td>{s.id}</td>
                <td>{s.project_id}</td>
                <td>{s.tool}</td>
                <td>{s.status}</td>
                <td className="vc-table__actions">
                  {can(UC_SCANS, "r") && (
                    <button type="button" className="vc-btn vc-btn--small" onClick={() => setModal({ mode: "view", row: s })}>
                      Ver
                    </button>
                  )}
                  {can(UC_SCANS, "u") && (
                    <>
                      <button type="button" className="vc-btn vc-btn--small" onClick={() => setModal({ mode: "edit", row: s })}>
                        Editar
                      </button>
                      <button type="button" className="vc-btn vc-btn--small" onClick={() => setTrivyModal(s)}>
                        Trivy JSON
                      </button>
                    </>
                  )}
                  {can(UC_SCANS, "d") && (
                    <button type="button" className="vc-btn vc-btn--small vc-btn--danger" onClick={() => onDelete(s.id)}>
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
      {trivyModal && (
        <TrivyModal
          token={token}
          scan={trivyModal}
          onClose={() => setTrivyModal(null)}
          onDone={() => {
            setTrivyModal(null);
            load();
          }}
        />
      )}
    </div>
  );
}

function ScanModal({ token, modal, onClose, onSaved }) {
  const { mode, row } = modal;
  const [projectId, setProjectId] = useState(String(row?.project_id || ""));
  const [tool, setTool] = useState(row?.tool || "trivy");
  const [status, setStatus] = useState(row?.status || "pending");
  const [err, setErr] = useState("");

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
        <div className="vc-modal" role="dialog" onClick={(e) => e.stopPropagation()}>
          <h2>Escaneo #{row.id}</h2>
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
        <h2>{mode === "create" ? "Nuevo escaneo" : `Editar escaneo #${row.id}`}</h2>
        {err && <div className="vc-banner vc-banner--error">{err}</div>}
        <form onSubmit={submit} className="vc-form">
          <label className="vc-field">
            <span>Proyecto ID</span>
            <input value={projectId} onChange={(e) => setProjectId(e.target.value)} required />
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

function TrivyModal({ token, scan, onClose, onDone }) {
  const [jsonText, setJsonText] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  async function submit(e) {
    e.preventDefault();
    setErr("");
    setMsg("");
    try {
      const r = await api.uploadTrivyReport(token, scan.id, jsonText);
      setMsg(`Encolado. task_id: ${r.task_id || "—"}`);
      setTimeout(onDone, 1500);
    } catch (e) {
      setErr(e.message);
    }
  }

  return (
    <div className="vc-modal-backdrop" role="presentation" onClick={onClose}>
      <div className="vc-modal vc-modal--wide" role="dialog" onClick={(ev) => ev.stopPropagation()}>
        <h2>Informe Trivy — escaneo #{scan.id}</h2>
        <p className="vc-muted">Pegue el JSON del informe. Se enviará al API (202 + cola).</p>
        {err && <div className="vc-banner vc-banner--error">{err}</div>}
        {msg && <div className="vc-banner vc-banner--ok">{msg}</div>}
        <form onSubmit={submit} className="vc-form">
          <label className="vc-field">
            <span>JSON</span>
            <textarea value={jsonText} onChange={(e) => setJsonText(e.target.value)} rows={12} className="vc-textarea-code" required />
          </label>
          <div className="vc-form__actions">
            <button type="button" className="vc-btn" onClick={onClose}>
              Cerrar
            </button>
            <button type="submit" className="vc-btn vc-btn--primary">
              Enviar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
