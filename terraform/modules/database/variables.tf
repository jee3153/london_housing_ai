variable "region" {
  type    = string
  default = "europe-west2"
}

variable "db_user" {
  type    = string
  default = "postgres"
}

variable "db_password" {
  type    = string
  default = "password"
}

variable "db_name" {
  type    = string
  default = "london-housing-db"
}
