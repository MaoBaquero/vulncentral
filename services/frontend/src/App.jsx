const apiBase = import.meta.env.VITE_API_BASE_URL || "";

export default function App() {
  return (
    <main className="app">
      <h1>VulnCentral</h1>
      <p className="tagline">Panel base (Fase 1 — sin lógica de negocio).</p>
      <p className="meta">
        API base configurada:{" "}
        <code>{apiBase || "(no definida en build)"}</code>
      </p>
    </main>
  );
}
