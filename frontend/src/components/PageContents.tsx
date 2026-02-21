import { useEffect, useState } from "react";

import { OVERVIEW, MODEL_COMPARISON, DATA_QUALITY, UPLOAD_DATA, PREDICT } from "../lib/constants";
import type { MlflowRunListResponse, MlflowRunResponse } from "../types/mlflow";
import ModelPerformance from "./model_performance/ModelPerformance";
import { TabsContent } from "./ui/tabs";
import PredictTab from './prediction/PredictTab'


function PageContents() {
  const [runs, setRuns] = useState<MlflowRunResponse[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchLatest() {
      try {
        setLoading(true)
        const runs = await getLatestRuns();
        if (runs.length > 0) {
          setRuns(runs);    // first run is the most recent
        } else {
          setRuns(null);
        }
      } catch (error) {
        console.error("Error fetching runs", error);
        setError("Error fetching runs")
        setRuns(null);
      } finally {
        setLoading(false)
      }
    }

    fetchLatest();
  }, []);

  return (
    <div className="p-4">
      {loading && <div>Loading latest run data…</div>}
      {error && <div className="text-red-500">{error}</div>}

      <TabsContent value={PREDICT}> <PredictTab /> </TabsContent>
      <TabsContent value={OVERVIEW}> … overview section … </TabsContent>
      <TabsContent value={MODEL_COMPARISON}>
        <ModelPerformance runs={runs} />
      </TabsContent>
      <TabsContent value={DATA_QUALITY}> … data quality section … </TabsContent>
      <TabsContent value={UPLOAD_DATA}> … upload data section … </TabsContent>
    </div>
  );
}

async function getLatestRuns(): Promise<MlflowRunResponse[]> {
  const API_BASE = import.meta.env.VITE_API_URL ?? "/api";
  const response = await fetch(`${API_BASE}/mlflow/runs`);
  if (!response.ok) {
    throw new Error(`Failed to fetch run metadata: ${response.statusText}`);
  }
  const data = (await response.json()) as MlflowRunListResponse;
  return data;
}

export default PageContents;
