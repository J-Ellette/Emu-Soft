# boto3 Emulator - AWS SDK for Python

This module emulates the **boto3** library, which is the Amazon Web Services (AWS) SDK for Python. It enables Python developers to write software that makes use of services like Amazon S3, Amazon EC2, Amazon DynamoDB, and more.

## What is boto3?

boto3 is the official AWS SDK for Python, developed and maintained by Amazon Web Services. It provides:
- Easy-to-use, object-oriented API for AWS services
- Low-level service clients and high-level resource interfaces
- Automatic pagination and retry logic
- Support for all AWS services
- Comprehensive documentation and examples

## Features

This emulator implements core functionality for three major AWS services:

### S3 (Simple Storage Service)
- Bucket operations (create, list, delete)
- Object operations (put, get, delete, list)
- Both client and resource interfaces
- Prefix-based filtering
- File upload/download support

### EC2 (Elastic Compute Cloud)
- Instance launching (run_instances)
- Instance management (describe, stop, terminate)
- Multiple instance support
- Instance metadata (IDs, IPs, state)

### DynamoDB (NoSQL Database)
- Table operations (create, describe, delete, list)
- Item operations (put, get, scan, query)
- Key schema and attribute definitions
- Both client and resource interfaces

### Session Management
- AWS credentials configuration
- Region selection
- Profile support
- Client and resource creation

## Usage Examples

### Creating Clients and Resources

```python
from boto3_emulator import client, resource, Session

# Using module-level functions
s3_client = client('s3')
s3_resource = resource('s3')

# Using sessions
session = Session(region_name='us-west-2')
ec2 = session.client('ec2')
dynamodb = session.resource('dynamodb')
```

### S3 Examples

#### Basic Bucket and Object Operations

```python
from boto3_emulator import client

s3 = client('s3')

# Create a bucket
s3.create_bucket(Bucket='my-bucket')

# Upload an object
s3.put_object(
    Bucket='my-bucket',
    Key='documents/report.pdf',
    Body=b'PDF content here'
)

# Download an object
response = s3.get_object(Bucket='my-bucket', Key='documents/report.pdf')
content = response['Body']

# List objects
response = s3.list_objects_v2(Bucket='my-bucket', Prefix='documents/')
for obj in response['Contents']:
    print(f"Key: {obj['Key']}, Size: {obj['Size']}")

# Delete an object
s3.delete_object(Bucket='my-bucket', Key='documents/report.pdf')

# List all buckets
response = s3.list_buckets()
for bucket in response['Buckets']:
    print(f"Bucket: {bucket['Name']}")

# Delete bucket
s3.delete_bucket(Bucket='my-bucket')
```

#### Using S3 Resource Interface

```python
from boto3_emulator import resource

s3 = resource('s3')

# Create a bucket
bucket = s3.Bucket('my-bucket')
bucket.create()

# Upload an object
obj = s3.Object('my-bucket', 'file.txt')
obj.put(Body=b'Hello, World!')

# Download an object
response = obj.get()
content = response['Body']

# Delete an object
obj.delete()

# List all buckets
for bucket in s3.buckets.all():
    print(f"Bucket: {bucket.name}")
```

#### File Upload/Download

```python
from boto3_emulator import resource

s3 = resource('s3')
bucket = s3.Bucket('my-bucket')
bucket.create()

# Upload a file
bucket.upload_file('local_file.txt', 'remote_file.txt')

# Download a file
bucket.download_file('remote_file.txt', 'downloaded_file.txt')
```

### EC2 Examples

#### Instance Management

```python
from boto3_emulator import client

ec2 = client('ec2', region_name='us-east-1')

# Launch instances
response = ec2.run_instances(
    ImageId='ami-0c55b159cbfafe1f0',
    MinCount=1,
    MaxCount=2,
    InstanceType='t2.micro'
)

instance_ids = [inst['InstanceId'] for inst in response['Instances']]
print(f"Launched instances: {instance_ids}")

# Describe instances
response = ec2.describe_instances(InstanceIds=instance_ids)
for reservation in response['Reservations']:
    for instance in reservation['Instances']:
        print(f"Instance {instance['InstanceId']}: {instance['State']['Name']}")

# Stop instances
ec2.stop_instances(InstanceIds=[instance_ids[0]])

# Terminate instances
response = ec2.terminate_instances(InstanceIds=instance_ids)
print(f"Terminated {len(response['TerminatingInstances'])} instances")
```

#### Querying All Instances

```python
from boto3_emulator import client

ec2 = client('ec2')

# Launch some instances
ec2.run_instances(ImageId='ami-12345', MinCount=1, MaxCount=3)

# Describe all instances
response = ec2.describe_instances()
for reservation in response['Reservations']:
    for instance in reservation['Instances']:
        print(f"Instance: {instance['InstanceId']}")
        print(f"  Type: {instance['InstanceType']}")
        print(f"  State: {instance['State']['Name']}")
        print(f"  Private IP: {instance['PrivateIpAddress']}")
        print(f"  Public IP: {instance['PublicIpAddress']}")
```

### DynamoDB Examples

#### Table and Item Operations (Client)

```python
from boto3_emulator import client

dynamodb = client('dynamodb')

# Create a table
response = dynamodb.create_table(
    TableName='users',
    KeySchema=[
        {'AttributeName': 'user_id', 'KeyType': 'HASH'}  # Partition key
    ],
    AttributeDefinitions=[
        {'AttributeName': 'user_id', 'AttributeType': 'S'}
    ]
)

print(f"Table status: {response['TableDescription']['TableStatus']}")

# Put an item
dynamodb.put_item(
    TableName='users',
    Item={
        'user_id': {'S': '123'},
        'username': {'S': 'john_doe'},
        'email': {'S': 'john@example.com'},
        'age': {'N': '30'}
    }
)

# Get an item
response = dynamodb.get_item(
    TableName='users',
    Key={'user_id': {'S': '123'}}
)

if 'Item' in response:
    item = response['Item']
    print(f"User: {item['username']['S']}, Email: {item['email']['S']}")

# Scan the table
response = dynamodb.scan(TableName='users')
print(f"Found {response['Count']} items")
for item in response['Items']:
    print(f"  User ID: {item['user_id']['S']}")

# List all tables
response = dynamodb.list_tables()
print(f"Tables: {response['TableNames']}")

# Describe a table
response = dynamodb.describe_table(TableName='users')
table = response['Table']
print(f"Table: {table['TableName']}, Status: {table['TableStatus']}")

# Delete the table
dynamodb.delete_table(TableName='users')
```

#### Using DynamoDB Resource Interface

```python
from boto3_emulator import client, resource

# Create table using client (required for table creation)
dynamodb_client = client('dynamodb')
dynamodb_client.create_table(
    TableName='products',
    KeySchema=[{'AttributeName': 'product_id', 'KeyType': 'HASH'}],
    AttributeDefinitions=[{'AttributeName': 'product_id', 'AttributeType': 'S'}]
)

# Use resource for item operations
dynamodb = resource('dynamodb')
table = dynamodb.Table('products')

# Put items
table.put_item(Item={
    'product_id': {'S': 'prod-001'},
    'name': {'S': 'Laptop'},
    'price': {'N': '999.99'}
})

table.put_item(Item={
    'product_id': {'S': 'prod-002'},
    'name': {'S': 'Mouse'},
    'price': {'N': '29.99'}
})

# Get an item
response = table.get_item(Key={'product_id': {'S': 'prod-001'}})
print(response['Item'])

# Scan the table
response = table.scan()
print(f"Products: {response['Count']}")
for item in response['Items']:
    print(f"  {item['product_id']['S']}: {item['name']['S']}")
```

### Complete Application Example

```python
from boto3_emulator import Session

# Initialize session
session = Session(
    aws_access_key_id='YOUR_ACCESS_KEY',
    aws_secret_access_key='YOUR_SECRET_KEY',
    region_name='us-east-1'
)

# S3: Store user uploads
s3 = session.client('s3')
s3.create_bucket(Bucket='user-uploads')
s3.put_object(
    Bucket='user-uploads',
    Key='profiles/user123.jpg',
    Body=b'image data...'
)

# DynamoDB: Store user metadata
dynamodb = session.client('dynamodb')
dynamodb.create_table(
    TableName='user-metadata',
    KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
    AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}]
)

dynamodb.put_item(
    TableName='user-metadata',
    Item={
        'user_id': {'S': 'user123'},
        'profile_pic': {'S': 's3://user-uploads/profiles/user123.jpg'},
        'created_at': {'S': '2024-01-01T00:00:00Z'}
    }
)

# EC2: Launch processing instances
ec2 = session.client('ec2')
response = ec2.run_instances(
    ImageId='ami-processing',
    MinCount=1,
    MaxCount=1,
    InstanceType='c5.xlarge'
)

instance_id = response['Instances'][0]['InstanceId']
print(f"Processing instance launched: {instance_id}")

# Clean up
s3.delete_object(Bucket='user-uploads', Key='profiles/user123.jpg')
ec2.terminate_instances(InstanceIds=[instance_id])
```

## Error Handling

```python
from boto3_emulator import client, ClientError

s3 = client('s3')

try:
    # Try to get non-existent object
    s3.get_object(Bucket='my-bucket', Key='missing.txt')
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'NoSuchBucket':
        print("Bucket does not exist")
    elif error_code == 'NoSuchKey':
        print("Object does not exist")
    else:
        print(f"Error: {error_code}")
```

## Testing

Run the comprehensive test suite:

```bash
python test_boto3_emulator.py
```

Tests cover:
- Session creation and configuration
- S3 bucket and object operations
- EC2 instance lifecycle
- DynamoDB table and item operations
- Resource interface usage
- Error handling
- Integration scenarios

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for boto3 in development and testing:

```python
# Instead of:
# import boto3

# Use:
import boto3_emulator as boto3

# The rest of your code remains unchanged
s3 = boto3.client('s3')
s3.create_bucket(Bucket='my-bucket')
```

## Use Cases

Perfect for:
- **Local Development**: Develop AWS applications without AWS account
- **Testing**: Test AWS integrations without incurring costs
- **CI/CD**: Run tests in CI pipelines without AWS credentials
- **Learning**: Learn AWS SDK patterns and best practices
- **Prototyping**: Quickly prototype AWS-based applications
- **Offline Development**: Work on AWS applications without internet

## Limitations

This is an emulator for development and testing purposes:
- In-memory storage only (data is lost when process ends)
- Simplified implementations of AWS services
- Not all boto3 features are implemented
- Does not connect to actual AWS services
- Limited to S3, EC2, and DynamoDB services

## Supported Services

### S3 Operations
- ✅ create_bucket
- ✅ list_buckets
- ✅ delete_bucket
- ✅ put_object
- ✅ get_object
- ✅ delete_object
- ✅ list_objects_v2
- ✅ Resource interface (Bucket, Object)

### EC2 Operations
- ✅ run_instances
- ✅ describe_instances
- ✅ terminate_instances
- ✅ stop_instances

### DynamoDB Operations
- ✅ create_table
- ✅ delete_table
- ✅ describe_table
- ✅ list_tables
- ✅ put_item
- ✅ get_item
- ✅ scan
- ✅ query (simplified)
- ✅ Resource interface (Table)

## Compatibility

Emulates core features of:
- boto3 1.x API
- AWS SDK patterns and conventions
- Common AWS service operations

## License

Part of the Emu-Soft project. See main repository LICENSE.
