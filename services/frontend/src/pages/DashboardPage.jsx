import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { UC_PROJECTS, UC_SCANS, UC_VULNS } from "../rbac";
import { useAuth } from "../context/AuthContext";
import * as api from "../services/vulnerabilities";

const OPEN_STATUSES = new Set(["OPEN", "IN_PROGRESS"]);

const SEVERITY_META = [
  { key: "CRITICAL", label: "Critical", color: "#dc2626" },
  { key: "HIGH", label: "High", color: "#ea580c" },
  { key: "MEDIUM", label: "Medium", color: "#eab308" },
  { key: "LOW", label: "Low", color: "#2563eb" },
];

function isCreatedThisCalendarMonth(createdAt) {
  const d = new Date(createdAt);
  if (Number.isNaN(d.getTime())) return false;
  const now = new Date();
  return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth();
}

function buildSeverityPieData(list) {
  const counts = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
  let other = 0;
  for (const v of list) {
    const s = v.severity;
    if (counts[s] !== undefined) counts[s] += 1;
    else other += 1;
  }
  const data = SEVERITY_META.map(({ key, label, color }) => ({
    name: label,
    value: counts[key],
    fill: color,
  }));
  if (other > 0) {
    data.push({ name: "Otro", value: other, fill: "#94a3b8" });
  }
  return data.filter((row) => row.value > 0);
}

function IconTarget() {
  return (
    <svg className="vc-dashboard-card__icon-svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="6" />
      <circle cx="12" cy="12" r="2" />
    </svg>
  );
}

function IconBug() {
  return (
    <svg className="vc-dashboard-card__icon-svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M8 2v4M16 2v4M9.5 22v-4.5M14.5 22v-4.5M5 9H3M21 9h-2M5 15H3M21 15h-2" />
      <rect x="6" y="6" width="12" height="12" rx="2" />
    </svg>
  );
}

function IconExtinguisher() {
  return (
    <svg className="vc-dashboard-card__icon-svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M6 21h12M9 21V9l3-6 3 6v12" />
      <path d="M7 9h10" />
      <circle cx="12" cy="14" r="2" />
    </svg>
  );
}

function IconCheck() {
  return (
    <svg className="vc-dashboard-card__icon-svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden>
      <path d="M20 6L9 17l-5-5" />
    </svg>
  );
}

function SeverityDonut({ title, data }) {
  const total = data.reduce((s, d) => s + d.value, 0);

  return (
    <div className="vc-dashboard-chart">
      <div className="vc-dashboard-chart__head">{title}</div>
      <div className="vc-dashboard-chart__body">
        {total === 0 ? (
          <div className="vc-dashboard-chart__empty">Sin datos</div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <PieChart margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                cx="38%"
                cy="50%"
                innerRadius={58}
                outerRadius={88}
                paddingAngle={1}
              >
                {data.map((entry) => (
                  <Cell key={entry.name} fill={entry.fill} stroke="#fff" strokeWidth={1} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => [value, "Cantidad"]} />
              <Legend layout="vertical" verticalAlign="middle" align="right" wrapperStyle={{ paddingLeft: "0.5rem" }} />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { user, token, can } = useAuth();
  const canReadVulns = can(UC_VULNS, "r");
  const [vulns, setVulns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadVulns = useCallback(async () => {
    if (!canReadVulns || !token) return;
    setLoading(true);
    setError("");
    try {
      const data = await api.listVulnerabilities(token);
      setVulns(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e.message || "Error al cargar vulnerabilidades");
      setVulns([]);
    } finally {
      setLoading(false);
    }
  }, [canReadVulns, token]);

  useEffect(() => {
    loadVulns();
  }, [loadVulns]);

  const sensors = useMemo(() => {
    let open = 0;
    let criticalOpen = 0;
    let mitigated = 0;
    let accepted = 0;
    for (const v of vulns) {
      const st = v.status;
      if (OPEN_STATUSES.has(st)) {
        open += 1;
        if (v.severity === "CRITICAL") criticalOpen += 1;
      }
      if (st === "MITIGATED") mitigated += 1;
      if (st === "ACCEPTED") accepted += 1;
    }
    return { open, criticalOpen, mitigated, accepted };
  }, [vulns]);

  const vulnsThisMonth = useMemo(() => vulns.filter((v) => isCreatedThisCalendarMonth(v.created_at)), [vulns]);

  const chartAll = useMemo(() => buildSeverityPieData(vulns), [vulns]);
  const chartMonth = useMemo(() => buildSeverityPieData(vulnsThisMonth), [vulnsThisMonth]);

  return (
    <div>
      <h1>Panel principal</h1>

      {canReadVulns && (
        <section className="vc-dashboard" aria-label="Resumen de vulnerabilidades">
          {error && <div className="vc-banner vc-banner--error">{error}</div>}
          {loading && <p className="vc-muted">Cargando datos de vulnerabilidades…</p>}

          {!loading && !error && (
            <>
              <div className="vc-dashboard-cards">
                <article className="vc-dashboard-card vc-dashboard-card--open">
                  <div className="vc-dashboard-card__head">
                    <span className="vc-dashboard-card__icon" aria-hidden>
                      <IconTarget />
                    </span>
                    <span className="vc-dashboard-card__value">{sensors.open}</span>
                  </div>
                  <h2 className="vc-dashboard-card__title">Vulnerabilidades abiertas</h2>
                  <footer className="vc-dashboard-card__foot">Registros sin cerrar</footer>
                </article>
                <article className="vc-dashboard-card vc-dashboard-card--critical">
                  <div className="vc-dashboard-card__head">
                    <span className="vc-dashboard-card__icon" aria-hidden>
                      <IconBug />
                    </span>
                    <span className="vc-dashboard-card__value">{sensors.criticalOpen}</span>
                  </div>
                  <h2 className="vc-dashboard-card__title">Vulnerabilidades críticas</h2>
                  <footer className="vc-dashboard-card__foot">Registros severidad crítica</footer>
                </article>
                <article className="vc-dashboard-card vc-dashboard-card--mitigated">
                  <div className="vc-dashboard-card__head">
                    <span className="vc-dashboard-card__icon" aria-hidden>
                      <IconExtinguisher />
                    </span>
                    <span className="vc-dashboard-card__value">{sensors.mitigated}</span>
                  </div>
                  <h2 className="vc-dashboard-card__title">Vulnerabilidades mitigadas</h2>
                  <footer className="vc-dashboard-card__foot">Registros mitigados</footer>
                </article>
                <article className="vc-dashboard-card vc-dashboard-card--accepted">
                  <div className="vc-dashboard-card__head">
                    <span className="vc-dashboard-card__icon" aria-hidden>
                      <IconCheck />
                    </span>
                    <span className="vc-dashboard-card__value">{sensors.accepted}</span>
                  </div>
                  <h2 className="vc-dashboard-card__title">Vulnerabilidades aceptadas</h2>
                  <footer className="vc-dashboard-card__foot">Registros aceptados</footer>
                </article>
              </div>

              <div className="vc-dashboard-charts">
                <SeverityDonut key="historic-all" title="Histórico vulnerabilidades" data={chartAll} />
                <SeverityDonut key="historic-month" title="Histórico vulnerabilidades mes actual" data={chartMonth} />
              </div>
            </>
          )}
        </section>
      )}
    </div>
  );
}
