import DataQuality from '../components/data_quality/DataQuality';
export interface MlflowRunMetrics {
  test_rmse: number;
  test_mse: number;
  validation_mse: number;
  validation_rmse: number;
  validation_r2: number;
  train_rmse: number;
}

export interface MlflowRunParams {
  loss_function: string;
  iterations: string;
  depth: string;
  learning_rate: string;
  early_stopping_rounds: string;
  random_seed: string;
  raw_csv_sha256: string;
  model_class: string;
}

export interface MlflowRunTags {
  "mlflow.user": string;
  "mlflow.source.name": string;
  "mlflow.source.type": string;
  "mlflow.runName": string;
}

export interface MlflowRunPayload {
  metrics: MlflowRunMetrics;
  params: MlflowRunParams;
  tags: MlflowRunTags;
}

export interface MlflowRunResponse {
  data: MlflowRunPayload;
  info: MlflowRunInfo;
}

export interface MlflowRunInfo {
  artifact_uri: string;
  end_time: number;
  experiment_id: string;
  lifecycle_stage: string;
  run_id: string;
  run_uuid: string;
  start_time: number;
  status: string;
  user_id: string;
}

export type MlflowRunListResponse = MlflowRunResponse[];

export interface DataQualityMissingData {
  column: string;
  count: string;
  percentage: string;
}

interface DataQualitySchemaSummaryColumns {
  price: string;
  date: string;
  postcode: string;
  property_type: string;
  "old/new": string;
  duration: string;
  country: string;
}
interface DataQualitySchemaSummaryDataCounts {
  columns: string;
  rows: string;
}

interface DataQualitySchemaSummary {
  counts: DataQualitySchemaSummaryDataCounts;
  columns: DataQualitySchemaSummaryColumns;
}

interface DataQualityNumericStat {
  column: string;
  count: string;
  mean: string;
  std: string;
  min: string;
  "25%": string;
  "50%": string;
  "75%": string;
  max: string;
}

interface DataQualityOutliers {
  price: string;
}

interface DataQualityTrainValueDrift {
  price: string;
}

interface DataQualityPropertyType {
  "Terraced": string;
  "Semi-detached": string;
  "Detached": string;
  "Flats / maisonette": string;
  "Other": string;
}

interface DataQualityBuildAgeType {
  "Historic property": string;
  "New build": string;
}

interface DataQualityDuration {
  "Freehold": string;
  "Leasehold": string;
}

interface DataQualityCategoryDistribution {
  property_type: DataQualityPropertyType;
  "old/new": DataQualityBuildAgeType;
  duration: DataQualityDuration;
}

export interface MlflowDataQualityPayload {
  filename: string;
  missing: DataQualityMissingData[];
  schema_summary: DataQualitySchemaSummary;
  numeric_stats: DataQualityNumericStat[];
  outliers: DataQualityOutliers;
  train_val_drift: DataQualityTrainValueDrift;
  category_distribution: DataQualityCategoryDistribution;
  message?: string;
}