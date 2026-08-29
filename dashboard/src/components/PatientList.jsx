import { useEffect, useState } from "react";
import { getPatients } from "../api/client";

export default function PatientList({ selectedPatientId, onSelectPatient }) {
  const [patients, setPatients] = useState([]);

  useEffect(() => {
    getPatients().then(setPatients).catch(() => {});
  }, []);

  return (
    <div className="panel">
      <h2>Patients</h2>
      <ul className="patient-list">
        {patients.map((p) => (
          <li key={p.id}>
            <button
              className={p.id === selectedPatientId ? "patient-btn active" : "patient-btn"}
              onClick={() => onSelectPatient(p.id)}
            >
              {p.name} <span className="muted">· Bed {p.bed || "—"}</span>
            </button>
          </li>
        ))}
        {patients.length === 0 && <p className="muted">No patients yet.</p>}
      </ul>
    </div>
  );
}
