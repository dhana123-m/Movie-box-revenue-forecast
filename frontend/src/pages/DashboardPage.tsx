import { Link } from "react-router-dom";
import {
  ArrowRight,
  BrainCircuit,
  CircleDollarSign,
  Clock,
  Film,
  Star,
  TrendingUp,
} from "lucide-react";
import { Card, ErrorBlock, LoadingBlock, StatCard } from "../components/ui";
import { api } from "../services/api";
import { useApi } from "../hooks/useApi";
import { formatCompact, formatCurrency, formatDate } from "../utils/format";

export function DashboardPage() {
  const overview = useApi(() => api.overview(), []);
  const top = useApi(() => api.topMovies(5), []);
  const info = useApi(() => api.modelInfo(), []);
  const months = useApi(() => api.releaseMonths(), []);

  if (overview.loading || top.loading || info.loading) return <LoadingBlock label="Loading dashboard…" />;
  if (overview.error || top.error || info.error) {
    return (
      <ErrorBlock
        code={overview.error?.code ?? top.error?.code ?? info.error?.code}
        message={overview.error?.message ?? top.error?.message ?? info.error?.message}
        onRetry={() => {
          overview.refetch();
          top.refetch();
          info.refetch();
        }}
      />
    );
  }

  const d = overview.data;
  const bestMonth = months.data?.reduce((a, b) => (b.total_revenue > a.total_revenue ? b : a));
  const worstMonth = months.data?.reduce((a, b) => (b.total_revenue < a.total_revenue ? b : a));

  return (
    <div className="space-y-6">
      <div className="animate-fade-up">
        <h1 className="text-2xl font-extrabold tracking-tight text-zinc-100">
          Box Office <span className="gradient-text">Forecast</span> Dashboard
        </h1>
        <p className="mt-1 text-sm text-zinc-400">
          Predictive analytics powered by a deep neural network trained on {d?.total_movies.toLocaleString()} movies.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Movies Analyzed"
          value={d?.total_movies.toLocaleString() ?? "—"}
          sub={d?.year_min ? `${d.year_min} – ${d.year_max}` : undefined}
          icon={<Film className="h-5 w-5" />}
          tone="violet"
        />
        <StatCard
          label="Total Revenue"
          value={formatCurrency(d?.total_revenue)}
          sub={`Avg ${formatCurrency(d?.avg_revenue)}`}
          icon={<CircleDollarSign className="h-5 w-5" />}
          tone="emerald"
        />
        <StatCard
          label="Avg Budget"
          value={formatCurrency(d?.avg_budget)}
          sub={`Avg ROI ${d?.avg_roi?.toFixed(2) ?? "—"}x`}
          icon={<TrendingUp className="h-5 w-5" />}
          tone="cyan"
        />
        <StatCard
          label="Top Grosser"
          value={d?.highest_revenue_movie ? (d.highest_revenue_movie.length > 14 ? d.highest_revenue_movie.slice(0, 14) + "…" : d.highest_revenue_movie) : "—"}
          sub={d?.highest_revenue ? formatCurrency(d.highest_revenue) : undefined}
          icon={<Star className="h-5 w-5" />}
          tone="amber"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="section-title">Top Grossing Movies</h2>
              <p className="section-sub">Highest worldwide box office revenue in the dataset</p>
            </div>
            <Link to="/analytics" className="btn-ghost !px-3 !py-1.5 text-xs">
              Analytics <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
          <div className="space-y-3">
            {top.data?.map((m, i) => {
              const max = top.data?.[0]?.revenue ?? 1;
              return (
                <div key={m.title} className="flex items-center gap-4">
                  <span className="w-5 text-right font-mono text-sm font-bold text-zinc-500">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate text-sm font-semibold text-zinc-200">{m.title}</span>
                      <span className="shrink-0 text-sm font-bold text-emerald-300">
                        {formatCurrency(m.revenue)}
                      </span>
                    </div>
                    <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500"
                        style={{ width: `${(m.revenue / max) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        <div className="space-y-6">
          <Card>
            <h2 className="section-title">🎯 Make a Forecast</h2>
            <p className="mt-1 text-sm text-zinc-400">
              Enter your movie details and get an instant box-office revenue prediction.
            </p>
            <Link to="/forecast" className="btn-primary mt-4 w-full">
              <BrainCircuit className="h-4 w-4" /> Open Forecast
            </Link>
          </Card>
          <Card>
            <h2 className="section-title">📈 Release Season</h2>
            <p className="mt-1 text-sm text-zinc-400">
              Months with the strongest box-office performance.
            </p>
            <div className="mt-4 space-y-3">
              <div className="flex items-center justify-between rounded-xl bg-emerald-500/10 px-3 py-2.5">
                <div>
                  <div className="text-xs text-zinc-400">Best month</div>
                  <div className="text-sm font-bold text-emerald-300">
                    {bestMonth?.label} <span className="font-normal text-zinc-500">({bestMonth?.movie_count} films)</span>
                  </div>
                </div>
                <span className="text-sm font-bold">{formatCurrency(bestMonth?.total_revenue)}</span>
              </div>
              <div className="flex items-center justify-between rounded-xl bg-rose-500/10 px-3 py-2.5">
                <div>
                  <div className="text-xs text-zinc-400">Weakest month</div>
                  <div className="text-sm font-bold text-rose-300">
                    {worstMonth?.label} <span className="font-normal text-zinc-500">({worstMonth?.movie_count} films)</span>
                  </div>
                </div>
                <span className="text-sm font-bold">{formatCurrency(worstMonth?.total_revenue)}</span>
              </div>
            </div>
          </Card>
        </div>
      </div>

      <Card>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="section-title">🧠 Model Summary</h2>
            <p className="section-sub">
              Trained {info.data?.training_date ? `on ${formatDate(info.data.training_date)}` : "recently"} ·{" "}
              {info.data?.framework}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="chip">v{info.data?.model_version}</span>
            <span className="chip">{info.data?.model_type}</span>
            <span className="chip">{info.data?.feature_count} features</span>
            <span className="chip">
              <Clock className="h-3 w-3" />
              {info.data?.dataset?.rows_used ? `${info.data.dataset.rows_used.toLocaleString()} training rows` : "—"}
            </span>
          </div>
          <Link to="/model" className="btn-ghost text-xs">
            Full metrics <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            { l: "Format", v: formatCompact(info.data?.dataset?.rows_used) + " movies" },
            { l: "Span", v: d?.year_min ? `${d.year_min}–${d.year_max}` : "—" },
            { l: "Target", v: info.data?.target_variable ?? "—" },
            { l: "Thresholds", v: Object.keys(info.data?.performance_thresholds ?? {}).length + " classes" },
          ].map((s) => (
            <div key={s.l} className="rounded-xl bg-white/[0.03] px-3 py-2.5">
              <div className="text-[11px] uppercase tracking-wider text-zinc-500">{s.l}</div>
              <div className="mt-0.5 text-sm font-semibold text-zinc-200">{s.v}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
