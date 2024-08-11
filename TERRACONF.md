# Terraform Configuration Explanation

## Provider Configuration

```hcl
provider "aws" {
  region = var.aws_region
}
```
This sets up the AWS provider, specifying the region to use from a variable.

## Variables

```hcl
variable "key_name" {
  description = "Name of an existing EC2 KeyPair to enable SSH access to the instances"
  type        = string
}
```
This defines a variable for the EC2 key pair name.

```hcl
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}
```
This defines a variable for the EC2 instance type with a default value.

```hcl
variable "ssh_location" {
  description = "The IP address range that can be used to SSH to the EC2 instances"
  type        = string
  default     = "0.0.0.0/0"
}
```
This defines a variable for the allowed SSH access IP range.

```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}
```
This defines a variable for the AWS region with a default value.

```hcl
variable "client_count" {
  description = "Number of client instances to create"
  type        = number
  default     = 5
}
```
This defines a variable for the number of client instances to create.

## VPC Configuration

```hcl
resource "aws_vpc" "android_orchestrator_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "AndroidOrchestratorVPC"
  }
}
```
This creates a VPC with the specified CIDR block and DNS settings.

## Internet Gateway

```hcl
resource "aws_internet_gateway" "android_orchestrator_igw" {
  vpc_id = aws_vpc.android_orchestrator_vpc.id
}
```
This creates an Internet Gateway and attaches it to the VPC.

## Public Subnet

```hcl
resource "aws_subnet" "android_orchestrator_public_subnet" {
  vpc_id                  = aws_vpc.android_orchestrator_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "AndroidOrchestratorPublicSubnet"
  }
}
```
This creates a public subnet within the VPC.

## Route Table

```hcl
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
```
This creates a route table for the public subnet, routing all traffic to the Internet Gateway.

## Route Table Association

```hcl
resource "aws_route_table_association" "android_orchestrator_public_rt_assoc" {
  subnet_id      = aws_subnet.android_orchestrator_public_subnet.id
  route_table_id = aws_route_table.android_orchestrator_public_rt.id
}
```
This associates the route table with the public subnet.

## Security Group

```hcl
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
```
This creates a security group allowing SSH access and traffic on port 5000, as well as all outbound traffic.

## ECR Repositories

```hcl
resource "aws_ecr_repository" "android_orchestrator" {
  name = "android-orchestrator"
}

resource "aws_ecr_repository" "android_client" {
  name = "android-client"
}
```
These create ECR repositories for the orchestrator and client Docker images.

## ECS Cluster

```hcl
resource "aws_ecs_cluster" "android_orchestrator" {
  name = "android-orchestrator-cluster"
}
```
This creates an ECS cluster to run the containers.

## ECS Task Definitions

### Orchestrator Task

```hcl
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
```
This defines the ECS task for the orchestrator, specifying the Docker image to use and the command to run.

### Client Task

```hcl
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
```
This defines the ECS task for the client, similar to the orchestrator.

## ECS Services

### Orchestrator Service

```hcl
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
```
This creates an ECS service to run the orchestrator task.

### Client Service

```hcl
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
```
This creates an ECS service to run the client tasks, with the number of tasks specified by `var.client_count`.

## Docker Build and Push

```hcl
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
```
This null resource builds and pushes the Docker images to the ECR repositories.

## Data Source

```hcl
data "aws_availability_zones" "available" {
  state = "available"
}
```
This retrieves information about available AWS availability zones.

## Outputs

```hcl
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
```