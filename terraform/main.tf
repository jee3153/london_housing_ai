terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "7.5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

module "network" {
  source = "./modules/network"
}

module "database" {
  source      = "./modules/database"
  region      = var.region
  db_name     = var.db_name
  db_password = var.db_password
}

module "storage" {
  source     = "./modules/storage"
  project_id = var.project_id
}

module "mlflow" {
  source             = "./modules/mlflow"
  db_private_ip      = module.database.db_private_ip
  db_password        = var.db_password
  project_id         = var.project_id
  network_private_ip = module.network.network_id
  mlflow_image_uri   = var.mlflow_image_uri
}
