import { useState } from "react";
import * as api from "../services/scans";

export default function TrivyUploadModal({ token, scanId, onClose, onDone, title }) {
  const [jsonText, setJsonText] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  async function submit(e) {
    e.preventDefault();
    setErr("");
    setMsg("");
    try {
      const r = await api.uploadTrivyReport(token, scanId, jsonText);
      setMsg(`Encolado. task_id: ${r.task_id || "—"}`);
      setTimeout(onDone, 1500);
    } catch (e) {
      setErr(e.message);
    }
  }

  return (
    <div className="vc-modal-backdrop" role="presentation" onClick={onClose}>
      <div className="vc-modal vc-modal--wide" role="dialog" onClick={(ev) => ev.stopPropagation()}>
        <h2>{title || `Informe Trivy — escaneo #${scanId}`}</h2>
        <p className="vc-muted">Pegue el JSON del informe. Se enviará al API (202 + cola).</p>
        {err && <div className="vc-banner vc-banner--error">{err}</div>}
        {msg && <div className="vc-banner vc-banner--ok">{msg}</div>}
        <form onSubmit={submit} className="vc-form">
          <label className="vc-field">
            <span>JSON</span>
            <textarea
              value={jsonText}
              onChange={(e) => setJsonText(e.target.value)}
              rows={12}
              className="vc-textarea-code"
              required
            />
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
