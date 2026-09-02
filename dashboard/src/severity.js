export const SEVERITY_COLORS = {
  red: "#f04438",
  amber: "#f79009",
  yellow: "#eaaa08",
  stable: "#12b76a",
};

export function severityColor(severity) {
  return SEVERITY_COLORS[severity] || SEVERITY_COLORS.stable;
}
