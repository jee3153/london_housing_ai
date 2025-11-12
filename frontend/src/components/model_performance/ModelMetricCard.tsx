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
    const showRightBadge = (rmse: number): JSX.Element => {
        if (rmse === bestRmse) {
            return <Badge>Champion</Badge>
        }
        if (rmse !== null && rmse === secondBest) {
            return <Badge variant="secondary">Challenger</Badge>
        }
        return <Badge variant="outline">Archive</Badge>
    }

    const showModelType = (run: MlflowRunResponse) => {
        const modelType = run.data.params.model_class
        if (Number(run.data.metrics.validation_rmse.toFixed(2)) == bestRmse) {
            return `${modelType} 🏆`
        }
        return modelType
    }
    return (
        <Card>
            <CardHeader>
                <div className="flex flex-col gap-1 text-left">
                    <CardTitle className="text-base font-semibold">{showModelType(run)}</CardTitle>
                    <CardDescription className="text-left">{`🕒 ${getReadableTimeStamp(run.info.end_time)}`}</CardDescription>
                </div>

                <CardAction className="row-span-1 self">
                    {showRightBadge(Number(run.data.metrics.validation_rmse.toFixed(2)))}
                </CardAction>

                <CardDescription className="col-span-full pt-3 text-left">
                    <Item className="gap-6 px-0 sm:px-2">
                        <ItemContent className="basis-1/3 items-center text-center flex-1!">
                            <ItemTitle>RMSE</ItemTitle>
                            <ItemDescription className="text-base font-semibold">
                                £{run.data.metrics.validation_rmse.toFixed(2)}
                            </ItemDescription>
                        </ItemContent>

                        <ItemContent className="basis-1/3 items-center text-center flex-1!">
                            <ItemTitle>MSE</ItemTitle>
                            <ItemDescription className="text-base font-semibold">
                                £{run.data.metrics.validation_mse.toFixed(2)}
                            </ItemDescription>
                        </ItemContent>

                        <ItemContent className="basis-1/3 items-center text-center flex-1!">
                            <ItemTitle>R²</ItemTitle>
                            <ItemDescription className="text-base font-semibold">
                                {run.data.metrics.validation_r2.toFixed(2)}
                            </ItemDescription>
                        </ItemContent>
                    </Item>
                    <Item className="mt-4 flex flex-col gap-2 px-0" variant="muted">
                        <Item className="w-full items-center justify-between rounded-none border-none px-4 py-0"
                            size="sm">
                            <ItemTitle className="text-muted-foreground">Train RMSE</ItemTitle>
                            <ItemDescription className="text-base font-semibold">£{run.data.metrics.train_rmse.toFixed(2)}</ItemDescription>
                        </Item>

                        <Item className="w-full items-center justify-between rounded-none border-none px-4 py-0"
                            size="sm">
                            <ItemTitle className="text-muted-foreground">Test RMSE</ItemTitle>
                            <ItemDescription className="text-base font-semibold">£{run.data.metrics.test_rmse.toFixed(2)}</ItemDescription>
                        </Item>
                    </Item>
                </CardDescription>
            </CardHeader>
        </Card>
    )
}

export default ModelMetricCard