output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.drift_test.id
}

output "instance_public_ip" {
  description = "Public IP address of the EC2 instance (if assigned)"
  value       = aws_instance.drift_test.public_ip
}

output "instance_private_ip" {
  description = "Private IP address of the EC2 instance"
  value       = aws_instance.drift_test.private_ip
}

output "instance_state" {
  description = "Current state of the EC2 instance"
  value       = aws_instance.drift_test.instance_state
}

output "ami_id" {
  description = "AMI ID used for the EC2 instance"
  value       = aws_instance.drift_test.ami
}

output "state_file_path" {
  description = "Path to Terraform state file for drift detection"
  value       = "${path.module}/terraform.tfstate"
}

output "tags" {
  description = "Tags applied to the EC2 instance"
  value       = aws_instance.drift_test.tags
}
