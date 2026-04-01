import { useCallback, useEffect, useState } from "react";
import { UC_VULNS } from "../rbac";
import { useAuth } from "../context/AuthContext";
import * as api from "../services/vulnerabilities";

const SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];
const STATUSES = ["OPEN", "IN_PROGRESS", "MITIGATED", "ACCEPTED"];

export default function VulnerabilitiesPage() {
  const { token, can } = useAuth();
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const [modal, setModal] = useState(null);

  const load = useCallback(async () => {
    setError("");
    try {
      const data = await api.listVulnerabilities(token);
      setRows(data);
    } catch (e) {
      setError(e.message);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  async function onDelete(id) {
    if (!window.confirm("¿Eliminar esta vulnerabilidad?")) return;
    try {
      await api.deleteVulnerability(token, id);
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div>
      <div className="vc-page-head">
        <h1>Vulnerabilidades</h1>
        {can(UC_VULNS, "c") && (
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
              <th>Scan ID</th>
              <th>CVE</th>
              <th>Título</th>
              <th>Severidad</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((v) => (
              <tr key={v.id}>
                <td>{v.id}</td>
                <td>{v.scan_id}</td>
                <td>{v.cve}</td>
                <td className="vc-ellipsis">{v.title}</td>
                <td>{v.severity}</td>
                <td>{v.status}</td>
                <td className="vc-table__actions">
                  {can(UC_VULNS, "r") && (
                    <button type="button" className="vc-btn vc-btn--small" onClick={() => setModal({ mode: "view", row: v })}>
                      Ver
                    </button>
                  )}
                  {can(UC_VULNS, "u") && (
                    <button type="button" className="vc-btn vc-btn--small" onClick={() => setModal({ mode: "edit", row: v })}>
                      Editar
                    </button>
                  )}
                  {can(UC_VULNS, "d") && (
                    <button type="button" className="vc-btn vc-btn--small vc-btn--danger" onClick={() => onDelete(v.id)}>
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
        <VulnModal
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

function VulnModal({ token, modal, onClose, onSaved }) {
  const { mode, row } = modal;
  const [scanId, setScanId] = useState(String(row?.scan_id || ""));
  const [title, setTitle] = useState(row?.title || "");
  const [description, setDescription] = useState(row?.description || "");
  const [severity, setSeverity] = useState(row?.severity || "HIGH");
  const [status, setStatus] = useState(row?.status || "OPEN");
  const [cve, setCve] = useState(row?.cve || "");
  const [filePath, setFilePath] = useState(row?.file_path || "/");
  const [lineNumber, setLineNumber] = useState(String(row?.line_number ?? "0"));
  const [err, setErr] = useState("");

  async function submit(e) {
    e.preventDefault();
    setErr("");
    try {
      const body = {
        scan_id: Number(scanId),
        title,
        description: description || null,
        severity,
        status,
        cve,
        file_path: filePath,
        line_number: Number(lineNumber),
      };
      if (mode === "create") {
        await api.createVulnerability(token, body);
      } else if (mode === "edit") {
        await api.updateVulnerability(token, row.id, body);
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
          <h2>Vulnerabilidad #{row.id}</h2>
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
      <div className="vc-modal vc-modal--wide" role="dialog" onClick={(e) => e.stopPropagation()}>
        <h2>{mode === "create" ? "Nueva vulnerabilidad" : `Editar #${row.id}`}</h2>
        {err && <div className="vc-banner vc-banner--error">{err}</div>}
        <form onSubmit={submit} className="vc-form">
          <label className="vc-field">
            <span>Escaneo ID</span>
            <input value={scanId} onChange={(e) => setScanId(e.target.value)} required />
          </label>
          <label className="vc-field">
            <span>Título</span>
            <input value={title} onChange={(e) => setTitle(e.target.value)} required />
          </label>
          <label className="vc-field">
            <span>Descripción</span>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
          </label>
          <label className="vc-field">
            <span>Severidad</span>
            <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
              {SEVERITIES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label className="vc-field">
            <span>Estado</span>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label className="vc-field">
            <span>CVE</span>
            <input value={cve} onChange={(e) => setCve(e.target.value)} required />
          </label>
          <label className="vc-field">
            <span>Ruta fichero</span>
            <input value={filePath} onChange={(e) => setFilePath(e.target.value)} required />
          </label>
          <label className="vc-field">
            <span>Línea</span>
            <input value={lineNumber} onChange={(e) => setLineNumber(e.target.value)} required />
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
