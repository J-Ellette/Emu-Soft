# Kubernetes Python Client Emulator

This module emulates the **kubernetes** Python client library, which is the official Python client for the Kubernetes API. It enables Python developers to interact with Kubernetes clusters programmatically to manage pods, services, deployments, and other Kubernetes resources.

## What is kubernetes-python?

The Kubernetes Python client is the official client library for Kubernetes API. It provides:
- Programmatic access to all Kubernetes resources
- Support for core API (v1) and extensions (apps/v1, etc.)
- Auto-generated client from Kubernetes OpenAPI spec
- Support for all CRUD operations on Kubernetes resources
- Configuration from kubeconfig files or in-cluster service accounts
- Watch functionality for real-time resource monitoring

## Features

This emulator implements core functionality for Kubernetes resource management:

### Client Configuration
- Load configuration from kubeconfig files
- Load in-cluster configuration
- API client creation
- Configuration management

### Core API (v1) Resources
- **Pods**: Create, read, list, update, delete pods
- **Services**: Manage Kubernetes services
- **Namespaces**: Manage Kubernetes namespaces
- **ConfigMaps**: Store configuration data
- **Secrets**: Store sensitive information
- Label selectors and filtering
- Cross-namespace queries

### Apps API (apps/v1) Resources
- **Deployments**: Manage deployment resources
- Replica scaling
- Update and patch operations

### Resource Management
- CRUD operations for all supported resources
- Metadata handling (labels, annotations)
- Status tracking
- Resource versioning

## Usage Examples

### Configuration

```python
from kubernetes_emulator import config, client

# Load configuration from ~/.kube/config
config.load_kube_config()

# Or load in-cluster configuration (when running inside Kubernetes)
config.load_incluster_config()

# Create API clients
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
```

### Working with Namespaces

```python
from kubernetes_emulator import client
from kubernetes_emulator import V1Namespace, V1ObjectMeta

v1 = client.CoreV1Api()

# Create a namespace
namespace = V1Namespace(
    metadata=V1ObjectMeta(name="my-namespace")
)
v1.create_namespace(namespace)

# List all namespaces
namespaces = v1.list_namespace()
for ns in namespaces.items:
    print(f"Namespace: {ns.metadata.name}")

# Read a specific namespace
ns = v1.read_namespace("my-namespace")

# Delete a namespace
v1.delete_namespace("my-namespace")
```

### Working with Pods

#### Creating Pods

```python
from kubernetes_emulator import client
from kubernetes_emulator import (
    V1Pod, V1PodSpec, V1Container, V1ObjectMeta
)

v1 = client.CoreV1Api()

# Create a simple pod
pod = V1Pod(
    metadata=V1ObjectMeta(
        name="my-pod",
        namespace="default",
        labels={"app": "web", "tier": "frontend"}
    ),
    spec=V1PodSpec(
        containers=[
            V1Container(
                name="nginx",
                image="nginx:1.21",
                ports=[{"containerPort": 80}],
                env=[
                    {"name": "ENV", "value": "production"},
                    {"name": "LOG_LEVEL", "value": "info"}
                ]
            )
        ],
        restart_policy="Always"
    )
)

created_pod = v1.create_namespaced_pod(namespace="default", body=pod)
print(f"Pod {created_pod.metadata.name} created")
print(f"Status: {created_pod.status.phase}")
```

#### Reading and Listing Pods

```python
# Read a specific pod
pod = v1.read_namespaced_pod(name="my-pod", namespace="default")
print(f"Pod IP: {pod.status.pod_ip}")
print(f"Host IP: {pod.status.host_ip}")

# List all pods in a namespace
pods = v1.list_namespaced_pod(namespace="default")
for pod in pods.items:
    print(f"{pod.metadata.name}: {pod.status.phase}")

# List pods with label selector
web_pods = v1.list_namespaced_pod(
    namespace="default",
    label_selector="app=web"
)

# List all pods across all namespaces
all_pods = v1.list_pod_for_all_namespaces()
for pod in all_pods.items:
    print(f"{pod.metadata.namespace}/{pod.metadata.name}")
```

#### Updating and Deleting Pods

```python
# Patch a pod (update labels)
patched_pod = v1.patch_namespaced_pod(
    name="my-pod",
    namespace="default",
    body={
        "metadata": {
            "labels": {
                "environment": "production",
                "version": "v2"
            }
        }
    }
)

# Delete a pod
v1.delete_namespaced_pod(name="my-pod", namespace="default")
```

### Working with Services

```python
from kubernetes_emulator import (
    V1Service, V1ServiceSpec, V1ServicePort
)

v1 = client.CoreV1Api()

# Create a service
service = V1Service(
    metadata=V1ObjectMeta(
        name="web-service",
        namespace="default",
        labels={"app": "web"}
    ),
    spec=V1ServiceSpec(
        selector={"app": "web"},
        ports=[
            V1ServicePort(
                name="http",
                port=80,
                target_port=8080,
                protocol="TCP"
            ),
            V1ServicePort(
                name="https",
                port=443,
                target_port=8443,
                protocol="TCP"
            )
        ],
        type="ClusterIP"
    )
)

created_service = v1.create_namespaced_service(
    namespace="default",
    body=service
)

# Read a service
service = v1.read_namespaced_service(
    name="web-service",
    namespace="default"
)
print(f"Cluster IP: {service.spec.cluster_ip}")

# List services
services = v1.list_namespaced_service(namespace="default")
for svc in services.items:
    print(f"{svc.metadata.name}: {svc.spec.type}")

# Delete a service
v1.delete_namespaced_service(
    name="web-service",
    namespace="default"
)
```

### Working with Deployments

```python
from kubernetes_emulator import (
    V1Deployment, V1DeploymentSpec
)

apps_v1 = client.AppsV1Api()

# Create a deployment
deployment = V1Deployment(
    metadata=V1ObjectMeta(
        name="web-deployment",
        namespace="default",
        labels={"app": "web"}
    ),
    spec=V1DeploymentSpec(
        replicas=3,
        selector={"matchLabels": {"app": "web"}},
        template={
            "metadata": {
                "labels": {"app": "web"}
            },
            "spec": {
                "containers": [
                    {
                        "name": "nginx",
                        "image": "nginx:1.21",
                        "ports": [{"containerPort": 80}]
                    }
                ]
            }
        }
    )
)

created_deployment = apps_v1.create_namespaced_deployment(
    namespace="default",
    body=deployment
)

# Read a deployment
deployment = apps_v1.read_namespaced_deployment(
    name="web-deployment",
    namespace="default"
)
print(f"Replicas: {deployment.spec.replicas}")
print(f"Ready: {deployment.status.ready_replicas}")

# List deployments
deployments = apps_v1.list_namespaced_deployment(namespace="default")
for dep in deployments.items:
    print(f"{dep.metadata.name}: {dep.status.ready_replicas}/{dep.spec.replicas}")

# Scale a deployment
scaled_deployment = apps_v1.patch_namespaced_deployment(
    name="web-deployment",
    namespace="default",
    body={"spec": {"replicas": 5}}
)

# Delete a deployment
apps_v1.delete_namespaced_deployment(
    name="web-deployment",
    namespace="default"
)
```

### Working with ConfigMaps

```python
from kubernetes_emulator import V1ConfigMap

v1 = client.CoreV1Api()

# Create a ConfigMap
config_map = V1ConfigMap(
    metadata=V1ObjectMeta(
        name="app-config",
        namespace="default"
    ),
    data={
        "database_host": "postgres.default.svc.cluster.local",
        "database_port": "5432",
        "app_config.yaml": """
app:
  name: myapp
  debug: false
  log_level: info
"""
    }
)

v1.create_namespaced_config_map(namespace="default", body=config_map)

# Read a ConfigMap
config_map = v1.read_namespaced_config_map(
    name="app-config",
    namespace="default"
)
print(config_map.data["database_host"])

# List ConfigMaps
config_maps = v1.list_namespaced_config_map(namespace="default")

# Delete a ConfigMap
v1.delete_namespaced_config_map(name="app-config", namespace="default")
```

### Working with Secrets

```python
from kubernetes_emulator import V1Secret
import base64

v1 = client.CoreV1Api()

# Create a Secret
secret = V1Secret(
    metadata=V1ObjectMeta(
        name="db-credentials",
        namespace="default"
    ),
    type="Opaque",
    data={
        "username": base64.b64encode(b"admin").decode(),
        "password": base64.b64encode(b"secret123").decode()
    }
)

v1.create_namespaced_secret(namespace="default", body=secret)

# Read a Secret
secret = v1.read_namespaced_secret(
    name="db-credentials",
    namespace="default"
)

# Decode secret data
username = base64.b64decode(secret.data["username"]).decode()
print(f"Username: {username}")

# List Secrets
secrets = v1.list_namespaced_secret(namespace="default")

# Delete a Secret
v1.delete_namespaced_secret(name="db-credentials", namespace="default")
```

## Real-World Use Cases

### Application Deployment Script

```python
from kubernetes_emulator import client, config
from kubernetes_emulator import (
    V1Namespace, V1ObjectMeta, V1Deployment, V1DeploymentSpec,
    V1Service, V1ServiceSpec, V1ServicePort, V1ConfigMap
)

def deploy_application():
    # Load config
    config.load_kube_config()
    
    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    
    # Create namespace
    namespace = V1Namespace(
        metadata=V1ObjectMeta(name="myapp")
    )
    v1.create_namespace(namespace)
    
    # Create ConfigMap
    config_map = V1ConfigMap(
        metadata=V1ObjectMeta(name="app-config", namespace="myapp"),
        data={"app.conf": "debug=false\nlog_level=info\n"}
    )
    v1.create_namespaced_config_map(namespace="myapp", body=config_map)
    
    # Create Deployment
    deployment = V1Deployment(
        metadata=V1ObjectMeta(name="web", namespace="myapp"),
        spec=V1DeploymentSpec(
            replicas=3,
            selector={"matchLabels": {"app": "web"}},
            template={
                "metadata": {"labels": {"app": "web"}},
                "spec": {
                    "containers": [{
                        "name": "nginx",
                        "image": "nginx:1.21",
                        "ports": [{"containerPort": 80}]
                    }]
                }
            }
        )
    )
    apps_v1.create_namespaced_deployment(namespace="myapp", body=deployment)
    
    # Create Service
    service = V1Service(
        metadata=V1ObjectMeta(name="web", namespace="myapp"),
        spec=V1ServiceSpec(
            selector={"app": "web"},
            ports=[V1ServicePort(port=80, target_port=80)],
            type="LoadBalancer"
        )
    )
    v1.create_namespaced_service(namespace="myapp", body=service)
    
    print("Application deployed successfully!")
```

### Resource Monitoring

```python
from kubernetes_emulator import client, config

def monitor_cluster():
    config.load_kube_config()
    v1 = client.CoreV1Api()
    
    # Get all namespaces
    namespaces = v1.list_namespace()
    
    for ns in namespaces.items:
        ns_name = ns.metadata.name
        
        # Count pods in this namespace
        pods = v1.list_namespaced_pod(namespace=ns_name)
        running_pods = [p for p in pods.items if p.status.phase == "Running"]
        
        # Count services
        services = v1.list_namespaced_service(namespace=ns_name)
        
        print(f"\nNamespace: {ns_name}")
        print(f"  Pods: {len(running_pods)}/{len(pods.items)} running")
        print(f"  Services: {len(services.items)}")
```

## API Compatibility

This emulator provides compatibility with kubernetes-python's core API:

- ✅ `config.load_kube_config()` - Load kubeconfig
- ✅ `config.load_incluster_config()` - Load in-cluster config
- ✅ `client.CoreV1Api()` - Core v1 API client
- ✅ `client.AppsV1Api()` - Apps v1 API client
- ✅ Pod operations (create, read, list, patch, delete)
- ✅ Service operations (create, read, list, delete)
- ✅ Deployment operations (create, read, list, patch, delete)
- ✅ Namespace operations (create, read, list, delete)
- ✅ ConfigMap operations (create, read, list, delete)
- ✅ Secret operations (create, read, list, delete)
- ✅ Label selectors and filtering
- ✅ Resource metadata and status
- ✅ Cross-namespace queries

## Emulated Concepts

### Kubernetes Resources
Simulates the core Kubernetes resources (Pods, Services, Deployments, etc.) with their specifications, status, and metadata.

### API Versioning
Emulates different API versions (v1 for core resources, apps/v1 for deployments) matching Kubernetes API structure.

### Namespace Isolation
Simulates namespace-based resource isolation and management.

### Label Selectors
Implements label-based resource filtering and selection.

### Resource Lifecycle
Tracks resource states and lifecycle (creating, running, terminating, etc.).

## Implementation Notes

- **In-Memory Storage**: All resources stored in memory, organized by namespace
- **UID Generation**: Uses random hexadecimal strings for resource UIDs
- **Timestamps**: Uses UTC timestamps in ISO 8601 format
- **Default Namespace**: Automatically creates 'default' namespace
- **Resource Versions**: Tracks resource versions for updates
- **Status Simulation**: Automatically sets appropriate status for resources

## Testing

Run the test suite:

```bash
python test_kubernetes_emulator.py
```

The test suite covers:
- Configuration loading
- Client creation
- Namespace operations
- Pod CRUD operations
- Service CRUD operations
- Deployment CRUD operations
- ConfigMap and Secret management
- Label selectors and filtering
- Multi-namespace operations

## Emulates

This module emulates the **kubernetes** Python client library (PyPI package: `kubernetes`):
- Repository: https://github.com/kubernetes-client/python
- Documentation: https://github.com/kubernetes-client/python/blob/master/README.md
- License: Apache 2.0

## Educational Purpose

This is an educational reimplementation created for the CIV-ARCOS project. It demonstrates:
- Kubernetes API architecture and design patterns
- RESTful API client implementation
- Resource-based API design
- Namespace-based multi-tenancy
- Declarative configuration management
- Container orchestration concepts

For production use with real Kubernetes clusters, please use the official kubernetes-python library.
