import type {
  ApiEnvelope,
  BatchResult,
  BudgetVsRevenuePoint,
  FiltersSummary,
  GenreStat,
  HealthStatus,
  MetricsEnvelope,
  ModelInfo,
  MovieListResponse,
  MovieSummary,
  OverviewStats,
  PredictionResult,
  PredictRequest,
  ReleaseMonthStat,
  TopMovieRow,
  TrainingStatus,
  YearlyStat,
} from "../types";

const BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  (import.meta.env.DEV ? "/api" : "http://localhost:8000/api");

export class ApiError extends Error {
  code: string;
  fields: Record<string, string> | null;
  constructor(code: string, message: string, fields: Record<string, string> | null) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.fields = fields;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, options);
  } catch {
    throw new ApiError(
      "NETWORK_ERROR",
      "Cannot reach the backend server. Make sure it is running on port 8000.",
      null,
    );
  }
  let body: ApiEnvelope<T>;
  try {
    body = (await res.json()) as ApiEnvelope<T>;
  } catch {
    throw new ApiError("BAD_RESPONSE", "The server returned an unreadable response.", null);
  }
  if (!res.ok || !body.success) {
    const err = body.error;
    throw new ApiError(err?.code ?? "ERROR", err?.message ?? "Something went wrong.", err?.fields ?? null);
  }
  return body.data as T;
}

function jsonBody(payload: unknown): RequestInit {
  return {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  };
}

export const api = {
  baseUrl: BASE_URL,

  health: () => request<HealthStatus>("/health"),

  modelInfo: () => request<ModelInfo>("/model/info"),

  predict: (payload: PredictRequest) => request<PredictionResult>("/predict", jsonBody(payload)),

  predictBatch: (payload: PredictRequest[]) => request<BatchResult>("/predict/batch", jsonBody(payload)),

  predictCsv: async (file: File): Promise<BatchResult> => {
    const form = new FormData();
    form.append("file", file);
    return request<BatchResult>("/predict/csv", { method: "POST", body: form });
  },

  overview: () => request<OverviewStats>("/analytics/overview"),

  genres: () => request<GenreStat[]>("/analytics/genres"),

  yearly: (minYear?: number) =>
    request<YearlyStat[]>(`/analytics/yearly${minYear ? `?min_year=${minYear}` : ""}`),

  budgetVsRevenue: (limit = 200) =>
    request<BudgetVsRevenuePoint[]>(`/analytics/budget-vs-revenue?limit=${limit}`),

  topMovies: (limit = 10) => request<TopMovieRow[]>(`/analytics/top-movies?limit=${limit}`),

  releaseMonths: () => request<ReleaseMonthStat[]>("/analytics/release-months"),

  movies: (params: {
    page?: number;
    per_page?: number;
    sort_by?: string;
    order?: string;
    genre?: string;
    search?: string;
    year_from?: number;
    year_to?: number;
  }) => {
    const qs = new URLSearchParams();
    const mapped: Record<string, string | number | undefined> = {
      page: params.page,
      per_page: params.per_page,
      sort_by: params.sort_by,
      order: params.order,
      genre: params.genre,
      q: params.search,
      min_year: params.year_from,
      max_year: params.year_to,
    };
    Object.entries(mapped).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
    });
    return request<MovieListResponse>(`/movies?${qs.toString()}`);
  },

  movieById: (id: number) => request<MovieSummary>(`/movies/${id}`),

  filtersSummary: () => request<FiltersSummary>("/movies/filters/summary"),

  trainingMetrics: () => request<MetricsEnvelope>("/training/metrics"),

  trainingStatus: () => request<TrainingStatus>("/training/status"),

  retrain: () => request<TrainingStatus>("/retrain", { method: "POST" }),
};
