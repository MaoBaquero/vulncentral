import { useCallback, useEffect, useState } from "react";
import * as api from "../services/auditLogs";
import { useAuth } from "../context/AuthContext";

const PAGE = 50;

export default function LogsPage() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const data = await api.listAuditLogs(token, skip, PAGE);
      setItems(data.items);
      setTotal(data.total);
    } catch (e) {
      setError(e.message);
    }
  }, [token, skip]);

  useEffect(() => {
    load();
  }, [load]);

  const canPrev = skip > 0;
  const canNext = skip + items.length < total;

  return (
    <div>
      <h1>Logs de auditoría</h1>
      
      {/*  <p className="vc-muted">Registros de la tabla `audit_logs` (puede estar vacía si aún no hay eventos).</p> */}

      {error && <div className="vc-banner vc-banner--error">{error}</div>}
      <div className="vc-page-head vc-page-head--tools">
        <span className="vc-muted">
          Total: {total} — mostrando {items.length} desde {skip}
        </span>
        <div>
          <button type="button" className="vc-btn vc-btn--small" disabled={!canPrev} onClick={() => setSkip((s) => Math.max(0, s - PAGE))}>
            Anterior
          </button>
          <button
            type="button"
            className="vc-btn vc-btn--small"
            disabled={!canNext}
            onClick={() => setSkip((s) => s + PAGE)}
          >
            Siguiente
          </button>
        </div>
      </div>
      <div className="vc-table-wrap">
        <table className="vc-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Usuario ID</th>
              <th>Acción</th>
              <th>Entidad</th>
              <th>Fecha</th>
            </tr>
          </thead>
          <tbody>
            {items.map((log) => (
              <tr key={log.id}>
                <td>{log.id}</td>
                <td>{log.user_id}</td>
                <td>{log.action}</td>
                <td>{log.entity}</td>
                <td>{log.timestamp ? new Date(log.timestamp).toLocaleString() : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
