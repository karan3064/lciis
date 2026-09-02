import { useEffect, useState } from "react";
import { acknowledgeAlert, getAlerts } from "../api/client";
import { timeAgo } from "../utils/time";
import SeverityBadge from "./SeverityBadge";

const REFRESH_MS = 5000;

export default function AlertsPanel({ onSelectPatient }) {
  const [alerts, setAlerts] = useState([]);
  const [expandedId, setExpandedId] = useState(null);
  const [error, setError] = useState(null);

  const refresh = () => {
    getAlerts({ activeOnly: true })
      .then((data) => {
        setAlerts(data);
        setError(null);
      })
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
      <div className="panel-header">
        <h2>Active Alerts</h2>
        {alerts.length > 0 && <span className="panel-count panel-count-alert">{alerts.length}</span>}
      </div>
      {error && <p className="error">{error}</p>}
      {alerts.length === 0 && !error && <p className="muted">No active alerts — all patients stable.</p>}
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
              <span className="alert-source-tag">{alert.source === "ml_engine" ? "ML" : "Rule"}</span>
            </div>
            <p className="alert-message">{alert.message}</p>
            <p className="alert-timestamp">{timeAgo(alert.triggered_at)}</p>
            {expandedId === alert.id && (
              <div className="alert-details">
                {alert.explanation && <p>{alert.explanation}</p>}
                {alert.risk_score != null && (
                  <p className="muted">Risk score {alert.risk_score.toFixed(2)}</p>
                )}
                <button onClick={() => handleAck(alert.id)}>Acknowledge</button>
              </div>
            )}
            {expandedId !== alert.id && (
              <button className="expand-hint" onClick={() => setExpandedId(alert.id)}>
                Details
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
