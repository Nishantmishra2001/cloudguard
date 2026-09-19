variable "name_prefix" {
  description = "Prefix for all resource names"
  type        = string
  default     = "cloudguard"
}

variable "alert_email" {
  description = "Email that receives Cost Guard reports and alarms (you must confirm the SNS subscription)"
  type        = string
}

variable "dry_run" {
  description = "true = only report, never stop instances. Keep true until you trust it."
  type        = bool
  default     = true
}

variable "idle_hours" {
  description = "Instance must be idle for this many hours before it is stopped"
  type        = number
  default     = 2
}

variable "cpu_threshold" {
  description = "CPU percent under which an instance counts as idle"
  type        = number
  default     = 5
}

variable "schedule" {
  description = "EventBridge schedule expression"
  type        = string
  default     = "rate(1 hour)"
}

variable "target_tag_key" {
  description = "Only instances with this tag key are managed (opt-in)"
  type        = string
  default     = "AutoStop"
}

variable "target_tag_value" {
  description = "Tag value that opts an instance in"
  type        = string
  default     = "true"
}

variable "tags" {
  description = "Extra tags for created resources"
  type        = map(string)
  default     = {}
}
