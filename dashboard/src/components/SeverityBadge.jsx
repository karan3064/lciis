import { severityColor } from "../severity";

export default function SeverityBadge({ severity }) {
  return (
    <span className="severity-badge" style={{ backgroundColor: severityColor(severity) }}>
      {severity}
    </span>
  );
}
