import { useEffect, useState } from "react";
import { acknowledgeAlert, getAlerts } from "../api/client";
import SeverityBadge from "./SeverityBadge";

const REFRESH_MS = 5000;

export default function AlertsPanel({ onSelectPatient }) {
  const [alerts, setAlerts] = useState([]);
  const [expandedId, setExpandedId] = useState(null);
  const [error, setError] = useState(null);

  const refresh = () => {
    getAlerts({ activeOnly: true })
      .then(setAlerts)
      .catch(() => setError("Could not reach LCIIS API"));
  };

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, REFRESH_MS);
    return () => clearInterval(id);
  }, []);

  const handleAck = async (alertId) => {
    await acknowledgeAlert(alertId, "clinician@dashboard");
    refresh();
  };

  return (
    <div className="panel">
      <h2>Active Alerts</h2>
      {error && <p className="error">{error}</p>}
      {alerts.length === 0 && !error && <p className="muted">No active alerts.</p>}
      <ul className="alert-list">
        {alerts.map((alert) => (
          <li key={alert.id} className={`alert-item severity-${alert.severity}`}>
            <div className="alert-row" onClick={() => setExpandedId(expandedId === alert.id ? null : alert.id)}>
              <SeverityBadge severity={alert.severity} />
              <button
                className="link-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectPatient(alert.patient_id);
                }}
              >
                {alert.patient_id}
              </button>
              <span className="alert-message">{alert.message}</span>
              <span className="alert-source">{alert.source === "ml_engine" ? "ML" : "Rule"}</span>
            </div>
            {expandedId === alert.id && (
              <div className="alert-details">
                {alert.explanation && <p>{alert.explanation}</p>}
                <p className="muted">
                  Triggered {new Date(alert.triggered_at).toLocaleString()}
                  {alert.risk_score != null && ` · risk score ${alert.risk_score.toFixed(2)}`}
                </p>
                <button onClick={() => handleAck(alert.id)}>Acknowledge</button>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
