import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import RequireAuth from "./components/RequireAuth";
import DashboardPage from "./pages/DashboardPage";
import FlowNewPage from "./pages/FlowNewPage";
import LoginPage from "./pages/LoginPage";
import LogsPage from "./pages/LogsPage";
import ProjectsPage from "./pages/ProjectsPage";
import ScansPage from "./pages/ScansPage";
import UsersPage from "./pages/UsersPage";
import VulnerabilitiesPage from "./pages/VulnerabilitiesPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="scans" element={<ScansPage />} />
        <Route path="vulnerabilities" element={<VulnerabilitiesPage />} />
        <Route path="logs" element={<LogsPage />} />
        <Route path="flow/nuevo" element={<FlowNewPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
