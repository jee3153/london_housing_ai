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
import {
  Item,
  ItemActions,
  ItemContent,
  ItemDescription,
  ItemMedia,
  ItemTitle,
} from "../ui/item"

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
  // const RMSE_TEST_DATA_KEY = "test_rmse"
  const R2_VALIDATION_DATA_KEY = "validation_r2"
  const RMSE_VALIDATION_DATA_KEY = "validation_rmse"

  // const testRmse = runs.map(run => run.data.metrics.test_rmse)
  const validationRmse = runs.map(run => run.data.metrics.validation_rmse)
  const validationR2 = runs.map(run => run.data.metrics.validation_r2)

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
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }),
      validation_rmse: run.data.metrics.validation_rmse.toFixed(2)
    }
  })

  const r2Data = runs.map(run => {
    return {
      name: new Date(run.info.end_time).toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }),
      validation_r2: run.data.metrics.validation_r2.toFixed(2)
    }
  })


  return (
    <section className="space-y-10">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
        {
          runs.map(run => (
            <Card>
              <CardHeader>
                <CardTitle>Model name</CardTitle>
                <CardDescription>
                  <Item>
                    <ItemContent>
                      <ItemTitle>RMSE</ItemTitle>
                      <ItemDescription>{run.data.metrics.validation_rmse}</ItemDescription>
                    </ItemContent>
                    <ItemContent>
                      <ItemTitle>MSE</ItemTitle>
                      <ItemDescription>{run.data.metrics.validation_mse}</ItemDescription>
                    </ItemContent>
                    <ItemContent>
                      <ItemTitle>R²</ItemTitle>
                      <ItemDescription>{run.data.metrics.validation_r2}</ItemDescription>
                    </ItemContent>
                  </Item>
                </CardDescription>
              </CardHeader>
            </Card>
          ))
        }
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
        <Card>
          <CardHeader>
            <CardTitle>Average Error Rate in £</CardTitle>
            <ChartContainer config={chartConfig} className="min-h-[200px] w-full">
              <LineChart data={rmseData}>
                <CartesianGrid stroke="#eee" strokeDasharray="5 5" />
                <XAxis
                  dataKey="name"
                  label={{ value: "Date", position: "insideBottom", offset: -5 }}
                  angle={-45}
                  textAnchor="end"
                  height={80} />
                <YAxis label={{ value: "£", angle: -90, position: "insideLeft" }} domain={[Math.min(...validationRmse), Math.max(...validationRmse)]} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey={RMSE_VALIDATION_DATA_KEY} stroke="var(--chart-1)" />
              </LineChart>
            </ChartContainer>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>R²</CardTitle>
            <ChartContainer config={chartConfig} className="min-h-[200px] w-full">
              <LineChart data={r2Data}>
                <CartesianGrid stroke="#eee" strokeDasharray="5 5" />
                <XAxis
                  dataKey="name"
                  label={{ value: "Date", position: "insideBottom", offset: -5 }}
                  angle={-45}
                  textAnchor="end"
                  height={80} />
                <YAxis label={{ value: "£", angle: -90, position: "insideLeft" }} domain={[Math.min(...validationR2), Math.max(...validationR2)]} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey={R2_VALIDATION_DATA_KEY} stroke="var(--chart-2)" />
              </LineChart>
            </ChartContainer>
          </CardHeader>
        </Card>
      </div>
    </section>
  )
}
