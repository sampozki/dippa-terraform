
variable "default_tags" {
  description = "Default tags for the resources"
  type        = map(string)
  default = {
    repository  = "https://github.com/sampozki/dippa-terraform"
    tool        = "terraform"
    deployed-by = "manual"
    owner       = "sampozki"
    application = "tf-drift-monitor"
  }
}

variable "region" {
  type        = string
  description = "AWS region where the monitoring system infrastructure is deployed."
  default     = "eu-north-1"
}

variable "name" {
  type        = string
  description = "Logical name prefix used for all monitoring system AWS resources."
  default     = "tf-drift-monitor"
}

variable "state_bucket" {
  type        = string
  description = "Name of the S3 bucket containing the Terraform state file to monitor."
  default     = "sampozki-thesis-state"
}

variable "state_key" {
  type        = string
  description = "Object key (path) of the Terraform state file inside the S3 bucket."
  default     = "test-terraform.tfstate"
}

variable "state_region" {
  type        = string
  description = "AWS region where the monitored Terraform state bucket resides."
  default     = "eu-north-1"
}

variable "results_bucket" {
  type        = string
  description = "Optional S3 bucket for storing monitoring execution summaries."
  default     = ""
}

variable "schedule_expression" {
  type        = string
  description = "EventBridge schedule expression defining how often monitoring runs."
  default     = "rate(6 hours)"
}

variable "ecr_image_uri" {
  type        = string
  description = "Full ECR image URI containing the Lambda runtime and Terraform binary."
}
