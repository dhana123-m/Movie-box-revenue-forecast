import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/layout/Layout";
import { DashboardPage } from "./pages/DashboardPage";
import { ForecastPage } from "./pages/ForecastPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { MovieExplorerPage } from "./pages/MovieExplorerPage";
import { ModelPerformancePage } from "./pages/ModelPerformancePage";
import { SettingsPage } from "./pages/SettingsPage";

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/forecast" element={<ForecastPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/movies" element={<MovieExplorerPage />} />
          <Route path="/model" element={<ModelPerformancePage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
