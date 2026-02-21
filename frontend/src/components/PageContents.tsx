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

      <TabsContent value={OVERVIEW}> … overview section … </TabsContent>
      <TabsContent value={MODEL_COMPARISON}>
        {error ? <div className="text-center text-gray-400 mt-8">Model comparison requires local MLflow server.{" "}
          <a href="https://github.com/jee3153/london_housing_ai" className="underline">Run locally</a> to see full dashboard.
        </div> : <ModelPerformance runs={runs} />}

      </TabsContent>
      <TabsContent value={DATA_QUALITY}> … data quality section … </TabsContent>
      <TabsContent value={UPLOAD_DATA}> … upload data section … </TabsContent>
      <TabsContent value={PREDICT}> <PredictTab /> </TabsContent>
    </div>
  );
}

async function getLatestRuns(): Promise<MlflowRunResponse[]> {
  const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:7777";
  const response = await fetch(`${API_BASE}/mlflow/runs`);
  if (!response.ok) {
    throw new Error(`Failed to fetch run metadata: ${response.statusText}`);
  }
  const data = (await response.json()) as MlflowRunListResponse;
  return data;
}

export default PageContents;
