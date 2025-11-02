variable "project_id" {
  type = string
}

variable "model_artifacts_bucket_name" {
  description = "The name of model artifact bucket which have to be globally unique across gcs namespaces"
  type        = string
  default     = "london-housing-ai-artifacts"
}

variable "db_password" {
  type = string
}

variable "db_private_ip" {
  type = string
}

variable "network_private_ip" {
  type = string
}

variable "mlflow_image_uri" {
  type = string
}
