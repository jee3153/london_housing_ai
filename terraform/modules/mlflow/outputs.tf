output "mlflow_internal_ip" {
  description = "Private IP for internal service-to-service connections"
  value       = google_compute_instance.mlflow_server.network_interface[0].network_ip
}

output "mlflow_image_uri" {
  description = "The container image deployed for MLflow server"
  value       = var.mlflow_image_uri
}
