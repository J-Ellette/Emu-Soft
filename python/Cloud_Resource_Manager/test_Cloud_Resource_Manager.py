"""
Tests for boto3 emulator

Comprehensive test suite for AWS SDK emulator functionality.


Developed by PowerShield
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from Cloud_Resource_Manager import (
    Session, client, resource,
    S3Client, EC2Client, DynamoDBClient,
    S3Resource, DynamoDBResource,
    ClientError, NoCredentialsError,
    _s3_storage, _s3_buckets, _ec2_instances, _dynamodb_tables, _dynamodb_items
)


class TestSession(unittest.TestCase):
    """Test AWS Session functionality."""
    
    def setUp(self):
        """Clean storage before each test."""
        _s3_storage.clear()
        _s3_buckets.clear()
        _ec2_instances.clear()
        _dynamodb_tables.clear()
        _dynamodb_items.clear()
    
    def test_session_creation(self):
        """Test basic session creation."""
        session = Session(
            aws_access_key_id='test_key',
            aws_secret_access_key='test_secret',
            region_name='us-west-2'
        )
        
        self.assertEqual(session.aws_access_key_id, 'test_key')
        self.assertEqual(session.aws_secret_access_key, 'test_secret')
        self.assertEqual(session.region_name, 'us-west-2')
    
    def test_session_defaults(self):
        """Test session default values."""
        session = Session()
        
        self.assertEqual(session.aws_access_key_id, 'EMULATED_ACCESS_KEY')
        self.assertEqual(session.region_name, 'us-east-1')
    
    def test_session_create_client(self):
        """Test creating clients from session."""
        session = Session()
        
        s3 = session.client('s3')
        self.assertIsInstance(s3, S3Client)
        
        ec2 = session.client('ec2')
        self.assertIsInstance(ec2, EC2Client)
        
        dynamodb = session.client('dynamodb')
        self.assertIsInstance(dynamodb, DynamoDBClient)


class TestS3Client(unittest.TestCase):
    """Test S3 client functionality."""
    
    def setUp(self):
        """Clean storage before each test."""
        _s3_storage.clear()
        _s3_buckets.clear()
    
    def test_create_bucket(self):
        """Test creating an S3 bucket."""
        s3 = client('s3')
        response = s3.create_bucket(Bucket='test-bucket')
        
        self.assertEqual(response['Location'], '/test-bucket')
        self.assertIn('test-bucket', _s3_buckets)
    
    def test_put_and_get_object(self):
        """Test uploading and retrieving object."""
        s3 = client('s3')
        s3.create_bucket(Bucket='test-bucket')
        
        s3.put_object(Bucket='test-bucket', Key='file.txt', Body=b'test content')
        response = s3.get_object(Bucket='test-bucket', Key='file.txt')
        
        self.assertEqual(response['Body'], b'test content')
        self.assertIn('ETag', response)
    
    def test_list_objects(self):
        """Test listing objects in bucket."""
        s3 = client('s3')
        s3.create_bucket(Bucket='test-bucket')
        s3.put_object(Bucket='test-bucket', Key='file1.txt', Body=b'content1')
        s3.put_object(Bucket='test-bucket', Key='file2.txt', Body=b'content2')
        
        response = s3.list_objects_v2(Bucket='test-bucket')
        
        self.assertEqual(response['KeyCount'], 2)
        self.assertEqual(len(response['Contents']), 2)
    
    def test_delete_object(self):
        """Test deleting object from S3."""
        s3 = client('s3')
        s3.create_bucket(Bucket='test-bucket')
        s3.put_object(Bucket='test-bucket', Key='file.txt', Body=b'content')
        
        s3.delete_object(Bucket='test-bucket', Key='file.txt')
        
        self.assertNotIn('file.txt', _s3_storage['test-bucket'])
    
    def test_error_on_nonexistent_bucket(self):
        """Test error when accessing nonexistent bucket."""
        s3 = client('s3')
        
        with self.assertRaises(ClientError) as context:
            s3.get_object(Bucket='nonexistent', Key='file.txt')
        
        self.assertIn('NoSuchBucket', str(context.exception))


class TestEC2Client(unittest.TestCase):
    """Test EC2 client functionality."""
    
    def setUp(self):
        """Clean storage before each test."""
        _ec2_instances.clear()
    
    def test_run_instances(self):
        """Test launching EC2 instances."""
        ec2 = client('ec2')
        
        response = ec2.run_instances(ImageId='ami-12345', MinCount=1, MaxCount=2)
        
        self.assertEqual(len(response['Instances']), 2)
        for instance in response['Instances']:
            self.assertIn('InstanceId', instance)
            self.assertEqual(instance['ImageId'], 'ami-12345')
    
    def test_describe_instances(self):
        """Test describing EC2 instances."""
        ec2 = client('ec2')
        response = ec2.run_instances(ImageId='ami-12345', MinCount=1, MaxCount=1)
        instance_id = response['Instances'][0]['InstanceId']
        
        response = ec2.describe_instances(InstanceIds=[instance_id])
        
        self.assertEqual(len(response['Reservations']), 1)
        self.assertEqual(response['Reservations'][0]['Instances'][0]['InstanceId'], instance_id)
    
    def test_terminate_instances(self):
        """Test terminating EC2 instances."""
        ec2 = client('ec2')
        response = ec2.run_instances(ImageId='ami-12345', MinCount=1, MaxCount=1)
        instance_id = response['Instances'][0]['InstanceId']
        
        response = ec2.terminate_instances(InstanceIds=[instance_id])
        
        self.assertEqual(len(response['TerminatingInstances']), 1)
        self.assertNotIn(instance_id, _ec2_instances)


class TestDynamoDBClient(unittest.TestCase):
    """Test DynamoDB client functionality."""
    
    def setUp(self):
        """Clean storage before each test."""
        _dynamodb_tables.clear()
        _dynamodb_items.clear()
    
    def test_create_table(self):
        """Test creating a DynamoDB table."""
        dynamodb = client('dynamodb')
        
        response = dynamodb.create_table(
            TableName='test-table',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}]
        )
        
        self.assertEqual(response['TableDescription']['TableName'], 'test-table')
        self.assertIn('test-table', _dynamodb_tables)
    
    def test_put_and_get_item(self):
        """Test putting and getting item."""
        dynamodb = client('dynamodb')
        dynamodb.create_table(
            TableName='test-table',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}]
        )
        
        item = {'id': {'S': '123'}, 'name': {'S': 'Test'}}
        dynamodb.put_item(TableName='test-table', Item=item)
        
        response = dynamodb.get_item(TableName='test-table', Key={'id': {'S': '123'}})
        
        self.assertEqual(response['Item'], item)
    
    def test_scan_table(self):
        """Test scanning DynamoDB table."""
        dynamodb = client('dynamodb')
        dynamodb.create_table(
            TableName='test-table',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}]
        )
        
        dynamodb.put_item(TableName='test-table', Item={'id': {'S': '1'}, 'name': {'S': 'Item1'}})
        dynamodb.put_item(TableName='test-table', Item={'id': {'S': '2'}, 'name': {'S': 'Item2'}})
        
        response = dynamodb.scan(TableName='test-table')
        
        self.assertEqual(response['Count'], 2)
        self.assertEqual(len(response['Items']), 2)
    
    def test_delete_table(self):
        """Test deleting a DynamoDB table."""
        dynamodb = client('dynamodb')
        dynamodb.create_table(
            TableName='test-table',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}]
        )
        
        dynamodb.delete_table(TableName='test-table')
        
        self.assertNotIn('test-table', _dynamodb_tables)


class TestS3Resource(unittest.TestCase):
    """Test S3 resource interface."""
    
    def setUp(self):
        """Clean storage before each test."""
        _s3_storage.clear()
        _s3_buckets.clear()
    
    def test_bucket_resource(self):
        """Test creating bucket via resource."""
        s3 = resource('s3')
        bucket = s3.Bucket('test-bucket')
        bucket.create()
        
        self.assertIn('test-bucket', _s3_buckets)
    
    def test_object_resource(self):
        """Test object operations via resource."""
        s3 = resource('s3')
        s3.Bucket('test-bucket').create()
        
        obj = s3.Object('test-bucket', 'file.txt')
        obj.put(Body=b'test content')
        
        response = obj.get()
        self.assertEqual(response['Body'], b'test content')


class TestIntegrationScenarios(unittest.TestCase):
    """Test complete usage scenarios."""
    
    def setUp(self):
        """Clean storage before each test."""
        _s3_storage.clear()
        _s3_buckets.clear()
        _ec2_instances.clear()
        _dynamodb_tables.clear()
        _dynamodb_items.clear()
    
    def test_s3_workflow(self):
        """Test complete S3 workflow."""
        s3 = client('s3')
        
        # Create bucket
        s3.create_bucket(Bucket='my-bucket')
        
        # Upload files
        s3.put_object(Bucket='my-bucket', Key='doc1.txt', Body=b'Document 1')
        s3.put_object(Bucket='my-bucket', Key='doc2.txt', Body=b'Document 2')
        
        # List objects
        response = s3.list_objects_v2(Bucket='my-bucket')
        self.assertEqual(response['KeyCount'], 2)
        
        # Download file
        obj = s3.get_object(Bucket='my-bucket', Key='doc1.txt')
        self.assertEqual(obj['Body'], b'Document 1')
        
        # Delete file
        s3.delete_object(Bucket='my-bucket', Key='doc1.txt')
        
        # Verify deletion
        response = s3.list_objects_v2(Bucket='my-bucket')
        self.assertEqual(response['KeyCount'], 1)
    
    def test_multi_service_integration(self):
        """Test using multiple AWS services together."""
        session = Session(region_name='us-west-2')
        
        # S3
        s3 = session.client('s3')
        s3.create_bucket(Bucket='data-bucket')
        s3.put_object(Bucket='data-bucket', Key='data.json', Body=b'{"key": "value"}')
        
        # EC2
        ec2 = session.client('ec2')
        response = ec2.run_instances(ImageId='ami-12345', MinCount=1, MaxCount=1)
        instance_id = response['Instances'][0]['InstanceId']
        
        # DynamoDB
        dynamodb = session.client('dynamodb')
        dynamodb.create_table(
            TableName='metadata',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}]
        )
        dynamodb.put_item(
            TableName='metadata',
            Item={'id': {'S': 'job-1'}, 'instance': {'S': instance_id}}
        )
        
        # Verify all services working
        self.assertIn('data-bucket', _s3_buckets)
        self.assertIn(instance_id, _ec2_instances)
        self.assertIn('metadata', _dynamodb_tables)


if __name__ == '__main__':
    unittest.main()
