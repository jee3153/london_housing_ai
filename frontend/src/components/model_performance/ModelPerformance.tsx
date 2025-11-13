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
import type { ModelPerformanceProps } from '../../types/props'
import { LineChartCard } from '../LineChartCard'
import ModelMetricCard from "./ModelMetricCard";
import { getReadableTimeStamp } from "../../lib/utils";

export default function ModelPerformance({ runs }: ModelPerformanceProps) {
  if (runs == null) return (
    <p className="mt-4 text-sm text-muted-foreground">No MLflow runs found yet.</p>
  )
  const R2_VALIDATION_DATA_KEY = "validation_r2"
  const RMSE_VALIDATION_DATA_KEY = "validation_rmse"

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
      name: getReadableTimeStamp(run.info.end_time),
      validation_rmse: Number(run.data.metrics.validation_rmse.toFixed(2))
    }
  })

  const r2Data = runs.map(run => {
    return {
      name: getReadableTimeStamp(run.info.end_time),
      validation_r2: Number(run.data.metrics.validation_r2.toFixed(2))
    }
  })

  const rmseSorted = rmseData.map(data => Number(data.validation_rmse)).sort()
  const bestRmse = rmseSorted[0]
  const secondBest = rmseSorted.length > 1 ? rmseSorted[1] : null

  return (
    <section className="space-y-10">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
        {runs.map(run => (<ModelMetricCard run={run} bestRmse={bestRmse} secondBest={secondBest} />))}
      </div>

      <div>
        <Table>
          <TableCaption>Latest and best training runs</TableCaption>
          <TableHeader>
            <TableRow>
              {
                Object.entries(runs[0].data.params).map(([key, _]) => {
                  const keyName = key.replaceAll("_", " ").toUpperCase()
                  return <TableHead>{keyName}</TableHead>
                })
              }
            </TableRow>
          </TableHeader>

          <TableBody>
            {
              runs.map(r => (
                <TableRow key={r.data.params.raw_csv_sha256}>
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
