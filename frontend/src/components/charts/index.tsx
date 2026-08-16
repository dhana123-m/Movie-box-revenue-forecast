import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type {
  BudgetVsRevenuePoint,
  GenreStat,
  ReleaseMonthStat,
  TopMovieRow,
  YearlyStat,
} from "../../types";
import { formatCompact, formatCurrency } from "../../utils/format";

const AXIS = { stroke: "#52525b", fontSize: 11 } as const;
const GRID = { stroke: "#27272a", strokeDasharray: "4 4" } as const;
const TOOLTIP_STYLE = {
  backgroundColor: "#10101a",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: "12px",
  fontSize: 12,
  color: "#e4e4e7",
} as const;

const GENRE_COLORS = [
  "#8b5cf6", "#6366f1", "#22d3ee", "#fbbf24", "#34d399", "#f472b6",
  "#fb7185", "#60a5fa", "#a3e635", "#f97316", "#2dd4bf", "#c084fc",
  "#facc15", "#4ade80", "#f87171", "#818cf8", "#5eead4", "#fda4af",
];

export function RevenueByYearChart({ data }: { data: YearlyStat[] }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={data} margin={{ left: 8, right: 8, top: 8 }}>
        <defs>
          <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.6} />
            <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid {...GRID} vertical={false} />
        <XAxis dataKey="year" {...AXIS} tickLine={false} axisLine={false} />
        <YAxis
          {...AXIS}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: number) => formatCompact(v)}
        />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(value: number, name: string) => [
            name === "total_revenue" ? formatCurrency(value) : value,
            name === "total_revenue" ? "Revenue" : name,
          ]}
        />
        <Area
          type="monotone"
          dataKey="total_revenue"
          stroke="#8b5cf6"
          strokeWidth={2}
          fill="url(#revGrad)"
        />
        <Area
          type="monotone"
          dataKey="avg_revenue"
          stroke="#22d3ee"
          strokeWidth={1.5}
          strokeDasharray="5 4"
          fill="transparent"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function GenreBarChart({ data }: { data: GenreStat[] }) {
  return (
    <ResponsiveContainer width="100%" height={360}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
        <CartesianGrid {...GRID} horizontal={false} />
        <XAxis
          type="number"
          {...AXIS}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: number) => formatCompact(v)}
        />
        <YAxis type="category" dataKey="genre" {...AXIS} width={92} tickLine={false} axisLine={false} />
        <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: number) => formatCurrency(v)} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
        <Bar dataKey="avg_revenue" radius={[0, 6, 6, 0]} barSize={16}>
          {data.map((_, i) => (
            <Cell key={i} fill={GENRE_COLORS[i % GENRE_COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function BudgetVsRevenueScatter({ data }: { data: BudgetVsRevenuePoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={360}>
      <ScatterChart margin={{ left: 8, right: 16, top: 8 }}>
        <CartesianGrid {...GRID} />
        <XAxis
          type="number"
          dataKey="budget"
          name="Budget"
          {...AXIS}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: number) => formatCompact(v)}
        />
        <YAxis
          type="number"
          dataKey="revenue"
          name="Revenue"
          {...AXIS}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: number) => formatCompact(v)}
        />
        <ZAxis range={[30, 60]} />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          cursor={{ strokeDasharray: "4 4", stroke: "#52525b" }}
          formatter={(value: number, name: string) => [
            formatCurrency(value),
            name === "budget" ? "Budget" : "Revenue",
          ]}
        />
        <Scatter data={data} fill="#8b5cf6" fillOpacity={0.55} />
      </ScatterChart>
    </ResponsiveContainer>
  );
}

export function TopMoviesChart({ data }: { data: TopMovieRow[] }) {
  const chart = [...data].reverse();
  return (
    <ResponsiveContainer width="100%" height={Math.max(260, data.length * 46)}>
      <BarChart data={chart} layout="vertical" margin={{ left: 8, right: 24 }}>
        <CartesianGrid {...GRID} horizontal={false} />
        <XAxis
          type="number"
          {...AXIS}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: number) => formatCompact(v)}
        />
        <YAxis type="category" dataKey="title" {...AXIS} width={130} tickLine={false} axisLine={false} />
        <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: number) => formatCurrency(v)} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
        <Bar dataKey="revenue" radius={[0, 6, 6, 0]} barSize={18}>
          {chart.map((_, i) => (
            <Cell key={i} fill={GENRE_COLORS[(data.length - 1 - i) % GENRE_COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ReleaseMonthsChart({ data }: { data: ReleaseMonthStat[] }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ left: 8, right: 8, top: 8 }}>
        <CartesianGrid {...GRID} vertical={false} />
        <XAxis dataKey="label" {...AXIS} tickLine={false} axisLine={false} />
        <YAxis {...AXIS} tickLine={false} axisLine={false} tickFormatter={(v: number) => formatCompact(v)} />
        <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: number) => formatCurrency(v)} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
        <Bar dataKey="total_revenue" radius={[6, 6, 0, 0]} barSize={26}>
          {data.map((_, i) => (
            <Cell key={i} fill={i === 5 || i === 6 || i === 11 ? "#fbbf24" : "#6366f1"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function GenreDistributionChart({ data }: { data: GenreStat[] }) {
  const sorted = [...data].sort((a, b) => b.total_revenue - a.total_revenue).slice(0, 8);
  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie
          data={sorted}
          dataKey="total_revenue"
          nameKey="genre"
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={3}
          stroke="none"
        >
          {sorted.map((_, i) => (
            <Cell key={i} fill={GENRE_COLORS[i % GENRE_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: number) => formatCurrency(v)} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function ModelComparisonChart({ data }: { data: Array<{ model: string; r2_log: number }> }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ left: 8, right: 16, top: 8 }}>
        <CartesianGrid {...GRID} vertical={false} />
        <XAxis dataKey="label" {...AXIS} tickLine={false} axisLine={false} />
        <YAxis {...AXIS} tickLine={false} axisLine={false} domain={[0, 1]} tickFormatter={(v: number) => v.toFixed(2)} />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(v: number) => v.toFixed(4)}
          cursor={{ fill: "rgba(255,255,255,0.03)" }}
        />
        <Bar dataKey="r2_log" name="R² (log-revenue)" radius={[6, 6, 0, 0]} barSize={34}>
          {data.map((d, i) => (
            <Cell key={i} fill={d.model === "Deep Neural Network" ? "#8b5cf6" : "#3f3f46"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function TrainingCurvesChart({
  epochs,
  trainLoss,
  valLoss,
  trainMae,
  valMae,
}: {
  epochs: number[];
  trainLoss: number[];
  valLoss: number[];
  trainMae: number[];
  valMae: number[];
}) {
  const data = epochs.map((e, i) => ({
    epoch: e,
    train_loss: trainLoss[i],
    val_loss: valLoss[i],
    train_mae: trainMae[i],
    val_mae: valMae[i],
  }));
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">Loss (Huber)</p>
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={data} margin={{ left: 8, right: 16, top: 8 }}>
            <CartesianGrid {...GRID} vertical={false} />
            <XAxis dataKey="epoch" {...AXIS} tickLine={false} axisLine={false} />
            <YAxis {...AXIS} tickLine={false} axisLine={false} width={44} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Line type="monotone" dataKey="train_loss" name="Train loss" stroke="#8b5cf6" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="val_loss" name="Val loss" stroke="#22d3ee" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">Mean Abs Error (log)</p>
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={data} margin={{ left: 8, right: 16, top: 8 }}>
            <CartesianGrid {...GRID} vertical={false} />
            <XAxis dataKey="epoch" {...AXIS} tickLine={false} axisLine={false} />
            <YAxis {...AXIS} tickLine={false} axisLine={false} width={44} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Line type="monotone" dataKey="train_mae" name="Train MAE" stroke="#34d399" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="val_mae" name="Val MAE" stroke="#fbbf24" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
