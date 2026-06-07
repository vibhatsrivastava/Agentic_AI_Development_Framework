# Data source to fetch the latest Amazon Linux 2023 AMI
# This is region-agnostic and always retrieves the latest version
data "aws_ssm_parameter" "amazon_linux_2023_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

# EC2 instance resource with tags for drift detection testing
resource "aws_instance" "drift_test" {
  ami           = data.aws_ssm_parameter.amazon_linux_2023_ami.value
  instance_type = var.instance_type

  # Tags that will be validated against policies/tags.yaml
  tags = {
    Name        = var.instance_name
    Environment = var.environment
    Owner       = var.owner
    Project     = "drift-detector-demo"
    ManagedBy   = "terraform"
  }

  # Root block device - Free Tier includes 30 GB
  root_block_device {
    volume_type = "gp3"
    volume_size = 8
    encrypted   = true

    tags = {
      Name = "${var.instance_name}-root-volume"
    }
  }

  # Metadata options for enhanced security
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # IMDSv2 only
    http_put_response_hop_limit = 1
  }

  lifecycle {
    create_before_destroy = false
  }
}
