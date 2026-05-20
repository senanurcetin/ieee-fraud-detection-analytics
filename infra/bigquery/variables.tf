variable "project_id" {
  description = "Google Cloud project id."
  type        = string
}

variable "location" {
  description = "BigQuery dataset location."
  type        = string
  default     = "US"
}
