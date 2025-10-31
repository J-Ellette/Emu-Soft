"""
Test suite for Kubernetes Python Client Emulator

Tests the core functionality of the kubernetes client emulator including:
- Client configuration and creation
- Pod operations
- Service operations
- Deployment operations
- Namespace operations
- ConfigMap and Secret operations
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from kubernetes_emulator import (
    client,
    config,
    CoreV1Api,
    AppsV1Api,
    V1Pod,
    V1PodSpec,
    V1PodStatus,
    V1Container,
    V1ObjectMeta,
    V1Service,
    V1ServiceSpec,
    V1ServicePort,
    V1Deployment,
    V1DeploymentSpec,
    V1Namespace,
    V1ConfigMap,
    V1Secret,
)


def test_config_loading():
    """Test loading Kubernetes configuration."""
    print("Testing config loading...")
    
    # Load kube config (should not raise)
    config.load_kube_config()
    
    # Load incluster config (should not raise)
    config.load_incluster_config()
    
    print("  ✓ Config loading works")


def test_client_creation():
    """Test creating API clients."""
    print("Testing client creation...")
    
    # Create CoreV1Api client
    v1 = client.CoreV1Api()
    assert v1 is not None
    
    # Create AppsV1Api client
    apps_v1 = client.AppsV1Api()
    assert apps_v1 is not None
    
    # Create with explicit api_client
    from kubernetes_emulator import ApiClient
    api_client = ApiClient()
    v1_with_client = CoreV1Api(api_client=api_client)
    assert v1_with_client is not None
    
    print("  ✓ Client creation works")


def test_namespace_operations():
    """Test namespace CRUD operations."""
    print("Testing namespace operations...")
    
    v1 = CoreV1Api()
    
    # Create a namespace
    namespace = V1Namespace(
        metadata=V1ObjectMeta(name="test-namespace")
    )
    created = v1.create_namespace(namespace)
    assert created.metadata.name == "test-namespace"
    assert created.status["phase"] == "Active"
    
    # Read the namespace
    read = v1.read_namespace("test-namespace")
    assert read.metadata.name == "test-namespace"
    
    # List namespaces
    namespace_list = v1.list_namespace()
    assert len(namespace_list.items) >= 2  # default + test-namespace
    
    # Delete the namespace
    deleted = v1.delete_namespace("test-namespace")
    assert deleted.metadata.name == "test-namespace"
    
    print("  ✓ Namespace operations work")


def test_pod_creation():
    """Test creating pods."""
    print("Testing pod creation...")
    
    v1 = CoreV1Api()
    
    # Create a pod
    pod = V1Pod(
        metadata=V1ObjectMeta(
            name="test-pod",
            namespace="default",
            labels={"app": "test"}
        ),
        spec=V1PodSpec(
            containers=[
                V1Container(
                    name="nginx",
                    image="nginx:latest",
                    ports=[{"containerPort": 80}]
                )
            ]
        )
    )
    
    created = v1.create_namespaced_pod(namespace="default", body=pod)
    assert created.metadata.name == "test-pod"
    assert created.status.phase == "Running"
    
    print("  ✓ Pod creation works")


def test_pod_read():
    """Test reading pods."""
    print("Testing pod read...")
    
    v1 = CoreV1Api()
    
    # Create a pod first
    pod = V1Pod(
        metadata=V1ObjectMeta(name="read-test-pod", namespace="default"),
        spec=V1PodSpec(
            containers=[V1Container(name="nginx", image="nginx:latest")]
        )
    )
    v1.create_namespaced_pod(namespace="default", body=pod)
    
    # Read the pod
    read_pod = v1.read_namespaced_pod(name="read-test-pod", namespace="default")
    assert read_pod.metadata.name == "read-test-pod"
    assert read_pod.status.phase == "Running"
    
    print("  ✓ Pod read works")


def test_pod_list():
    """Test listing pods."""
    print("Testing pod list...")
    
    v1 = CoreV1Api()
    
    # Create some pods
    for i in range(3):
        pod = V1Pod(
            metadata=V1ObjectMeta(
                name=f"list-pod-{i}",
                namespace="default",
                labels={"app": "test", "number": str(i)}
            ),
            spec=V1PodSpec(
                containers=[V1Container(name="nginx", image="nginx:latest")]
            )
        )
        v1.create_namespaced_pod(namespace="default", body=pod)
    
    # List all pods in namespace
    pod_list = v1.list_namespaced_pod(namespace="default")
    assert len(pod_list.items) >= 3
    
    # List pods with label selector
    filtered = v1.list_namespaced_pod(namespace="default", label_selector="app=test")
    assert len(filtered.items) >= 3
    
    # List all pods across all namespaces
    all_pods = v1.list_pod_for_all_namespaces()
    assert len(all_pods.items) >= 3
    
    print("  ✓ Pod list works")


def test_pod_delete():
    """Test deleting pods."""
    print("Testing pod delete...")
    
    v1 = CoreV1Api()
    
    # Create a pod
    pod = V1Pod(
        metadata=V1ObjectMeta(name="delete-pod", namespace="default"),
        spec=V1PodSpec(
            containers=[V1Container(name="nginx", image="nginx:latest")]
        )
    )
    v1.create_namespaced_pod(namespace="default", body=pod)
    
    # Delete the pod
    deleted = v1.delete_namespaced_pod(name="delete-pod", namespace="default")
    assert deleted.metadata.name == "delete-pod"
    
    # Verify it's deleted
    try:
        v1.read_namespaced_pod(name="delete-pod", namespace="default")
        assert False, "Pod should have been deleted"
    except Exception as e:
        assert "not found" in str(e)
    
    print("  ✓ Pod delete works")


def test_pod_patch():
    """Test patching pods."""
    print("Testing pod patch...")
    
    v1 = CoreV1Api()
    
    # Create a pod
    pod = V1Pod(
        metadata=V1ObjectMeta(
            name="patch-pod",
            namespace="default",
            labels={"app": "test"}
        ),
        spec=V1PodSpec(
            containers=[V1Container(name="nginx", image="nginx:latest")]
        )
    )
    v1.create_namespaced_pod(namespace="default", body=pod)
    
    # Patch the pod labels
    patched = v1.patch_namespaced_pod(
        name="patch-pod",
        namespace="default",
        body={"metadata": {"labels": {"env": "production"}}}
    )
    assert patched.metadata.labels["app"] == "test"
    assert patched.metadata.labels["env"] == "production"
    
    print("  ✓ Pod patch works")


def test_service_creation():
    """Test creating services."""
    print("Testing service creation...")
    
    v1 = CoreV1Api()
    
    # Create a service
    service = V1Service(
        metadata=V1ObjectMeta(
            name="test-service",
            namespace="default",
            labels={"app": "web"}
        ),
        spec=V1ServiceSpec(
            selector={"app": "web"},
            ports=[
                V1ServicePort(port=80, target_port=8080, protocol="TCP", name="http")
            ],
            type="ClusterIP"
        )
    )
    
    created = v1.create_namespaced_service(namespace="default", body=service)
    assert created.metadata.name == "test-service"
    assert created.spec.type == "ClusterIP"
    assert len(created.spec.ports) == 1
    assert created.spec.ports[0].port == 80
    
    print("  ✓ Service creation works")


def test_service_read_and_list():
    """Test reading and listing services."""
    print("Testing service read and list...")
    
    v1 = CoreV1Api()
    
    # Create a service
    service = V1Service(
        metadata=V1ObjectMeta(name="read-service", namespace="default"),
        spec=V1ServiceSpec(
            selector={"app": "test"},
            ports=[V1ServicePort(port=80, target_port=80)]
        )
    )
    v1.create_namespaced_service(namespace="default", body=service)
    
    # Read the service
    read_service = v1.read_namespaced_service(name="read-service", namespace="default")
    assert read_service.metadata.name == "read-service"
    
    # List services
    service_list = v1.list_namespaced_service(namespace="default")
    assert len(service_list.items) >= 1
    
    print("  ✓ Service read and list works")


def test_service_delete():
    """Test deleting services."""
    print("Testing service delete...")
    
    v1 = CoreV1Api()
    
    # Create a service
    service = V1Service(
        metadata=V1ObjectMeta(name="delete-service", namespace="default"),
        spec=V1ServiceSpec(
            selector={"app": "test"},
            ports=[V1ServicePort(port=80)]
        )
    )
    v1.create_namespaced_service(namespace="default", body=service)
    
    # Delete the service
    deleted = v1.delete_namespaced_service(name="delete-service", namespace="default")
    assert deleted.metadata.name == "delete-service"
    
    print("  ✓ Service delete works")


def test_deployment_creation():
    """Test creating deployments."""
    print("Testing deployment creation...")
    
    apps_v1 = AppsV1Api()
    
    # Create a deployment
    deployment = V1Deployment(
        metadata=V1ObjectMeta(
            name="test-deployment",
            namespace="default",
            labels={"app": "web"}
        ),
        spec=V1DeploymentSpec(
            replicas=3,
            selector={"matchLabels": {"app": "web"}},
            template={
                "metadata": {"labels": {"app": "web"}},
                "spec": {
                    "containers": [
                        {"name": "nginx", "image": "nginx:latest"}
                    ]
                }
            }
        )
    )
    
    created = apps_v1.create_namespaced_deployment(namespace="default", body=deployment)
    assert created.metadata.name == "test-deployment"
    assert created.spec.replicas == 3
    assert created.status.replicas == 3
    assert created.status.ready_replicas == 3
    
    print("  ✓ Deployment creation works")


def test_deployment_read_and_list():
    """Test reading and listing deployments."""
    print("Testing deployment read and list...")
    
    apps_v1 = AppsV1Api()
    
    # Create a deployment
    deployment = V1Deployment(
        metadata=V1ObjectMeta(name="read-deployment", namespace="default"),
        spec=V1DeploymentSpec(
            replicas=2,
            selector={"matchLabels": {"app": "test"}},
            template={"metadata": {"labels": {"app": "test"}}}
        )
    )
    apps_v1.create_namespaced_deployment(namespace="default", body=deployment)
    
    # Read the deployment
    read_dep = apps_v1.read_namespaced_deployment(name="read-deployment", namespace="default")
    assert read_dep.metadata.name == "read-deployment"
    assert read_dep.spec.replicas == 2
    
    # List deployments
    deployment_list = apps_v1.list_namespaced_deployment(namespace="default")
    assert len(deployment_list.items) >= 1
    
    print("  ✓ Deployment read and list works")


def test_deployment_patch():
    """Test patching deployments (scaling)."""
    print("Testing deployment patch...")
    
    apps_v1 = AppsV1Api()
    
    # Create a deployment
    deployment = V1Deployment(
        metadata=V1ObjectMeta(name="patch-deployment", namespace="default"),
        spec=V1DeploymentSpec(
            replicas=2,
            selector={"matchLabels": {"app": "test"}},
            template={"metadata": {"labels": {"app": "test"}}}
        )
    )
    apps_v1.create_namespaced_deployment(namespace="default", body=deployment)
    
    # Patch the deployment (scale replicas)
    patched = apps_v1.patch_namespaced_deployment(
        name="patch-deployment",
        namespace="default",
        body={"spec": {"replicas": 5}}
    )
    assert patched.spec.replicas == 5
    assert patched.status.replicas == 5
    
    print("  ✓ Deployment patch works")


def test_deployment_delete():
    """Test deleting deployments."""
    print("Testing deployment delete...")
    
    apps_v1 = AppsV1Api()
    
    # Create a deployment
    deployment = V1Deployment(
        metadata=V1ObjectMeta(name="delete-deployment", namespace="default"),
        spec=V1DeploymentSpec(
            replicas=1,
            selector={"matchLabels": {"app": "test"}},
            template={"metadata": {"labels": {"app": "test"}}}
        )
    )
    apps_v1.create_namespaced_deployment(namespace="default", body=deployment)
    
    # Delete the deployment
    deleted = apps_v1.delete_namespaced_deployment(name="delete-deployment", namespace="default")
    assert deleted.metadata.name == "delete-deployment"
    
    print("  ✓ Deployment delete works")


def test_configmap_operations():
    """Test ConfigMap operations."""
    print("Testing ConfigMap operations...")
    
    v1 = CoreV1Api()
    
    # Create a ConfigMap
    config_map = V1ConfigMap(
        metadata=V1ObjectMeta(name="test-config", namespace="default"),
        data={
            "key1": "value1",
            "key2": "value2",
            "config.yaml": "app:\n  name: myapp\n"
        }
    )
    created = v1.create_namespaced_config_map(namespace="default", body=config_map)
    assert created.metadata.name == "test-config"
    assert created.data["key1"] == "value1"
    
    # Read the ConfigMap
    read_cm = v1.read_namespaced_config_map(name="test-config", namespace="default")
    assert read_cm.data["key2"] == "value2"
    
    # List ConfigMaps
    cm_list = v1.list_namespaced_config_map(namespace="default")
    assert len(cm_list.items) >= 1
    
    # Delete the ConfigMap
    deleted = v1.delete_namespaced_config_map(name="test-config", namespace="default")
    assert deleted.metadata.name == "test-config"
    
    print("  ✓ ConfigMap operations work")


def test_secret_operations():
    """Test Secret operations."""
    print("Testing Secret operations...")
    
    v1 = CoreV1Api()
    
    # Create a Secret
    secret = V1Secret(
        metadata=V1ObjectMeta(name="test-secret", namespace="default"),
        type="Opaque",
        data={
            "username": "YWRtaW4=",  # base64 encoded
            "password": "cGFzc3dvcmQ="  # base64 encoded
        }
    )
    created = v1.create_namespaced_secret(namespace="default", body=secret)
    assert created.metadata.name == "test-secret"
    assert created.type == "Opaque"
    assert created.data["username"] == "YWRtaW4="
    
    # Read the Secret
    read_secret = v1.read_namespaced_secret(name="test-secret", namespace="default")
    assert read_secret.data["password"] == "cGFzc3dvcmQ="
    
    # List Secrets
    secret_list = v1.list_namespaced_secret(namespace="default")
    assert len(secret_list.items) >= 1
    
    # Delete the Secret
    deleted = v1.delete_namespaced_secret(name="test-secret", namespace="default")
    assert deleted.metadata.name == "test-secret"
    
    print("  ✓ Secret operations work")


def test_resource_to_dict():
    """Test converting resources to dictionaries."""
    print("Testing resource to_dict...")
    
    # Test Pod to_dict
    pod = V1Pod(
        metadata=V1ObjectMeta(name="dict-pod", namespace="default"),
        spec=V1PodSpec(
            containers=[V1Container(name="nginx", image="nginx:latest")]
        ),
        status=V1PodStatus(phase="Running")
    )
    pod_dict = pod.to_dict()
    assert pod_dict["kind"] == "Pod"
    assert pod_dict["metadata"]["name"] == "dict-pod"
    assert pod_dict["status"]["phase"] == "Running"
    
    # Test Service to_dict
    service = V1Service(
        metadata=V1ObjectMeta(name="dict-service", namespace="default"),
        spec=V1ServiceSpec(
            selector={"app": "test"},
            ports=[V1ServicePort(port=80, target_port=8080)]
        )
    )
    service_dict = service.to_dict()
    assert service_dict["kind"] == "Service"
    assert service_dict["metadata"]["name"] == "dict-service"
    assert service_dict["spec"]["ports"][0]["port"] == 80
    
    # Test Deployment to_dict
    deployment = V1Deployment(
        metadata=V1ObjectMeta(name="dict-deployment", namespace="default"),
        spec=V1DeploymentSpec(
            replicas=3,
            selector={"matchLabels": {"app": "test"}},
            template={"metadata": {"labels": {"app": "test"}}}
        )
    )
    dep_dict = deployment.to_dict()
    assert dep_dict["kind"] == "Deployment"
    assert dep_dict["spec"]["replicas"] == 3
    
    print("  ✓ Resource to_dict works")


def test_multiple_namespaces():
    """Test operations across multiple namespaces."""
    print("Testing multiple namespaces...")
    
    v1 = CoreV1Api()
    
    # Create additional namespaces
    ns1 = V1Namespace(metadata=V1ObjectMeta(name="namespace-1"))
    ns2 = V1Namespace(metadata=V1ObjectMeta(name="namespace-2"))
    v1.create_namespace(ns1)
    v1.create_namespace(ns2)
    
    # Create pods in different namespaces
    for ns in ["namespace-1", "namespace-2"]:
        pod = V1Pod(
            metadata=V1ObjectMeta(name=f"pod-in-{ns}", namespace=ns),
            spec=V1PodSpec(
                containers=[V1Container(name="nginx", image="nginx:latest")]
            )
        )
        v1.create_namespaced_pod(namespace=ns, body=pod)
    
    # List pods in specific namespaces
    ns1_pods = v1.list_namespaced_pod(namespace="namespace-1")
    assert len(ns1_pods.items) == 1
    
    ns2_pods = v1.list_namespaced_pod(namespace="namespace-2")
    assert len(ns2_pods.items) == 1
    
    # List all pods
    all_pods = v1.list_pod_for_all_namespaces()
    assert len(all_pods.items) >= 2
    
    # Clean up
    v1.delete_namespace("namespace-1")
    v1.delete_namespace("namespace-2")
    
    print("  ✓ Multiple namespaces work")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Kubernetes Python Client Emulator Test Suite")
    print("=" * 60)
    
    tests = [
        test_config_loading,
        test_client_creation,
        test_namespace_operations,
        test_pod_creation,
        test_pod_read,
        test_pod_list,
        test_pod_delete,
        test_pod_patch,
        test_service_creation,
        test_service_read_and_list,
        test_service_delete,
        test_deployment_creation,
        test_deployment_read_and_list,
        test_deployment_patch,
        test_deployment_delete,
        test_configmap_operations,
        test_secret_operations,
        test_resource_to_dict,
        test_multiple_namespaces,
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"  ✗ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
