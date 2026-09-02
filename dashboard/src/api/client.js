import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_BASE_URL });

export const getPatients = () => api.get("/api/patients").then((r) => r.data);

export const getPatientSummaries = () =>
  api.get("/api/patients/summary").then((r) => r.data);

export const getPatientTrend = (patientId) =>
  api.get(`/api/patients/${patientId}/trend`).then((r) => r.data);

export const getAlerts = ({ activeOnly = true, patientId } = {}) =>
  api
    .get("/api/alerts", { params: { active_only: activeOnly, patient_id: patientId } })
    .then((r) => r.data);

export const acknowledgeAlert = (alertId, acknowledgedBy) =>
  api
    .post(`/api/alerts/${alertId}/ack`, { acknowledged_by: acknowledgedBy })
    .then((r) => r.data);
