import { useEffect, useState } from "react";
import { getPatientTrend } from "./api/client";
import AlertsPanel from "./components/AlertsPanel";
import PatientList from "./components/PatientList";
import TrendChart from "./components/TrendChart";
import "./App.css";

function App() {
  const [selectedPatientId, setSelectedPatientId] = useState(null);
  const [trend, setTrend] = useState([]);

  useEffect(() => {
    if (!selectedPatientId) return;
    getPatientTrend(selectedPatientId).then(setTrend).catch(() => setTrend([]));
  }, [selectedPatientId]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>LCIIS</h1>
        <span className="subtitle">Longitudinal Clinical Investigation Intelligence System</span>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <PatientList selectedPatientId={selectedPatientId} onSelectPatient={setSelectedPatientId} />
          <AlertsPanel onSelectPatient={setSelectedPatientId} />
        </aside>

        <main className="main">
          {selectedPatientId ? (
            <>
              <h2>{selectedPatientId}</h2>
              <TrendChart series={trend} />
            </>
          ) : (
            <p className="muted">Select a patient to view their longitudinal lab trends.</p>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
