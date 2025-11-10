import type { MlflowRunResponse } from "../../types/mlflow";
import type { JSX } from "react";
import { Monitor } from "lucide-react"
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
import { ChartContainer } from "../ui/chart"
import type { ChartConfig } from "../ui/chart"
import { CartesianGrid, Line, LineChart, XAxis, YAxis, Tooltip, Legend } from 'recharts';

type ModelPerformanceProps = {
  runs: MlflowRunResponse[] | null;
};

type ChartConfigProps = {
  desktop: ChartConfig
}

export default function ModelPerformance({ runs }: ModelPerformanceProps) {
  if (runs == null) return (
    <p className="mt-4 text-sm text-muted-foreground">No MLflow runs found yet.</p>
  )
  const RMSE_DATA_KEY = "rmse"
  const RMSE_VALIDATION_DATA_KEY = "rmse_validation"
  const latestRun = runs[0]
  const latestMetrics = latestRun.data.metrics;
  const latestParams = latestRun.data.params;
  const latestParamEntries = Object.entries(latestParams)

  const listOfRmse = runs.map(r => r.data.metrics.rmse)

  const bestRunId = listOfRmse.reduce((minIdx, curr, idx, arr) => curr < arr[minIdx] ? idx : minIdx, 0)
  const bestRun = runs[bestRunId]
  const bestMetrics = bestRun.data.metrics
  const bestParams = bestRun.data.params


  const renderTableCells = (paramData: { [key: string]: any }): JSX.Element[] => {
    return Object.entries(paramData).map(([_, val]) => <TableCell>{val}</TableCell>)
  }

  const chartConfig = {
    desktop: {
      label: "Desktop",
      icon: Monitor,
      // A color like 'hsl(220, 98%, 61%)' or 'var(--color-name)'
      color: "var(--primary)",
    }
  } satisfies ChartConfig

  const rmseData = runs.map(run => {
    return {
      name: new Date(run.info.end_time).toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
      }),
      rmse: run.data.metrics.rmse,
      rmse_validation: run.data.metrics.validation_rmse
    }
  })


  return (
    <section className="space-y-10">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
        <Card>
          <CardHeader>
            <CardTitle>Latest RMSE</CardTitle>
            <CardDescription>
              {latestMetrics.rmse.toFixed(2)}
            </CardDescription>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Latest Validation RMSE</CardTitle>
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

      <div>
        <ChartContainer config={chartConfig} className="min-h-[200px] w-full">
          <LineChart data={rmseData}>
            <CartesianGrid stroke="#eee" strokeDasharray="5 5" />
            <XAxis
              dataKey="name"
              label={{ value: "Date", position: "insideBottom", offset: -5 }}
              angle={-45}
              textAnchor="end"
              height={80} />
            <YAxis label={{ value: "RMSE", angle: -90, position: "insideLeft" }} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey={RMSE_DATA_KEY} stroke="var(--chart-1)" />
            <Line type="monotone" dataKey={RMSE_VALIDATION_DATA_KEY} stroke="var(--chart-2)" />
          </LineChart>
        </ChartContainer>
      </div>
    </section>
  )
}
