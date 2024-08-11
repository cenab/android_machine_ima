# Provider configuration
provider "aws" {
  region = var.aws_region
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

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "client_count" {
  description = "Number of client instances to create"
  type        = number
  default     = 5
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
  name        = "AndroidOrchestratorSG"
  description = "Security group for Android Orchestrator"
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

# ECR Repositories
resource "aws_ecr_repository" "android_orchestrator" {
  name = "android-orchestrator"
}

resource "aws_ecr_repository" "android_client" {
  name = "android-client"
}

# ECS Cluster
resource "aws_ecs_cluster" "android_orchestrator" {
  name = "android-orchestrator-cluster"
}

# ECS Task Definition for Orchestrator
resource "aws_ecs_task_definition" "orchestrator" {
  family                   = "android-orchestrator-server"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"

  container_definitions = jsonencode([{
    name  = "orchestrator"
    image = "${aws_ecr_repository.android_orchestrator.repository_url}:latest"
    portMappings = [{
      containerPort = 5000
      hostPort      = 5000
    }]
    command = ["python", "orchestrator/server.py"]
  }])
}

# ECS Task Definition for Client
resource "aws_ecs_task_definition" "client" {
  family                   = "android-orchestrator-client"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"

  container_definitions = jsonencode([{
    name  = "client"
    image = "${aws_ecr_repository.android_client.repository_url}:latest"
    command = ["python", "client/client.py"]
  }])
}

# ECS Service for Orchestrator
resource "aws_ecs_service" "orchestrator" {
  name            = "android-orchestrator-server"
  cluster         = aws_ecs_cluster.android_orchestrator.id
  task_definition = aws_ecs_task_definition.orchestrator.arn
  launch_type     = "FARGATE"
  desired_count   = 1

  network_configuration {
    subnets          = [aws_subnet.android_orchestrator_public_subnet.id]
    assign_public_ip = true
    security_groups  = [aws_security_group.android_orchestrator_sg.id]
  }
}

# ECS Service for Clients
resource "aws_ecs_service" "client" {
  name            = "android-orchestrator-client"
  cluster         = aws_ecs_cluster.android_orchestrator.id
  task_definition = aws_ecs_task_definition.client.arn
  launch_type     = "FARGATE"
  desired_count   = var.client_count

  network_configuration {
    subnets          = [aws_subnet.android_orchestrator_public_subnet.id]
    assign_public_ip = true
    security_groups  = [aws_security_group.android_orchestrator_sg.id]
  }
}

# Null resource to build and push Docker images
resource "null_resource" "docker_builds" {
  triggers = {
    orchestrator_dockerfile = filemd5("${path.module}/orchestrator/Dockerfile")
    client_dockerfile      = filemd5("${path.module}/client/Dockerfile")
  }

  provisioner "local-exec" {
    command = <<EOF
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.android_orchestrator.repository_url}
      docker build -t ${aws_ecr_repository.android_orchestrator.repository_url}:latest -f orchestrator/Dockerfile ./orchestrator
      docker push ${aws_ecr_repository.android_orchestrator.repository_url}:latest

      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.android_client.repository_url}
      docker build -t ${aws_ecr_repository.android_client.repository_url}:latest -f client/Dockerfile ./client
      docker push ${aws_ecr_repository.android_client.repository_url}:latest
    EOF
  }
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# Outputs
output "orchestrator_repository_url" {
  description = "The URL of the ECR repository for the orchestrator"
  value       = aws_ecr_repository.android_orchestrator.repository_url
}

output "client_repository_url" {
  description = "The URL of the ECR repository for the client"
  value       = aws_ecr_repository.android_client.repository_url
}

output "ecs_cluster_name" {
  description = "The name of the ECS cluster"
  value       = aws_ecs_cluster.android_orchestrator.name
}

output "orchestrator_service_name" {
  description = "The name of the ECS service running the orchestrator"
  value       = aws_ecs_service.orchestrator.name
}

output "client_service_name" {
  description = "The name of the ECS service running the clients"
  value       = aws_ecs_service.client.name
}