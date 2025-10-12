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

resource "google_compute_network" "vpc_network" {
  name = "terraform-network"
}

resource "google_compute_instance" "vm_instance" {
  name         = "terraform-instance"
  machine_type = "f1-micro"
  tags         = ["web", "dev"]

  boot_disk {
    initialize_params {
      image = "cos-cloud/cos-stable"
    }
  }

  network_interface {
    network = google_compute_network.vpc_network.name
    access_config { # gives VM an external IP address, even without any arguments in the block.
    }
  }
}

module "database" {
  source      = "./modules/database"
  region      = var.region
  db_password = var.db_password
}

module "storage" {
  source = "./modules/storage"
  project_id = var.project_id
}