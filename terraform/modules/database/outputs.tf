output "db_connection_url" {
  value = "postgresql://${var.db_user}:${var.db_password}@${google_sql_database_instance.postgres.ip_address[0].ip_address}/${var.db_name}"
}

output "db_private_ip" {
  value = google_sql_database_instance.postgres.ip_address[0].ip_address
}
