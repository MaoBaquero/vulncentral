import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import TrivyUploadModal from "../components/TrivyUploadModal";
import { syncAndGetVulnsContext } from "../flowContext";
import { UC_SCANS, UC_VULNS } from "../rbac";
import { useAuth } from "../context/AuthContext";
import * as api from "../services/vulnerabilities";
import { uploadTrivyReport } from "../services/scans";

const SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];
const STATUSES = ["OPEN", "IN_PROGRESS", "MITIGATED", "ACCEPTED"];

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

function IconUpload() {
  return (
    <svg className="vc-btn__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  );
}

function IconFileDoc() {
  return (
    <svg className="vc-btn__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
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

export default function VulnerabilitiesPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { token, can } = useAuth();
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const [modal, setModal] = useState(null);
  const [trivyOpen, setTrivyOpen] = useState(false);
  const [trivyUploading, setTrivyUploading] = useState(false);
  const [trivyUploadOk, setTrivyUploadOk] = useState("");
  const fileInputRef = useRef(null);
  const [flowScanId, setFlowScanId] = useState(undefined);
  const [flowProjectId, setFlowProjectId] = useState(undefined);

  const routeKey = `${location.key}-${JSON.stringify(location.state ?? null)}`;
  useEffect(() => {
    const { scanId, projectId } = syncAndGetVulnsContext(location.state);
    setFlowScanId(scanId);
    setFlowProjectId(projectId);
  }, [routeKey, location.state]);

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

  const filteredRows = useMemo(() => {
    if (flowScanId == null) return rows;
    return rows.filter((v) => v.scan_id === flowScanId);
  }, [rows, flowScanId]);

  async function onDelete(id) {
    if (!window.confirm("¿Eliminar esta vulnerabilidad?")) return;
    try {
      await api.deleteVulnerability(token, id);
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  function goBackToScans() {
    const state = flowProjectId != null ? { projectId: flowProjectId } : undefined;
    navigate("/scans", { state });
  }

  const canLoadTrivy = can(UC_SCANS, "u") && flowScanId != null;

  async function onTrivyFileSelected(e) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file || flowScanId == null) return;
    setError("");
    setTrivyUploadOk("");
    setTrivyUploading(true);
    try {
      const text = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result));
        reader.onerror = () => reject(new Error("No se pudo leer el archivo"));
        reader.readAsText(file);
      });
      await uploadTrivyReport(token, flowScanId, text);
      setTrivyUploadOk(`Encolado: ${file.name}`);
      window.setTimeout(() => setTrivyUploadOk(""), 4000);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setTrivyUploading(false);
    }
  }

  return (
    <div>
      <div className="vc-page-head">
        <h1>Vulnerabilidades</h1>
        <div className="vc-page-head__actions">
          {canLoadTrivy && (
            <>
              <button type="button" className="vc-btn vc-btn--primary" onClick={() => setTrivyOpen(true)}>
                <span className="vc-btn__inner">
                  <IconUpload />
                  Cargar
                </span>
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".json,application/json"
                style={{ display: "none" }}
                aria-hidden
                tabIndex={-1}
                onChange={onTrivyFileSelected}
              />
              <button
                type="button"
                className="vc-btn"
                disabled={trivyUploading}
                onClick={() => fileInputRef.current?.click()}
              >
                <span className="vc-btn__inner">
                  <IconFileDoc />
                  Subir
                </span>
              </button>
            </>
          )}
          {can(UC_VULNS, "c") && (
            <button
              type="button"
              className="vc-btn"
              onClick={() =>
                setModal({
                  mode: "create",
                  defaultScanId: flowScanId,
                  scanIdReadOnly: flowScanId != null,
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
      {flowScanId == null && (
        <p className="vc-muted">Abra esta vista desde Escaneos (botón Vulnerabilidades) para asociar el contexto del escaneo sin usar la URL.</p>
      )}
      {flowScanId != null && (
        <p className="vc-muted">Contexto de escaneo activo (no visible en la URL).</p>
      )}
      */}

      {error && <div className="vc-banner vc-banner--error">{error}</div>}
      {trivyUploadOk && <div className="vc-banner vc-banner--ok">{trivyUploadOk}</div>}
      <div className="vc-table-wrap">
        <table className="vc-table">
          <thead>
            <tr>
              <th>Herramienta</th>
              <th>CVE</th>
              <th>Título</th>
              <th>Severidad</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((v) => (
              <tr key={v.id}>
                <td>{v.scan_tool ?? "—"}</td>
                <td>{v.cve}</td>
                <td className="vc-ellipsis">{v.title}</td>
                <td>{v.severity}</td>
                <td>{v.status}</td>
                <td className="vc-table__actions">
                  {can(UC_VULNS, "r") && (
                    <button type="button" className="vc-btn vc-btn--small" onClick={() => setModal({ mode: "view", row: v })}>
                      <span className="vc-btn__inner">
                        <IconEye />
                        Ver
                      </span>
                    </button>
                  )}
                  {can(UC_VULNS, "u") && (
                    <button type="button" className="vc-btn vc-btn--small" onClick={() => setModal({ mode: "edit", row: v })}>
                      <span className="vc-btn__inner">
                        <IconPencil />
                        Editar
                      </span>
                    </button>
                  )}
                  {can(UC_VULNS, "d") && (
                    <button type="button" className="vc-btn vc-btn--small vc-btn--danger" onClick={() => onDelete(v.id)}>
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
      <div className="vc-page-footer-back">
        <button type="button" className="vc-btn" onClick={goBackToScans}>
          <span className="vc-btn__inner">
            <IconArrowLeft />
            Atrás
          </span>
        </button>
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
      {trivyOpen && flowScanId != null && (
        <TrivyUploadModal
          token={token}
          scanId={flowScanId}
          title={`Cargar informe Trivy — escaneo #${flowScanId}`}
          onClose={() => setTrivyOpen(false)}
          onDone={() => {
            setTrivyOpen(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function VulnModal({ token, modal, onClose, onSaved }) {
  const { mode, row, defaultScanId, scanIdReadOnly } = modal;
  const [scanId, setScanId] = useState(String(row?.scan_id ?? defaultScanId ?? ""));
  const [title, setTitle] = useState(row?.title || "");
  const [description, setDescription] = useState(row?.description || "");
  const [severity, setSeverity] = useState(row?.severity || "HIGH");
  const [status, setStatus] = useState(row?.status || "OPEN");
  const [cve, setCve] = useState(row?.cve || "");
  const [filePath, setFilePath] = useState(row?.file_path || "/");
  const [lineNumber, setLineNumber] = useState(String(row?.line_number ?? "0"));
  const [err, setErr] = useState("");

  const readOnlyScan = mode === "create" && scanIdReadOnly;

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
        <div className="vc-modal vc-modal--wide" role="dialog" onClick={(e) => e.stopPropagation()} aria-labelledby="vuln-view-title">
          <h2 id="vuln-view-title">Vulnerabilidad #{row.id}</h2>
          <div className="vc-form">
            <label className="vc-field">
              <span>ID</span>
              <input value={String(row.id)} readOnly className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>Herramienta (escaneo)</span>
              <input value={row.scan_tool ?? "—"} readOnly className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>Escaneo (ID interno)</span>
              <input value={String(row.scan_id)} readOnly className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>Título</span>
              <input value={row.title} readOnly className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>Descripción</span>
              <textarea value={row.description || ""} readOnly rows={3} className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>Severidad</span>
              <input value={row.severity} readOnly className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>Estado</span>
              <input value={row.status} readOnly className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>CVE</span>
              <input value={row.cve} readOnly className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>Ruta fichero</span>
              <input value={row.file_path} readOnly className="vc-input-readonly" />
            </label>
            <label className="vc-field">
              <span>Línea</span>
              <input value={String(row.line_number)} readOnly className="vc-input-readonly" />
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
      <div className="vc-modal vc-modal--wide" role="dialog" onClick={(e) => e.stopPropagation()}>
        <h2>{mode === "create" ? "Nueva vulnerabilidad" : `Editar #${row.id}`}</h2>
        {err && <div className="vc-banner vc-banner--error">{err}</div>}
        <form onSubmit={submit} className="vc-form">
          <label className="vc-field">
            <span>Escaneo ID</span>
            <input
              value={scanId}
              onChange={(e) => setScanId(e.target.value)}
              required
              readOnly={readOnlyScan}
              disabled={readOnlyScan}
            />
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
