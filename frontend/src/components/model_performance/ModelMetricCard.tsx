import type { JSX } from 'react'
import type { ModelMetricCardProps } from '../../types/props'
import { Card, CardHeader, CardTitle, CardDescription, CardAction } from "../ui/card"
import { Badge } from "../ui/badge"
import type { MlflowRunResponse } from "../../types/mlflow"
import { getReadableTimeStamp } from '../../lib/utils'
import {
    Item,
    ItemContent,
    ItemDescription,
    ItemTitle,
} from "../ui/item"

function ModelMetricCard({ run, bestRmse, secondBest }: ModelMetricCardProps) {
    const toNumber = (value: unknown): number | null => {
        const parsed = Number(value)
        return Number.isFinite(parsed) ? parsed : null
    }
    /**
     * Rounds to 2 decimal places by shifting digits, rounding the integer, and shifting back.
     * Returns a number (unlike toFixed) to allow strict numeric comparisons.
     */
    const round2 = (value: number): number => Math.round(value * 100) / 100
    const formatNumber = (value: unknown): string => {
        const n = toNumber(value)
        return n === null ? "N/A" : round2(n).toFixed(2)
    }
    const validationRmse = toNumber(run.data.metrics.validation_rmse)
    const trainRmse = toNumber(run.data.metrics.train_rmse)
    const validationRmseRounded = validationRmse === null ? null : round2(validationRmse)

    const showRightBadge = (rmse: number | null): JSX.Element => {
        if (rmse === null) {
            return <Badge variant="outline">Unknown</Badge>
        }
        if (rmse === bestRmse) {
            return <Badge>Champion</Badge>
        }
        if (secondBest !== null && rmse === secondBest) {
            return <Badge variant="secondary">Challenger</Badge>
        }
        return <Badge variant="outline">Archive</Badge>
    }

    const showModelType = (run: MlflowRunResponse) => {
        const modelType = run.data.params.model_class ?? "Model"
        if (validationRmseRounded !== null && validationRmseRounded === bestRmse) {
            return `${modelType} 🏆`
        }
        return modelType
    }

    const showGeneralisationText = (computedGap: number): JSX.Element => {
        if (computedGap < 0.1) {
            return <p className="text-center mt-8 p-3 text-green-400">✅ Excellent generalization</p>
        }
        else if (computedGap < 0.25) {
            return <p className="text-center mt-8 p-3 text-yellow-400">Acceptable generalization</p>
        }
        else if (computedGap < 0.4) {
            return <p className="text-center mt-8 p-3 text-orange-400">`⚠️ Potential overfit (${computedGap * 100}% gap)`</p>
        }
        else {
            return <p className="text-center mt-8 p-3 text-red-400">`🔴 Likely overfit (${computedGap * 100}% gap)`</p>
        }

    }
    return (
        <Card>
            <CardHeader>
                <div className="flex flex-col gap-1 text-left">
                    <CardTitle className="text-base font-semibold">{showModelType(run)}</CardTitle>
                    <CardDescription className="text-left">{`🕒 ${getReadableTimeStamp(run.info.end_time)}`}</CardDescription>
                    <CardDescription className="text-left text-xs font-mono">
                        Run ID: {run.info.run_id}
                    </CardDescription>
                </div>

                <CardAction className="row-span-1 self">
                    {showRightBadge(validationRmseRounded)}
                </CardAction>

                <CardDescription className="col-span-full pt-3 text-left">
                    <Item className="gap-6 px-0 sm:px-2">
                        <ItemContent className="basis-1/3 items-center text-center flex-1!">
                            <ItemTitle>RMSE</ItemTitle>
                            <ItemDescription className="text-base font-semibold">
                                £{formatNumber(run.data.metrics.validation_rmse)}
                            </ItemDescription>
                        </ItemContent>

                        <ItemContent className="basis-1/3 items-center text-center flex-1!">
                            <ItemTitle>MSE</ItemTitle>
                            <ItemDescription className="text-base font-semibold">
                                £{formatNumber(run.data.metrics.validation_mse)}
                            </ItemDescription>
                        </ItemContent>

                        <ItemContent className="basis-1/3 items-center text-center flex-1!">
                            <ItemTitle>R²</ItemTitle>
                            <ItemDescription className="text-base font-semibold">
                                {formatNumber(run.data.metrics.validation_r2)}
                            </ItemDescription>
                        </ItemContent>
                    </Item>
                    <Item className="mt-4 flex flex-col gap-2 px-0" variant="muted">
                        <Item className="w-full items-center justify-between rounded-none border-none px-4 py-0"
                            size="sm">
                            <ItemTitle className="text-muted-foreground">Train RMSE</ItemTitle>
                            <ItemDescription className="text-base font-semibold">£{formatNumber(run.data.metrics.train_rmse)}</ItemDescription>
                        </Item>

                        <Item className="w-full items-center justify-between rounded-none border-none px-4 py-0"
                            size="sm">
                            <ItemTitle className="text-muted-foreground">Test RMSE</ItemTitle>
                            <ItemDescription className="text-base font-semibold">£{formatNumber(run.data.metrics.test_rmse)}</ItemDescription>
                        </Item>
                    </Item>
                    {validationRmse !== null && trainRmse !== null && trainRmse !== 0
                        ? showGeneralisationText((validationRmse - trainRmse) / trainRmse)
                        : <p className="text-center mt-8 p-3 text-muted-foreground">Generalization unavailable</p>}
                </CardDescription>
            </CardHeader>
        </Card >
    )
}

export default ModelMetricCard
