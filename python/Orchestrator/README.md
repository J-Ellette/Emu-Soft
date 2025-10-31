# Kubernetes Orchestrator Emulator - Container Orchestration

A lightweight emulation of **Kubernetes** container orchestration functionality for managing containerized applications.

## Features

This emulator implements core Kubernetes orchestration functionality:

### Resource Management
- **Namespaces**: Logical cluster isolation
- **Nodes**: Worker node simulation
- **Pods**: Container runtime units
- **Deployments**: Declarative application updates
- **ReplicaSets**: Pod replication management
- **Services**: Service discovery and load balancing

### Workload Management
- **Pod Scheduling**: Automatic pod placement on nodes
- **Scaling**: Manual deployment scaling
- **Rolling Updates**: Zero-downtime deployments
- **Health Checks**: Liveness and readiness probes
- **Container Management**: Multi-container pods

### Configuration & Secrets
- **ConfigMaps**: Configuration data storage
- **Secrets**: Sensitive data management
- **Environment Variables**: Container configuration

### Networking
- **Service Discovery**: DNS-based service resolution
- **Load Balancing**: Traffic distribution across pods
- **Cluster IP**: Internal cluster networking
- **NodePort**: External access via node ports
- **LoadBalancer**: External load balancer integration

## What It Emulates

This tool emulates core functionality of [Kubernetes](https://kubernetes.io/), the industry-standard container orchestration platform originally developed by Google.

### Core Components Implemented

1. **Control Plane**
   - API server simulation
   - Scheduler (simplified)
   - Resource management

2. **Workload Resources**
   - Pods (container groups)
   - Deployments (declarative updates)
   - ReplicaSets (pod replication)

3. **Service & Discovery**
   - Services (load balancing)
   - Endpoints (service backends)
   - DNS-based service discovery

4. **Configuration**
   - ConfigMaps (configuration)
   - Secrets (sensitive data)
   - Environment injection

## Usage

### Create Cluster and Namespace

```python
from kubernetes_orchestrator_tool import KubernetesOrchestrator

# Create cluster
k8s = KubernetesOrchestrator(cluster_name="production")

# Create namespace
namespace = k8s.create_namespace(
    name="myapp",
    labels={"team": "backend", "env": "prod"}
)
```

### Create Deployment

```python
from kubernetes_orchestrator_tool import Container

# Define container
container = Container(
    name="web-server",
    image="nginx:1.21",
    ports=[80, 443],
    env={
        "ENV": "production",
        "LOG_LEVEL": "info"
    },
    resources_requests={
        "cpu": "100m",
        "memory": "128Mi"
    },
    resources_limits={
        "cpu": "500m",
        "memory": "512Mi"
    }
)

# Create deployment
deployment = k8s.create_deployment(
    name="web-deployment",
    namespace="myapp",
    replicas=3,
    selector={"app": "web", "tier": "frontend"},
    container_spec=container,
    labels={"app": "web", "version": "v1"}
)

print(f"Created deployment with {deployment.replicas} replicas")
```

### Scale Deployment

```python
# Scale up to 5 replicas
k8s.scale_deployment(
    name="web-deployment",
    namespace="myapp",
    replicas=5
)

# Scale down to 2 replicas
k8s.scale_deployment(
    name="web-deployment",
    namespace="myapp",
    replicas=2
)
```

### Create Service

```python
from kubernetes_orchestrator_tool import ServiceType

# Create LoadBalancer service
service = k8s.create_service(
    name="web-service",
    namespace="myapp",
    service_type=ServiceType.LOAD_BALANCER,
    selector={"app": "web"},
    ports=[
        {"port": 80, "targetPort": 80, "protocol": "TCP"},
        {"port": 443, "targetPort": 443, "protocol": "TCP"}
    ],
    labels={"app": "web"}
)

print(f"Service cluster IP: {service.cluster_ip}")
print(f"Service external IP: {service.load_balancer_ip}")
```

### Get Service Endpoints

```python
# Get backend pods for service
endpoints = k8s.get_service_endpoints("web-service", "myapp")

print("Service backends:")
for endpoint in endpoints:
    print(f"  - {endpoint}")
```

### Create ConfigMap

```python
# Create configuration
config = k8s.create_config_map(
    name="app-config",
    namespace="myapp",
    data={
        "database.host": "db.example.com",
        "database.port": "5432",
        "cache.ttl": "3600",
        "log.level": "info",
        "feature.flags": "new_ui,advanced_search"
    },
    labels={"app": "web"}
)
```

### Create Secret

```python
import base64

# Create secret
secret = k8s.create_secret(
    name="db-credentials",
    namespace="myapp",
    data={
        "username": base64.b64encode(b"admin").decode(),
        "password": base64.b64encode(b"secretpass").decode(),
        "connection-string": base64.b64encode(
            b"postgresql://admin:secretpass@db.example.com:5432/mydb"
        ).decode()
    },
    secret_type="Opaque",
    labels={"app": "web"}
)
```

### List Pods

```python
# Get all pods in namespace
all_pods = k8s.get_pods("myapp")

# Get pods with selector
web_pods = k8s.get_pods(
    "myapp",
    selector={"app": "web", "tier": "frontend"}
)

for pod in web_pods:
    print(f"Pod: {pod.name}")
    print(f"  Node: {pod.node_name}")
    print(f"  IP: {pod.pod_ip}")
    print(f"  Phase: {pod.phase.value}")
    print(f"  Ready: {pod.is_ready()}")
```

### Get Cluster Status

```python
# Get overall cluster health
status = k8s.get_cluster_status()

print(f"Cluster: {status['cluster_name']}")
print(f"Nodes: {status['ready_nodes']}/{status['nodes']}")
print(f"Pods: {status['running_pods']}/{status['total_pods']}")
print(f"Deployments: {status['deployments']}")
print(f"Services: {status['services']}")
```

### Complete Example - Microservices Deployment

```python
# Create namespace for microservices
k8s.create_namespace("microservices", labels={"env": "prod"})

# Deploy frontend service
frontend_container = Container(
    name="frontend",
    image="myapp/frontend:v1.0",
    ports=[3000],
    env={"API_URL": "http://api-service:8080"},
    resources_requests={"cpu": "100m", "memory": "128Mi"}
)

k8s.create_deployment(
    name="frontend",
    namespace="microservices",
    replicas=3,
    selector={"app": "frontend"},
    container_spec=frontend_container
)

# Deploy API service
api_container = Container(
    name="api",
    image="myapp/api:v1.0",
    ports=[8080],
    env={"DB_HOST": "postgres-service"},
    resources_requests={"cpu": "200m", "memory": "256Mi"}
)

k8s.create_deployment(
    name="api",
    namespace="microservices",
    replicas=5,
    selector={"app": "api"},
    container_spec=api_container
)

# Create services
k8s.create_service(
    name="frontend-service",
    namespace="microservices",
    service_type=ServiceType.LOAD_BALANCER,
    selector={"app": "frontend"},
    ports=[{"port": 80, "targetPort": 3000}]
)

k8s.create_service(
    name="api-service",
    namespace="microservices",
    service_type=ServiceType.CLUSTER_IP,
    selector={"app": "api"},
    ports=[{"port": 8080, "targetPort": 8080}]
)

# Create shared configuration
k8s.create_config_map(
    name="app-settings",
    namespace="microservices",
    data={
        "environment": "production",
        "region": "us-east-1",
        "log_level": "info"
    }
)

print("Microservices deployed successfully!")
```

## Testing

```bash
python kubernetes_orchestrator_tool.py
```

The demo script will demonstrate:
1. Namespace creation
2. Deployment creation
3. Service creation and endpoints
4. Deployment scaling
5. ConfigMap creation
6. Secret creation
7. Pod listing
8. Cluster status

## Use Cases

1. **Development**: Test Kubernetes manifests locally
2. **Learning**: Understand Kubernetes concepts
3. **Testing**: Mock Kubernetes for integration tests
4. **CI/CD**: Simulate deployments in pipelines
5. **Education**: Teaching container orchestration

## Key Differences from Real Kubernetes

1. **No Real Containers**: Simulates containers, doesn't run them
2. **Simplified Scheduling**: Basic node selection
3. **No Networking**: Simulates IPs and services
4. **No Persistent Storage**: No volume management
5. **Limited APIs**: Subset of Kubernetes API
6. **No Authentication**: No RBAC or auth
7. **In-Memory**: No etcd or persistent storage

## License

Educational emulator for learning purposes.

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kubernetes API Reference](https://kubernetes.io/docs/reference/kubernetes-api/)
- [Kubernetes Concepts](https://kubernetes.io/docs/concepts/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
