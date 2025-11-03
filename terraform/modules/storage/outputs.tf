output "data_lake_bucket_name" {
  value = google_storage_bucket.data_lake_bucket.name
}

output "data_lake_bucket_url" {
  value = "gs://${google_storage_bucket.data_lake_bucket.name}"
}

output "model_artifact_bucket_name" {
  value = google_storage_bucket.model_artifacts_bucket.name
}

output "model_artifact_bucket_url" {
  value = "gs://${google_storage_bucket.model_artifacts_bucket.name}"
}
