variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type (t2.micro is Free Tier eligible)"
  type        = string
  default     = "t2.micro"
}

variable "instance_name" {
  description = "Name tag for the EC2 instance"
  type        = string
  default     = "drift-detector-test-instance"
}

variable "environment" {
  description = "Environment tag (production, staging, development)"
  type        = string
  default     = "production"
}

variable "owner" {
  description = "Owner tag for the EC2 instance"
  type        = string
  default     = "test-user"
}
