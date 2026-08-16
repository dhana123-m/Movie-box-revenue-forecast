import { useMemo, useState } from "react";
import { Sparkles } from "lucide-react";
import type { FiltersSummary, PredictRequest } from "../../types";

export interface FormValues {
  title: string;
  budget: string;
  runtime: string;
  genres: string[];
  release_month: string;
  release_day: string;
  release_year: string;
  original_language: string;
  production_company: string;
  director: string;
  lead_actors: string;
  rating: string;
  vote_count: string;
  popularity: string;
}

export const EMPTY_FORM: FormValues = {
  title: "",
  budget: "",
  runtime: "",
  genres: [],
  release_month: "",
  release_day: "",
  release_year: "",
  original_language: "en",
  production_company: "",
  director: "",
  lead_actors: "",
  rating: "",
  vote_count: "",
  popularity: "",
};

export const DEMO_PRESETS: Record<string, Partial<FormValues>> = {
  "Blockbuster Action": {
    title: "Example: Titan Rising",
    budget: "180000000",
    runtime: "142",
    genres: ["Action", "Science Fiction", "Adventure"],
    release_month: "7",
    release_day: "18",
    release_year: "2026",
    original_language: "en",
    production_company: "Warner Bros.",
    director: "Christopher Nolan",
    lead_actors: "Leonardo DiCaprio|Tom Hardy|Cillian Murphy",
    rating: "8.2",
    vote_count: "45000",
    popularity: "120.0",
  },
  "Mid-Budget Drama": {
    title: "Example: The Quiet Hour",
    budget: "25000000",
    runtime: "118",
    genres: ["Drama", "Mystery"],
    release_month: "10",
    release_day: "3",
    release_year: "2026",
    original_language: "en",
    production_company: "A24",
    director: "Greta Gerwig",
    lead_actors: "Florence Pugh|Timothée Chalamet",
    rating: "7.9",
    vote_count: "12000",
    popularity: "38.0",
  },
  "Low Budget Indie": {
    title: "Example: Paper Lanterns",
    budget: "2000000",
    runtime: "96",
    genres: ["Comedy", "Romance"],
    release_month: "2",
    release_day: "14",
    release_year: "2026",
    original_language: "en",
    production_company: "Focus Features",
    director: "Sean Baker",
    lead_actors: "Mikey Madison|Paul Walter Hauser",
    rating: "7.4",
    vote_count: "2500",
    popularity: "12.0",
  },
};

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "Hindi" },
  { code: "ta", label: "Tamil" },
  { code: "te", label: "Telugu" },
  { code: "fr", label: "French" },
  { code: "es", label: "Spanish" },
  { code: "zh", label: "Chinese" },
  { code: "ja", label: "Japanese" },
  { code: "ko", label: "Korean" },
  { code: "ru", label: "Russian" },
  { code: "de", label: "German" },
  { code: "it", label: "Italian" },
  { code: "other", label: "Other" },
];

export function PredictionForm({
  filters,
  onSubmit,
  loading,
}: {
  filters: FiltersSummary | null;
  onSubmit: (payload: PredictRequest) => void;
  loading: boolean;
}) {
  const [form, setForm] = useState<FormValues>(EMPTY_FORM);

  const companySuggestions = useMemo(() => {
    const list = filters?.companies ?? [];
    return Array.from(new Set(list)).sort().slice(0, 60);
  }, [filters]);

  const directorSuggestions = useMemo(() => {
    const list = filters?.directors ?? [];
    return Array.from(new Set(list)).sort().slice(0, 60);
  }, [filters]);

  const genreList = useMemo(() => filters?.genres ?? [], [filters]);

  const set = <K extends keyof FormValues>(key: K, value: FormValues[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const toggleGenre = (g: string) =>
    set(
      "genres",
      form.genres.includes(g) ? form.genres.filter((x) => x !== g) : [...form.genres, g],
    );

  const applyPreset = (key: string) => {
    const preset = DEMO_PRESETS[key];
    if (!preset) return;
    setForm((f) => ({ ...f, ...preset }));
  };

  const submit = () => {
    const payload: PredictRequest = {
      title: form.title.trim() || undefined,
      budget: Number(form.budget) || 0,
      runtime: Number(form.runtime) || 0,
      genres: form.genres,
      release_month: form.release_month ? Number(form.release_month) : undefined,
      release_day: form.release_day ? Number(form.release_day) : undefined,
      release_year: form.release_year ? Number(form.release_year) : undefined,
      original_language: form.original_language || undefined,
      production_company: form.production_company.trim() || undefined,
      director: form.director.trim() || undefined,
      lead_actors: form.lead_actors
        .split("|")
        .map((s) => s.trim())
        .filter(Boolean),
      rating: form.rating ? Number(form.rating) : undefined,
      vote_count: form.vote_count ? Number(form.vote_count) : undefined,
      popularity: form.popularity ? Number(form.popularity) : undefined,
    };
    onSubmit(payload);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="section-title">New Movie</h2>
          <p className="section-sub">Provide as much detail as possible for a better prediction</p>
        </div>
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-violet-300" />
          <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Quick fill</span>
          <select className="input !w-auto !py-1.5 text-xs" onChange={(e) => applyPreset(e.target.value)} defaultValue="">
            <option value="" disabled>
              Choose a preset…
            </option>
            {Object.keys(DEMO_PRESETS).map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Section 1: Movie Information */}
      <section className="glass p-5">
        <h3 className="mb-4 text-sm font-bold uppercase tracking-wider text-violet-300">🎞️ Movie Information</h3>
        <div className="space-y-4">
          <div>
            <label className="label">Title</label>
            <input
              className="input"
              placeholder="e.g. Avatar 3"
              value={form.title}
              onChange={(e) => set("title", e.target.value)}
            />
          </div>
          <div>
            <span className="label">Genres</span>
            <div className="flex flex-wrap gap-2">
              {genreList.map((g) => (
                <button
                  key={g}
                  type="button"
                  onClick={() => toggleGenre(g)}
                  className={`chip ${form.genres.includes(g) ? "chip-active" : "hover:border-white/20"}`}
                >
                  {g}
                </button>
              ))}
              {genreList.length === 0 && <p className="text-xs text-zinc-500">Loading genres…</p>}
            </div>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="label">Primary Language</label>
              <select
                className="input"
                value={form.original_language}
                onChange={(e) => set("original_language", e.target.value)}
              >
                {LANGUAGES.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Runtime (minutes)</label>
              <input
                type="number"
                className="input"
                placeholder="120"
                min={1}
                value={form.runtime}
                onChange={(e) => set("runtime", e.target.value)}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Section 2: Budget */}
      <section className="glass p-5">
        <h3 className="mb-4 text-sm font-bold uppercase tracking-wider text-amber-300">💰 Budget</h3>
        <div>
          <label className="label">Production Budget (USD)</label>
          <div className="relative">
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-sm text-zinc-500">$</span>
            <input
              type="number"
              className="input !pl-8"
              placeholder="e.g. 100000000"
              min={1}
              value={form.budget}
              onChange={(e) => set("budget", e.target.value)}
            />
          </div>
          <p className="mt-1.5 text-xs text-zinc-500">Required field · the single strongest revenue driver</p>
        </div>
      </section>

      {/* Section 3: Release */}
      <section className="glass p-5">
        <h3 className="mb-4 text-sm font-bold uppercase tracking-wider text-cyan-300">📅 Release</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="label">Month</label>
            <select className="input" value={form.release_month} onChange={(e) => set("release_month", e.target.value)}>
              <option value="">Any</option>
              {[
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December",
              ].map((m, i) => (
                <option key={m} value={String(i + 1)}>
                  {m}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Day</label>
            <input
              type="number"
              className="input"
              placeholder="1–31"
              min={1}
              max={31}
              value={form.release_day}
              onChange={(e) => set("release_day", e.target.value)}
            />
          </div>
          <div>
            <label className="label">Year</label>
            <input
              type="number"
              className="input"
              placeholder="e.g. 2026"
              min={1960}
              max={2100}
              value={form.release_year}
              onChange={(e) => set("release_year", e.target.value)}
            />
          </div>
        </div>
      </section>

      {/* Section 4: Audience Signals */}
      <section className="glass p-5">
        <h3 className="mb-4 text-sm font-bold uppercase tracking-wider text-emerald-300">📊 Audience Signals</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="label">Rating (0–10)</label>
            <input
              type="number"
              className="input"
              placeholder="7.5"
              min={0}
              max={10}
              step={0.1}
              value={form.rating}
              onChange={(e) => set("rating", e.target.value)}
            />
          </div>
          <div>
            <label className="label">Vote Count</label>
            <input
              type="number"
              className="input"
              placeholder="e.g. 10000"
              min={0}
              value={form.vote_count}
              onChange={(e) => set("vote_count", e.target.value)}
            />
          </div>
          <div>
            <label className="label">Popularity Score</label>
            <input
              type="number"
              className="input"
              placeholder="e.g. 80.5"
              min={0}
              step={0.1}
              value={form.popularity}
              onChange={(e) => set("popularity", e.target.value)}
            />
          </div>
        </div>
      </section>

      {/* Section 5: Cast & Crew */}
      <section className="glass p-5">
        <h3 className="mb-4 text-sm font-bold uppercase tracking-wider text-fuchsia-300">🎭 Cast & Crew</h3>
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="label">Director</label>
              <input
                className="input"
                list="director-list"
                placeholder="Type or choose a known director"
                value={form.director}
                onChange={(e) => set("director", e.target.value)}
              />
              <datalist id="director-list">
                {directorSuggestions.map((d) => (
                  <option key={d} value={d} />
                ))}
              </datalist>
            </div>
            <div>
              <label className="label">Production Company</label>
              <input
                className="input"
                list="company-list"
                placeholder="Type or choose a known studio"
                value={form.production_company}
                onChange={(e) => set("production_company", e.target.value)}
              />
              <datalist id="company-list">
                {companySuggestions.map((c) => (
                  <option key={c} value={c} />
                ))}
              </datalist>
            </div>
          </div>
          <div>
            <label className="label">Lead Actors <span className="normal-case text-zinc-600">(separate with |)</span></label>
            <input
              className="input"
              placeholder="e.g. Tom Cruise|Hayley Atwell"
              value={form.lead_actors}
              onChange={(e) => set("lead_actors", e.target.value)}
            />
          </div>
        </div>
      </section>

      <button className="btn-primary w-full py-3 text-base" onClick={submit} disabled={loading}>
        {loading ? "Predicting…" : "🚀 Predict Box Office Revenue"}
      </button>
    </div>
  );
}
