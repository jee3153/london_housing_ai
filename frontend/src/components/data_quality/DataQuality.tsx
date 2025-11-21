import { Item, ItemDescription, ItemHeader, ItemTitle } from '../ui/item'
import type { MlflowDataQualityPayload } from '../../types/mlflow'
import { useEffect, useState } from 'react'
import { Card, CardDescription, CardHeader, CardTitle, CardContent } from '../ui/card'
import { Badge } from '../ui/badge'
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "../ui/table"
import type { DataQualityMissingData } from '../../types/mlflow'


function missingRepotTable(missingData: DataQualityMissingData[]) {
    const renderTableHeader = (column: string, index: number, dataLength: number) => {
        let className = ""
        if (index == 0) {
            className = "w-[100px]"
        }
        if (index == dataLength - 1) {
            className = "text-right"
        }
        return <TableHead className={className}>{column.charAt(0).toUpperCase() + column.slice(1)}</TableHead>
    }
    return (
        <Table>
            <TableHeader>
                <TableRow key="missingness">
                    {Object.keys(missingData[0]).map((col, index) => renderTableHeader(col, index, missingData.length))}
                </TableRow>
            </TableHeader>
            <TableBody>
                {missingData.map((missing) => (
                    <TableRow >
                        <TableCell className="font-medium">{missing.column}</TableCell>
                        <TableCell>{missing.count}</TableCell>
                        <TableCell className="text-right">{missing.percentage}%</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    )
}


function DataQuality() {
    const [dataQuality, setDataQuality] = useState<MlflowDataQualityPayload | null>(null)
    useEffect(() => {
        async function fetchDataQuality() {
            try {
                const dataQualityData = await getDataQualityForLatestExperiment();
                if ("message" in dataQualityData) {
                    console.info(dataQuality?.message)
                } else {
                    setDataQuality(dataQualityData)
                    console.log(dataQualityData)
                }
            } catch (error) {
                console.error("Error fetching data quality metadata", error)
            }
        }
        fetchDataQuality()
    }, [])
    if (!dataQuality) {
        return <section><p>There is no data quality metadata to present.</p></section>
    }
    const { missing, schema_summary, numeric_stats, outliers, train_val_drift, category_distribution } = dataQuality

    const badgeForColumnType = (columnType: string) => {
        const icon: string = columnType === "object" ? "📄" : "🔢"
        return <Badge variant="outline">{`${icon} ${columnType}`}</Badge>
    }

    const getMissings = (missingData: DataQualityMissingData[]) => {
        let missingColumns = 0
        let missingTotal = 0

        for (const missing of missingData) {
            const missingCountNumber = Number(missing.count)
            if (missingCountNumber > 0) {
                missingColumns++
                missingTotal += missingCountNumber
            }
        }
        return { "missingTotal": missingTotal, "missingColumns": missingColumns }
    }
    const { missingTotal, missingColumns } = getMissings(missing)

    return (
        <section className="max-w-6xl mx-auto px-4 space-y-10">
            <Item className="flex flex-col items-start text-left px-0">
                <ItemHeader className="flex flex-col items-start gap-1">
                    <ItemTitle className="text-lg font-semibold">Data Quality Assessment</ItemTitle>
                    <ItemDescription>Monitor data quality metrics and trends</ItemDescription>
                </ItemHeader>
            </Item>

            <div className="flex flex-col gap-6 md:flex-row md:flex-wrap w-full min-w-0">
                <Card className="flex-1 min-w-0">
                    <CardHeader>
                        <CardTitle>Schema Validation</CardTitle>
                        <CardDescription>{`Dataset: ${schema_summary.counts.rows} rows x ${schema_summary.counts.columns} columns`}</CardDescription>
                    </CardHeader>
                    <CardContent className="min-w-0">
                        <div className="rounded-lg border bg-muted/50 p-4">
                            {Object.entries(schema_summary.columns).map(([columnName, columnType]) => (
                                <div key={columnName} className="flex justify-between py-1">
                                    <span>{columnName}</span>
                                    {badgeForColumnType(columnType)}
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                <Card className="flex-1 min-w-0">
                    <CardHeader>
                        <CardTitle>Missingness Report</CardTitle>
                        <CardDescription>{missingTotal} missing values across {missingColumns} columns</CardDescription>
                    </CardHeader>
                    <CardContent className="min-w-0">
                        <div className="max-w-full overflow-x-auto">
                            {missingRepotTable(missing)}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </section >
    )
}

async function getDataQualityForLatestExperiment(): Promise<MlflowDataQualityPayload> {
    const response = await fetch("http://localhost:7777/artifacts/data_quality");
    if (!response.ok) {
        throw new Error(`Failed to fetch run metadata: ${response.statusText}`);
    }
    const data = (await response.json()) as MlflowDataQualityPayload;
    return data;
}

export default DataQuality