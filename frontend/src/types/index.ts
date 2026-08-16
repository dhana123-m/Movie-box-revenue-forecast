export interface ApiEnvelope<T> {
  success: boolean;
  data: T | null;
  message: string | null;
  error: {
    code: string;
    message: string;
    fields: Record<string, string> | null;
  } | null;
}

export interface HealthStatus {
  status: string;
  app: string;
  version: string;
  environment: string;
  database: string;
  movies_in_database: number;
  model_ready: boolean;
  model_version: string | null;
}

export interface ModelInfo {
  model_version: string;
  model_type: string;
  framework: string;
  feature_count: number;
  target_variable: string;
  performance_thresholds: Record<string, number>;
  dataset: {
    name: string;
    rows_used: number;
    train: number;
    validation: number;
    test: number;
    features: number;
    target: string;
    split: string;
  };
  training_date: string | null;
  training_duration_seconds: number | null;
}

export interface FeatureContribution {
  feature: string;
  label: string;
  impact: "positive" | "negative" | "neutral";
  magnitude: number;
}

export interface PredictionResult {
  predicted_revenue: number;
  predicted_revenue_usd: string;
  predicted_revenue_million: string;
  predicted_revenue_crore: string;
  performance_category: string;
  budget: number;
  revenue_budget_ratio: number;
  confidence_score: number;
  expected_range: { lower: number; upper: number; method: string };
  model: string;
  model_version: string;
  contributions: FeatureContribution[];
  disclaimer: string;
}

export interface PredictRequest {
  title?: string;
  budget: number;
  runtime: number;
  genres: string[];
  release_month?: number;
  release_day?: number;
  release_year?: number;
  original_language?: string;
  production_company?: string;
  director?: string;
  lead_actors?: string[];
  rating?: number;
  vote_count?: number;
  popularity?: number;
}

export interface BatchRowResult {
  row: number;
  title: string | null;
  status: "success" | "error";
  predicted_revenue: number | null;
  predicted_revenue_usd: string | null;
  performance_category: string | null;
  error: string | null;
}

export interface BatchResult {
  total_rows: number;
  successful: number;
  failed: number;
  results: BatchRowResult[];
  summary: PredictionResult | null;
}

export interface GenreStat {
  genre: string;
  movie_count: number;
  total_revenue: number;
  avg_revenue: number;
  avg_budget: number;
  avg_roi: number;
}

export interface YearlyStat {
  year: number;
  movie_count: number;
  total_revenue: number;
  avg_revenue: number;
  total_budget: number;
  avg_roi: number;
}

export interface OverviewStats {
  total_movies: number;
  avg_budget: number;
  avg_revenue: number;
  median_revenue: number;
  highest_revenue: number;
  highest_revenue_movie: string;
  highest_budget: number;
  total_revenue: number;
  avg_roi: number;
  year_min: number;
  year_max: number;
}

export interface BudgetVsRevenuePoint {
  title: string;
  year: number | null;
  budget: number;
  revenue: number;
}

export interface TopMovieRow {
  title: string;
  year: number | null;
  budget: number;
  revenue: number;
  roi: number | null;
  rating: number | null;
  primary_genre: string | null;
}

export interface ReleaseMonthStat {
  month: number;
  label: string;
  movie_count: number;
  avg_revenue: number;
  total_revenue: number;
  avg_profit: number;
}

export interface MovieSummary {
  id: number;
  title: string;
  year: number | null;
  genres: string[];
  primary_genre: string | null;
  budget: number;
  revenue: number;
  roi: number | null;
  rating: number | null;
  popularity: number | null;
  classification: string;
  director: string | null;
  production_company: string | null;
  runtime: number | null;
  original_language: string | null;
  vote_count: number | null;
  release_date: string | null;
}

export interface MovieListResponse {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  items: MovieSummary[];
}

export interface FiltersSummary {
  genres: string[];
  year_min: number | null;
  year_max: number | null;
  languages: string[];
  companies: string[];
  directors: string[];
}

export interface MetricRow {
  model: string;
  mae_log: number;
  rmse_log: number;
  r2_log: number;
  mae_revenue: number;
  rmse_revenue: number;
  r2_revenue: number;
  mape_pct: number;
}

export interface ModelMetrics {
  dnn: MetricRow;
  baselines: Record<string, MetricRow>;
  comparison: MetricRow[];
  dataset: {
    name: string;
    rows_used: number;
    train: number;
    validation: number;
    test: number;
    features: number;
    target: string;
    split: string;
  };
  feature_importance: Array<{ feature: string; importance: number }>;
  architecture: { layers: string[]; optimizer: string; loss: string; metric: string };
}

export interface TrainingHistory {
  epochs: number;
  loss: number[];
  val_loss: number[];
  mae: number[];
  val_mae: number[];
}

export interface MetricsEnvelope {
  metrics: ModelMetrics;
  training_history: TrainingHistory;
}

export interface TrainingStatus {
  status: "idle" | "running" | "completed" | "failed" | "started" | "already_running";
  running: boolean;
  started_at: string | null;
  completed_at: string | null;
  current_epoch: number | null;
  total_epochs: number | null;
  message: string;
}
