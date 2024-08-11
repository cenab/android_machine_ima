# Provider configuration
provider "aws" {
  region = "us-west-2"  # Change this to your preferred region
}

# Variables
variable "key_name" {
  description = "Name of an existing EC2 KeyPair to enable SSH access to the instances"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "ssh_location" {
  description = "The IP address range that can be used to SSH to the EC2 instances"
  type        = string
  default     = "0.0.0.0/0"
}

# VPC
resource "aws_vpc" "android_orchestrator_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "AndroidOrchestratorVPC"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "android_orchestrator_igw" {
  vpc_id = aws_vpc.android_orchestrator_vpc.id
}

# Public Subnet
resource "aws_subnet" "android_orchestrator_public_subnet" {
  vpc_id                  = aws_vpc.android_orchestrator_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "AndroidOrchestratorPublicSubnet"
  }
}

# Route Table
resource "aws_route_table" "android_orchestrator_public_rt" {
  vpc_id = aws_vpc.android_orchestrator_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.android_orchestrator_igw.id
  }

  tags = {
    Name = "AndroidOrchestratorPublicRouteTable"
  }
}

# Route Table Association
resource "aws_route_table_association" "android_orchestrator_public_rt_assoc" {
  subnet_id      = aws_subnet.android_orchestrator_public_subnet.id
  route_table_id = aws_route_table.android_orchestrator_public_rt.id
}

# Security Group
resource "aws_security_group" "android_orchestrator_sg" {
  name        = "AndroidOrchestratorServerSG"
  description = "Security group for Android Orchestrator server"
  vpc_id      = aws_vpc.android_orchestrator_vpc.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_location]
  }

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EC2 Instance
resource "aws_instance" "android_orchestrator_server" {
  ami           = "ami-0c55b159cbfafe1f0"  # Amazon Linux 2 AMI (HVM), SSD Volume Type
  instance_type = var.instance_type
  key_name      = var.key_name

  vpc_security_group_ids = [aws_security_group.android_orchestrator_sg.id]
  subnet_id              = aws_subnet.android_orchestrator_public_subnet.id

  user_data = base64encode(<<-EOF
              #!/bin/bash
              yum update -y
              yum install -y docker git python3 python3-pip
              systemctl start docker
              systemctl enable docker
              usermod -a -G docker ec2-user
              pip3 install flask flask-socketio
              git clone https://github.com/yourusername/android-machine-orchestrator.git
              cd android-machine-orchestrator
              docker build -t android-orchestrator .
              docker run -d -p 5000:5000 android-orchestrator
              EOF
  )

  tags = {
    Name = "AndroidOrchestratorServer"
  }
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# Outputs
output "server_public_ip" {
  description = "Public IP address of the Android Orchestrator server"
  value       = aws_instance.android_orchestrator_server.public_ip
}

output "server_public_dns" {
  description = "Public DNS name of the Android Orchestrator server"
  value       = aws_instance.android_orchestrator_server.public_dns
}