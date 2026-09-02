import { severityColor } from "../severity";
import { timeAgo } from "../utils/time";
import { IconBed, IconHeart, IconSpo2, IconThermometer } from "./icons";

function StatTile({ icon, label, value, unit }) {
  return (
    <div className="stat-tile">
      <span className="stat-icon">{icon}</span>
      <div>
        <div className="stat-value">
          {value != null ? value : "—"}
          {value != null && unit && <span className="stat-unit">{unit}</span>}
        </div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  );
}

export default function PatientHeader({ patient }) {
  const severity = patient.worst_active_severity;
  const color = severityColor(severity || "stable");

  return (
    <div className="patient-header">
      <div className="patient-header-top">
        <div className="patient-ring patient-ring-lg" style={{ "--ring-color": color }}>
          {patient.name.split(" ").map((n) => n[0]).slice(0, 2).join("")}
        </div>
        <div>
          <h2 className="patient-header-name">{patient.name}</h2>
          <div className="patient-header-meta">
            <IconBed /> Bed {patient.bed || "—"} · {patient.id}
          </div>
        </div>
        <div className="patient-header-status" style={{ color }}>
          <span className="status-dot" style={{ backgroundColor: color }} />
          {severity ? `${severity.toUpperCase()} — ${patient.active_alert_count} active` : "Stable"}
        </div>
      </div>

      {patient.worst_active_alert_message && (
        <div className="patient-header-banner" style={{ borderColor: color }}>
          {patient.worst_active_alert_message}
        </div>
      )}

      <div className="stat-tiles">
        <StatTile icon={<IconSpo2 />} label="SpO2" value={patient.vitals.spo2} unit="%" />
        <StatTile icon={<IconHeart />} label="Heart Rate" value={patient.vitals.heart_rate} unit=" bpm" />
        <StatTile icon={<IconThermometer />} label="Temp" value={patient.vitals.temperature} unit="°C" />
        <div className="stat-tile">
          <div>
            <div className="stat-value stat-value-sm">
              {patient.last_lab_result ? timeAgo(patient.last_lab_result.collected_at) : "—"}
            </div>
            <div className="stat-label">Last lab update</div>
          </div>
        </div>
      </div>
    </div>
  );
}
