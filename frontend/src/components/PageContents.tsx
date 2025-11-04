import { useEffect, useState } from "react";

import { OVERVIEW, MODEL_COMPARISON, DATA_QUALITY, UPLOAD_DATA } from "../lib/constants";
import type { MlflowRunListResponse, MlflowRunResponse } from "../types/mlflow";
import ModelPerformance from "./model_performance/ModelPerformance";
import { TabsContent } from "./ui/tabs";


function PageContents() {
  const [latestRun, setLatestRun] = useState<MlflowRunResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchLatest() {
      try {
        setLoading(true)
        const runs = await getLatestRuns();
        if (runs.length > 0) {
          setLatestRun(runs[0]);    // first run is the most recent
        } else {
          setLatestRun(null);
        }
      } catch (error) {
        console.error("Error fetching runs", error);
        setError("Error fetching runs")
        setLatestRun(null);
      } finally {
        setLoading(true)
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
        <ModelPerformance latestRun={latestRun} />
      </TabsContent>
      <TabsContent value={DATA_QUALITY}> … data quality section … </TabsContent>
      <TabsContent value={UPLOAD_DATA}> … upload data section … </TabsContent>
    </div>
  );
}

async function getLatestRuns(): Promise<MlflowRunResponse[]> {
  const response = await fetch("http://localhost:7777/experiment_runs");
  if (!response.ok) {
    throw new Error(`Failed to fetch run metadata: ${response.statusText}`);
  }
  const data = (await response.json()) as MlflowRunListResponse;
  return data;
}

export default PageContents;
