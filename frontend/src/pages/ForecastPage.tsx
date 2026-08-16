import { useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import { PredictionForm } from "../components/forecast/PredictionForm";
import { PredictionResultCard } from "../components/forecast/PredictionResultCard";
import { Badge, Card, ErrorBlock, LoadingBlock } from "../components/ui";
import { api } from "../services/api";
import { useApi } from "../hooks/useApi";
import { classificationTone } from "../utils/format";
import type { BatchResult, PredictionResult, PredictRequest } from "../types";

export function ForecastPage() {
  const filters = useApi(() => api.filtersSummary(), []);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [batch, setBatch] = useState<BatchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [csvError, setCsvError] = useState<string | null>(null);
  const [csvLoading, setCsvLoading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (payload: PredictRequest) => {
    setLoading(true);
    setError(null);
    setBatch(null);
    try {
      setResult(await api.predict(payload));
    } catch (e) {
      const err = e as { code: string; message: string; fields?: Record<string, string> | null };
      const fieldMsg = err.fields ? Object.entries(err.fields).map(([k, v]) => `${k}: ${v}`).join(" · ") : null;
      setError(fieldMsg ? `${err.message} — ${fieldMsg}` : err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCsv = async (file: File) => {
    setCsvLoading(true);
    setCsvError(null);
    try {
      const res = await api.predictCsv(file);
      setBatch(res);
      setResult(null);
    } catch (e) {
      setCsvError((e as { message: string }).message);
    } finally {
      setCsvLoading(false);
    }
  };

  if (filters.loading) return <LoadingBlock label="Loading forecast workspace…" />;
  if (filters.error) {
    return (
      <ErrorBlock code={filters.error.code} message={filters.error.message} onRetry={filters.refetch} />
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-zinc-100">
          Revenue <span className="gradient-text">Forecast</span>
        </h1>
        <p className="mt-1 text-sm text-zinc-400">
          Predict worldwide box office revenue from budget, release window, audience signals and cast & crew.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <div className="space-y-6">
          <PredictionForm filters={filters.data} onSubmit={handleSubmit} loading={loading} />

          <section className="glass p-5">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="section-title">📦 Batch Prediction (CSV)</h3>
                <p className="section-sub">Upload a CSV of movies to predict in bulk</p>
              </div>
              <UploadCloud className="h-5 w-5 text-zinc-500" />
            </div>
            <input
              ref={fileRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleCsv(f);
                e.target.value = "";
              }}
            />
            <button
              className="btn-ghost mt-4 w-full"
              disabled={csvLoading}
              onClick={() => fileRef.current?.click()}
            >
              {csvLoading ? "Processing…" : "Choose CSV file"}
            </button>
            <p className="mt-2 text-center text-[11px] text-zinc-600">
              Columns: title, budget, runtime, genres (Action|Drama), release_month, release_day,
              production_company, director, lead_actors, rating, vote_count, popularity
            </p>
            {csvError && <p className="mt-3 rounded-lg bg-rose-500/10 px-3 py-2 text-xs text-rose-300">{csvError}</p>}
          </section>
        </div>

        <div>
          {error && <ErrorBlock message={error} />}

          {loading && (
            <div className="glass flex items-center justify-center gap-3 py-20">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-violet-400 border-t-transparent" />
              <span className="text-sm text-zinc-400">Running inference…</span>
            </div>
          )}

          {result && !loading && <PredictionResultCard result={result} />}

          {batch && !loading && (
            <div className="animate-fade-up space-y-4">
              <div className="glass grid grid-cols-3 gap-3 p-5">
                {[
                  { l: "Total rows", v: batch.total_rows, t: "text-zinc-100" },
                  { l: "Successful", v: batch.successful, t: "text-emerald-300" },
                  { l: "Failed", v: batch.failed, t: batch.failed > 0 ? "text-rose-300" : "text-zinc-100" },
                ].map((s) => (
                  <div key={s.l} className="text-center">
                    <div className={`text-2xl font-extrabold ${s.t}`}>{s.v}</div>
                    <div className="text-[11px] uppercase tracking-wider text-zinc-500">{s.l}</div>
                  </div>
                ))}
              </div>

              <Card className="overflow-hidden !p-0">
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[560px] text-left text-sm">
                    <thead>
                      <tr className="border-b border-white/10 text-[11px] uppercase tracking-wider text-zinc-500">
                        <th className="px-4 py-3 font-semibold">#</th>
                        <th className="px-4 py-3 font-semibold">Movie</th>
                        <th className="px-4 py-3 font-semibold">Predicted Revenue</th>
                        <th className="px-4 py-3 font-semibold">Verdict</th>
                        <th className="px-4 py-3 font-semibold">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {batch.results.map((r) => (
                        <tr key={r.row} className="border-b border-white/5 transition hover:bg-white/[0.03]">
                          <td className="px-4 py-3 font-mono text-xs text-zinc-600">{r.row}</td>
                          <td className="px-4 py-3 font-semibold text-zinc-100">{r.title ?? "—"}</td>
                          <td className="px-4 py-3 font-bold text-zinc-100">
                            {r.predicted_revenue_usd ?? "—"}
                          </td>
                          <td className="px-4 py-3">
                            {r.performance_category ? (
                              <Badge className={classificationTone(r.performance_category)}>
                                {r.performance_category.replace("_", " ")}
                              </Badge>
                            ) : (
                              <span className="text-zinc-600">—</span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            {r.status === "success" ? (
                              <Badge className="border-emerald-400/40 bg-emerald-400/10 text-emerald-300">✓ OK</Badge>
                            ) : (
                              <div className="text-xs text-rose-300">{r.error}</div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            </div>
          )}

          {!result && !batch && !loading && !error && (
            <div className="glass flex flex-col items-center justify-center gap-3 py-24 text-center">
              <div className="text-4xl">🎬</div>
              <p className="text-sm font-semibold text-zinc-300">Your prediction will appear here</p>
              <p className="max-w-sm text-xs text-zinc-500">
                Fill the form with your movie details and hit “Predict Box Office Revenue”.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
