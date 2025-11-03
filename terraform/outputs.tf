output "db_connection_url" {
  value = module.database.db_connection_url
}

output "mlflow_tracking_uri" {
  value = module.storage.data_lake_bucket_url
}

output "mlflow_artifact_uri" {
  value = module.storage.model_artifact_bucket_url
}
