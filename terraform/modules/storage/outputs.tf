output "bucket_name" {
    value = google_storage_bucket.data_bucket.name
}

output "bucket_url" {
    value = "gs://${google_storage_bucket.data_bucket.name}"
}