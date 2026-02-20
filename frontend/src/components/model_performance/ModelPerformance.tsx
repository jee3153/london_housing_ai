import type { JSX } from "react";
import { Monitor } from "lucide-react"
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table"
import type { ChartConfig } from "../ui/chart"
import type { ModelExperimentProps } from '../../types/props'
import { LineChartCard } from '../LineChartCard'
import ModelMetricCard from "./ModelMetricCard";
import { getReadableTimeStamp } from "../../lib/utils";

export default function ModelPerformance({ runs }: ModelExperimentProps) {
  if (runs == null || runs.length === 0) return (
    <p className="mt-4 text-sm text-muted-foreground">No MLflow runs found yet.</p>
  )
  const R2_VALIDATION_DATA_KEY = "validation_r2"
  const RMSE_VALIDATION_DATA_KEY = "validation_rmse"
  const toNumber = (value: unknown): number | null => {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  /**
   * Rounds to 2 decimal places by shifting digits, rounding the integer, and shifting back.
   * Returns a number (unlike toFixed) to allow strict numeric comparisons.
   */
  const round2 = (value: number): number => Math.round(value * 100) / 100

  const renderTableCells = (paramData: { [key: string]: any }): JSX.Element[] => {
    return Object.entries(paramData).map(([key, val]) => <TableCell key={key}>{val}</TableCell>)
  }

  const chartConfig = {
    desktop: {
      label: "Desktop",
      icon: Monitor,
      // A color like 'hsl(220, 98%, 61%)' or 'var(--color-name)'
      color: "var(--primary)",
    }
  } satisfies ChartConfig

  const metricRuns = runs.filter(run => {
    const metrics = run.data?.metrics ?? {}
    return (
      toNumber(metrics.validation_rmse) !== null &&
      toNumber(metrics.validation_r2) !== null &&
      toNumber(metrics.validation_mse) !== null &&
      toNumber(metrics.train_rmse) !== null &&
      toNumber(metrics.test_rmse) !== null
    )
  })

  if (metricRuns.length === 0) {
    return <p className="mt-4 text-sm text-muted-foreground">MLflow runs found, but required metrics are missing.</p>
  }

  const rmseData = metricRuns.map(run => {
    return {
      name: getReadableTimeStamp(run.info.end_time),
      validation_rmse: round2(Number(run.data.metrics.validation_rmse))
    }
  })

  const r2Data = metricRuns.map(run => {
    return {
      name: getReadableTimeStamp(run.info.end_time),
      validation_r2: round2(Number(run.data.metrics.validation_r2))
    }
  })

  const rmseSorted = rmseData.map(data => Number(data.validation_rmse)).sort((a, b) => a - b)
  const bestRmse = rmseSorted[0]
  const secondBest = rmseSorted.length > 1 ? rmseSorted[1] : null

  return (
    <section className="space-y-10">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
        {metricRuns.map(run => (
          <ModelMetricCard key={run.info.run_id} run={run} bestRmse={bestRmse} secondBest={secondBest} />
        ))}
      </div>

      <div>
        <Table>
          <TableCaption>Latest and best training runs</TableCaption>
          <TableHeader>
            <TableRow>
              {
                Object.entries(metricRuns[0].data.params).map(([key, _]) => {
                  const keyName = key.replaceAll("_", " ").toUpperCase()
                  return <TableHead key={key}>{keyName}</TableHead>
                })
              }
            </TableRow>
          </TableHeader>

          <TableBody>
            {
              metricRuns.map(r => (
                <TableRow key={r.info.run_id}>
                  {renderTableCells(r.data.params)}
                </TableRow>
              ))
            }
          </TableBody>
        </Table>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <LineChartCard data={rmseData} chartConfig={chartConfig} dataKey={RMSE_VALIDATION_DATA_KEY} stroke="var(--chart-1)" title="RMSE" />
        <LineChartCard data={r2Data} chartConfig={chartConfig} dataKey={R2_VALIDATION_DATA_KEY} stroke="var(--chart-2)" title="R²" />
      </div>
    </section>
  )
}
