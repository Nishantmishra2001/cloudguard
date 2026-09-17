data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}


data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_security_group" "cloudguard" {
  name        = "cloudguard-preview-sg"
  description = "Security group for CloudGuard preview environment"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "CloudGuard application"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project     = "CloudGuard"
    Environment = "Preview"
  }
}

resource "aws_instance" "cloudguard" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  key_name      = "nishantkey"

  subnet_id                   = data.aws_subnets.default.ids[0]
  vpc_security_group_ids      = [aws_security_group.cloudguard.id]
  associate_public_ip_address = true

  user_data = <<-EOF
            #!/bin/bash
            apt-get update -y
            apt-get install -y docker.io git

            systemctl enable docker
            systemctl start docker

            git clone https://github.com/Nishantmishra2001/cloudguard.git /opt/cloudguard

            cd /opt/cloudguard

            docker build -t cloudguard:latest .

            docker run -d \
              --name cloudguard \
              --restart unless-stopped \
              -p 5000:5000 \
              cloudguard:latest
            EOF

  tags = {
    Name        = "cloudguard-preview"
    Project     = "CloudGuard"
    Environment = "Preview"
  }
}


output "cloudguard_public_ip" {
  description = "Public IP of CloudGuard preview environment"
  value       = aws_instance.cloudguard.public_ip
}

output "cloudguard_url" {
  description = "CloudGuard preview URL"
  value       = "http://${aws_instance.cloudguard.public_ip}:5000"
}
