
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