import type { ModelExperimentProps } from '../../types/props'
import { Item, ItemDescription, ItemHeader, ItemTitle } from '../ui/item'
import type { MlflowDataQualityPayload } from '../../types/mlflow'
import { useEffect, useState } from 'react'

function DataQuality({ runs }: ModelExperimentProps) {
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
    return (
        <section className="space-y-10">
            <Item className="flex flex-col items-start text-left px-0">
                <ItemHeader className="flex flex-col items-start gap-1">
                    <ItemTitle className="text-lg font-semibold">Data Quality Assessment</ItemTitle>
                    <ItemDescription>Monitor data quality metrics and trends</ItemDescription>
                </ItemHeader>
            </Item>
        </section>
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