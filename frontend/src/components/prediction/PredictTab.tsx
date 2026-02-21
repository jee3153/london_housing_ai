import { useState } from "react";
import type { PredictionRequest, PredictionResponse } from "../../types/predict";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

const API_BASE = import.meta.env.VITE_API_URL ?? "/api";

const PROPERTY_TYPES = [
    { value: "F", label: "Flat / Maisonette" },
    { value: "D", label: "Detached" },
    { value: "S", label: "Semi-Detached" },
    { value: "T", label: "Terraced" },
];

async function fetchPrediction(req: PredictionRequest): Promise<PredictionResponse> {
    const res = await fetch(`${API_BASE}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `Request failed: ${res.status}`);
    }
    return res.json();
}

export default function PredictTab() {
    const [postcode, setPostcode] = useState("");
    const [propertyType, setPropertyType] = useState<"F" | "D" | "S" | "T">("F");
    const [isNewBuild, setIsNewBuild] = useState<"Y" | "N">("N");
    const [isLeasehold, setIsLeasehold] = useState<"Y" | "N">("N");
    const [result, setResult] = useState<PredictionResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResult(null);
        try {
            const data = await fetchPrediction({
                postcode,
                property_type: propertyType,
                is_new_build: isNewBuild,
                is_leasehold: isLeasehold,
            });
            setResult(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Unknown error");
        } finally {
            setLoading(false);
        }
    }

    const fmt = (n: number) =>
        `£${Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 }).format(n)}`;

    return (
        <div className="max-w-xl mx-auto mt-8 space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle>Predict London Housing Price</CardTitle>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">

                        <div className="flex flex-col gap-1">
                            <label className="text-sm font-medium">Postcode</label>
                            <input
                                type="text"
                                value={postcode}
                                onChange={e => setPostcode(e.target.value)}
                                placeholder="e.g. SW1A 1AA"
                                required
                                className="border rounded px-3 py-2 text-sm"
                            />
                        </div>

                        <div className="flex flex-col gap-1">
                            <label className="text-sm font-medium">Property Type</label>
                            <select
                                value={propertyType}
                                onChange={e => setPropertyType(e.target.value as typeof propertyType)}
                                className="border rounded px-3 py-2 text-sm"
                            >
                                {PROPERTY_TYPES.map(pt => (
                                    <option key={pt.value} value={pt.value}>{pt.label}</option>
                                ))}
                            </select>
                        </div>

                        <div className="flex gap-6">
                            <label className="flex items-center gap-2 text-sm">
                                <input
                                    type="checkbox"
                                    checked={isNewBuild === "Y"}
                                    onChange={e => setIsNewBuild(e.target.checked ? "Y" : "N")}
                                />
                                New Build
                            </label>
                            <label className="flex items-center gap-2 text-sm">
                                <input
                                    type="checkbox"
                                    checked={isLeasehold === "Y"}
                                    onChange={e => setIsLeasehold(e.target.checked ? "Y" : "N")}
                                />
                                Leasehold
                            </label>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-black text-white py-2 rounded text-sm font-medium hover:bg-gray-800 disabled:opacity-50"
                        >
                            {loading ? "Predicting…" : "Predict Price"}
                        </button>
                    </form>
                </CardContent>
            </Card>

            {error && (
                <div className="text-red-600 text-sm border border-red-200 rounded p-3 bg-red-50">
                    {error}
                </div>
            )}

            {result && (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-2xl">{fmt(result.predicted_price)}</CardTitle>
                        <p className="text-sm text-gray-500">
                            Range: {fmt(result.confidence_interval[0])} – {fmt(result.confidence_interval[1])}
                        </p>
                    </CardHeader>
                    <CardContent className="space-y-2 text-sm text-gray-600">
                        <p>Model: {result.model_version}</p>
                        {result.features_used.user_provided.length > 0 && (
                            <p>
                                User-provided features: {result.features_used.user_provided.join(", ")}
                            </p>
                        )}
                        {result.features_used.enriched.length > 0 && (
                            <p>
                                Enriched features: {result.features_used.enriched.join(", ")}
                            </p>
                        )}
                        {result.features_used.defaulted.length > 0 && (
                            <p className="text-amber-600">
                                ⚠ Defaulted features: {result.features_used.defaulted.join(", ")}
                            </p>
                        )}
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
