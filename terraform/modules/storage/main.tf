resource "google_storage_bucket" "data_bucket" {
  name                        = var.bucket_name
  project                     = var.project_id
  location                    = var.region
  storage_class               = var.storage_class
  force_destroy               = true
  uniform_bucket_level_access = true # control bucket permissions only via IAM roled (no per object ACLs) for simplified security

  versioning {
    enabled = var.versioning_enabled
  }
  # automatically delete objects older than 90 days
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 90
    }
  }

  # shows billing report in GCP
  labels = {
    environment = "dev"
    project     = "london-housing-ai"
  }
}

