import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import {
  BarChart3,
  BrainCircuit,
  Clapperboard,
  Film,
  Gauge,
  LayoutDashboard,
  Menu,
  Search,
  Settings2,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../../services/api";
import type { HealthStatus } from "../../types";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/forecast", label: "Revenue Forecast", icon: BrainCircuit },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/movies", label: "Movie Explorer", icon: Film },
  { to: "/model", label: "Model Performance", icon: Gauge },
  { to: "/settings", label: "Settings", icon: Settings2 },
];

function Brand() {
  return (
    <div className="flex items-center gap-3 px-2 py-5">
      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 shadow-glow">
        <Clapperboard className="h-5 w-5 text-white" />
      </div>
      <div className="leading-tight">
        <div className="text-sm font-extrabold tracking-tight text-zinc-100">BoxOffice</div>
        <div className="text-[11px] font-medium text-zinc-500">Revenue Forecast</div>
      </div>
    </div>
  );
}

export function Layout({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null));
    const id = setInterval(() => {
      api.health().then(setHealth).catch(() => setHealth(null));
    }, 20000);
    return () => clearInterval(id);
  }, []);

  const sidebar = (
    <div className="flex h-full flex-col">
      <Brand />
      <nav className="flex-1 space-y-1 px-3">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={() => setOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                isActive
                  ? "bg-gradient-to-r from-violet-600/30 to-indigo-600/20 text-violet-200 shadow-glow"
                  : "text-zinc-400 hover:bg-white/5 hover:text-zinc-200"
              }`
            }
          >
            <Icon className="h-[18px] w-[18px]" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-white/10 p-4">
        <div className="flex items-center justify-between text-xs">
          <span className="text-zinc-500">API status</span>
          <span className="flex items-center gap-1.5 font-semibold">
            <span
              className={`h-2 w-2 rounded-full ${
                health?.status === "healthy" ? "bg-emerald-400 shadow-[0_0_8px_2px_rgba(52,211,153,0.6)]" : "bg-rose-500"
              }`}
            />
            <span className={health?.status === "healthy" ? "text-emerald-300" : "text-rose-400"}>
              {health?.status === "healthy" ? "Online" : "Offline"}
            </span>
          </span>
        </div>
        {health?.movies_in_database != null && (
          <p className="mt-1.5 text-[11px] text-zinc-600">
            {health.movies_in_database.toLocaleString()} movies · model v{health.model_version ?? "—"}
          </p>
        )}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen lg:pl-64">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 border-r border-white/10 bg-cinema-900/80 backdrop-blur lg:block">
        {sidebar}
      </aside>

      {open && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/70" onClick={() => setOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-64 border-r border-white/10 bg-cinema-900">
            {sidebar}
          </aside>
        </div>
      )}

      <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-white/10 bg-cinema-950/80 px-4 py-3 backdrop-blur lg:px-8">
        <button className="btn-ghost !px-2.5 !py-2 lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu">
          <Menu className="h-5 w-5" />
        </button>
        <div className="flex flex-1 items-center gap-3">
          <div className="relative hidden max-w-sm flex-1 sm:block">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
            <input
              className="input !pl-9"
              placeholder="Search movies…"
              onKeyDown={(e) => {
                if (e.key === "Enter" && e.currentTarget.value.trim()) {
                  window.location.hash = "#/movies?search=" + encodeURIComponent(e.currentTarget.value.trim());
                }
              }}
            />
          </div>
        </div>
        <button
          className="btn-ghost !px-2.5 !py-2 lg:hidden"
          onClick={() => setOpen(false)}
          aria-label="Close menu"
        >
          <X className="h-5 w-5" />
        </button>
        <div className="hidden items-center gap-2 lg:flex">
          <span className="chip">🎬 TMDB 5000</span>
          <span className="chip">🤖 Deep Learning</span>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 lg:px-8">{children}</main>

      <footer className="mx-auto max-w-7xl px-4 pb-8 pt-4 lg:px-8">
        <p className="text-center text-xs text-zinc-600">
          Movie Box Office Revenue Forecast · DNN + FastAPI + React · Mini Project
        </p>
      </footer>
    </div>
  );
}
