export interface PredictionRequest {
    postcode: string;
    property_type: "F" | "D" | "T" | "S";
    is_new_build?: "Y" | "N";
    is_leasehold?: "Y" | "N";
}

export interface PredictionResponse {
    predicted_price: number;
    confidence_interval: [number, number];
    model_version: string;
    run_id: string;
    features_used: {
        user_provided: string[];
        enriched: string[];
        defaulted: string[];
    };
}