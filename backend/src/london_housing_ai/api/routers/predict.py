from __future__ import annotations

import numpy as np
from fastapi import APIRouter, HTTPException

from london_housing_ai.api.schemas import PredictionRequest, PredictResponse
from london_housing_ai.api.services import mlflow_service
from london_housing_ai.api.services.model_cache import get_or_load_model
from london_housing_ai.api.services.transformer_cache import get_or_load_transformer
from london_housing_ai.services.postcode_service import resolve_district
from london_housing_ai.utils.logger import get_logger

router = APIRouter(tags=["prediction"])
logger = get_logger()


@router.post("/predict", response_model=PredictResponse)
async def predict(data: PredictionRequest) -> PredictResponse:
    # Resolve postcode -> district
    district = await resolve_district(data.postcode)
    if district is None:
        raise HTTPException(
            status_code=400, detail=f"Postcode '{data.postcode}' not found"
        )

    user_input = data.model_dump()
    user_input["district"] = district

    run_id = mlflow_service.get_latest_finished_run_id()
    if not run_id:
        raise HTTPException(status_code=503, detail="No trained runs available")

    model = get_or_load_model(run_id)

    transformer = get_or_load_transformer(run_id)
    features = transformer.transform(user_input)
    logger.info(features.to_dict(orient="records"))
    logger.info(features.dtypes)

    use_log_target = mlflow_service.run_uses_log_target(run_id, default=True)
    try:
        preds = model.predict(features)
        value = float(np.expm1(preds[0])) if use_log_target else float(preds[0])
    except Exception:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail="Prediction failed")

    return PredictResponse(predicted_price=round(value, 2), run_id=run_id)
