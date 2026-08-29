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

const SERIES_COLORS = ["#1570ef", "#dc6803", "#12b76a", "#7a5af8", "#d92d20"];

export default function TrendChart({ series }) {
  if (!series || series.length === 0) {
    return <p className="muted">No lab results for this patient yet.</p>;
  }

  const data = {
    datasets: series.map((s, i) => ({
      label: `${s.test_name}${s.unit ? ` (${s.unit})` : ""}`,
      data: s.points.map((p) => ({ x: p.collected_at, y: p.value })),
      borderColor: SERIES_COLORS[i % SERIES_COLORS.length],
      backgroundColor: SERIES_COLORS[i % SERIES_COLORS.length],
      tension: 0.2,
    })),
  };

  const options = {
    responsive: true,
    interaction: { mode: "nearest", intersect: false },
    scales: {
      x: { type: "time", time: { unit: "day" } },
      y: { title: { display: true, text: "Value" } },
    },
    plugins: {
      title: { display: true, text: "Longitudinal Lab Trend" },
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

  return <Line data={data} options={options} />;
}
