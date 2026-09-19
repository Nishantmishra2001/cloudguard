variable "aws_region" {
  description = "AWS region for CloudGuard"
  type        = string
  default     = "us-east-1"
}


variable "alert_email" {
  description = "Email for Cost Guard reports"
  type        = string
}
