variable "project" {
  type    = string
  default = "newsimpact"
}

variable "region" {
  description = "Primary region. Pick by client data-residency first, price second."
  type        = string
  default     = "us-east-1"
}

variable "monthly_budget_usd" {
  description = "Total monthly AWS spend you are comfortable with."
  type        = number
  default     = 20
}

variable "anomaly_threshold_usd" {
  description = "Alert when an unexpected spike exceeds this many USD."
  type        = number
  default     = 5
}

variable "alert_emails" {
  description = "Who receives budget/anomaly alerts. Set in terraform.tfvars (git-ignored)."
  type        = list(string)
  validation {
    condition     = length(var.alert_emails) > 0
    error_message = "Provide at least one alert email."
  }
}
