import type { ReactNode } from "react";

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`glass p-5 ${className}`}>{children}</div>;
}

export function StatCard({
  label,
  value,
  sub,
  icon,
  tone = "violet",
}: {
  label: string;
  value: string;
  sub?: string;
  icon?: ReactNode;
  tone?: "violet" | "cyan" | "amber" | "emerald" | "rose";
}) {
  const tones: Record<string, string> = {
    violet: "from-violet-500/20 to-indigo-500/10 text-violet-300",
    cyan: "from-cyan-500/20 to-sky-500/10 text-cyan-300",
    amber: "from-amber-500/20 to-orange-500/10 text-amber-300",
    emerald: "from-emerald-500/20 to-teal-500/10 text-emerald-300",
    rose: "from-rose-500/20 to-pink-500/10 text-rose-300",
  };
  return (
    <div className="glass glass-hover flex items-start gap-4 p-5">
      <div
        className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${tones[tone]}`}
      >
        {icon}
      </div>
      <div className="min-w-0">
        <div className="text-xs font-semibold uppercase tracking-wider text-zinc-400">{label}</div>
        <div className="mt-1 truncate text-2xl font-bold text-zinc-100">{value}</div>
        {sub && <div className="mt-0.5 truncate text-xs text-zinc-500">{sub}</div>}
      </div>
    </div>
  );
}

export function Spinner({ size = 24 }: { size?: number }) {
  return (
    <svg
      className="animate-spin text-violet-400"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-90"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

export function LoadingBlock({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="glass flex flex-col items-center justify-center gap-3 py-16">
      <Spinner size={32} />
      <p className="text-sm text-zinc-400">{label}</p>
    </div>
  );
}

export function ErrorBlock({
  message = "Something went wrong.",
  onRetry,
  code,
}: {
  message?: string;
  onRetry?: () => void;
  code?: string;
}) {
  return (
    <div className="glass flex flex-col items-center gap-3 border-rose-400/30 py-12 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-rose-500/15 text-2xl">⚠</div>
      <div>
        <p className="text-sm font-semibold text-rose-300">{code ?? "Error"}</p>
        <p className="mt-1 max-w-md text-sm text-zinc-400">{message}</p>
      </div>
      {onRetry && (
        <button className="btn-ghost mt-1" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function SkeletonRows({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="skeleton h-12 w-full" />
      ))}
    </div>
  );
}

export function EmptyState({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-14 text-center">
      <div className="text-3xl">🍿</div>
      <p className="text-sm font-semibold text-zinc-300">{title}</p>
      {sub && <p className="max-w-sm text-xs text-zinc-500">{sub}</p>}
    </div>
  );
}

export function Badge({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${className}`}
    >
      {children}
    </span>
  );
}

export function ProgressBar({ value, tone = "violet" }: { value: number; tone?: string }) {
  const colors: Record<string, string> = {
    violet: "from-violet-500 to-fuchsia-500",
    emerald: "from-emerald-500 to-teal-400",
    cyan: "from-cyan-500 to-sky-400",
    rose: "from-rose-500 to-orange-400",
  };
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
      <div
        className={`h-full rounded-full bg-gradient-to-r ${colors[tone] ?? colors.violet} transition-all duration-700`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}
