"""
Developed by PowerShield, as an alternative to Kubernetes Orchestrator
"""

#!/usr/bin/env python3
"""
Kubernetes Orchestrator Emulator - Container Orchestration

This module emulates core Kubernetes orchestration functionality including:
- Pod management and scheduling
- Service discovery and load balancing
- Deployment management with rolling updates
- ReplicaSet management
- ConfigMap and Secret management
- Namespace isolation
- Resource quotas and limits
- Health checks and probes
"""

import time
import secrets
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class PodPhase(Enum):
    """Pod lifecycle phases"""
    PENDING = "Pending"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    UNKNOWN = "Unknown"


class ServiceType(Enum):
    """Service types"""
    CLUSTER_IP = "ClusterIP"
    NODE_PORT = "NodePort"
    LOAD_BALANCER = "LoadBalancer"


class ProbeType(Enum):
    """Health probe types"""
    HTTP_GET = "httpGet"
    TCP_SOCKET = "tcpSocket"
    EXEC = "exec"


@dataclass
class Container:
    """Container specification"""
    name: str
    image: str
    ports: List[int] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    command: Optional[List[str]] = None
    args: Optional[List[str]] = None
    resources_requests: Dict[str, str] = field(default_factory=dict)
    resources_limits: Dict[str, str] = field(default_factory=dict)
    
    # Health probes
    liveness_probe: Optional[Dict] = None
    readiness_probe: Optional[Dict] = None
    
    # State
    ready: bool = False
    restart_count: int = 0


@dataclass
class Pod:
    """Kubernetes Pod"""
    name: str
    namespace: str
    containers: List[Container]
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    
    # Scheduling
    node_name: Optional[str] = None
    node_selector: Dict[str, str] = field(default_factory=dict)
    
    # Status
    phase: PodPhase = PodPhase.PENDING
    pod_ip: Optional[str] = None
    start_time: Optional[datetime] = None
    
    # Metadata
    uid: str = field(default_factory=lambda: secrets.token_hex(16))
    creation_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def is_ready(self) -> bool:
        """Check if all containers are ready"""
        return all(c.ready for c in self.containers)


@dataclass
class ReplicaSet:
    """Kubernetes ReplicaSet"""
    name: str
    namespace: str
    replicas: int
    selector: Dict[str, str]
    pod_template: Dict  # Contains pod spec
    labels: Dict[str, str] = field(default_factory=dict)
    
    # Status
    ready_replicas: int = 0
    available_replicas: int = 0
    
    uid: str = field(default_factory=lambda: secrets.token_hex(16))
    creation_timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Deployment:
    """Kubernetes Deployment"""
    name: str
    namespace: str
    replicas: int
    selector: Dict[str, str]
    pod_template: Dict
    labels: Dict[str, str] = field(default_factory=dict)
    
    # Update strategy
    strategy_type: str = "RollingUpdate"
    max_unavailable: int = 1
    max_surge: int = 1
    
    # Status
    ready_replicas: int = 0
    updated_replicas: int = 0
    available_replicas: int = 0
    
    uid: str = field(default_factory=lambda: secrets.token_hex(16))
    creation_timestamp: datetime = field(default_factory=datetime.utcnow)
    revision: int = 1


@dataclass
class Service:
    """Kubernetes Service"""
    name: str
    namespace: str
    service_type: ServiceType
    selector: Dict[str, str]
    ports: List[Dict] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    
    # IP addresses
    cluster_ip: Optional[str] = None
    external_ips: List[str] = field(default_factory=list)
    load_balancer_ip: Optional[str] = None
    
    uid: str = field(default_factory=lambda: secrets.token_hex(16))
    creation_timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConfigMap:
    """Kubernetes ConfigMap"""
    name: str
    namespace: str
    data: Dict[str, str] = field(default_factory=dict)
    binary_data: Dict[str, bytes] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    
    uid: str = field(default_factory=lambda: secrets.token_hex(16))
    creation_timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Secret:
    """Kubernetes Secret"""
    name: str
    namespace: str
    secret_type: str = "Opaque"
    data: Dict[str, str] = field(default_factory=dict)  # Base64 encoded
    labels: Dict[str, str] = field(default_factory=dict)
    
    uid: str = field(default_factory=lambda: secrets.token_hex(16))
    creation_timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Namespace:
    """Kubernetes Namespace"""
    name: str
    labels: Dict[str, str] = field(default_factory=dict)
    
    # Resource quotas
    resource_quota: Dict[str, str] = field(default_factory=dict)
    
    status: str = "Active"
    uid: str = field(default_factory=lambda: secrets.token_hex(16))
    creation_timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Node:
    """Kubernetes Node"""
    name: str
    labels: Dict[str, str] = field(default_factory=dict)
    
    # Capacity
    capacity_cpu: str = "4"
    capacity_memory: str = "8Gi"
    capacity_pods: int = 110
    
    # Allocatable
    allocatable_cpu: str = "3.5"
    allocatable_memory: str = "7Gi"
    allocatable_pods: int = 100
    
    # Status
    ready: bool = True
    
    uid: str = field(default_factory=lambda: secrets.token_hex(16))
    creation_timestamp: datetime = field(default_factory=datetime.utcnow)


class KubernetesOrchestrator:
    """Kubernetes orchestrator emulator"""
    
    def __init__(self, cluster_name: str = "test-cluster"):
        self.cluster_name = cluster_name
        
        # Resources
        self.namespaces: Dict[str, Namespace] = {}
        self.nodes: Dict[str, Node] = {}
        self.pods: Dict[str, Dict[str, Pod]] = {}  # namespace -> name -> pod
        self.deployments: Dict[str, Dict[str, Deployment]] = {}
        self.replica_sets: Dict[str, Dict[str, ReplicaSet]] = {}
        self.services: Dict[str, Dict[str, Service]] = {}
        self.config_maps: Dict[str, Dict[str, ConfigMap]] = {}
        self.secrets: Dict[str, Dict[str, Secret]] = {}
        
        # Create default namespace
        self.create_namespace("default")
        
        # Create default nodes
        for i in range(1, 4):
            self.create_node(f"node-{i}")
        
        # IP allocation
        self.next_pod_ip = 100
        self.next_service_ip = 1
    
    def create_namespace(self, name: str, labels: Optional[Dict[str, str]] = None) -> Namespace:
        """Create a namespace"""
        ns = Namespace(name=name, labels=labels or {})
        self.namespaces[name] = ns
        
        # Initialize resource dictionaries for namespace
        self.pods[name] = {}
        self.deployments[name] = {}
        self.replica_sets[name] = {}
        self.services[name] = {}
        self.config_maps[name] = {}
        self.secrets[name] = {}
        
        return ns
    
    def create_node(self, name: str, labels: Optional[Dict[str, str]] = None) -> Node:
        """Create a node"""
        node = Node(name=name, labels=labels or {})
        self.nodes[name] = node
        return node
    
    def create_pod(
        self,
        name: str,
        namespace: str,
        containers: List[Container],
        labels: Optional[Dict[str, str]] = None
    ) -> Pod:
        """Create a pod"""
        if namespace not in self.namespaces:
            raise ValueError(f"Namespace {namespace} does not exist")
        
        pod = Pod(
            name=name,
            namespace=namespace,
            containers=containers,
            labels=labels or {}
        )
        
        # Schedule pod
        self._schedule_pod(pod)
        
        self.pods[namespace][name] = pod
        return pod
    
    def _schedule_pod(self, pod: Pod):
        """Schedule pod to a node"""
        # Simple round-robin scheduling
        available_nodes = [n for n in self.nodes.values() if n.ready]
        if available_nodes:
            # Select node
            node = available_nodes[0]
            pod.node_name = node.name
            
            # Assign IP
            pod.pod_ip = f"10.244.0.{self.next_pod_ip}"
            self.next_pod_ip += 1
            
            # Start pod
            pod.phase = PodPhase.RUNNING
            pod.start_time = datetime.utcnow()
            
            # Mark containers as ready (simplified)
            for container in pod.containers:
                container.ready = True
    
    def create_deployment(
        self,
        name: str,
        namespace: str,
        replicas: int,
        selector: Dict[str, str],
        container_spec: Container,
        labels: Optional[Dict[str, str]] = None
    ) -> Deployment:
        """Create a deployment"""
        if namespace not in self.namespaces:
            raise ValueError(f"Namespace {namespace} does not exist")
        
        pod_template = {
            "labels": selector,
            "containers": [container_spec]
        }
        
        deployment = Deployment(
            name=name,
            namespace=namespace,
            replicas=replicas,
            selector=selector,
            pod_template=pod_template,
            labels=labels or {}
        )
        
        self.deployments[namespace][name] = deployment
        
        # Create ReplicaSet
        rs_name = f"{name}-{secrets.token_hex(4)}"
        replica_set = ReplicaSet(
            name=rs_name,
            namespace=namespace,
            replicas=replicas,
            selector=selector,
            pod_template=pod_template
        )
        self.replica_sets[namespace][rs_name] = replica_set
        
        # Create pods
        for i in range(replicas):
            pod_name = f"{name}-{rs_name}-{i}"
            self.create_pod(
                name=pod_name,
                namespace=namespace,
                containers=[container_spec],
                labels=selector
            )
        
        # Update deployment status
        deployment.ready_replicas = replicas
        deployment.updated_replicas = replicas
        deployment.available_replicas = replicas
        
        return deployment
    
    def scale_deployment(self, name: str, namespace: str, replicas: int) -> bool:
        """Scale a deployment"""
        if namespace not in self.deployments or name not in self.deployments[namespace]:
            return False
        
        deployment = self.deployments[namespace][name]
        current_replicas = deployment.replicas
        
        if replicas > current_replicas:
            # Scale up
            for i in range(current_replicas, replicas):
                pod_name = f"{name}-{secrets.token_hex(4)}-{i}"
                container = deployment.pod_template["containers"][0]
                self.create_pod(
                    name=pod_name,
                    namespace=namespace,
                    containers=[container],
                    labels=deployment.selector
                )
        elif replicas < current_replicas:
            # Scale down
            pods_to_delete = list(self.pods[namespace].keys())[:current_replicas - replicas]
            for pod_name in pods_to_delete:
                if pod_name in self.pods[namespace]:
                    del self.pods[namespace][pod_name]
        
        deployment.replicas = replicas
        deployment.ready_replicas = replicas
        deployment.updated_replicas = replicas
        deployment.available_replicas = replicas
        
        return True
    
    def create_service(
        self,
        name: str,
        namespace: str,
        service_type: ServiceType,
        selector: Dict[str, str],
        ports: List[Dict],
        labels: Optional[Dict[str, str]] = None
    ) -> Service:
        """Create a service"""
        if namespace not in self.namespaces:
            raise ValueError(f"Namespace {namespace} does not exist")
        
        service = Service(
            name=name,
            namespace=namespace,
            service_type=service_type,
            selector=selector,
            ports=ports,
            labels=labels or {}
        )
        
        # Assign cluster IP
        service.cluster_ip = f"10.96.{self.next_service_ip // 256}.{self.next_service_ip % 256}"
        self.next_service_ip += 1
        
        # Assign external IP for LoadBalancer type
        if service_type == ServiceType.LOAD_BALANCER:
            service.load_balancer_ip = f"203.0.113.{self.next_service_ip}"
        
        self.services[namespace][name] = service
        return service
    
    def get_service_endpoints(self, name: str, namespace: str) -> List[str]:
        """Get endpoints for a service"""
        if namespace not in self.services or name not in self.services[namespace]:
            return []
        
        service = self.services[namespace][name]
        endpoints = []
        
        # Find matching pods
        for pod in self.pods[namespace].values():
            if pod.phase == PodPhase.RUNNING and pod.is_ready():
                # Check if pod matches selector
                if all(pod.labels.get(k) == v for k, v in service.selector.items()):
                    endpoints.append(f"{pod.pod_ip}")
        
        return endpoints
    
    def create_config_map(
        self,
        name: str,
        namespace: str,
        data: Dict[str, str],
        labels: Optional[Dict[str, str]] = None
    ) -> ConfigMap:
        """Create a ConfigMap"""
        if namespace not in self.namespaces:
            raise ValueError(f"Namespace {namespace} does not exist")
        
        cm = ConfigMap(
            name=name,
            namespace=namespace,
            data=data,
            labels=labels or {}
        )
        self.config_maps[namespace][name] = cm
        return cm
    
    def create_secret(
        self,
        name: str,
        namespace: str,
        data: Dict[str, str],
        secret_type: str = "Opaque",
        labels: Optional[Dict[str, str]] = None
    ) -> Secret:
        """Create a Secret"""
        if namespace not in self.namespaces:
            raise ValueError(f"Namespace {namespace} does not exist")
        
        secret = Secret(
            name=name,
            namespace=namespace,
            secret_type=secret_type,
            data=data,
            labels=labels or {}
        )
        self.secrets[namespace][name] = secret
        return secret
    
    def get_pods(self, namespace: str, selector: Optional[Dict[str, str]] = None) -> List[Pod]:
        """Get pods in a namespace"""
        if namespace not in self.pods:
            return []
        
        pods = list(self.pods[namespace].values())
        
        if selector:
            pods = [
                p for p in pods
                if all(p.labels.get(k) == v for k, v in selector.items())
            ]
        
        return pods
    
    def delete_pod(self, name: str, namespace: str) -> bool:
        """Delete a pod"""
        if namespace in self.pods and name in self.pods[namespace]:
            del self.pods[namespace][name]
            return True
        return False
    
    def get_cluster_status(self) -> Dict:
        """Get overall cluster status"""
        total_pods = sum(len(pods) for pods in self.pods.values())
        running_pods = sum(
            1 for pods in self.pods.values()
            for pod in pods.values()
            if pod.phase == PodPhase.RUNNING
        )
        
        return {
            "cluster_name": self.cluster_name,
            "nodes": len(self.nodes),
            "ready_nodes": sum(1 for n in self.nodes.values() if n.ready),
            "namespaces": len(self.namespaces),
            "total_pods": total_pods,
            "running_pods": running_pods,
            "deployments": sum(len(d) for d in self.deployments.values()),
            "services": sum(len(s) for s in self.services.values())
        }


if __name__ == "__main__":
    # Example usage
    print("=== Kubernetes Orchestrator Emulator Demo ===\n")
    
    k8s = KubernetesOrchestrator(cluster_name="demo-cluster")
    
    # Create namespace
    ns = k8s.create_namespace("production", labels={"env": "prod"})
    print(f"1. Created namespace: {ns.name}")
    
    # Create deployment
    container = Container(
        name="nginx",
        image="nginx:1.21",
        ports=[80],
        resources_requests={"cpu": "100m", "memory": "128Mi"},
        resources_limits={"cpu": "500m", "memory": "512Mi"}
    )
    
    deployment = k8s.create_deployment(
        name="nginx-deployment",
        namespace="production",
        replicas=3,
        selector={"app": "nginx"},
        container_spec=container,
        labels={"app": "nginx", "version": "1.21"}
    )
    
    print(f"\n2. Created deployment: {deployment.name}")
    print(f"   Replicas: {deployment.replicas}")
    print(f"   Ready: {deployment.ready_replicas}")
    
    # Create service
    service = k8s.create_service(
        name="nginx-service",
        namespace="production",
        service_type=ServiceType.LOAD_BALANCER,
        selector={"app": "nginx"},
        ports=[{"port": 80, "targetPort": 80, "protocol": "TCP"}],
        labels={"app": "nginx"}
    )
    
    print(f"\n3. Created service: {service.name}")
    print(f"   Type: {service.service_type.value}")
    print(f"   Cluster IP: {service.cluster_ip}")
    print(f"   Load Balancer IP: {service.load_balancer_ip}")
    
    # Get service endpoints
    endpoints = k8s.get_service_endpoints("nginx-service", "production")
    print(f"\n4. Service endpoints:")
    for ep in endpoints:
        print(f"   - {ep}")
    
    # Scale deployment
    print(f"\n5. Scaling deployment to 5 replicas...")
    k8s.scale_deployment("nginx-deployment", "production", 5)
    deployment = k8s.deployments["production"]["nginx-deployment"]
    print(f"   New replicas: {deployment.replicas}")
    
    # Create ConfigMap
    cm = k8s.create_config_map(
        name="app-config",
        namespace="production",
        data={
            "database_host": "db.example.com",
            "cache_ttl": "3600",
            "log_level": "info"
        }
    )
    print(f"\n6. Created ConfigMap: {cm.name}")
    print(f"   Keys: {', '.join(cm.data.keys())}")
    
    # Create Secret
    secret = k8s.create_secret(
        name="db-credentials",
        namespace="production",
        data={
            "username": "YWRtaW4=",  # base64 encoded
            "password": "cGFzc3dvcmQ="
        }
    )
    print(f"\n7. Created Secret: {secret.name}")
    print(f"   Type: {secret.secret_type}")
    
    # Get pods
    pods = k8s.get_pods("production", selector={"app": "nginx"})
    print(f"\n8. Pods in production namespace:")
    for pod in pods:
        print(f"   - {pod.name}")
        print(f"     Node: {pod.node_name}")
        print(f"     Phase: {pod.phase.value}")
        print(f"     IP: {pod.pod_ip}")
        print(f"     Ready: {pod.is_ready()}")
    
    # Cluster status
    status = k8s.get_cluster_status()
    print(f"\n9. Cluster Status:")
    for key, value in status.items():
        print(f"   {key}: {value}")
