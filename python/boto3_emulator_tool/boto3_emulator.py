"""
boto3 Emulator - AWS SDK for Python

This module emulates the boto3 library, which is the Amazon Web Services (AWS) SDK
for Python. It enables Python developers to write software that makes use of
services like Amazon S3, Amazon EC2, Amazon DynamoDB, and more.

Key Features:
- S3 (Simple Storage Service) client
- EC2 (Elastic Compute Cloud) client
- DynamoDB client
- Session management
- Resource and client interfaces
- Basic AWS service operations
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from collections import defaultdict
import json
import uuid


class BotoClientError(Exception):
    """Base exception for boto client errors."""
    pass


class NoCredentialsError(BotoClientError):
    """Raised when AWS credentials are not found."""
    pass


class ClientError(BotoClientError):
    """Raised when an AWS service returns an error."""
    
    def __init__(self, error_response: Dict[str, Any], operation_name: str):
        self.response = error_response
        self.operation_name = operation_name
        super().__init__(f"An error occurred ({error_response.get('Error', {}).get('Code')}) when calling the {operation_name} operation")


# In-memory storage for emulated AWS services
_s3_storage: Dict[str, Dict[str, bytes]] = defaultdict(dict)  # bucket -> {key: data}
_s3_buckets: Dict[str, Dict[str, Any]] = {}  # bucket metadata
_dynamodb_tables: Dict[str, Dict[str, Any]] = {}  # table_name -> table_data
_dynamodb_items: Dict[str, List[Dict[str, Any]]] = defaultdict(list)  # table_name -> items
_ec2_instances: Dict[str, Dict[str, Any]] = {}  # instance_id -> instance_data


class Session:
    """AWS session for managing configurations and credentials."""
    
    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        region_name: Optional[str] = None,
        profile_name: Optional[str] = None
    ):
        """
        Initialize AWS session.
        
        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            aws_session_token: AWS session token
            region_name: AWS region name (e.g., 'us-east-1')
            profile_name: AWS profile name
        """
        self.aws_access_key_id = aws_access_key_id or 'EMULATED_ACCESS_KEY'
        self.aws_secret_access_key = aws_secret_access_key or 'EMULATED_SECRET_KEY'
        self.aws_session_token = aws_session_token
        self.region_name = region_name or 'us-east-1'
        self.profile_name = profile_name
    
    def client(self, service_name: str, **kwargs) -> Union[S3Client, EC2Client, DynamoDBClient]:
        """
        Create a low-level service client.
        
        Args:
            service_name: Name of the service (e.g., 's3', 'ec2', 'dynamodb')
            **kwargs: Additional client configuration
        
        Returns:
            Service client instance
        """
        region = kwargs.get('region_name', self.region_name)
        
        if service_name == 's3':
            return S3Client(region_name=region, session=self)
        elif service_name == 'ec2':
            return EC2Client(region_name=region, session=self)
        elif service_name == 'dynamodb':
            return DynamoDBClient(region_name=region, session=self)
        else:
            raise ValueError(f"Unknown service: {service_name}")
    
    def resource(self, service_name: str, **kwargs) -> Union[S3Resource, DynamoDBResource]:
        """
        Create a high-level service resource.
        
        Args:
            service_name: Name of the service (e.g., 's3', 'dynamodb')
            **kwargs: Additional resource configuration
        
        Returns:
            Service resource instance
        """
        region = kwargs.get('region_name', self.region_name)
        
        if service_name == 's3':
            return S3Resource(region_name=region, session=self)
        elif service_name == 'dynamodb':
            return DynamoDBResource(region_name=region, session=self)
        else:
            raise ValueError(f"Unknown service resource: {service_name}")


class S3Client:
    """Amazon S3 client for object storage operations."""
    
    def __init__(self, region_name: str = 'us-east-1', session: Optional[Session] = None):
        self.region_name = region_name
        self.session = session
    
    def create_bucket(self, Bucket: str, **kwargs) -> Dict[str, Any]:
        """Create a new S3 bucket."""
        if Bucket in _s3_buckets:
            raise ClientError(
                {'Error': {'Code': 'BucketAlreadyExists', 'Message': 'The requested bucket name is not available'}},
                'CreateBucket'
            )
        
        _s3_buckets[Bucket] = {
            'Name': Bucket,
            'CreationDate': datetime.utcnow(),
            'Region': self.region_name
        }
        
        return {'Location': f'/{Bucket}'}
    
    def list_buckets(self) -> Dict[str, Any]:
        """List all S3 buckets."""
        buckets = [
            {'Name': name, 'CreationDate': data['CreationDate']}
            for name, data in _s3_buckets.items()
        ]
        return {
            'Buckets': buckets,
            'Owner': {'ID': 'emulated-owner-id'}
        }
    
    def delete_bucket(self, Bucket: str) -> Dict[str, Any]:
        """Delete an S3 bucket."""
        if Bucket not in _s3_buckets:
            raise ClientError(
                {'Error': {'Code': 'NoSuchBucket', 'Message': 'The specified bucket does not exist'}},
                'DeleteBucket'
            )
        
        if _s3_storage[Bucket]:
            raise ClientError(
                {'Error': {'Code': 'BucketNotEmpty', 'Message': 'The bucket you tried to delete is not empty'}},
                'DeleteBucket'
            )
        
        del _s3_buckets[Bucket]
        del _s3_storage[Bucket]
        return {}
    
    def put_object(self, Bucket: str, Key: str, Body: Union[str, bytes], **kwargs) -> Dict[str, Any]:
        """Upload an object to S3."""
        if Bucket not in _s3_buckets:
            raise ClientError(
                {'Error': {'Code': 'NoSuchBucket', 'Message': 'The specified bucket does not exist'}},
                'PutObject'
            )
        
        if isinstance(Body, str):
            Body = Body.encode('utf-8')
        
        _s3_storage[Bucket][Key] = Body
        
        return {
            'ETag': f'"{uuid.uuid4().hex}"',
            'VersionId': str(uuid.uuid4())
        }
    
    def get_object(self, Bucket: str, Key: str, **kwargs) -> Dict[str, Any]:
        """Retrieve an object from S3."""
        if Bucket not in _s3_buckets:
            raise ClientError(
                {'Error': {'Code': 'NoSuchBucket', 'Message': 'The specified bucket does not exist'}},
                'GetObject'
            )
        
        if Key not in _s3_storage[Bucket]:
            raise ClientError(
                {'Error': {'Code': 'NoSuchKey', 'Message': 'The specified key does not exist'}},
                'GetObject'
            )
        
        body = _s3_storage[Bucket][Key]
        
        return {
            'Body': body,
            'ContentLength': len(body),
            'ContentType': 'binary/octet-stream',
            'ETag': f'"{uuid.uuid4().hex}"',
            'LastModified': datetime.utcnow()
        }
    
    def delete_object(self, Bucket: str, Key: str, **kwargs) -> Dict[str, Any]:
        """Delete an object from S3."""
        if Bucket not in _s3_buckets:
            raise ClientError(
                {'Error': {'Code': 'NoSuchBucket', 'Message': 'The specified bucket does not exist'}},
                'DeleteObject'
            )
        
        if Key in _s3_storage[Bucket]:
            del _s3_storage[Bucket][Key]
        
        return {'DeleteMarker': True}
    
    def list_objects_v2(self, Bucket: str, **kwargs) -> Dict[str, Any]:
        """List objects in an S3 bucket."""
        if Bucket not in _s3_buckets:
            raise ClientError(
                {'Error': {'Code': 'NoSuchBucket', 'Message': 'The specified bucket does not exist'}},
                'ListObjectsV2'
            )
        
        prefix = kwargs.get('Prefix', '')
        max_keys = kwargs.get('MaxKeys', 1000)
        
        objects = []
        for key, data in _s3_storage[Bucket].items():
            if key.startswith(prefix):
                objects.append({
                    'Key': key,
                    'Size': len(data),
                    'LastModified': datetime.utcnow(),
                    'ETag': f'"{uuid.uuid4().hex}"'
                })
        
        objects = objects[:max_keys]
        
        return {
            'Contents': objects,
            'Name': Bucket,
            'KeyCount': len(objects),
            'IsTruncated': False
        }


class EC2Client:
    """Amazon EC2 client for compute operations."""
    
    def __init__(self, region_name: str = 'us-east-1', session: Optional[Session] = None):
        self.region_name = region_name
        self.session = session
    
    def run_instances(
        self,
        ImageId: str,
        MinCount: int = 1,
        MaxCount: int = 1,
        InstanceType: str = 't2.micro',
        **kwargs
    ) -> Dict[str, Any]:
        """Launch EC2 instances."""
        instances = []
        
        for _ in range(MaxCount):
            instance_id = f"i-{uuid.uuid4().hex[:17]}"
            instance = {
                'InstanceId': instance_id,
                'ImageId': ImageId,
                'InstanceType': InstanceType,
                'State': {'Code': 0, 'Name': 'pending'},
                'LaunchTime': datetime.utcnow(),
                'Placement': {'AvailabilityZone': f"{self.region_name}a"},
                'PrivateIpAddress': f"10.0.{len(_ec2_instances)}.{len(instances) + 1}",
                'PublicIpAddress': f"54.{len(_ec2_instances)}.{len(instances)}.1"
            }
            _ec2_instances[instance_id] = instance
            instances.append(instance)
        
        return {'Instances': instances}
    
    def describe_instances(self, InstanceIds: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """Describe EC2 instances."""
        if InstanceIds:
            instances = [_ec2_instances[iid] for iid in InstanceIds if iid in _ec2_instances]
        else:
            instances = list(_ec2_instances.values())
        
        reservations = [{
            'ReservationId': f"r-{uuid.uuid4().hex[:17]}",
            'Instances': instances
        }] if instances else []
        
        return {'Reservations': reservations}
    
    def terminate_instances(self, InstanceIds: List[str], **kwargs) -> Dict[str, Any]:
        """Terminate EC2 instances."""
        terminating = []
        
        for instance_id in InstanceIds:
            if instance_id in _ec2_instances:
                instance = _ec2_instances[instance_id]
                instance['State'] = {'Code': 32, 'Name': 'shutting-down'}
                terminating.append({
                    'InstanceId': instance_id,
                    'CurrentState': instance['State'],
                    'PreviousState': {'Code': 16, 'Name': 'running'}
                })
                del _ec2_instances[instance_id]
        
        return {'TerminatingInstances': terminating}
    
    def stop_instances(self, InstanceIds: List[str], **kwargs) -> Dict[str, Any]:
        """Stop EC2 instances."""
        stopping = []
        
        for instance_id in InstanceIds:
            if instance_id in _ec2_instances:
                instance = _ec2_instances[instance_id]
                instance['State'] = {'Code': 64, 'Name': 'stopping'}
                stopping.append({
                    'InstanceId': instance_id,
                    'CurrentState': instance['State'],
                    'PreviousState': {'Code': 16, 'Name': 'running'}
                })
        
        return {'StoppingInstances': stopping}


class DynamoDBClient:
    """Amazon DynamoDB client for NoSQL database operations."""
    
    def __init__(self, region_name: str = 'us-east-1', session: Optional[Session] = None):
        self.region_name = region_name
        self.session = session
    
    def create_table(
        self,
        TableName: str,
        KeySchema: List[Dict[str, str]],
        AttributeDefinitions: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Create a DynamoDB table."""
        if TableName in _dynamodb_tables:
            raise ClientError(
                {'Error': {'Code': 'ResourceInUseException', 'Message': 'Table already exists'}},
                'CreateTable'
            )
        
        table = {
            'TableName': TableName,
            'TableStatus': 'ACTIVE',
            'CreationDateTime': datetime.utcnow(),
            'KeySchema': KeySchema,
            'AttributeDefinitions': AttributeDefinitions,
            'ItemCount': 0
        }
        
        _dynamodb_tables[TableName] = table
        return {'TableDescription': table}
    
    def delete_table(self, TableName: str) -> Dict[str, Any]:
        """Delete a DynamoDB table."""
        if TableName not in _dynamodb_tables:
            raise ClientError(
                {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}},
                'DeleteTable'
            )
        
        table = _dynamodb_tables[TableName]
        table['TableStatus'] = 'DELETING'
        del _dynamodb_tables[TableName]
        if TableName in _dynamodb_items:
            del _dynamodb_items[TableName]
        
        return {'TableDescription': table}
    
    def describe_table(self, TableName: str) -> Dict[str, Any]:
        """Describe a DynamoDB table."""
        if TableName not in _dynamodb_tables:
            raise ClientError(
                {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}},
                'DescribeTable'
            )
        
        return {'Table': _dynamodb_tables[TableName]}
    
    def list_tables(self, **kwargs) -> Dict[str, Any]:
        """List all DynamoDB tables."""
        return {'TableNames': list(_dynamodb_tables.keys())}
    
    def put_item(self, TableName: str, Item: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Put an item into a DynamoDB table."""
        if TableName not in _dynamodb_tables:
            raise ClientError(
                {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}},
                'PutItem'
            )
        
        _dynamodb_items[TableName].append(Item)
        _dynamodb_tables[TableName]['ItemCount'] = len(_dynamodb_items[TableName])
        
        return {'Attributes': Item}
    
    def get_item(self, TableName: str, Key: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Get an item from a DynamoDB table."""
        if TableName not in _dynamodb_tables:
            raise ClientError(
                {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}},
                'GetItem'
            )
        
        # Simple key matching
        for item in _dynamodb_items[TableName]:
            if all(item.get(k) == v for k, v in Key.items()):
                return {'Item': item}
        
        return {}
    
    def scan(self, TableName: str, **kwargs) -> Dict[str, Any]:
        """Scan a DynamoDB table."""
        if TableName not in _dynamodb_tables:
            raise ClientError(
                {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}},
                'Scan'
            )
        
        items = _dynamodb_items[TableName]
        limit = kwargs.get('Limit', len(items))
        
        return {
            'Items': items[:limit],
            'Count': min(len(items), limit),
            'ScannedCount': min(len(items), limit)
        }
    
    def query(self, TableName: str, KeyConditionExpression: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Query a DynamoDB table."""
        if TableName not in _dynamodb_tables:
            raise ClientError(
                {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}},
                'Query'
            )
        
        # Simplified query - return all items
        items = _dynamodb_items[TableName]
        limit = kwargs.get('Limit', len(items))
        
        return {
            'Items': items[:limit],
            'Count': min(len(items), limit),
            'ScannedCount': min(len(items), limit)
        }


class S3Resource:
    """High-level S3 resource interface."""
    
    def __init__(self, region_name: str = 'us-east-1', session: Optional[Session] = None):
        self.region_name = region_name
        self.session = session
        self.client = S3Client(region_name=region_name, session=session)
    
    def Bucket(self, name: str):
        """Get a bucket resource."""
        return S3Bucket(name, self.client)
    
    def Object(self, bucket_name: str, key: str):
        """Get an object resource."""
        return S3Object(bucket_name, key, self.client)
    
    @property
    def buckets(self):
        """Get buckets collection."""
        return S3BucketsCollection(self.client)


class S3Bucket:
    """S3 Bucket resource."""
    
    def __init__(self, name: str, client: S3Client):
        self.name = name
        self.client = client
    
    def create(self, **kwargs):
        """Create the bucket."""
        return self.client.create_bucket(Bucket=self.name, **kwargs)
    
    def delete(self):
        """Delete the bucket."""
        return self.client.delete_bucket(Bucket=self.name)
    
    def upload_file(self, filename: str, key: str):
        """Upload a file to the bucket.
        
        Note: This is a simplified emulator implementation.
        In production, file I/O errors should be handled.
        """
        try:
            with open(filename, 'rb') as f:
                return self.client.put_object(Bucket=self.name, Key=key, Body=f.read())
        except (IOError, OSError) as e:
            raise ClientError(
                {'Error': {'Code': 'FileReadError', 'Message': f'Failed to read file: {e}'}},
                'UploadFile'
            )
    
    def download_file(self, key: str, filename: str):
        """Download a file from the bucket."""
        response = self.client.get_object(Bucket=self.name, Key=key)
        with open(filename, 'wb') as f:
            f.write(response['Body'])


class S3Object:
    """S3 Object resource."""
    
    def __init__(self, bucket_name: str, key: str, client: S3Client):
        self.bucket_name = bucket_name
        self.key = key
        self.client = client
    
    def put(self, Body: Union[str, bytes], **kwargs):
        """Upload object."""
        return self.client.put_object(Bucket=self.bucket_name, Key=self.key, Body=Body, **kwargs)
    
    def get(self):
        """Get object."""
        return self.client.get_object(Bucket=self.bucket_name, Key=self.key)
    
    def delete(self):
        """Delete object."""
        return self.client.delete_object(Bucket=self.bucket_name, Key=self.key)


class S3BucketsCollection:
    """Collection of S3 buckets."""
    
    def __init__(self, client: S3Client):
        self.client = client
    
    def all(self):
        """Get all buckets."""
        response = self.client.list_buckets()
        return [S3Bucket(b['Name'], self.client) for b in response['Buckets']]


class DynamoDBResource:
    """High-level DynamoDB resource interface."""
    
    def __init__(self, region_name: str = 'us-east-1', session: Optional[Session] = None):
        self.region_name = region_name
        self.session = session
        self.client = DynamoDBClient(region_name=region_name, session=session)
    
    def Table(self, name: str):
        """Get a table resource."""
        return DynamoDBTable(name, self.client)


class DynamoDBTable:
    """DynamoDB Table resource."""
    
    def __init__(self, name: str, client: DynamoDBClient):
        self.name = name
        self.client = client
    
    def put_item(self, Item: Dict[str, Any], **kwargs):
        """Put an item into the table."""
        return self.client.put_item(TableName=self.name, Item=Item, **kwargs)
    
    def get_item(self, Key: Dict[str, Any], **kwargs):
        """Get an item from the table."""
        return self.client.get_item(TableName=self.name, Key=Key, **kwargs)
    
    def scan(self, **kwargs):
        """Scan the table."""
        return self.client.scan(TableName=self.name, **kwargs)
    
    def query(self, **kwargs):
        """Query the table."""
        return self.client.query(TableName=self.name, **kwargs)


# Module-level convenience functions
def client(service_name: str, **kwargs):
    """Create a low-level service client."""
    session = Session(**kwargs)
    return session.client(service_name, **kwargs)


def resource(service_name: str, **kwargs):
    """Create a high-level service resource."""
    session = Session(**kwargs)
    return session.resource(service_name, **kwargs)
