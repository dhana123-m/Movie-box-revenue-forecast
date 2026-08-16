import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import { Badge, Card, EmptyState, LoadingBlock, ProgressBar } from "../components/ui";
import { api } from "../services/api";
import { useApi } from "../hooks/useApi";
import { classificationTone, formatCurrency, formatDate, formatRoi } from "../utils/format";
import type { MovieSummary } from "../types";

const SORTS = [
  { key: "revenue", label: "Revenue" },
  { key: "budget", label: "Budget" },
  { key: "rating", label: "Rating" },
  { key: "year", label: "Year" },
  { key: "popularity", label: "Popularity" },
  { key: "roi", label: "ROI" },
  { key: "title", label: "Title" },
];

export function MovieExplorerPage() {
  const [params] = useSearchParams();
  const initialSearch = params.get("search") ?? "";

  const [search, setSearch] = useState(initialSearch);
  const [genre, setGenre] = useState("");
  const [yearFrom, setYearFrom] = useState("");
  const [yearTo, setYearTo] = useState("");
  const [sortBy, setSortBy] = useState("revenue");
  const [order, setOrder] = useState<"desc" | "asc">("desc");
  const [page, setPage] = useState(1);
  const perPage = 15;

  const [genres, setGenres] = useState<string[]>([]);
  const [years, setYears] = useState<{ min: number; max: number } | null>(null);

  useEffect(() => {
    api.filtersSummary().then((f) => {
      setGenres(f.genres);
      setYears({ min: f.year_min ?? 1960, max: f.year_max ?? 2020 });
    }).catch(() => undefined);
  }, []);

  const query = useMemo(
    () => ({
      page,
      per_page: perPage,
      sort_by: sortBy,
      order,
      genre: genre || undefined,
      search: search.trim() || undefined,
      year_from: yearFrom ? Number(yearFrom) : undefined,
      year_to: yearTo ? Number(yearTo) : undefined,
    }),
    [page, perPage, sortBy, order, genre, search, yearFrom, yearTo],
  );

  const { data, loading, error } = useApi(() => api.movies(query), [
    page,
    sortBy,
    order,
    genre,
    search,
    yearFrom,
    yearTo,
  ]);

  useEffect(() => {
    setPage(1);
  }, [sortBy, order, genre, search, yearFrom, yearTo]);

  useEffect(() => {
    setSearch(initialSearch);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialSearch]);

  const applySearch = () => {
    setSearch(search);
    setPage(1);
  };

  const toggleOrder = () => setOrder((o) => (o === "desc" ? "asc" : "desc"));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-zinc-100">
          Movie <span className="gradient-text">Explorer</span>
        </h1>
        <p className="mt-1 text-sm text-zinc-400">
          Browse and filter the {data?.total?.toLocaleString() ?? "3,164"} movies in the database
        </p>
      </div>

      <Card>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
          <div className="relative xl:col-span-2">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
            <input
              className="input !pl-9"
              placeholder="Search by title, director…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && applySearch()}
            />
          </div>
          <select className="input" value={genre} onChange={(e) => setGenre(e.target.value)}>
            <option value="">All genres</option>
            {genres.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
          <div className="grid grid-cols-2 gap-2">
            <input
              type="number"
              className="input !py-2"
              placeholder={years ? `${years.min}` : "From"}
              value={yearFrom}
              onChange={(e) => setYearFrom(e.target.value)}
            />
            <input
              type="number"
              className="input !py-2"
              placeholder={years ? `${years.max}` : "To"}
              value={yearTo}
              onChange={(e) => setYearTo(e.target.value)}
            />
          </div>
          <div className="grid grid-cols-[1fr_auto] gap-2">
            <select className="input" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
              {SORTS.map((s) => (
                <option key={s.key} value={s.key}>
                  Sort: {s.label}
                </option>
              ))}
            </select>
            <button className="btn-ghost !px-3" onClick={toggleOrder} title="Toggle order">
              {order === "desc" ? "↓" : "↑"}
            </button>
          </div>
        </div>
      </Card>

      {loading && <LoadingBlock label="Fetching movies…" />}
      {error && <div className="glass px-4 py-3 text-sm text-rose-300">{error.message}</div>}

      {!loading && !error && data && (
        <>
          {data.items.length === 0 ? (
            <Card>
              <EmptyState title="No movies found" sub="Try adjusting your filters or search query." />
            </Card>
          ) : (
            <Card className="overflow-hidden !p-0">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[820px] text-left text-sm">
                  <thead>
                    <tr className="border-b border-white/10 text-[11px] uppercase tracking-wider text-zinc-500">
                      <th className="px-4 py-3 font-semibold">#</th>
                      <th className="px-4 py-3 font-semibold">Movie</th>
                      <th className="px-4 py-3 font-semibold">Genre</th>
                      <th className="px-4 py-3 font-semibold">Budget</th>
                      <th className="px-4 py-3 font-semibold">Revenue</th>
                      <th className="px-4 py-3 font-semibold">ROI</th>
                      <th className="px-4 py-3 font-semibold">Rating</th>
                      <th className="px-4 py-3 font-semibold">Verdict</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.map((m: MovieSummary, i: number) => (
                      <tr key={m.id} className="border-b border-white/5 transition hover:bg-white/[0.03]">
                        <td className="px-4 py-3 font-mono text-xs text-zinc-600">
                          {(data.page - 1) * data.per_page + i + 1}
                        </td>
                        <td className="px-4 py-3">
                          <div className="font-semibold text-zinc-100">{m.title}</div>
                          <div className="text-xs text-zinc-500">
                            {m.year ?? "—"} · {m.director || "Unknown director"}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex max-w-[220px] flex-wrap gap-1">
                            {(m.genres ?? []).slice(0, 2).map((g) => (
                              <span key={g} className="rounded-md bg-white/[0.06] px-1.5 py-0.5 text-[11px] text-zinc-400">
                                {g}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-zinc-300">{formatCurrency(m.budget)}</td>
                        <td className="px-4 py-3">
                          <div className="font-bold text-zinc-100">{formatCurrency(m.revenue)}</div>
                          <div className="text-[11px] text-zinc-500">{formatDate(m.release_date)}</div>
                        </td>
                        <td className="px-4 py-3 text-zinc-300">{formatRoi(m.roi)}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <span className="w-7 text-right font-mono text-xs text-zinc-300">
                              {m.rating != null ? m.rating.toFixed(1) : "—"}
                            </span>
                            <div className="hidden w-16 sm:block">
                              <ProgressBar value={((m.rating ?? 0) / 10) * 100} tone="emerald" />
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <Badge className={classificationTone(m.classification)}>
                            {m.classification.replace("_", " ")}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/10 px-4 py-3">
                <span className="text-xs text-zinc-500">
                  Page {data.page} of {data.total_pages} · {data.total.toLocaleString()} results
                </span>
                <div className="flex items-center gap-2">
                  <button className="btn-ghost !px-3 !py-1.5 text-xs" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                    <ChevronLeft className="h-4 w-4" /> Prev
                  </button>
                  <button
                    className="btn-ghost !px-3 !py-1.5 text-xs"
                    disabled={page >= data.total_pages}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    Next <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
