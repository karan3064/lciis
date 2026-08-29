const COLORS = {
  red: "#d92d20",
  amber: "#dc6803",
  yellow: "#eaaa08",
};

export default function SeverityBadge({ severity }) {
  const color = COLORS[severity] || "#667085";
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 10px",
        borderRadius: 12,
        fontSize: 12,
        fontWeight: 700,
        letterSpacing: 0.4,
        textTransform: "uppercase",
        color: "#fff",
        backgroundColor: color,
      }}
    >
      {severity}
    </span>
  );
}
