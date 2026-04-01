import { useState } from "react";
import { UC_PROJECTS, UC_SCANS, UC_VULNS } from "../rbac";
import { useAuth } from "../context/AuthContext";
import * as projectsApi from "../services/projects";
import * as scansApi from "../services/scans";
import * as vulnsApi from "../services/vulnerabilities";

const SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];
const STATUSES = ["OPEN", "IN_PROGRESS", "MITIGATED", "ACCEPTED"];

/**
 * Asistente: proyecto → escaneo → vulnerabilidades (manual o Trivy).
 */
export default function FlowNewPage() {
  const { token, user, can } = useAuth();
  const [step, setStep] = useState(1);
  const [projectId, setProjectId] = useState(null);
  const [scanId, setScanId] = useState(null);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  const [pName, setPName] = useState("");
  const [pDesc, setPDesc] = useState("");
  const [pUserId, setPUserId] = useState(String(user?.id || ""));

  const [sTool, setSTool] = useState("trivy");
  const [sStatus, setSStatus] = useState("pending");

  const [vTitle, setVTitle] = useState("");
  const [vDesc, setVDesc] = useState("");
  const [vSev, setVSev] = useState("HIGH");
  const [vStat, setVStat] = useState("OPEN");
  const [vCve, setVCve] = useState("");
  const [vPath, setVPath] = useState("/");
  const [vLine, setVLine] = useState("0");
  const [trivyJson, setTrivyJson] = useState("");

  async function createProject(e) {
    e.preventDefault();
    setErr("");
    setOk("");
    try {
      const p = await projectsApi.createProject(token, {
        user_id: Number(pUserId),
        name: pName,
        description: pDesc || null,
      });
      setProjectId(p.id);
      setOk(`Proyecto creado (id ${p.id}).`);
      setStep(2);
    } catch (e) {
      setErr(e.message);
    }
  }

  async function createScan(e) {
    e.preventDefault();
    setErr("");
    setOk("");
    try {
      const s = await scansApi.createScan(token, {
        project_id: projectId,
        tool: sTool,
        status: sStatus,
      });
      setScanId(s.id);
      setOk(`Escaneo creado (id ${s.id}).`);
      setStep(3);
    } catch (e) {
      setErr(e.message);
    }
  }

  async function createVuln(e) {
    e.preventDefault();
    setErr("");
    setOk("");
    try {
      await vulnsApi.createVulnerability(token, {
        scan_id: scanId,
        title: vTitle,
        description: vDesc || null,
        severity: vSev,
        status: vStat,
        cve: vCve,
        file_path: vPath,
        line_number: Number(vLine),
      });
      setOk("Vulnerabilidad creada.");
    } catch (e) {
      setErr(e.message);
    }
  }

  async function sendTrivy(e) {
    e.preventDefault();
    setErr("");
    setOk("");
    try {
      const r = await scansApi.uploadTrivyReport(token, scanId, trivyJson);
      setOk(`Informe encolado. task_id: ${r.task_id}`);
    } catch (e) {
      setErr(e.message);
    }
  }

  if (!can(UC_PROJECTS, "c") || !can(UC_SCANS, "c")) {
    return (
      <div>
        <h1>Nuevo flujo</h1>
        <p className="vc-banner vc-banner--error">No tiene permisos para crear proyectos y escaneos.</p>
      </div>
    );
  }

  return (
    <div>
      <h1>Nuevo flujo</h1>
      <p className="vc-muted">Proyecto → escaneo → vulnerabilidades (manual o JSON Trivy).</p>
      <ol className="vc-steps">
        <li className={step >= 1 ? "vc-steps__on" : ""}>1. Proyecto</li>
        <li className={step >= 2 ? "vc-steps__on" : ""}>2. Escaneo</li>
        <li className={step >= 3 ? "vc-steps__on" : ""}>3. Vulnerabilidades</li>
      </ol>
      {err && <div className="vc-banner vc-banner--error">{err}</div>}
      {ok && <div className="vc-banner vc-banner--ok">{ok}</div>}

      {step === 1 && (
        <form onSubmit={createProject} className="vc-form vc-panel">
          <h2>Paso 1 — Proyecto</h2>
          <label className="vc-field">
            <span>Usuario propietario (ID)</span>
            <input value={pUserId} onChange={(e) => setPUserId(e.target.value)} required />
          </label>
          <label className="vc-field">
            <span>Nombre</span>
            <input value={pName} onChange={(e) => setPName(e.target.value)} required />
          </label>
          <label className="vc-field">
            <span>Descripción</span>
            <textarea value={pDesc} onChange={(e) => setPDesc(e.target.value)} rows={2} />
          </label>
          <button type="submit" className="vc-btn vc-btn--primary">
            Crear y continuar
          </button>
        </form>
      )}

      {step === 2 && (
        <form onSubmit={createScan} className="vc-form vc-panel">
          <h2>Paso 2 — Escaneo (proyecto {projectId})</h2>
          <label className="vc-field">
            <span>Herramienta</span>
            <input value={sTool} onChange={(e) => setSTool(e.target.value)} required />
          </label>
          <label className="vc-field">
            <span>Estado</span>
            <input value={sStatus} onChange={(e) => setSStatus(e.target.value)} required />
          </label>
          <button type="submit" className="vc-btn vc-btn--primary">
            Crear y continuar
          </button>
        </form>
      )}

      {step === 3 && (
        <div className="vc-panel">
          <h2>Paso 3 — Vulnerabilidades (escaneo {scanId})</h2>
          {can(UC_VULNS, "c") && (
            <form onSubmit={createVuln} className="vc-form">
              <h3>Alta manual</h3>
              <label className="vc-field">
                <span>Título</span>
                <input value={vTitle} onChange={(e) => setVTitle(e.target.value)} required />
              </label>
              <label className="vc-field">
                <span>Descripción</span>
                <textarea value={vDesc} onChange={(e) => setVDesc(e.target.value)} rows={2} />
              </label>
              <label className="vc-field">
                <span>Severidad</span>
                <select value={vSev} onChange={(e) => setVSev(e.target.value)}>
                  {SEVERITIES.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </label>
              <label className="vc-field">
                <span>Estado</span>
                <select value={vStat} onChange={(e) => setVStat(e.target.value)}>
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </label>
              <label className="vc-field">
                <span>CVE</span>
                <input value={vCve} onChange={(e) => setVCve(e.target.value)} required />
              </label>
              <label className="vc-field">
                <span>Ruta fichero</span>
                <input value={vPath} onChange={(e) => setVPath(e.target.value)} required />
              </label>
              <label className="vc-field">
                <span>Línea</span>
                <input value={vLine} onChange={(e) => setVLine(e.target.value)} required />
              </label>
              <button type="submit" className="vc-btn vc-btn--primary">
                Crear vulnerabilidad
              </button>
            </form>
          )}
          {can(UC_SCANS, "u") && (
            <form onSubmit={sendTrivy} className="vc-form" style={{ marginTop: "1.5rem" }}>
              <h3>Ingesta Trivy (JSON)</h3>
              <label className="vc-field">
                <span>JSON del informe</span>
                <textarea value={trivyJson} onChange={(e) => setTrivyJson(e.target.value)} rows={10} className="vc-textarea-code" required />
              </label>
              <button type="submit" className="vc-btn vc-btn--primary">
                Enviar a cola
              </button>
            </form>
          )}
        </div>
      )}
    </div>
  );
}
