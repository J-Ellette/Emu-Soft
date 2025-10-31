"""
Test suite for Terraform Emulator
This file contains comprehensive tests for the Terraform IaC emulator

Developed by PowerShield
"""

import unittest
import json
from Infra_Code import (
    Terraform, Resource, DataSource, Variable, Output, Module,
    ResourceState, Plan, State,
    aws_instance, aws_s3_bucket, aws_security_group
)


class TestResource(unittest.TestCase):
    """Test Resource class"""
    
    def test_resource_creation(self):
        """Test resource creation"""
        resource = Resource("aws_instance", "web", {"ami": "ami-123", "instance_type": "t2.micro"})
        self.assertEqual(resource.type, "aws_instance")
        self.assertEqual(resource.name, "web")
        self.assertEqual(resource.state, ResourceState.PLANNED)
        self.assertIsNone(resource.id)
    
    def test_resource_full_name(self):
        """Test resource full name"""
        resource = Resource("aws_s3_bucket", "data", {})
        self.assertEqual(resource.full_name(), "aws_s3_bucket.data")


class TestDataSource(unittest.TestCase):
    """Test DataSource class"""
    
    def test_data_source_creation(self):
        """Test data source creation"""
        ds = DataSource("aws_ami", "ubuntu", {"most_recent": True})
        self.assertEqual(ds.type, "aws_ami")
        self.assertEqual(ds.name, "ubuntu")
    
    def test_data_source_full_name(self):
        """Test data source full name"""
        ds = DataSource("aws_vpc", "main", {})
        self.assertEqual(ds.full_name(), "data.aws_vpc.main")


class TestVariable(unittest.TestCase):
    """Test Variable class"""
    
    def test_variable_creation(self):
        """Test variable creation"""
        var = Variable("region", "string", "us-east-1", "AWS region")
        self.assertEqual(var.name, "region")
        self.assertEqual(var.type, "string")
        self.assertEqual(var.default, "us-east-1")
        self.assertEqual(var.value, "us-east-1")
    
    def test_variable_set_value(self):
        """Test setting variable value"""
        var = Variable("instance_count", "number", 1)
        var.set_value(5)
        self.assertEqual(var.value, 5)


class TestOutput(unittest.TestCase):
    """Test Output class"""
    
    def test_output_creation(self):
        """Test output creation"""
        output = Output("instance_ip", "192.168.1.1", "Instance IP address")
        self.assertEqual(output.name, "instance_ip")
        self.assertEqual(output.value, "192.168.1.1")
        self.assertFalse(output.sensitive)
    
    def test_sensitive_output(self):
        """Test sensitive output"""
        output = Output("db_password", "secret123", sensitive=True)
        self.assertTrue(output.sensitive)


class TestModule(unittest.TestCase):
    """Test Module class"""
    
    def test_module_creation(self):
        """Test module creation"""
        module = Module("vpc", "./modules/vpc", {"cidr": "10.0.0.0/16"})
        self.assertEqual(module.name, "vpc")
        self.assertEqual(module.source, "./modules/vpc")


class TestTerraformConfig(unittest.TestCase):
    """Test TerraformConfig class"""
    
    def test_add_resource(self):
        """Test adding a resource"""
        from Infra_Code import TerraformConfig
        config = TerraformConfig()
        
        resource = config.add_resource("aws_instance", "web", {
            "ami": "ami-123",
            "instance_type": "t2.micro"
        })
        
        self.assertIn("aws_instance.web", config.resources)
        self.assertEqual(resource.type, "aws_instance")
    
    def test_add_variable(self):
        """Test adding a variable"""
        from Infra_Code import TerraformConfig
        config = TerraformConfig()
        
        var = config.add_variable("region", "string", "us-east-1")
        
        self.assertIn("region", config.variables)
        self.assertEqual(var.default, "us-east-1")
    
    def test_add_output(self):
        """Test adding an output"""
        from Infra_Code import TerraformConfig
        config = TerraformConfig()
        
        output = config.add_output("instance_id", "i-12345")
        
        self.assertIn("instance_id", config.outputs)
        self.assertEqual(output.value, "i-12345")
    
    def test_add_provider(self):
        """Test adding a provider"""
        from Infra_Code import TerraformConfig
        config = TerraformConfig()
        
        config.add_provider("aws", {"region": "us-east-1"})
        
        self.assertIn("aws", config.providers)


class TestState(unittest.TestCase):
    """Test State class"""
    
    def test_state_creation(self):
        """Test state creation"""
        state = State()
        self.assertEqual(state.version, 4)
        self.assertEqual(len(state.resources), 0)
    
    def test_add_resource_to_state(self):
        """Test adding resource to state"""
        state = State()
        resource = Resource("aws_instance", "web", {"ami": "ami-123"})
        resource.id = "i-12345"
        resource.attributes = {"id": "i-12345", "ami": "ami-123"}
        
        state.add_resource(resource)
        
        self.assertIn("aws_instance.web", state.resources)
    
    def test_remove_resource_from_state(self):
        """Test removing resource from state"""
        state = State()
        resource = Resource("aws_instance", "web", {})
        resource.id = "i-12345"
        
        state.add_resource(resource)
        state.remove_resource("aws_instance.web")
        
        self.assertNotIn("aws_instance.web", state.resources)
    
    def test_state_to_json(self):
        """Test exporting state to JSON"""
        state = State()
        json_str = state.to_json()
        
        data = json.loads(json_str)
        self.assertEqual(data["version"], 4)


class TestPlan(unittest.TestCase):
    """Test Plan class"""
    
    def test_plan_creation(self):
        """Test plan creation"""
        from Infra_Code import TerraformConfig
        config = TerraformConfig()
        plan = Plan(config)
        
        self.assertEqual(len(plan.actions), 0)
    
    def test_plan_analyze(self):
        """Test plan analysis"""
        from Infra_Code import TerraformConfig
        config = TerraformConfig()
        config.add_resource("aws_instance", "web", {"ami": "ami-123"})
        
        plan = Plan(config)
        plan.analyze()
        
        self.assertEqual(len(plan.add), 1)
        self.assertEqual(len(plan.actions), 1)


class TestTerraform(unittest.TestCase):
    """Test Terraform main class"""
    
    def test_terraform_init(self):
        """Test terraform init"""
        tf = Terraform()
        tf.config.add_provider("aws", {"region": "us-east-1"})
        
        result = tf.init()
        self.assertTrue(result)
    
    def test_terraform_validate(self):
        """Test terraform validate"""
        tf = Terraform()
        result = tf.validate()
        self.assertTrue(result)
    
    def test_terraform_fmt(self):
        """Test terraform fmt"""
        tf = Terraform()
        result = tf.fmt()
        self.assertTrue(result)
    
    def test_terraform_plan(self):
        """Test terraform plan"""
        tf = Terraform()
        tf.config.add_resource("aws_instance", "web", {
            "ami": "ami-123",
            "instance_type": "t2.micro"
        })
        
        plan = tf.plan()
        self.assertIsNotNone(plan)
        self.assertEqual(len(plan.add), 1)
    
    def test_terraform_apply(self):
        """Test terraform apply"""
        tf = Terraform()
        tf.config.add_resource("aws_instance", "web", {
            "ami": "ami-123",
            "instance_type": "t2.micro"
        })
        
        tf.plan()
        result = tf.apply(auto_approve=True)
        
        self.assertTrue(result)
        resource = tf.config.resources["aws_instance.web"]
        self.assertEqual(resource.state, ResourceState.CREATED)
        self.assertIsNotNone(resource.id)
    
    def test_terraform_destroy(self):
        """Test terraform destroy"""
        tf = Terraform()
        resource = tf.config.add_resource("aws_instance", "web", {
            "ami": "ami-123",
            "instance_type": "t2.micro"
        })
        
        # First apply to create
        tf.plan()
        tf.apply(auto_approve=True)
        
        # Then destroy
        result = tf.destroy(auto_approve=True)
        self.assertTrue(result)
        self.assertEqual(resource.state, ResourceState.DESTROYED)
    
    def test_terraform_output(self):
        """Test terraform output"""
        tf = Terraform()
        tf.config.add_output("test_output", "test_value")
        
        value = tf.output("test_output")
        self.assertEqual(value, "test_value")
        
        all_outputs = tf.output()
        self.assertIn("test_output", all_outputs)
    
    def test_terraform_import(self):
        """Test terraform import"""
        tf = Terraform()
        result = tf.import_resource("aws_instance.imported", "i-existing123")
        
        self.assertTrue(result)
        self.assertIn("aws_instance.imported", tf.config.resources)
    
    def test_terraform_taint(self):
        """Test terraform taint"""
        tf = Terraform()
        tf.config.add_resource("aws_instance", "web", {})
        
        result = tf.taint("aws_instance.web")
        self.assertTrue(result)
    
    def test_terraform_refresh(self):
        """Test terraform refresh"""
        tf = Terraform()
        result = tf.refresh()
        self.assertTrue(result)
    
    def test_terraform_workspace_list(self):
        """Test workspace list"""
        tf = Terraform()
        workspaces = tf.workspace_list()
        
        self.assertIn("default", workspaces)
    
    def test_terraform_workspace_new(self):
        """Test creating new workspace"""
        tf = Terraform()
        result = tf.workspace_new("staging")
        self.assertTrue(result)
    
    def test_terraform_workspace_select(self):
        """Test selecting workspace"""
        tf = Terraform()
        result = tf.workspace_select("production")
        self.assertTrue(result)


class TestHelpers(unittest.TestCase):
    """Test helper functions"""
    
    def test_aws_instance_helper(self):
        """Test AWS instance helper"""
        resource_type, name, config = aws_instance("web", "ami-123", "t2.micro")
        
        self.assertEqual(resource_type, "aws_instance")
        self.assertEqual(name, "web")
        self.assertEqual(config["ami"], "ami-123")
        self.assertEqual(config["instance_type"], "t2.micro")
    
    def test_aws_s3_bucket_helper(self):
        """Test AWS S3 bucket helper"""
        resource_type, name, config = aws_s3_bucket("data", "my-bucket")
        
        self.assertEqual(resource_type, "aws_s3_bucket")
        self.assertEqual(name, "data")
        self.assertEqual(config["bucket"], "my-bucket")
    
    def test_aws_security_group_helper(self):
        """Test AWS security group helper"""
        resource_type, name, config = aws_security_group("web", "web-sg", "vpc-123")
        
        self.assertEqual(resource_type, "aws_security_group")
        self.assertEqual(name, "web")
        self.assertEqual(config["name"], "web-sg")
        self.assertEqual(config["vpc_id"], "vpc-123")


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_full_terraform_workflow(self):
        """Test complete Terraform workflow"""
        # Initialize Terraform
        tf = Terraform()
        
        # Add provider
        tf.config.add_provider("aws", {"region": "us-east-1"})
        
        # Add variables
        tf.config.add_variable("instance_type", "string", "t2.micro")
        tf.config.add_variable("region", "string", "us-east-1")
        
        # Add resources
        tf.config.add_resource("aws_instance", "web", {
            "ami": "ami-0c55b159cbfafe1f0",
            "instance_type": "t2.micro",
            "tags": {"Name": "WebServer"}
        })
        
        tf.config.add_resource("aws_s3_bucket", "data", {
            "bucket": "my-data-bucket",
            "acl": "private"
        })
        
        # Add outputs
        tf.config.add_output("instance_id", "TBD", "Web server instance ID")
        tf.config.add_output("bucket_name", "my-data-bucket", "S3 bucket name")
        
        # Initialize
        result = tf.init()
        self.assertTrue(result)
        
        # Validate
        result = tf.validate()
        self.assertTrue(result)
        
        # Plan
        plan = tf.plan()
        self.assertEqual(len(plan.add), 2)
        
        # Apply
        result = tf.apply(auto_approve=True)
        self.assertTrue(result)
        
        # Check resources are created
        web_instance = tf.config.resources["aws_instance.web"]
        self.assertEqual(web_instance.state, ResourceState.CREATED)
        self.assertIsNotNone(web_instance.id)
        
        s3_bucket = tf.config.resources["aws_s3_bucket.data"]
        self.assertEqual(s3_bucket.state, ResourceState.CREATED)
        
        # Get outputs
        bucket_name = tf.output("bucket_name")
        self.assertEqual(bucket_name, "my-data-bucket")
        
        # Destroy
        result = tf.destroy(auto_approve=True)
        self.assertTrue(result)
        
        # Verify destruction
        self.assertEqual(web_instance.state, ResourceState.DESTROYED)
        self.assertEqual(s3_bucket.state, ResourceState.DESTROYED)
    
    def test_multiple_resources_with_dependencies(self):
        """Test multiple resources with dependencies"""
        tf = Terraform()
        
        # VPC
        vpc = tf.config.add_resource("aws_vpc", "main", {
            "cidr_block": "10.0.0.0/16"
        })
        
        # Subnet (depends on VPC)
        subnet = tf.config.add_resource("aws_subnet", "public", {
            "vpc_id": "${aws_vpc.main.id}",
            "cidr_block": "10.0.1.0/24"
        })
        
        # Instance (depends on subnet)
        instance = tf.config.add_resource("aws_instance", "web", {
            "ami": "ami-123",
            "instance_type": "t2.micro",
            "subnet_id": "${aws_subnet.public.id}"
        })
        
        # Apply
        tf.plan()
        tf.apply(auto_approve=True)
        
        # All resources should be created
        self.assertEqual(vpc.state, ResourceState.CREATED)
        self.assertEqual(subnet.state, ResourceState.CREATED)
        self.assertEqual(instance.state, ResourceState.CREATED)


if __name__ == "__main__":
    print("Running Terraform Emulator tests...")
    unittest.main(verbosity=2)
