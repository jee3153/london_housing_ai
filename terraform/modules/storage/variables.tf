variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The region where the bucket will be created"
  type        = string
  default     = "us-central1"
}

variable "bucket_name" {
  description = "The name of bucket which have to be globally unique across gcs namespaces"
  type        = string
  default     = "london-housing-ai"
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
