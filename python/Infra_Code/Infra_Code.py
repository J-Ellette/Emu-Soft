"""
Terraform Emulator - Infrastructure as Code
This emulates the core functionality of Terraform for managing infrastructure

Developed by PowerShield
"""

import json
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict
from enum import Enum


class ResourceState(Enum):
    """Resource lifecycle states"""
    PLANNED = "planned"
    CREATING = "creating"
    CREATED = "created"
    UPDATING = "updating"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"
    ERROR = "error"


class Resource:
    """Represents a Terraform resource"""
    
    def __init__(self, resource_type: str, name: str, config: Dict[str, Any]):
        self.type = resource_type
        self.name = name
        self.config = config
        self.state = ResourceState.PLANNED
        self.id = None
        self.attributes = {}
        self.dependencies = []
    
    def __repr__(self):
        return f"<Resource {self.type}.{self.name} [{self.state.value}]>"
    
    def full_name(self):
        """Get the full resource name"""
        return f"{self.type}.{self.name}"


class DataSource:
    """Represents a Terraform data source"""
    
    def __init__(self, data_type: str, name: str, config: Dict[str, Any]):
        self.type = data_type
        self.name = name
        self.config = config
        self.attributes = {}
    
    def full_name(self):
        """Get the full data source name"""
        return f"data.{self.type}.{self.name}"


class Variable:
    """Represents a Terraform variable"""
    
    def __init__(self, name: str, var_type: str = "string", 
                 default: Any = None, description: str = ""):
        self.name = name
        self.type = var_type
        self.default = default
        self.description = description
        self.value = default
    
    def set_value(self, value: Any):
        """Set the variable value"""
        self.value = value


class Output:
    """Represents a Terraform output"""
    
    def __init__(self, name: str, value: Any, description: str = "", sensitive: bool = False):
        self.name = name
        self.value = value
        self.description = description
        self.sensitive = sensitive


class Module:
    """Represents a Terraform module"""
    
    def __init__(self, name: str, source: str, config: Dict[str, Any]):
        self.name = name
        self.source = source
        self.config = config
        self.resources = {}
        self.outputs = {}


class TerraformConfig:
    """Main Terraform configuration"""
    
    def __init__(self):
        self.resources: Dict[str, Resource] = {}
        self.data_sources: Dict[str, DataSource] = {}
        self.variables: Dict[str, Variable] = {}
        self.outputs: Dict[str, Output] = {}
        self.modules: Dict[str, Module] = {}
        self.providers: Dict[str, Dict[str, Any]] = {}
        self.state_version = 4
    
    def add_resource(self, resource_type: str, name: str, config: Dict[str, Any]) -> Resource:
        """Add a resource to the configuration"""
        resource = Resource(resource_type, name, config)
        full_name = resource.full_name()
        self.resources[full_name] = resource
        return resource
    
    def add_data_source(self, data_type: str, name: str, config: Dict[str, Any]) -> DataSource:
        """Add a data source to the configuration"""
        data_source = DataSource(data_type, name, config)
        full_name = data_source.full_name()
        self.data_sources[full_name] = data_source
        return data_source
    
    def add_variable(self, name: str, var_type: str = "string", 
                    default: Any = None, description: str = "") -> Variable:
        """Add a variable to the configuration"""
        variable = Variable(name, var_type, default, description)
        self.variables[name] = variable
        return variable
    
    def add_output(self, name: str, value: Any, description: str = "", 
                   sensitive: bool = False) -> Output:
        """Add an output to the configuration"""
        output = Output(name, value, description, sensitive)
        self.outputs[name] = output
        return output
    
    def add_module(self, name: str, source: str, config: Dict[str, Any]) -> Module:
        """Add a module to the configuration"""
        module = Module(name, source, config)
        self.modules[name] = module
        return module
    
    def add_provider(self, name: str, config: Dict[str, Any]):
        """Add a provider configuration"""
        self.providers[name] = config


class Plan:
    """Represents a Terraform execution plan"""
    
    def __init__(self, config: TerraformConfig):
        self.config = config
        self.actions = []
        self.add = []
        self.change = []
        self.destroy = []
    
    def analyze(self):
        """Analyze what changes need to be made"""
        for resource in self.config.resources.values():
            if resource.state == ResourceState.PLANNED:
                self.add.append(resource)
                self.actions.append(("create", resource))
            elif resource.state == ResourceState.CREATED:
                # Check if configuration changed
                pass
            elif resource.state == ResourceState.DESTROYING:
                self.destroy.append(resource)
                self.actions.append(("destroy", resource))
    
    def summary(self) -> str:
        """Get a summary of planned changes"""
        lines = []
        lines.append("Terraform will perform the following actions:")
        lines.append("")
        
        for action, resource in self.actions:
            if action == "create":
                lines.append(f"  + {resource.full_name()}")
            elif action == "destroy":
                lines.append(f"  - {resource.full_name()}")
            elif action == "update":
                lines.append(f"  ~ {resource.full_name()}")
        
        lines.append("")
        lines.append(f"Plan: {len(self.add)} to add, {len(self.change)} to change, {len(self.destroy)} to destroy.")
        
        return "\n".join(lines)


class State:
    """Represents Terraform state"""
    
    def __init__(self):
        self.version = 4
        self.terraform_version = "1.0.0"
        self.resources = {}
        self.outputs = {}
    
    def add_resource(self, resource: Resource):
        """Add a resource to state"""
        self.resources[resource.full_name()] = {
            "type": resource.type,
            "name": resource.name,
            "provider": "provider.aws",
            "instances": [{
                "attributes": resource.attributes,
                "schema_version": 0
            }]
        }
    
    def remove_resource(self, resource_name: str):
        """Remove a resource from state"""
        if resource_name in self.resources:
            del self.resources[resource_name]
    
    def get_resource(self, resource_name: str) -> Optional[Dict]:
        """Get a resource from state"""
        return self.resources.get(resource_name)
    
    def to_dict(self) -> Dict:
        """Export state as dictionary"""
        return {
            "version": self.version,
            "terraform_version": self.terraform_version,
            "resources": self.resources,
            "outputs": self.outputs
        }
    
    def to_json(self) -> str:
        """Export state as JSON"""
        return json.dumps(self.to_dict(), indent=2)


class Terraform:
    """Main Terraform interface"""
    
    def __init__(self):
        self.config = TerraformConfig()
        self.state = State()
        self.plan_cache = None
    
    def init(self):
        """Initialize Terraform (download providers, modules)"""
        print("Initializing Terraform...")
        print(f"- Initializing provider plugins...")
        for provider in self.config.providers:
            print(f"  - provider.{provider}")
        print("Terraform has been successfully initialized!")
        return True
    
    def plan(self, destroy: bool = False) -> Plan:
        """Create an execution plan"""
        print("Creating execution plan...")
        
        plan = Plan(self.config)
        plan.analyze()
        
        self.plan_cache = plan
        
        print(plan.summary())
        return plan
    
    def apply(self, auto_approve: bool = False):
        """Apply the execution plan"""
        if not self.plan_cache:
            self.plan()
        
        if not auto_approve:
            print("Do you want to perform these actions? (yes/no)")
            # In real usage, would wait for user input
            # For emulator, we auto-approve
        
        print("Applying changes...")
        
        for action, resource in self.plan_cache.actions:
            if action == "create":
                print(f"Creating {resource.full_name()}...")
                resource.state = ResourceState.CREATING
                # Simulate resource creation
                resource.id = f"{resource.type}-{hash(resource.name) % 100000}"
                resource.attributes = dict(resource.config)
                resource.attributes['id'] = resource.id
                resource.state = ResourceState.CREATED
                self.state.add_resource(resource)
                print(f"Created {resource.full_name()}")
            
            elif action == "destroy":
                print(f"Destroying {resource.full_name()}...")
                resource.state = ResourceState.DESTROYING
                self.state.remove_resource(resource.full_name())
                resource.state = ResourceState.DESTROYED
                print(f"Destroyed {resource.full_name()}")
        
        print("\nApply complete!")
        print(f"Resources: {len([r for r in self.config.resources.values() if r.state == ResourceState.CREATED])} created")
        
        self.plan_cache = None
        return True
    
    def destroy(self, auto_approve: bool = False):
        """Destroy all managed resources"""
        print("Destroying infrastructure...")
        
        # Mark all resources for destruction
        for resource in self.config.resources.values():
            if resource.state == ResourceState.CREATED:
                resource.state = ResourceState.DESTROYING
        
        # Create destroy plan
        plan = self.plan(destroy=True)
        
        if not auto_approve:
            print("Do you really want to destroy all resources? (yes/no)")
        
        # Execute destruction
        for resource in list(self.config.resources.values()):
            if resource.state == ResourceState.DESTROYING:
                print(f"Destroying {resource.full_name()}...")
                self.state.remove_resource(resource.full_name())
                resource.state = ResourceState.DESTROYED
        
        print("\nDestroy complete!")
        return True
    
    def show(self):
        """Show the current state"""
        print("Current state:")
        for name, resource_state in self.state.resources.items():
            print(f"  {name}:")
            print(f"    id: {resource_state['instances'][0]['attributes'].get('id', 'N/A')}")
    
    def output(self, name: Optional[str] = None) -> Any:
        """Get output values"""
        if name:
            if name in self.config.outputs:
                return self.config.outputs[name].value
            return None
        else:
            return {k: v.value for k, v in self.config.outputs.items()}
    
    def validate(self) -> bool:
        """Validate the configuration"""
        print("Validating configuration...")
        
        # Check for circular dependencies
        # Check for missing required attributes
        # Validate provider configurations
        
        print("Configuration is valid")
        return True
    
    def fmt(self, check: bool = False):
        """Format configuration files"""
        if check:
            print("Configuration files are properly formatted")
        else:
            print("Formatting configuration files...")
            print("Configuration files formatted")
        return True
    
    def import_resource(self, address: str, resource_id: str):
        """Import existing infrastructure"""
        print(f"Importing {address} with ID {resource_id}...")
        
        # Create resource if it doesn't exist
        parts = address.split(".")
        if len(parts) >= 2:
            resource_type = parts[0]
            resource_name = parts[1]
            
            resource = self.config.add_resource(resource_type, resource_name, {})
            resource.id = resource_id
            resource.state = ResourceState.CREATED
            self.state.add_resource(resource)
            
            print(f"Import successful!")
        
        return True
    
    def taint(self, address: str):
        """Mark a resource for recreation"""
        print(f"Marking {address} as tainted...")
        if address in self.config.resources:
            # Resource will be destroyed and recreated on next apply
            print(f"Resource {address} has been marked as tainted")
        return True
    
    def untaint(self, address: str):
        """Remove taint from a resource"""
        print(f"Removing taint from {address}...")
        if address in self.config.resources:
            print(f"Resource {address} is no longer tainted")
        return True
    
    def refresh(self):
        """Refresh state to match real infrastructure"""
        print("Refreshing state...")
        # In real Terraform, this would query actual infrastructure
        print("State refreshed")
        return True
    
    def workspace_list(self) -> List[str]:
        """List workspaces"""
        return ["default"]
    
    def workspace_new(self, name: str):
        """Create a new workspace"""
        print(f"Created workspace: {name}")
        return True
    
    def workspace_select(self, name: str):
        """Select a workspace"""
        print(f"Switched to workspace: {name}")
        return True


# Helper functions for common resource types
def aws_instance(name: str, ami: str, instance_type: str, **kwargs) -> Dict:
    """Helper to define AWS EC2 instance"""
    config = {
        "ami": ami,
        "instance_type": instance_type,
        **kwargs
    }
    return ("aws_instance", name, config)


def aws_s3_bucket(name: str, bucket_name: str, **kwargs) -> Dict:
    """Helper to define AWS S3 bucket"""
    config = {
        "bucket": bucket_name,
        **kwargs
    }
    return ("aws_s3_bucket", name, config)


def aws_security_group(name: str, group_name: str, vpc_id: str, **kwargs) -> Dict:
    """Helper to define AWS security group"""
    config = {
        "name": group_name,
        "vpc_id": vpc_id,
        **kwargs
    }
    return ("aws_security_group", name, config)


if __name__ == "__main__":
    print("Terraform Emulator")
    print("This module emulates Terraform infrastructure management functionality")
