import { Link } from "react-router-dom";
import { BrainCircuit, CheckCircle2, CircleDollarSign, Ruler, Target } from "lucide-react";
import { ModelComparisonChart, TrainingCurvesChart } from "../components/charts";
import { Card, ErrorBlock, LoadingBlock, StatCard } from "../components/ui";
import { api } from "../services/api";
import { useApi } from "../hooks/useApi";
import { formatCurrency, formatR2 } from "../utils/format";

export function ModelPerformancePage() {
  const metrics = useApi(() => api.trainingMetrics(), []);
  const info = useApi(() => api.modelInfo(), []);

  const loading = metrics.loading || info.loading;
  const error = metrics.error ?? info.error;

  if (loading) return <LoadingBlock label="Loading model performance…" />;
  if (error) {
    return (
      <ErrorBlock
        code={error.code}
        message={error.message}
        onRetry={() => {
          metrics.refetch();
          info.refetch();
        }}
      />
    );
  }

  const m = metrics.data?.metrics;
  const dnn = m?.dnn;
  const dataset = m?.dataset;
  const comparison = m?.comparison ?? [];
  const history = metrics.data?.training_history;
  const bestValMae = history?.val_mae?.length ? Math.min(...history.val_mae) : null;

  const splitTotal = dataset ? dataset.train + dataset.validation + dataset.test : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-zinc-100">
          Model <span className="gradient-text">Performance</span>
        </h1>
        <p className="mt-1 text-sm text-zinc-400">
          Deep Neural Network vs. classical baselines · evaluated on a held-out test split
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Test R² (log)"
          value={formatR2(dnn?.r2_log)}
          sub={`${(100 * (dnn?.r2_log ?? 0)).toFixed(1)}% variance explained`}
          icon={<Target className="h-5 w-5" />}
          tone="violet"
        />
        <StatCard
          label="Test MAE"
          value={formatCurrency(dnn?.mae_revenue)}
          sub={`${dnn?.mae_log?.toFixed(4)} in log-space`}
          icon={<CircleDollarSign className="h-5 w-5" />}
          tone="emerald"
        />
        <StatCard
          label="Test RMSE"
          value={formatCurrency(dnn?.rmse_revenue)}
          sub={`${dnn?.rmse_log?.toFixed(4)} in log-space`}
          icon={<Ruler className="h-5 w-5" />}
          tone="cyan"
        />
        <StatCard
          label="Epochs Trained"
          value={history?.epochs?.toString() ?? "—"}
          sub={bestValMae != null ? `Best val MAE ${bestValMae.toFixed(4)}` : "—"}
          icon={<BrainCircuit className="h-5 w-5" />}
          tone="amber"
        />
      </div>

      <Card>
        <h2 className="section-title mb-1">DNN vs. Baselines — R² on log-revenue</h2>
        <p className="section-sub mb-4">
          The neural network competes with Random Forest, Gradient Boosting, XGBoost and Linear Regression.
        </p>
        <ModelComparisonChart
          data={comparison.map((c) => ({ model: c.model, label: c.model, r2_log: c.r2_log }))}
        />
        <div className="mt-6 overflow-x-auto">
          <table className="w-full min-w-[560px] text-left text-sm">
            <thead>
              <tr className="border-b border-white/10 text-[11px] uppercase tracking-wider text-zinc-500">
                <th className="py-2.5 pr-4 font-semibold">Model</th>
                <th className="py-2.5 pr-4 font-semibold">R² (log)</th>
                <th className="py-2.5 pr-4 font-semibold">RMSE (log)</th>
                <th className="py-2.5 font-semibold">MAE (revenue)</th>
              </tr>
            </thead>
            <tbody>
              {comparison.map((c) => {
                const isBest = c.r2_log === Math.max(...comparison.map((x) => x.r2_log));
                return (
                  <tr key={c.model} className="border-b border-white/5">
                    <td className="flex items-center gap-2 py-2.5 pr-4 font-medium text-zinc-200">
                      {isBest && <CheckCircle2 className="h-4 w-4 text-emerald-400" />}
                      {c.model}
                      {isBest && <span className="chip !text-[10px]">Best</span>}
                    </td>
                    <td className={`py-2.5 pr-4 font-mono ${isBest ? "font-bold text-emerald-300" : "text-zinc-400"}`}>
                      {c.r2_log.toFixed(4)}
                    </td>
                    <td className="py-2.5 pr-4 font-mono text-zinc-400">{c.rmse_log.toFixed(4)}</td>
                    <td className="py-2.5 font-mono text-zinc-400">{formatCurrency(c.mae_revenue)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      <Card>
        <h2 className="section-title mb-1">Training Curves</h2>
        <p className="section-sub mb-4">
          Loss and MAE over training epochs · early stopping on validation loss
        </p>
        <TrainingCurvesChart
          epochs={Array.from({ length: history?.loss?.length ?? 0 }, (_, i) => i + 1)}
          trainLoss={history?.loss ?? []}
          valLoss={history?.val_loss ?? []}
          trainMae={history?.mae ?? []}
          valMae={history?.val_mae ?? []}
        />
      </Card>

      <Card>
        <h2 className="section-title mb-1">Feature Importance</h2>
        <p className="section-sub mb-4">
          Permutation importance (drop in test MAE when a feature is shuffled) · top 10 of 34 inputs
        </p>
        <div className="space-y-2.5">
          {m?.feature_importance?.slice(0, 10).map((f) => {
            const max = m.feature_importance[0]?.importance ?? 1;
            const pct = Math.max(0, (f.importance / max) * 100);
            return (
              <div key={f.feature} className="flex items-center gap-3">
                <span className="w-40 shrink-0 truncate text-right text-xs font-medium text-zinc-300">
                  {f.feature}
                </span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/10">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-violet-500"
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className="w-16 shrink-0 font-mono text-[11px] text-zinc-500">
                  {f.importance.toFixed(4)}
                </span>
              </div>
            );
          })}
        </div>
        <p className="mt-4 text-xs text-zinc-500">
          Budget and audience signals (vote count, popularity) dominate — release timing and genre flags follow.
        </p>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="section-title mb-4">Dataset Split</h2>
          {dataset && splitTotal > 0 && (
            <div className="space-y-3">
              {[
                { l: "Training samples", v: dataset.train },
                { l: "Validation samples", v: dataset.validation },
                { l: "Test samples", v: dataset.test },
                { l: "Total samples", v: dataset.rows_used },
              ].map((s) => (
                <div key={s.l} className="flex items-center justify-between rounded-xl bg-white/[0.03] px-4 py-3">
                  <span className="text-sm text-zinc-400">{s.l}</span>
                  <span className="font-mono text-sm font-bold text-zinc-200">{s.v.toLocaleString()}</span>
                </div>
              ))}
              <div className="mt-4 h-3 w-full overflow-hidden rounded-full bg-white/10">
                <div className="flex h-full">
                  <div
                    className="bg-violet-500"
                    style={{ width: `${(dataset.train / splitTotal) * 100}%` }}
                  />
                  <div
                    className="bg-cyan-500"
                    style={{ width: `${(dataset.validation / splitTotal) * 100}%` }}
                  />
                  <div
                    className="bg-amber-400"
                    style={{ width: `${(dataset.test / splitTotal) * 100}%` }}
                  />
                </div>
              </div>
              <div className="flex gap-4 text-[11px] text-zinc-500">
                <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-violet-500" /> Train</span>
                <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-cyan-500" /> Validation</span>
                <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-amber-400" /> Test</span>
              </div>
              <p className="pt-2 text-xs text-zinc-500">{dataset.split}</p>
            </div>
          )}
        </Card>

        <Card>
          <h2 className="section-title mb-1">Model Details</h2>
          <p className="section-sub mb-4">Architecture and training configuration</p>
          <div className="space-y-3">
            {[
              { l: "Architecture", v: (m?.architecture?.layers ?? []).join(" → ") },
              { l: "Output", v: "1 unit (linear, log-revenue)" },
              { l: "Loss", v: `${m?.architecture?.loss ?? "Huber"} (Huber delta = 1.0)` },
              { l: "Optimizer", v: m?.architecture?.optimizer ?? "Adam" },
              { l: "Regularization", v: "L2 (1e-4) + Dropout (0.30/0.25/0.20/0.20)" },
              { l: "Early stopping", v: "patience 25 (validation loss)" },
              { l: "Features", v: `${info.data?.feature_count ?? 34} engineered inputs` },
            ].map((s) => (
              <div key={s.l} className="flex items-start justify-between gap-3 border-b border-white/5 pb-2.5">
                <span className="text-sm text-zinc-400">{s.l}</span>
                <span className="text-right text-sm font-medium text-zinc-200">{s.v}</span>
              </div>
            ))}
          </div>
          <Link to="/settings" className="btn-ghost mt-4 w-full text-xs">
            Retraining options →
          </Link>
        </Card>
      </div>
    </div>
  );
}
