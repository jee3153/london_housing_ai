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
