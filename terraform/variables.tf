variable "project_id" {
  type = string
}

variable "region" {
  default = "us-central1"
}

variable "zone" {
  default = "us-central1-a"
}

variable "db_name" {
  type    = string
  default = "london-housing-db"
}

variable "db_password" {
  type    = string
  default = "password"
}

variable "mlflow_image_uri" {
  type    = string
  default = "ghcr.io/mlflow/mlflow:latest"
}
