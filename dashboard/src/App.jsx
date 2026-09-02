import { useEffect, useState } from "react";
import { getPatientSummaries, getPatientTrend } from "./api/client";
import AlertsPanel from "./components/AlertsPanel";
import PatientHeader from "./components/PatientHeader";
import PatientList from "./components/PatientList";
import TrendChart from "./components/TrendChart";
import "./App.css";

const REFRESH_MS = 5000;

function App() {
  const [patients, setPatients] = useState([]);
  const [selectedPatientId, setSelectedPatientId] = useState(null);
  const [trend, setTrend] = useState([]);

  useEffect(() => {
    const refresh = () => {
      getPatientSummaries()
        .then(setPatients)
        .catch(() => {});
    };
    refresh();
    const id = setInterval(refresh, REFRESH_MS);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (!selectedPatientId) return;
    getPatientTrend(selectedPatientId).then(setTrend).catch(() => setTrend([]));
  }, [selectedPatientId]);

  const selectedPatient = patients.find((p) => p.id === selectedPatientId);
  const redCount = patients.filter((p) => p.worst_active_severity === "red").length;
  const amberCount = patients.filter((p) => p.worst_active_severity === "amber").length;

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-title">
          <div className="app-logo">L</div>
          <div>
            <h1>LCIIS</h1>
            <span className="subtitle">Longitudinal Clinical Investigation Intelligence System</span>
          </div>
        </div>
        <div className="app-header-stats">
          <div className="header-stat">
            <span className="header-stat-value">{patients.length}</span>
            <span className="header-stat-label">Patients</span>
          </div>
          <div className="header-stat header-stat-red">
            <span className="header-stat-value">{redCount}</span>
            <span className="header-stat-label">Critical</span>
          </div>
          <div className="header-stat header-stat-amber">
            <span className="header-stat-value">{amberCount}</span>
            <span className="header-stat-label">Warning</span>
          </div>
          <div className="live-indicator">
            <span className="live-dot" /> Live
          </div>
        </div>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <PatientList
            patients={patients}
            selectedPatientId={selectedPatientId}
            onSelectPatient={setSelectedPatientId}
          />
          <AlertsPanel onSelectPatient={setSelectedPatientId} />
        </aside>

        <main className="main">
          {selectedPatient ? (
            <>
              <PatientHeader patient={selectedPatient} />
              <TrendChart series={trend} />
            </>
          ) : (
            <div className="empty-state">
              <p className="muted">Select a patient to view their longitudinal lab trends.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
