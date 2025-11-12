import type { ChartConfig } from "../components/ui/chart"
import type { MlflowRunResponse } from "./mlflow";


export type ChartConfigProps = {
    desktop: ChartConfig
}

export type ModelPerformanceProps = {
    runs: MlflowRunResponse[] | null;
};

export type LineChartCardProps<TData extends Record<string, unknown>> = {
    data: TData[]
    chartConfig: ChartConfig
    dataKey: string
    stroke: string
    title: string
}

export type ModelMetricCardProps = {
    run: MlflowRunResponse
    bestRmse: number
    secondBest: number | null
}