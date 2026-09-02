import { severityColor } from "../severity";
import { timeAgo } from "../utils/time";
import { IconBed, IconHeart, IconSpo2, IconThermometer } from "./icons";

export default function PatientList({ patients, selectedPatientId, onSelectPatient }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Patients</h2>
        <span className="panel-count">{patients.length}</span>
      </div>
      <ul className="patient-list">
        {patients.map((p) => {
          const ringColor = severityColor(p.worst_active_severity || "stable");
          const active = p.id === selectedPatientId;
          return (
            <li key={p.id}>
              <button
                className={active ? "patient-card active" : "patient-card"}
                onClick={() => onSelectPatient(p.id)}
              >
                <span className="patient-ring" style={{ "--ring-color": ringColor }}>
                  {p.name.split(" ").map((n) => n[0]).slice(0, 2).join("")}
                </span>
                <span className="patient-body">
                  <span className="patient-top-row">
                    <span className="patient-name">{p.name}</span>
                    {p.active_alert_count > 0 && (
                      <span className="patient-alert-count" style={{ backgroundColor: ringColor }}>
                        {p.active_alert_count}
                      </span>
                    )}
                  </span>
                  <span className="patient-meta">
                    <IconBed /> Bed {p.bed || "—"}
                    {p.last_lab_result && (
                      <span className="patient-meta-sep">· updated {timeAgo(p.last_lab_result.collected_at)}</span>
                    )}
                  </span>
                  {(p.vitals.spo2 != null || p.vitals.heart_rate != null || p.vitals.temperature != null) && (
                    <span className="patient-vitals">
                      {p.vitals.spo2 != null && (
                        <span className="vital-chip">
                          <IconSpo2 /> {p.vitals.spo2}%
                        </span>
                      )}
                      {p.vitals.heart_rate != null && (
                        <span className="vital-chip">
                          <IconHeart /> {p.vitals.heart_rate}
                        </span>
                      )}
                      {p.vitals.temperature != null && (
                        <span className="vital-chip">
                          <IconThermometer /> {p.vitals.temperature}°
                        </span>
                      )}
                    </span>
                  )}
                </span>
              </button>
            </li>
          );
        })}
        {patients.length === 0 && <p className="muted">No patients yet.</p>}
      </ul>
    </div>
  );
}
