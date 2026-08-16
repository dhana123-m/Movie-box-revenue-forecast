import { useState } from "react";
import {
  BudgetVsRevenueScatter,
  GenreBarChart,
  GenreDistributionChart,
  ReleaseMonthsChart,
  RevenueByYearChart,
  TopMoviesChart,
} from "../components/charts";
import { Card, ErrorBlock, LoadingBlock, StatCard } from "../components/ui";
import { api } from "../services/api";
import { useApi } from "../hooks/useApi";
import { formatCurrency } from "../utils/format";

export function AnalyticsPage() {
  const [yearRange, setYearRange] = useState("1960");
  const overview = useApi(() => api.overview(), []);
  const yearly = useApi(() => api.yearly(Number(yearRange)), [yearRange]);
  const genres = useApi(() => api.genres(), []);
  const scatter = useApi(() => api.budgetVsRevenue(300), []);
  const top = useApi(() => api.topMovies(10), []);
  const months = useApi(() => api.releaseMonths(), []);

  const loading = yearly.loading || genres.loading || scatter.loading || top.loading || months.loading;
  const error = yearly.error ?? genres.error ?? scatter.error ?? top.error ?? months.error;

  if (loading) return <LoadingBlock label="Loading analytics…" />;
  if (error) {
    return (
      <ErrorBlock
        code={error.code}
        message={error.message}
        onRetry={() => {
          yearly.refetch();
          genres.refetch();
          scatter.refetch();
          top.refetch();
          months.refetch();
        }}
      />
    );
  }

  const bestGenre = genres.data?.reduce((a, b) => (b.avg_revenue > a.avg_revenue ? b : a));
  const peakYear = yearly.data?.reduce((a, b) => (b.avg_revenue > a.avg_revenue ? b : a));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-zinc-100">
            Box Office <span className="gradient-text">Analytics</span>
          </h1>
          <p className="mt-1 text-sm text-zinc-400">Explore revenue trends across 56 years of cinema</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">From year</span>
          <select className="input !w-auto !py-1.5 text-xs" value={yearRange} onChange={(e) => setYearRange(e.target.value)}>
            {["1960", "1970", "1980", "1990", "2000", "2010"].map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Movies Analyzed"
          value={overview.data?.total_movies.toLocaleString() ?? "—"}
          sub={`${overview.data?.year_min ?? "—"} – ${overview.data?.year_max ?? "—"}`}
          tone="violet"
        />
        <StatCard
          label="Best Avg Revenue Genre"
          value={bestGenre?.genre ?? "—"}
          sub={bestGenre ? `${bestGenre.movie_count} films` : undefined}
          tone="cyan"
        />
        <StatCard
          label="Peak Year (avg)"
          value={peakYear?.year?.toString() ?? "—"}
          sub={formatCurrency(peakYear?.avg_revenue)}
          tone="emerald"
        />
        <StatCard
          label="Total Box Office"
          value={formatCurrency(overview.data?.total_revenue)}
          sub="Across all analyzed movies"
          tone="amber"
        />
      </div>

      <Card>
        <h2 className="section-title mb-1">Total Revenue by Year</h2>
        <p className="section-sub mb-4">Blue line = average revenue · purple area = total revenue</p>
        <RevenueByYearChart data={yearly.data ?? []} />
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="section-title mb-1">Average Revenue by Genre</h2>
          <p className="section-sub mb-4">Genres with the highest earning potential</p>
          <GenreBarChart data={genres.data ?? []} />
        </Card>
        <Card>
          <h2 className="section-title mb-1">Budget vs Revenue</h2>
          <p className="section-sub mb-4">300-movie sample · higher is better</p>
          <BudgetVsRevenueScatter data={scatter.data ?? []} />
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="section-title mb-1">Top 10 Highest Grossing</h2>
          <p className="section-sub mb-4">All-time worldwide box office</p>
          <TopMoviesChart data={top.data ?? []} />
        </Card>
        <Card>
          <h2 className="section-title mb-1">Revenue Share by Genre</h2>
          <p className="section-sub mb-4">Which genres dominate total earnings</p>
          <GenreDistributionChart data={genres.data ?? []} />
        </Card>
      </div>

      <Card>
        <h2 className="section-title mb-1">Revenue by Release Month</h2>
        <p className="section-sub mb-4">Summer & holiday season advantage</p>
        <ReleaseMonthsChart data={months.data ?? []} />
      </Card>
    </div>
  );
}
