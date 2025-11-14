resource "google_service_account" "mlflow_sa" {
  account_id   = "mlflow-sa"
  display_name = "MLflow Server SA"
}

resource "google_project_iam_member" "mlflow_sa_gcs" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.mlflow_sa.email}"
}

resource "google_project_iam_member" "mlflow_sa_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.mlflow_sa.email}"
}

resource "google_compute_instance" "mlflow_server" {
  name         = "mlflow-instance"
  machine_type = "e2-micro"
  tags         = ["mlflow-server"]

  boot_disk {
    initialize_params {
      image = "cos-cloud/cos-stable" # container-optimized OS
      size  = 20
    }
  }

  network_interface {
    network = var.network_private_ip
    access_config {}
  }

  service_account {
    email  = google_service_account.mlflow_sa.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    # Docker run command as startup script
    "gce-container-declaration" = <<-EOT
        spec:
            containers:
                - name: mlflow
                image: "${var.mlflow_image_uri}"
                args:
                    - "server"
                    - "--backend-store-uri"
                    - "postgresql://mlflow_user:${var.db_password}@${var.db_private_ip}:5432/mlflow"
                    - "--default-artifact-root"
                    - "gs://${var.model_artifacts_bucket_name}/artifacts
                    - "--host"
                    - "0.0.0.0"
                    - "--port"
                    - "5000"
                ports:
                    - name: mlflow
                    containerPort: 5000
            restartPolicy: Always    
    EOT
  }

  metadata_startup_script = <<-SCRIPT
    echo "MLflow server container launched."
    SCRIPT
}

