variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The region where the bucket will be created"
  type        = string
  default     = "us-central1"
}

variable "data_lake_bucket_name" {
  description = "The name of data lake bucket which have to be globally unique across gcs namespaces"
  type        = string
  default     = "london-housing-ai-data-lake"
}

variable "model_artifacts_bucket_name" {
  description = "The name of model artifact bucket which have to be globally unique across gcs namespaces"
  type        = string
  default     = "london-housing-ai-artifacts"
}

variable "storage_class" {
  description = "The name of storage class"
  type        = string
  default     = "STANDARD"
}

variable "versioning_enabled" {
  description = "Switch of whether or not GCS keeps the previous version on overwrite"
  default     = true
}
