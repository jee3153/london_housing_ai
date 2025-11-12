import { Card, CardHeader, CardTitle } from "./ui/card"
import { ChartContainer } from "./ui/chart"
import { CartesianGrid, Line, LineChart, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import type { LineChartCardProps } from '../types/props';


export function LineChartCard<TData extends Record<string, unknown>>({ data, chartConfig, dataKey, stroke, title }: LineChartCardProps<TData>) {
    const lineData = data.map(data => Number(data[`${dataKey}`]))
    return (
        <Card>
            <CardHeader>
                <CardTitle>{title}</CardTitle>
                <ChartContainer config={chartConfig} className="min-h-[200px] w-full">
                    <LineChart data={data}>
                        <CartesianGrid stroke="#eee" strokeDasharray="5 5" />
                        <XAxis
                            dataKey="timestamp"
                            label={{ value: "Date", position: "insideBottom", offset: -5 }}
                            angle={-45}
                            textAnchor="end"
                            height={80} />
                        <YAxis
                            tickFormatter={(value) =>
                                `£${Intl.NumberFormat("en-GB", { notation: "compact" }).format(value)}`
                            }
                            domain={[Math.min(...lineData), Math.max(...lineData)]}
                            tickMargin={10}
                        />
                        <Tooltip />
                        <Legend
                            verticalAlign="top"
                            align="right"
                            wrapperStyle={{ paddingBottom: 8 }}
                        />
                        <Line type="monotone" dataKey={dataKey} stroke={stroke} />
                    </LineChart>
                </ChartContainer>
            </CardHeader>
        </Card>
    )
}

export default LineChartCard