# Terraform Emulator - Infrastructure as Code

This module emulates **Terraform**, an Infrastructure as Code (IaC) tool that allows you to define and provision infrastructure using declarative configuration files. Terraform enables you to manage infrastructure across multiple cloud providers with a consistent workflow.

## What is Terraform?

Terraform is an open-source infrastructure as code software tool created by HashiCorp. It provides:
- **Declarative configuration** - Define what you want, not how to create it
- **Infrastructure as Code** - Version control your infrastructure
- **Execution plans** - Preview changes before applying them
- **Resource graph** - Understand dependencies between resources
- **State management** - Track infrastructure state over time
- **Provider ecosystem** - Support for AWS, Azure, GCP, and more

Key features:
- Write infrastructure as code in HCL (HashiCorp Configuration Language)
- Plan and preview infrastructure changes
- Apply changes safely with automatic rollback
- Manage infrastructure lifecycle (create, update, destroy)
- Support for multiple cloud providers and services

## Features

This emulator implements core Terraform functionality:

### Resource Management
- **Resource definition** - Define infrastructure resources
- **Resource lifecycle** - Create, update, and destroy resources
- **Resource dependencies** - Track relationships between resources
- **Resource state** - Maintain current infrastructure state

### Configuration
- **Variables** - Parameterize configurations
- **Outputs** - Export values from infrastructure
- **Providers** - Configure cloud provider settings
- **Modules** - Reusable infrastructure components
- **Data sources** - Query existing infrastructure

### Operations
- **init** - Initialize Terraform working directory
- **plan** - Preview infrastructure changes
- **apply** - Apply infrastructure changes
- **destroy** - Destroy managed infrastructure
- **import** - Import existing infrastructure
- **validate** - Validate configuration files
- **fmt** - Format configuration files

### State Management
- **State tracking** - Track infrastructure state
- **State export** - Export state as JSON
- **State modification** - Add/remove resources from state

## Usage Examples

### Basic Infrastructure Setup

```python
from terraform_emulator import Terraform

# Create Terraform instance
tf = Terraform()

# Configure provider
tf.config.add_provider("aws", {
    "region": "us-east-1",
    "access_key": "YOUR_ACCESS_KEY",
    "secret_key": "YOUR_SECRET_KEY"
})

# Initialize Terraform
tf.init()
```

### Defining Resources

#### EC2 Instance

```python
from terraform_emulator import Terraform

tf = Terraform()

# Add an EC2 instance
tf.config.add_resource("aws_instance", "web_server", {
    "ami": "ami-0c55b159cbfafe1f0",
    "instance_type": "t2.micro",
    "tags": {
        "Name": "WebServer",
        "Environment": "Production"
    }
})
```

#### S3 Bucket

```python
# Add an S3 bucket
tf.config.add_resource("aws_s3_bucket", "data_bucket", {
    "bucket": "my-application-data",
    "acl": "private",
    "versioning": {
        "enabled": True
    }
})
```

#### Security Group

```python
# Add a security group
tf.config.add_resource("aws_security_group", "web_sg", {
    "name": "web-security-group",
    "description": "Security group for web servers",
    "vpc_id": "vpc-12345",
    "ingress": [
        {
            "from_port": 80,
            "to_port": 80,
            "protocol": "tcp",
            "cidr_blocks": ["0.0.0.0/0"]
        },
        {
            "from_port": 443,
            "to_port": 443,
            "protocol": "tcp",
            "cidr_blocks": ["0.0.0.0/0"]
        }
    ]
})
```

### Using Helper Functions

```python
from terraform_emulator import Terraform, aws_instance, aws_s3_bucket

tf = Terraform()

# Use helper functions for common resources
resource_type, name, config = aws_instance(
    "app_server",
    "ami-0c55b159cbfafe1f0",
    "t2.micro",
    tags={"Name": "AppServer"}
)

tf.config.add_resource(resource_type, name, config)

# S3 bucket helper
resource_type, name, config = aws_s3_bucket(
    "logs",
    "application-logs-bucket",
    acl="private"
)

tf.config.add_resource(resource_type, name, config)
```

### Variables

Define reusable parameters:

```python
from terraform_emulator import Terraform

tf = Terraform()

# Define variables
tf.config.add_variable("region", "string", "us-east-1", "AWS region")
tf.config.add_variable("instance_type", "string", "t2.micro", "EC2 instance type")
tf.config.add_variable("instance_count", "number", 2, "Number of instances")

# Set variable values
tf.config.variables["region"].set_value("us-west-2")
tf.config.variables["instance_count"].set_value(3)

# Use variables in resources (conceptually)
tf.config.add_resource("aws_instance", "web", {
    "ami": "ami-123",
    "instance_type": "${var.instance_type}",
    "count": "${var.instance_count}"
})
```

### Outputs

Export values from your infrastructure:

```python
from terraform_emulator import Terraform

tf = Terraform()

# Add resources
tf.config.add_resource("aws_instance", "web", {
    "ami": "ami-123",
    "instance_type": "t2.micro"
})

# Define outputs
tf.config.add_output(
    "instance_id",
    "${aws_instance.web.id}",
    "The ID of the web server instance"
)

tf.config.add_output(
    "instance_ip",
    "${aws_instance.web.public_ip}",
    "Public IP of web server"
)

# After apply, get output values
tf.plan()
tf.apply(auto_approve=True)

instance_id = tf.output("instance_id")
print(f"Instance ID: {instance_id}")

# Get all outputs
all_outputs = tf.output()
for name, value in all_outputs.items():
    print(f"{name}: {value}")
```

### Sensitive Outputs

```python
# Mark outputs as sensitive
tf.config.add_output(
    "db_password",
    "super-secret-password",
    "Database password",
    sensitive=True
)
```

### Plan and Apply

#### Creating Infrastructure

```python
from terraform_emulator import Terraform

tf = Terraform()

# Configure resources
tf.config.add_provider("aws", {"region": "us-east-1"})
tf.config.add_resource("aws_instance", "web", {
    "ami": "ami-123",
    "instance_type": "t2.micro"
})

# Initialize
tf.init()

# Validate configuration
tf.validate()

# Create execution plan
plan = tf.plan()

# Review plan summary
print(plan.summary())

# Apply changes
tf.apply(auto_approve=True)

# Check state
tf.show()
```

#### Updating Infrastructure

```python
# Modify resource configuration
tf.config.resources["aws_instance.web"].config["instance_type"] = "t2.small"

# Plan the update
plan = tf.plan()

# Apply the update
tf.apply(auto_approve=True)
```

#### Destroying Infrastructure

```python
# Destroy all managed infrastructure
tf.destroy(auto_approve=True)
```

### State Management

#### Viewing State

```python
from terraform_emulator import Terraform

tf = Terraform()

# After applying resources
tf.config.add_resource("aws_instance", "web", {"ami": "ami-123"})
tf.plan()
tf.apply(auto_approve=True)

# Show current state
tf.show()

# Export state to JSON
state_json = tf.state.to_json()
print(state_json)
```

#### Importing Existing Resources

```python
# Import an existing EC2 instance
tf.import_resource("aws_instance.existing", "i-1234567890abcdef0")

# The resource is now managed by Terraform
```

### Advanced Operations

#### Tainting Resources

Mark a resource for recreation:

```python
# Taint a resource (will be destroyed and recreated on next apply)
tf.taint("aws_instance.web")

# Apply to recreate
tf.plan()
tf.apply(auto_approve=True)

# Untaint if needed
tf.untaint("aws_instance.web")
```

#### Refreshing State

```python
# Refresh state to match real infrastructure
tf.refresh()
```

#### Formatting Configuration

```python
# Format configuration files
tf.fmt()

# Check if files are properly formatted
tf.fmt(check=True)
```

### Workspaces

Manage multiple environments:

```python
from terraform_emulator import Terraform

tf = Terraform()

# List workspaces
workspaces = tf.workspace_list()
print(f"Available workspaces: {workspaces}")

# Create new workspace
tf.workspace_new("staging")
tf.workspace_new("production")

# Switch workspace
tf.workspace_select("staging")

# Deploy to staging
tf.config.add_resource("aws_instance", "web", {
    "ami": "ami-123",
    "instance_type": "t2.micro"
})
tf.plan()
tf.apply(auto_approve=True)

# Switch to production
tf.workspace_select("production")

# Deploy to production with different config
tf.config.add_resource("aws_instance", "web", {
    "ami": "ami-123",
    "instance_type": "t2.large"  # Larger instance for production
})
tf.plan()
tf.apply(auto_approve=True)
```

### Modules

Organize reusable infrastructure:

```python
from terraform_emulator import Terraform

tf = Terraform()

# Use a module
tf.config.add_module("vpc", "./modules/vpc", {
    "cidr_block": "10.0.0.0/16",
    "availability_zones": ["us-east-1a", "us-east-1b"],
    "public_subnets": ["10.0.1.0/24", "10.0.2.0/24"],
    "private_subnets": ["10.0.10.0/24", "10.0.20.0/24"]
})

tf.config.add_module("app_cluster", "./modules/app", {
    "vpc_id": "${module.vpc.vpc_id}",
    "subnet_ids": "${module.vpc.private_subnet_ids}",
    "instance_count": 3
})
```

### Complete Application Example

```python
from terraform_emulator import Terraform

def deploy_web_application():
    """Deploy a complete web application infrastructure"""
    
    # Initialize Terraform
    tf = Terraform()
    
    # Configure AWS provider
    tf.config.add_provider("aws", {
        "region": "us-east-1",
        "profile": "default"
    })
    
    # Define variables
    tf.config.add_variable("environment", "string", "production")
    tf.config.add_variable("instance_count", "number", 2)
    
    # VPC
    tf.config.add_resource("aws_vpc", "main", {
        "cidr_block": "10.0.0.0/16",
        "enable_dns_hostnames": True,
        "tags": {"Name": "main-vpc"}
    })
    
    # Subnet
    tf.config.add_resource("aws_subnet", "public", {
        "vpc_id": "${aws_vpc.main.id}",
        "cidr_block": "10.0.1.0/24",
        "availability_zone": "us-east-1a",
        "map_public_ip_on_launch": True,
        "tags": {"Name": "public-subnet"}
    })
    
    # Security Group
    tf.config.add_resource("aws_security_group", "web", {
        "name": "web-sg",
        "description": "Security group for web servers",
        "vpc_id": "${aws_vpc.main.id}",
        "ingress": [
            {"from_port": 80, "to_port": 80, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"]},
            {"from_port": 443, "to_port": 443, "protocol": "tcp", "cidr_blocks": ["0.0.0.0/0"]}
        ],
        "egress": [
            {"from_port": 0, "to_port": 0, "protocol": "-1", "cidr_blocks": ["0.0.0.0/0"]}
        ]
    })
    
    # EC2 Instances
    tf.config.add_resource("aws_instance", "web", {
        "ami": "ami-0c55b159cbfafe1f0",
        "instance_type": "t2.micro",
        "subnet_id": "${aws_subnet.public.id}",
        "vpc_security_group_ids": ["${aws_security_group.web.id}"],
        "user_data": "#!/bin/bash\napt-get update\napt-get install -y nginx",
        "tags": {"Name": "web-server", "Environment": "${var.environment}"}
    })
    
    # S3 Bucket for static assets
    tf.config.add_resource("aws_s3_bucket", "assets", {
        "bucket": "my-app-static-assets",
        "acl": "public-read",
        "website": {
            "index_document": "index.html",
            "error_document": "error.html"
        }
    })
    
    # Outputs
    tf.config.add_output("vpc_id", "${aws_vpc.main.id}", "VPC ID")
    tf.config.add_output("instance_id", "${aws_instance.web.id}", "Web server instance ID")
    tf.config.add_output("instance_public_ip", "${aws_instance.web.public_ip}", "Public IP")
    tf.config.add_output("bucket_url", "${aws_s3_bucket.assets.website_endpoint}", "Static assets URL")
    
    # Terraform workflow
    print("=== Initializing Terraform ===")
    tf.init()
    
    print("\n=== Validating Configuration ===")
    tf.validate()
    
    print("\n=== Creating Execution Plan ===")
    plan = tf.plan()
    
    print("\n=== Applying Changes ===")
    tf.apply(auto_approve=True)
    
    print("\n=== Infrastructure Deployed ===")
    print(f"VPC ID: {tf.output('vpc_id')}")
    print(f"Instance ID: {tf.output('instance_id')}")
    print(f"Public IP: {tf.output('instance_public_ip')}")
    print(f"Assets URL: {tf.output('bucket_url')}")
    
    return tf

# Deploy infrastructure
tf = deploy_web_application()

# Later, to destroy
# tf.destroy(auto_approve=True)
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python test_terraform_emulator.py

# Run with verbose output
python test_terraform_emulator.py -v

# Run specific test class
python -m unittest test_terraform_emulator.TestTerraform
```

The test suite covers:
- Resource, variable, and output management
- State operations
- Plan generation
- Apply and destroy workflows
- Import and taint operations
- Workspace management
- Complete integration scenarios

## Use Cases

Perfect for:
- **Infrastructure Automation** - Automate infrastructure provisioning
- **Multi-cloud Deployment** - Deploy across multiple cloud providers
- **Development Environments** - Create consistent dev environments
- **Testing** - Test infrastructure code without cloud resources
- **CI/CD Integration** - Automate infrastructure in pipelines
- **Learning** - Learn Terraform concepts and workflows

## Best Practices

### Resource Naming

```python
# Good: Descriptive, consistent names
tf.config.add_resource("aws_instance", "web_server", {})
tf.config.add_resource("aws_s3_bucket", "application_logs", {})

# Bad: Generic, unclear names
tf.config.add_resource("aws_instance", "server1", {})
tf.config.add_resource("aws_s3_bucket", "bucket", {})
```

### Use Variables for Reusability

```python
# Good: Parameterized configuration
tf.config.add_variable("environment", "string", "dev")
tf.config.add_variable("instance_type", "string", "t2.micro")

# Use in resources
tf.config.add_resource("aws_instance", "web", {
    "instance_type": "${var.instance_type}",
    "tags": {"Environment": "${var.environment}"}
})
```

### Always Plan Before Apply

```python
# Good: Review changes before applying
plan = tf.plan()
# Review the plan
tf.apply(auto_approve=True)

# Bad: Applying without planning
# tf.apply(auto_approve=True)  # Don't skip planning!
```

## Limitations

This is an emulator for development and learning:
- No actual cloud API calls
- Simplified state management
- No remote state backends
- No provider plugins
- Simplified dependency resolution
- No actual resource creation
- Limited HCL parsing

## Supported Operations

### Commands
- ✅ init - Initialize working directory
- ✅ plan - Create execution plan
- ✅ apply - Apply changes
- ✅ destroy - Destroy infrastructure
- ✅ validate - Validate configuration
- ✅ fmt - Format files
- ✅ show - Show state
- ✅ import - Import resources
- ✅ taint/untaint - Mark for recreation
- ✅ refresh - Refresh state
- ✅ output - Show outputs

### Configuration
- ✅ Resources
- ✅ Data sources
- ✅ Variables
- ✅ Outputs
- ✅ Providers
- ✅ Modules

### Workspaces
- ✅ List workspaces
- ✅ Create workspace
- ✅ Select workspace

## Compatibility

Emulates patterns from:
- Terraform 1.x CLI
- HCL configuration concepts
- Common Terraform workflows
- AWS provider patterns

## License

Part of the Emu-Soft project. See main repository LICENSE.
