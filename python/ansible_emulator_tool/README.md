# Ansible Emulator - Configuration Management and Automation

A lightweight emulation of **Ansible**, the popular IT automation platform used for configuration management, application deployment, and task automation.

## Features

This emulator implements core Ansible functionality:

### Inventory Management
- **Host Definition**: Define hosts with connection parameters
- **Group Management**: Organize hosts into groups
- **Group Variables**: Define variables at group level
- **Host Variables**: Define host-specific variables
- **Dynamic Patterns**: Match hosts using patterns

### Playbook Execution
- **Play Definition**: Define plays targeting specific hosts
- **Task Execution**: Execute tasks in order on target hosts
- **Variable Management**: Use variables at play, group, and host levels
- **Fact Gathering**: Gather system facts from hosts
- **Conditional Execution**: Skip tasks based on when conditions

### Module System
- **Built-in Modules**: Ping, command, shell, copy, file, template, service, package
- **Package Managers**: apt, yum modules for package management
- **Service Management**: systemd, service modules
- **Version Control**: git module for repository management
- **User Management**: user, group modules
- **Debug Module**: Output messages and variables

### Task Features
- **Loops**: Execute tasks with item loops
- **Conditionals**: when clause for conditional execution
- **Error Handling**: ignore_errors for fault tolerance
- **Result Registration**: Store task results in variables
- **Tags**: Tag tasks for selective execution

### Handlers
- **Notification System**: Notify handlers when tasks make changes
- **Handler Execution**: Run handlers at end of play
- **Idempotent Operations**: Handlers only run when notified

### Ad-Hoc Commands
- **Quick Execution**: Run single commands across hosts
- **Pattern Matching**: Target specific hosts or groups
- **Module Support**: Use any module in ad-hoc mode

## What It Emulates

This tool emulates core functionality of [Ansible](https://www.ansible.com/), Red Hat's open-source automation platform used by thousands of organizations worldwide.

### Core Components Implemented

1. **Ansible Core**
   - Inventory management (hosts and groups)
   - Playbook parsing and execution
   - Task execution engine
   - Variable resolution

2. **Module Library**
   - System modules (command, shell, ping)
   - File modules (copy, file, template)
   - Package modules (apt, yum, package)
   - Service modules (service, systemd)
   - Source control modules (git)
   - User modules (user, group)

3. **Features**
   - Task loops (with_items emulation)
   - Conditional execution (when clause)
   - Handler notifications
   - Fact gathering
   - Variable interpolation
   - Result registration

## Usage

### Basic Inventory and Ad-Hoc Commands

```python
from ansible_emulator import AnsibleEmulator, Host

# Create emulator
ansible = AnsibleEmulator()

# Add hosts to inventory
web1 = Host(name="web1", ansible_host="192.168.1.10", ansible_user="ubuntu")
web2 = Host(name="web2", ansible_host="192.168.1.11", ansible_user="ubuntu")
db1 = Host(name="db1", ansible_host="192.168.1.20", ansible_user="ubuntu")

ansible.inventory.add_host(web1, groups=["webservers"])
ansible.inventory.add_host(web2, groups=["webservers"])
ansible.inventory.add_host(db1, groups=["databases"])

# Run ad-hoc command
results = ansible.run_ad_hoc("ping", {}, pattern="all")
for result in results:
    print(f"{result.host}: {result.state.value}")

# Run command on specific group
results = ansible.run_ad_hoc(
    "command",
    {"_raw_params": "uptime"},
    pattern="webservers"
)
```

### Playbook Execution

```python
from ansible_emulator import Playbook, Play, Task, Handler

# Create playbook
playbook = Playbook(name="Deploy Web Application")

# Define play
play = Play(
    name="Configure web servers",
    hosts="webservers",
    vars={"app_version": "1.0", "nginx_port": 80},
    gather_facts=True
)

# Add tasks
play.tasks = [
    Task(
        name="Install nginx",
        module="apt",
        args={"name": "nginx", "state": "present"}
    ),
    Task(
        name="Copy nginx config",
        module="copy",
        args={
            "src": "/local/nginx.conf",
            "dest": "/etc/nginx/nginx.conf"
        },
        notify=["restart nginx"]
    ),
    Task(
        name="Ensure nginx is running",
        module="service",
        args={"name": "nginx", "state": "started", "enabled": True}
    )
]

# Add handlers
play.handlers = [
    Handler(
        name="restart nginx",
        module="service",
        args={"name": "nginx", "state": "restarted"}
    )
]

playbook.plays.append(play)

# Run playbook
result = ansible.run_playbook(playbook)
print(f"Playbook: {result['playbook_name']}")
print(f"Summary: {result['summary']}")
```

### Task Loops

```python
# Task with loop
task = Task(
    name="Install multiple packages",
    module="apt",
    args={"name": "{{ item }}", "state": "present"},
    loop=["nginx", "python3", "git", "vim"]
)

play.tasks.append(task)
```

### Conditional Execution

```python
# Conditional task
task = Task(
    name="Install package only on Ubuntu",
    module="apt",
    args={"name": "ubuntu-specific", "state": "present"},
    when="ansible_distribution == 'Ubuntu'"
)
```

### Variable Registration

```python
# Register task output
check_task = Task(
    name="Check if file exists",
    module="command",
    args={"_raw_params": "ls /tmp/myfile"},
    register="file_check",
    ignore_errors=True
)

# Use registered variable
conditional_task = Task(
    name="Create file if missing",
    module="file",
    args={"path": "/tmp/myfile", "state": "touch"},
    when="file_check.rc != 0"
)
```

### Complete Example

```python
# Setup inventory
ansible = AnsibleEmulator()

# Add hosts with variables
for i in range(1, 4):
    host = Host(
        name=f"web{i}",
        ansible_host=f"192.168.1.{10+i}",
        vars={"server_id": i, "env": "production"}
    )
    ansible.inventory.add_host(host, groups=["webservers", "production"])

# Set group variables
ansible.inventory.groups["webservers"].vars = {
    "nginx_workers": 4,
    "nginx_port": 8080
}

# Create multi-play playbook
playbook = Playbook(name="Full Stack Deployment")

# Play 1: Configure web servers
web_play = Play(name="Setup Web Servers", hosts="webservers")
web_play.tasks = [
    Task(name="Update apt cache", module="apt", 
         args={"update_cache": True}),
    Task(name="Install nginx", module="apt",
         args={"name": "nginx", "state": "present"}),
    Task(name="Deploy application", module="git",
         args={"repo": "https://github.com/app/repo", "dest": "/var/www/app"})
]

playbook.plays.append(web_play)

# Play 2: Configure databases  
db_play = Play(name="Setup Databases", hosts="databases")
db_play.tasks = [
    Task(name="Install PostgreSQL", module="apt",
         args={"name": "postgresql", "state": "present"}),
    Task(name="Start PostgreSQL", module="service",
         args={"name": "postgresql", "state": "started", "enabled": True})
]

playbook.plays.append(db_play)

# Execute
result = ansible.run_playbook(playbook)

# Display results
for play_result in result['plays']:
    print(f"\nPlay: {play_result['play_name']}")
    print(f"Hosts: {', '.join(play_result['hosts'])}")
    for task in play_result['tasks']:
        status = "✓" if not task.failed else "✗"
        print(f"  {status} [{task.host}] {task.task_name}: {task.state.value}")
```

## Testing

```bash
python test_ansible_emulator.py
```

## Use Cases

1. **Learning Ansible**: Understand Ansible concepts without infrastructure
2. **Testing Playbooks**: Validate playbook logic before deployment
3. **CI/CD Integration**: Test automation in CI pipelines
4. **Education**: Teaching infrastructure automation
5. **Development**: Develop Ansible-dependent tools

## Key Differences from Real Ansible

1. **No SSH**: Doesn't actually connect to hosts via SSH
2. **No Real Execution**: Tasks are simulated, not executed
3. **Simplified Modules**: Module implementations are simplified
4. **Limited Jinja2**: Basic variable substitution only
5. **No Vault**: Secret management not implemented
6. **No Galaxy**: Role management not included

## License

Educational emulator for learning purposes.

## References

- [Ansible Documentation](https://docs.ansible.com/)
- [Ansible Module Index](https://docs.ansible.com/ansible/latest/modules/modules_by_category.html)
- [Ansible Best Practices](https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html)
