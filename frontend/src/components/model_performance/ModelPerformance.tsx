import type { MlflowRunResponse } from "../../types/mlflow";
import type { JSX } from "react";
import { Card, CardHeader, CardTitle, CardDescription } from "../ui/card"
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table"
type ModelPerformanceProps = {
  runs: MlflowRunResponse[] | null;
};

export default function ModelPerformance({ runs }: ModelPerformanceProps) {
  if (runs == null) return (
    <p className="mt-4 text-sm text-muted-foreground">No MLflow runs found yet.</p>
  )
  const latestRun = runs[0]
  const latestMetrics = latestRun.data.metrics;
  const latestParams = latestRun.data.params;
  const latestParamEntries = Object.entries(latestParams)

  const rmseArr = runs.map(r => r.data.metrics.rmse)

  const bestRunId = rmseArr.reduce((minIdx, curr, idx, arr) => curr < arr[minIdx] ? idx : minIdx, 0)
  const bestRun = runs[bestRunId]
  const bestMetrics = bestRun.data.metrics
  const bestParams = bestRun.data.params


  const renderTableCells = (paramData: { [key: string]: any }): JSX.Element[] => {
    return Object.entries(paramData).map(([_, val]) => <TableCell>{val}</TableCell>)
  }

  return (
    <section>
      <h2 className="text-lg font-semibold">Model Performance Board</h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
        <Card>
          <CardHeader>
            <CardTitle>RMSE</CardTitle>
            <CardDescription>
              {latestMetrics.rmse.toFixed(2)}
            </CardDescription>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Validation RMSE</CardTitle>
            <CardDescription>
              {latestMetrics.rmse.toFixed(2)}
            </CardDescription>
          </CardHeader>
        </Card>
      </div>

      <div>
        <Table>
          <TableCaption>Latest and best training runs</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>RUN</TableHead>
              {
                Object.entries(latestParams).map(([key, _]) => {
                  const keyName = key.replaceAll("_", " ").toUpperCase()
                  return <TableHead>{keyName}</TableHead>
                })
              }
            </TableRow>
          </TableHeader>

          <TableBody>

            <TableRow key={latestParams.raw_csv_sha256}>
              <TableCell>LATEST</TableCell>
              {renderTableCells(latestParams)}
            </TableRow>

            <TableRow key={bestParams.raw_csv_sha256}>
              <TableCell>BEST</TableCell>
              {renderTableCells(bestParams)}
            </TableRow>

          </TableBody>
        </Table>
      </div>
    </section>
  )
}
