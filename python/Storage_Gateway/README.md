# Google Cloud Storage Emulator - Object Storage for Google Cloud

This module emulates the **google-cloud-storage** library, which is the official Google Cloud client library for Cloud Storage, an object storage service for storing and accessing data on Google Cloud Platform.

## What is Google Cloud Storage?

Google Cloud Storage (GCS) is a RESTful online file storage web service for storing and accessing data on Google Cloud Platform infrastructure. It combines the performance and scalability of Google's cloud with advanced security and sharing capabilities.

Key features:
- **Object Storage**: Store and retrieve any amount of data
- **Global Availability**: Access data from anywhere
- **Strong Consistency**: Immediate read-after-write consistency
- **Versioning**: Maintain multiple versions of objects
- **Access Control**: Fine-grained access control with ACLs and IAM
- **Storage Classes**: Multiple tiers for cost optimization

The google-cloud-storage library provides the idiomatic Python interface to Cloud Storage.

## Features

This emulator implements core GCS functionality:

### Bucket Operations
- Create, delete, and list buckets
- Bucket metadata (location, storage class)
- Bucket versioning support
- Check bucket existence

### Blob (Object) Operations
- Upload from string, bytes, file, or filename
- Download as bytes, string, to file, or to filename
- Delete blobs
- List blobs with prefix filtering
- Check blob existence
- Copy blobs between buckets

### Metadata & Properties
- Content type and encoding
- MD5 hash and CRC32C checksums
- Custom metadata
- Blob size and timestamps
- Public/private access control

### Advanced Features
- Signed URLs for temporary access
- Batch operations
- Storage classes (STANDARD, NEARLINE, COLDLINE, ARCHIVE)
- Public URL generation

## Usage Examples

### Client Creation

```python
from google_cloud_storage_emulator import Client

# Create client with project
client = Client(project='my-project-id')

# Create client with default project
client = Client()
```

### Bucket Operations

#### Creating Buckets

```python
from google_cloud_storage_emulator import Client

client = Client(project='my-project')

# Create a bucket (method 1)
bucket = client.bucket('my-bucket')
bucket.create()

# Create a bucket (method 2)
bucket = client.create_bucket('my-bucket')

# Create bucket with options
bucket = client.create_bucket(
    'my-bucket',
    location='EU',
    storage_class='NEARLINE'
)
```

#### Listing Buckets

```python
from google_cloud_storage_emulator import Client

client = Client(project='my-project')

# Create some buckets
client.create_bucket('bucket1')
client.create_bucket('bucket2')
client.create_bucket('bucket3')

# List all buckets
for bucket in client.list_buckets():
    print(f"Bucket: {bucket.name}")

# List with prefix
for bucket in client.list_buckets(prefix='test-'):
    print(f"Test bucket: {bucket.name}")

# Limit results
for bucket in client.list_buckets(max_results=10):
    print(f"Bucket: {bucket.name}")
```

#### Bucket Properties

```python
from google_cloud_storage_emulator import Client, COLDLINE

client = Client(project='my-project')
bucket = client.create_bucket('my-bucket', location='US', storage_class=COLDLINE)

# Get bucket properties
print(f"Location: {bucket.location}")
print(f"Storage class: {bucket.storage_class}")
print(f"Versioning: {bucket.versioning_enabled}")

# Check if bucket exists
if bucket.exists():
    print("Bucket exists!")
```

#### Deleting Buckets

```python
from google_cloud_storage_emulator import Client

client = Client()
bucket = client.bucket('my-bucket')

# Delete empty bucket
bucket.delete()

# Force delete (deletes all blobs first)
bucket.delete(force=True)
```

### Blob (Object) Operations

#### Uploading Data

```python
from google_cloud_storage_emulator import Client

client = Client()
bucket = client.bucket('my-bucket')
bucket.create()

# Upload from string
blob = bucket.blob('data/file.txt')
blob.upload_from_string('Hello, World!')

# Upload from bytes
blob = bucket.blob('data/binary.dat')
blob.upload_from_string(b'\x00\x01\x02\x03')

# Upload from file object
import io
file_obj = io.BytesIO(b'File content')
blob = bucket.blob('data/from_file.txt')
blob.upload_from_file(file_obj)

# Upload from filename
blob = bucket.blob('data/document.pdf')
blob.upload_from_filename('/path/to/local/document.pdf')

# Upload with content type
blob = bucket.blob('index.html')
blob.upload_from_string('<html>...</html>', content_type='text/html')

# Upload with custom metadata
blob = bucket.blob('photo.jpg')
blob.upload_from_filename('photo.jpg', metadata={
    'camera': 'iPhone 12',
    'location': 'Paris'
})
```

#### Downloading Data

```python
from google_cloud_storage_emulator import Client

client = Client()
bucket = client.bucket('my-bucket')

# Download as bytes
blob = bucket.blob('data/file.txt')
content = blob.download_as_bytes()
print(content)  # b'Hello, World!'

# Download as string
content = blob.download_as_string()
print(content)  # 'Hello, World!'

# Download to file object
import io
file_obj = io.BytesIO()
blob.download_to_file(file_obj)
file_obj.seek(0)
content = file_obj.read()

# Download to filename
blob.download_to_filename('/path/to/local/downloaded_file.txt')
```

#### Listing Blobs

```python
from google_cloud_storage_emulator import Client

client = Client()
bucket = client.bucket('my-bucket')

# Upload some files
bucket.blob('docs/file1.txt').upload_from_string('content1')
bucket.blob('docs/file2.txt').upload_from_string('content2')
bucket.blob('images/photo1.jpg').upload_from_string('photo1')
bucket.blob('images/photo2.jpg').upload_from_string('photo2')

# List all blobs
for blob in bucket.list_blobs():
    print(f"Blob: {blob.name}")

# List with prefix (like a folder)
for blob in bucket.list_blobs(prefix='docs/'):
    print(f"Document: {blob.name}")

# Limit results
for blob in bucket.list_blobs(max_results=10):
    print(f"Blob: {blob.name}")

# Get specific blob
blob = bucket.get_blob('docs/file1.txt')
if blob:
    print(f"Found blob: {blob.name}")
else:
    print("Blob not found")
```

#### Blob Operations

```python
from google_cloud_storage_emulator import Client

client = Client()
bucket = client.bucket('my-bucket')
bucket.create()

# Create blob
blob = bucket.blob('myfile.txt')
blob.upload_from_string('content')

# Check if blob exists
if blob.exists():
    print("Blob exists")

# Get blob properties
print(f"Size: {blob.size} bytes")
print(f"Content type: {blob.content_type}")
print(f"MD5 hash: {blob.md5_hash}")
print(f"Public URL: {blob.public_url}")

# Access custom metadata
print(f"Metadata: {blob.metadata}")

# Delete blob
blob.delete()
```

#### Copying Blobs

```python
from google_cloud_storage_emulator import Client

client = Client()
source_bucket = client.create_bucket('source-bucket')
dest_bucket = client.create_bucket('dest-bucket')

# Upload original file
source_blob = source_bucket.blob('original.txt')
source_blob.upload_from_string('Original content')

# Copy to destination bucket with new name
new_blob = source_bucket.copy_blob(
    source_blob,
    dest_bucket,
    'copied.txt'
)

print(f"Copied to: {new_blob.name}")
print(f"Content: {new_blob.download_as_string()}")

# Copy with same name
new_blob = source_bucket.copy_blob(source_blob, dest_bucket)
```

### Access Control

```python
from google_cloud_storage_emulator import Client

client = Client()
bucket = client.bucket('my-bucket')
bucket.create()

# Upload blob
blob = bucket.blob('document.pdf')
blob.upload_from_filename('document.pdf')

# Make blob publicly accessible
blob.make_public()

# Make blob private again
blob.make_private()

# Get public URL
print(f"Public URL: {blob.public_url}")
# https://storage.googleapis.com/my-bucket/document.pdf
```

### Signed URLs

```python
from google_cloud_storage_emulator import Client
from datetime import timedelta

client = Client()
bucket = client.bucket('my-bucket')
bucket.create()

blob = bucket.blob('private-file.pdf')
blob.upload_from_string('Confidential content')

# Generate signed URL valid for 1 hour
url = blob.generate_signed_url(expiration=3600)

# Using timedelta
url = blob.generate_signed_url(expiration=timedelta(hours=1))

# For download (GET)
url = blob.generate_signed_url(expiration=3600, method='GET')

# For upload (PUT)
url = blob.generate_signed_url(expiration=3600, method='PUT')

print(f"Signed URL: {url}")
```

### Storage Classes

```python
from google_cloud_storage_emulator import (
    Client,
    STANDARD, NEARLINE, COLDLINE, ARCHIVE
)

client = Client()

# Create bucket with different storage classes

# Standard: Frequently accessed data
standard_bucket = client.create_bucket(
    'hot-data',
    storage_class=STANDARD
)

# Nearline: Data accessed once per month
nearline_bucket = client.create_bucket(
    'monthly-reports',
    storage_class=NEARLINE
)

# Coldline: Data accessed once per quarter
coldline_bucket = client.create_bucket(
    'quarterly-archives',
    storage_class=COLDLINE
)

# Archive: Long-term archival storage
archive_bucket = client.create_bucket(
    'annual-backups',
    storage_class=ARCHIVE
)

print(f"Standard bucket: {standard_bucket.storage_class}")
print(f"Nearline bucket: {nearline_bucket.storage_class}")
print(f"Coldline bucket: {coldline_bucket.storage_class}")
print(f"Archive bucket: {archive_bucket.storage_class}")
```

## Complete Application Examples

### Static Website Hosting

```python
from google_cloud_storage_emulator import Client

client = Client(project='my-website-project')

# Create bucket for website
bucket = client.create_bucket('www.example.com')

# Upload HTML pages
index = bucket.blob('index.html')
index.upload_from_string('''
<!DOCTYPE html>
<html>
<head><title>Home</title></head>
<body><h1>Welcome!</h1></body>
</html>
''', content_type='text/html')
index.make_public()

# Upload CSS
styles = bucket.blob('styles.css')
styles.upload_from_string('body { font-family: Arial; }', content_type='text/css')
styles.make_public()

# Upload images
logo = bucket.blob('images/logo.png')
logo.upload_from_filename('logo.png', content_type='image/png')
logo.make_public()

print("Website deployed!")
print(f"Homepage: {index.public_url}")
```

### File Backup System

```python
from google_cloud_storage_emulator import Client
import os

client = Client(project='backup-project')

def backup_directory(local_path, bucket_name, prefix=''):
    """Backup a local directory to GCS."""
    bucket = client.bucket(bucket_name)
    if not bucket.exists():
        bucket.create()
    
    for root, dirs, files in os.walk(local_path):
        for filename in files:
            local_file = os.path.join(root, filename)
            relative_path = os.path.relpath(local_file, local_path)
            blob_name = os.path.join(prefix, relative_path).replace('\\', '/')
            
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(local_file)
            print(f"Uploaded: {blob_name}")

# Backup documents
backup_directory('/home/user/documents', 'my-backups', prefix='documents/')

# List backed up files
bucket = client.bucket('my-backups')
print("\nBacked up files:")
for blob in bucket.list_blobs(prefix='documents/'):
    print(f"  {blob.name} ({blob.size} bytes)")
```

### Data Processing Pipeline

```python
from google_cloud_storage_emulator import Client
import json

client = Client(project='data-project')

# Input and output buckets
input_bucket = client.create_bucket('input-data')
output_bucket = client.create_bucket('processed-data')

# Upload raw data
raw_data = {
    'records': [
        {'id': 1, 'value': 100},
        {'id': 2, 'value': 200},
        {'id': 3, 'value': 300}
    ]
}

input_blob = input_bucket.blob('raw/data.json')
input_blob.upload_from_string(json.dumps(raw_data), content_type='application/json')

# Process data
def process_data(input_blob, output_blob):
    # Download and parse
    data = json.loads(input_blob.download_as_string())
    
    # Process
    total = sum(record['value'] for record in data['records'])
    result = {
        'total': total,
        'count': len(data['records']),
        'average': total / len(data['records'])
    }
    
    # Upload result
    output_blob.upload_from_string(
        json.dumps(result, indent=2),
        content_type='application/json'
    )

# Process
output_blob = output_bucket.blob('processed/results.json')
process_data(input_blob, output_blob)

# Verify result
result = json.loads(output_blob.download_as_string())
print(f"Processed results: {result}")
```

### Log Archival

```python
from google_cloud_storage_emulator import Client
from datetime import datetime

client = Client(project='logging-project')
bucket = client.create_bucket('application-logs')

def archive_log(log_content, app_name):
    """Archive application logs to GCS."""
    timestamp = datetime.utcnow().strftime('%Y/%m/%d/%H%M%S')
    blob_name = f'{app_name}/logs/{timestamp}.log'
    
    blob = bucket.blob(blob_name)
    blob.upload_from_string(
        log_content,
        content_type='text/plain',
        metadata={
            'app': app_name,
            'timestamp': timestamp,
            'log_level': 'INFO'
        }
    )
    
    return blob.public_url

# Archive logs
log_url = archive_log('Application started\nProcessing requests...\n', 'web-server')
print(f"Log archived: {log_url}")

# List logs for an application
print("\nWeb server logs:")
for blob in bucket.list_blobs(prefix='web-server/logs/'):
    print(f"  {blob.name} - {blob.size} bytes")
    print(f"    Metadata: {blob.metadata}")
```

### Multi-Region Backup

```python
from google_cloud_storage_emulator import Client

client = Client(project='dr-project')

# Create buckets in different regions
us_bucket = client.create_bucket('data-us', location='US')
eu_bucket = client.create_bucket('data-eu', location='EU')
asia_bucket = client.create_bucket('data-asia', location='ASIA')

# Upload data to primary region (US)
data_blob = us_bucket.blob('critical-data.json')
data_blob.upload_from_string('{"status": "critical", "value": 12345}')

# Replicate to other regions
us_bucket.copy_blob(data_blob, eu_bucket, data_blob.name)
us_bucket.copy_blob(data_blob, asia_bucket, data_blob.name)

# Verify replication
for region, bucket in [('US', us_bucket), ('EU', eu_bucket), ('ASIA', asia_bucket)]:
    blob = bucket.get_blob('critical-data.json')
    if blob:
        print(f"{region}: Data replicated ✓")
    else:
        print(f"{region}: Replication failed ✗")
```

## Testing

Run the comprehensive test suite:

```bash
python test_google_cloud_storage_emulator.py
```

Tests cover:
- Client creation and configuration
- Bucket operations (create, delete, list, get)
- Blob operations (upload, download, delete, copy)
- File operations (upload/download from files)
- Metadata management
- Access control (public/private)
- Signed URL generation
- Integration scenarios

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for google-cloud-storage:

```python
# Instead of:
# from google.cloud import storage

# Use:
from google_cloud_storage_emulator import Client

# The rest of your code remains largely unchanged
client = Client(project='my-project')
bucket = client.bucket('my-bucket')
blob = bucket.blob('file.txt')
blob.upload_from_string('Hello!')
```

## Use Cases

Perfect for:
- **Local Development**: Develop GCS applications without Google Cloud account
- **Testing**: Test GCS integrations without incurring costs
- **CI/CD**: Run tests in CI pipelines without GCS credentials
- **Learning**: Learn Google Cloud Storage patterns and APIs
- **Prototyping**: Quickly prototype GCS-based applications
- **Offline Development**: Work on GCS applications without internet

## Common Patterns

### Organizing Data in Folders

```python
# GCS doesn't have folders, but uses blob names with slashes
blob = bucket.blob('users/john/profile.jpg')
blob.upload_from_filename('profile.jpg')

# List files in "folder"
for blob in bucket.list_blobs(prefix='users/john/'):
    print(blob.name)
```

### Temporary File Storage

```python
from datetime import timedelta

# Upload with metadata indicating expiration
blob = bucket.blob('temp/upload.dat')
blob.upload_from_string(data, metadata={
    'expires': (datetime.utcnow() + timedelta(days=1)).isoformat()
})
```

### Versioned Files

```python
# Enable versioning
bucket = client.create_bucket('versioned-bucket', versioning_enabled=True)

# Upload multiple versions
blob = bucket.blob('document.txt')
blob.upload_from_string('Version 1')
blob.upload_from_string('Version 2')
blob.upload_from_string('Version 3')
```

## Limitations

This is an emulator for development and testing purposes:
- In-memory storage only (data is lost when process ends)
- No actual Google Cloud integration
- Simplified signed URLs (not cryptographically secure)
- No IAM integration
- No lifecycle policies
- No object composition
- No server-side encryption (CSEK/CMEK)
- No Pub/Sub notifications
- Limited ACL support

## Supported Operations

### Bucket Operations
- ✅ create, delete, exists
- ✅ list_buckets with filtering
- ✅ get_bucket
- ✅ Bucket properties (location, storage_class)
- ✅ copy_blob

### Blob Operations
- ✅ upload_from_string, upload_from_bytes
- ✅ upload_from_file, upload_from_filename
- ✅ download_as_bytes, download_as_string
- ✅ download_to_file, download_to_filename
- ✅ delete, exists
- ✅ list_blobs with prefix filtering
- ✅ get_blob

### Metadata & Properties
- ✅ content_type, size
- ✅ md5_hash, crc32c
- ✅ custom metadata
- ✅ public_url
- ✅ make_public, make_private

### Advanced Features
- ✅ generate_signed_url
- ✅ Storage classes (STANDARD, NEARLINE, COLDLINE, ARCHIVE)
- ✅ Batch operations (basic)

## Compatibility

Emulates core features of:
- google-cloud-storage 2.x API
- Google Cloud Storage REST API v1
- Common GCS usage patterns

## License

Part of the Emu-Soft project. See main repository LICENSE.
