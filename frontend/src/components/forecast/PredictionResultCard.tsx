import { ArrowDownRight, ArrowUpRight, Info } from "lucide-react";
import type { PredictionResult } from "../../types";
import { classificationTone, confidenceTone } from "../../utils/format";
import { Badge, Card, ProgressBar } from "../ui";

const CONF_COLORS = { high: "emerald", medium: "cyan", low: "rose" } as const;

export function PredictionResultCard({ result }: { result: PredictionResult }) {
  const tone = confidenceTone(result.confidence_score);
  const range = result.expected_range;
  const positiveContribs = result.contributions.filter((c) => c.impact === "positive").length;
  const neutralContribs = result.contributions.filter((c) => c.impact === "neutral").length;

  return (
    <div className="animate-fade-up space-y-5">
      <Card className="overflow-hidden border-violet-500/30">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Predicted Worldwide Box Office</p>
            <h2 className="mt-1 text-3xl font-extrabold tracking-tight text-zinc-100">
              {result.predicted_revenue_usd}
            </h2>
            <p className="mt-1 text-sm text-zinc-400">≈ {result.predicted_revenue_crore}</p>
          </div>
          <Badge className={`${classificationTone(result.performance_category)} px-3 py-1 text-sm`}>
            {result.performance_category.replace("_", " ")}
          </Badge>
        </div>

        <div className="mb-1.5 flex items-center justify-between text-xs">
          <span className="text-zinc-400">Model confidence</span>
          <span className="font-bold text-zinc-200">{result.confidence_score.toFixed(1)}%</span>
        </div>
        <ProgressBar value={result.confidence_score} tone={CONF_COLORS[tone]} />

        <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="rounded-xl bg-white/[0.03] px-4 py-3">
            <div className="text-[11px] uppercase tracking-wider text-zinc-500">Expected range</div>
            <div className="mt-1 text-sm font-bold text-zinc-200">
              {result.predicted_revenue_usd.startsWith("$")
                ? "$" + range.lower.toLocaleString(undefined, { maximumFractionDigits: 0 })
                : range.lower.toLocaleString()}{" "}
              –{" "}
              {result.predicted_revenue_usd.startsWith("$")
                ? "$" + range.upper.toLocaleString(undefined, { maximumFractionDigits: 0 })
                : range.upper.toLocaleString()}
            </div>
            <div className="text-xs text-zinc-500">95% interval</div>
          </div>
          <div className="rounded-xl bg-white/[0.03] px-4 py-3">
            <div className="text-[11px] uppercase tracking-wider text-zinc-500">Revenue / budget</div>
            <div className="mt-1 text-sm font-bold text-zinc-200">{result.revenue_budget_ratio.toFixed(2)}x</div>
            <div className="text-xs text-zinc-500">budget {result.budget.toLocaleString(undefined, { maximumFractionDigits: 0 })} USD</div>
          </div>
          <div className="rounded-xl bg-white/[0.03] px-4 py-3">
            <div className="text-[11px] uppercase tracking-wider text-zinc-500">Model</div>
            <div className="mt-1 text-sm font-bold text-zinc-200">{result.model}</div>
            <div className="text-xs text-zinc-500">version {result.model_version}</div>
          </div>
        </div>
      </Card>

      {result.contributions.length > 0 && (
        <Card>
          <div className="mb-1 flex items-center justify-between">
            <h3 className="section-title">🔍 Why this number?</h3>
            <span className="text-xs text-zinc-500">
              {positiveContribs} positive · {neutralContribs} neutral
            </span>
          </div>
          <p className="section-sub mb-4">Feature sensitivity — impact on predicted revenue vs. a neutral movie</p>
          <div className="space-y-3">
            {result.contributions.map((c) => {
              const max = Math.max(...result.contributions.map((x) => x.magnitude), 1e-6);
              const width = (c.magnitude / max) * 100;
              const positive = c.impact === "positive";
              const pct = Math.exp(c.magnitude) - 1;
              return (
                <div key={c.feature} className="flex items-center gap-3">
                  <span className="w-40 shrink-0 truncate text-xs font-medium text-zinc-400" title={c.label}>
                    {c.label}
                  </span>
                  <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-white/10">
                    <div
                      className={`h-full rounded-full ${
                        positive
                          ? "bg-gradient-to-r from-emerald-500 to-teal-400"
                          : c.impact === "neutral"
                            ? "bg-zinc-500/50"
                            : "bg-gradient-to-r from-rose-500 to-orange-400"
                      }`}
                      style={{
                        width: `${width}%`,
                        marginLeft: positive ? 0 : `${100 - width}%`,
                      }}
                    />
                  </div>
                  <span className="flex w-24 shrink-0 items-center justify-end gap-1 text-xs font-semibold">
                    {positive ? (
                      <ArrowUpRight className="h-3.5 w-3.5 text-emerald-400" />
                    ) : c.impact === "neutral" ? (
                      <span className="text-zinc-500">±</span>
                    ) : (
                      <ArrowDownRight className="h-3.5 w-3.5 text-rose-400" />
                    )}
                    <span
                      className={
                        positive ? "text-emerald-300" : c.impact === "neutral" ? "text-zinc-500" : "text-rose-300"
                      }
                    >
                      {positive ? "+" : ""}
                      {Math.abs(pct * 100).toFixed(1)}%
                    </span>
                  </span>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      <div className="flex items-start gap-2.5 rounded-xl border border-white/10 bg-white/[0.02] p-3.5 text-xs text-zinc-400">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-violet-400" />
        <p>{result.disclaimer}</p>
      </div>
    </div>
  );
}
