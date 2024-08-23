provider "aws" {
  region     = "us-west-2"
  access_key = "your_aws_access_key"
  secret_key = "your_aws_secret_key"
}

data "aws_iam_policy_document" "assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecsTaskExecutionRole" {
  name               = "ecsTestTaskExecutionRole"
  assume_role_policy = data.aws_iam_policy_document.assume_role_policy.json
}

resource "aws_iam_role_policy_attachment" "ecsTaskExecutionRole_policy" {
  role       = aws_iam_role.ecsTaskExecutionRole.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_default_vpc" "default_vpc" {
}

resource "aws_default_subnet" "default_subnet_a" {
  availability_zone = "us-west-2a"
}

resource "aws_security_group" "sg_service" {
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_ecs_cluster" "ecs_cluster" {
  name = "wager-optimiser-cluster"
}

resource "aws_ecs_task_definition" "ecs_task" {
  family                   = "wager-optimiser-task"
  cpu                      = "1024"
  memory                   = "3072"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.ecsTaskExecutionRole.arn
  
  container_definitions = <<DEFINITION
  [
    {
      "name": "wager-optimiser-backend",
      "image": "jackcky/wager-optimiser-backend",
      "cpu": 0,
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000
        }
      ],
      "essential": true
    },
    {
      "name": "wager-optimiser-frontend",
      "image": "jackcky/wager-optimiser-frontend",
      "cpu": 0,
      "portMappings": [
        {
          "containerPort": 8501,
          "hostPort": 8501
        }
      ],
      "essential": true,
      "environment": [
        {
          "name": "ENDPOINT",
          "value": "http://0.0.0.0:8000"
        }
      ]
    }
  ]
  DEFINITION
  
  runtime_platform {
    cpu_architecture        = "ARM64"
    operating_system_family = "LINUX"
  }
}  

resource "aws_ecs_service" "ecs_service" {
  name            = "wager-optimiser-service"
  cluster         = aws_ecs_cluster.ecs_cluster.id
  task_definition = aws_ecs_task_definition.ecs_task.arn
  launch_type     = "FARGATE"
  desired_count   = 1
  
  network_configuration {
    subnets          = [aws_default_subnet.default_subnet_a.id]
    assign_public_ip = true
    security_groups  = [aws_security_group.sg_service.id]
  }
}
