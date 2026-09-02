import {
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  TimeScale,
  Title,
  Tooltip,
} from "chart.js";
import "chartjs-adapter-date-fns";
import zoomPlugin from "chartjs-plugin-zoom";
import { useMemo } from "react";
import { Line } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  TimeScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  zoomPlugin
);

const SERIES_COLORS = ["#4f8cff", "#f79009", "#12b76a", "#a78bfa", "#f04438"];

export default function TrendChart({ series }) {
  const isDark = useMemo(
    () => typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches,
    []
  );
  const textColor = isDark ? "#b4bbcc" : "#4b5567";
  const gridColor = isDark ? "rgba(255,255,255,0.06)" : "rgba(16,20,31,0.06)";

  if (!series || series.length === 0) {
    return (
      <div className="chart-card">
        <p className="muted">No lab results for this patient yet.</p>
      </div>
    );
  }

  const data = {
    datasets: series.map((s, i) => ({
      label: `${s.test_name}${s.unit ? ` (${s.unit})` : ""}`,
      data: s.points.map((p) => ({ x: p.collected_at, y: p.value })),
      borderColor: SERIES_COLORS[i % SERIES_COLORS.length],
      backgroundColor: SERIES_COLORS[i % SERIES_COLORS.length],
      pointRadius: 4,
      pointHoverRadius: 6,
      borderWidth: 2.5,
      tension: 0.25,
    })),
  };

  const options = {
    responsive: true,
    interaction: { mode: "nearest", intersect: false },
    scales: {
      x: {
        type: "time",
        time: { unit: "day" },
        grid: { color: gridColor },
        ticks: { color: textColor },
      },
      y: {
        grid: { color: gridColor },
        ticks: { color: textColor },
      },
    },
    plugins: {
      legend: {
        position: "top",
        align: "start",
        labels: { color: textColor, usePointStyle: true, boxWidth: 8, padding: 16 },
      },
      tooltip: {
        backgroundColor: isDark ? "#1a2032" : "#ffffff",
        titleColor: isDark ? "#f5f7fb" : "#10141f",
        bodyColor: textColor,
        borderColor: isDark ? "#232a3d" : "#e2e6f0",
        borderWidth: 1,
        padding: 10,
        cornerRadius: 8,
      },
      zoom: {
        pan: { enabled: true, mode: "x" },
        zoom: {
          wheel: { enabled: true },
          pinch: { enabled: true },
          mode: "x",
        },
      },
    },
  };

  return (
    <div className="chart-card">
      <div className="panel-header">
        <h2>Longitudinal Lab Trend</h2>
        <span className="muted">scroll to zoom · drag to pan</span>
      </div>
      <Line data={data} options={options} />
    </div>
  );
}
