# Local terraform deployment

## Before everything

remove any existing buckets

```bash
gsutil rm -r gs://london-housing-ai-artifacts
gsutil rm -r gs://london-housing-ai-data-lake
```

If buckets already exist:

```bash
terraform import google_storage_bucket.data_lake_bucket london-housing-ai-data-lake
terraform import google_storage_bucket.model_artifacts_bucket london-housing-ai-artifacts
```

Check whether:

- `terraform-network` already exists or not
- `london-housing-db-instance` already exists or not
- `terraform-instance` already exists or not

```bash
gcloud compute networks list
gcloud sql instances list
gcloud storage buckets list
gcloud compute instances list
```

If exists:

```bash
terraform import google_compute_network.vpc_network projects/abiding-sunset-333516/global/networks/terraform-network
terraform import module.database.google_sql_database_instance.postgres projects/abiding-sunset-333516/instances/london-housing-db-instance
terraform import google_compute_instance.vm_instance projects/abiding-sunset-333516/zones/us-central1-a/instances/terraform-instance
```

Verify import success:

```bash
terraform state list
```

Deploy

```bash
terraform init
terraform apply -var-file="terraform.tfvars" -auto-approve
```

Expose mlflow tracking uri

```bash
export MLFLOW_TRACKING_URI=$(terraform output -raw mlflow_tracking_uri)
```

Manual clean up

```bash
gcloud iam service-accounts delete mlflow-sa@abiding-sunset-333516.iam.gserviceaccount.com --quiet
gcloud compute instances delete mlflow-instance --zone=us-central1-a --quiet
gcloud sql instances delete london-housing-db-instance
gcloud storage rm -r gs://london-housing-ai-artifacts
gcloud storage rm -r gs://london-housing-ai-data-lake
gcloud compute networks subnets delete london-housing-vpc --region=us-central1 --quiet
gcloud compute networks delete london-housing-vpc
```
