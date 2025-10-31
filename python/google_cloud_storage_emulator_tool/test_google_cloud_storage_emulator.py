"""
Tests for Google Cloud Storage emulator

Comprehensive test suite for Google Cloud Storage emulator functionality.
"""

import unittest
import sys
import os
import io

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from google_cloud_storage_emulator import (
    Client, Bucket, Blob, Batch,
    CloudStorageError, NotFound, Conflict, Forbidden,
    STANDARD, NEARLINE, COLDLINE, ARCHIVE,
    PRIVATE, PUBLIC_READ,
    _gcs_buckets, _gcs_blobs, _gcs_blob_metadata
)


class TestClient(unittest.TestCase):
    """Test Google Cloud Storage client functionality."""
    
    def setUp(self):
        """Clean storage before each test."""
        _gcs_buckets.clear()
        _gcs_blobs.clear()
        _gcs_blob_metadata.clear()
    
    def test_client_creation(self):
        """Test creating a client."""
        client = Client(project='test-project')
        self.assertEqual(client.project, 'test-project')
    
    def test_client_default_project(self):
        """Test client with default project."""
        client = Client()
        self.assertEqual(client.project, 'emulated-project')
    
    def test_get_bucket(self):
        """Test getting a bucket reference."""
        client = Client()
        bucket = client.bucket('test-bucket')
        self.assertIsInstance(bucket, Bucket)
        self.assertEqual(bucket.name, 'test-bucket')


class TestBucket(unittest.TestCase):
    """Test bucket operations."""
    
    def setUp(self):
        """Clean storage before each test."""
        _gcs_buckets.clear()
        _gcs_blobs.clear()
        _gcs_blob_metadata.clear()
        self.client = Client(project='test-project')
    
    def test_create_bucket(self):
        """Test creating a bucket."""
        bucket = self.client.bucket('test-bucket')
        bucket.create()
        
        self.assertTrue(bucket.exists())
        self.assertIn('test-bucket', _gcs_buckets)
    
    def test_create_bucket_via_client(self):
        """Test creating bucket via client.create_bucket."""
        bucket = self.client.create_bucket('test-bucket')
        
        self.assertTrue(bucket.exists())
        self.assertEqual(bucket.name, 'test-bucket')
    
    def test_create_bucket_duplicate(self):
        """Test error when creating duplicate bucket."""
        bucket = self.client.bucket('test-bucket')
        bucket.create()
        
        with self.assertRaises(Conflict):
            bucket.create()
    
    def test_delete_bucket(self):
        """Test deleting a bucket."""
        bucket = self.client.bucket('test-bucket')
        bucket.create()
        bucket.delete()
        
        self.assertFalse(bucket.exists())
        self.assertNotIn('test-bucket', _gcs_buckets)
    
    def test_delete_nonempty_bucket(self):
        """Test deleting a non-empty bucket fails."""
        bucket = self.client.bucket('test-bucket')
        bucket.create()
        
        blob = bucket.blob('test-file.txt')
        blob.upload_from_string('test content')
        
        with self.assertRaises(Conflict):
            bucket.delete()
    
    def test_delete_nonempty_bucket_force(self):
        """Test force deleting a non-empty bucket."""
        bucket = self.client.bucket('test-bucket')
        bucket.create()
        
        blob = bucket.blob('test-file.txt')
        blob.upload_from_string('test content')
        
        bucket.delete(force=True)
        self.assertFalse(bucket.exists())
    
    def test_bucket_location(self):
        """Test bucket location."""
        bucket = self.client.bucket('test-bucket')
        bucket.create(location='EU')
        
        self.assertEqual(bucket.location, 'EU')
    
    def test_bucket_storage_class(self):
        """Test bucket storage class."""
        bucket = self.client.bucket('test-bucket')
        bucket.create(storage_class=NEARLINE)
        
        self.assertEqual(bucket.storage_class, NEARLINE)
    
    def test_list_buckets(self):
        """Test listing buckets."""
        self.client.create_bucket('bucket1')
        self.client.create_bucket('bucket2')
        self.client.create_bucket('bucket3')
        
        buckets = list(self.client.list_buckets())
        self.assertEqual(len(buckets), 3)
        bucket_names = [b.name for b in buckets]
        self.assertIn('bucket1', bucket_names)
        self.assertIn('bucket2', bucket_names)
        self.assertIn('bucket3', bucket_names)
    
    def test_list_buckets_with_prefix(self):
        """Test listing buckets with prefix filter."""
        self.client.create_bucket('test-bucket1')
        self.client.create_bucket('test-bucket2')
        self.client.create_bucket('prod-bucket1')
        
        buckets = list(self.client.list_buckets(prefix='test-'))
        self.assertEqual(len(buckets), 2)
    
    def test_list_buckets_max_results(self):
        """Test listing buckets with max results."""
        self.client.create_bucket('bucket1')
        self.client.create_bucket('bucket2')
        self.client.create_bucket('bucket3')
        
        buckets = list(self.client.list_buckets(max_results=2))
        self.assertEqual(len(buckets), 2)
    
    def test_get_bucket_not_found(self):
        """Test getting non-existent bucket raises NotFound."""
        with self.assertRaises(NotFound):
            self.client.get_bucket('nonexistent-bucket')


class TestBlob(unittest.TestCase):
    """Test blob operations."""
    
    def setUp(self):
        """Clean storage before each test."""
        _gcs_buckets.clear()
        _gcs_blobs.clear()
        _gcs_blob_metadata.clear()
        self.client = Client(project='test-project')
        self.bucket = self.client.create_bucket('test-bucket')
    
    def test_upload_from_string(self):
        """Test uploading blob from string."""
        blob = self.bucket.blob('test-file.txt')
        blob.upload_from_string('Hello, World!')
        
        self.assertTrue(blob.exists())
        self.assertIn('test-file.txt', _gcs_blobs['test-bucket'])
    
    def test_upload_from_bytes(self):
        """Test uploading blob from bytes."""
        blob = self.bucket.blob('test-file.bin')
        blob.upload_from_string(b'Binary content')
        
        self.assertTrue(blob.exists())
    
    def test_download_as_bytes(self):
        """Test downloading blob as bytes."""
        blob = self.bucket.blob('test-file.txt')
        blob.upload_from_string('Hello, World!')
        
        content = blob.download_as_bytes()
        self.assertEqual(content, b'Hello, World!')
    
    def test_download_as_string(self):
        """Test downloading blob as string."""
        blob = self.bucket.blob('test-file.txt')
        blob.upload_from_string('Hello, World!')
        
        content = blob.download_as_string()
        self.assertEqual(content, 'Hello, World!')
    
    def test_download_nonexistent_blob(self):
        """Test downloading non-existent blob raises NotFound."""
        blob = self.bucket.blob('nonexistent.txt')
        
        with self.assertRaises(NotFound):
            blob.download_as_bytes()
    
    def test_delete_blob(self):
        """Test deleting a blob."""
        blob = self.bucket.blob('test-file.txt')
        blob.upload_from_string('content')
        
        self.assertTrue(blob.exists())
        blob.delete()
        self.assertFalse(blob.exists())
    
    def test_delete_nonexistent_blob(self):
        """Test deleting non-existent blob raises NotFound."""
        blob = self.bucket.blob('nonexistent.txt')
        
        with self.assertRaises(NotFound):
            blob.delete()
    
    def test_blob_size(self):
        """Test getting blob size."""
        blob = self.bucket.blob('test-file.txt')
        blob.upload_from_string('Hello')
        
        self.assertEqual(blob.size, 5)
    
    def test_blob_content_type(self):
        """Test blob content type."""
        blob = self.bucket.blob('test-file.txt')
        blob.upload_from_string('content', content_type='text/plain')
        
        self.assertEqual(blob.content_type, 'text/plain')
    
    def test_blob_md5_hash(self):
        """Test blob MD5 hash."""
        blob = self.bucket.blob('test-file.txt')
        blob.upload_from_string('content')
        
        self.assertIsNotNone(blob.md5_hash)
    
    def test_blob_public_url(self):
        """Test blob public URL."""
        blob = self.bucket.blob('test-file.txt')
        expected_url = 'https://storage.googleapis.com/test-bucket/test-file.txt'
        
        self.assertEqual(blob.public_url, expected_url)
    
    def test_list_blobs(self):
        """Test listing blobs."""
        self.bucket.blob('file1.txt').upload_from_string('content1')
        self.bucket.blob('file2.txt').upload_from_string('content2')
        self.bucket.blob('file3.txt').upload_from_string('content3')
        
        blobs = list(self.bucket.list_blobs())
        self.assertEqual(len(blobs), 3)
        blob_names = [b.name for b in blobs]
        self.assertIn('file1.txt', blob_names)
    
    def test_list_blobs_with_prefix(self):
        """Test listing blobs with prefix."""
        self.bucket.blob('docs/file1.txt').upload_from_string('content1')
        self.bucket.blob('docs/file2.txt').upload_from_string('content2')
        self.bucket.blob('images/pic1.jpg').upload_from_string('image1')
        
        blobs = list(self.bucket.list_blobs(prefix='docs/'))
        self.assertEqual(len(blobs), 2)
    
    def test_list_blobs_max_results(self):
        """Test listing blobs with max results."""
        self.bucket.blob('file1.txt').upload_from_string('content1')
        self.bucket.blob('file2.txt').upload_from_string('content2')
        self.bucket.blob('file3.txt').upload_from_string('content3')
        
        blobs = list(self.bucket.list_blobs(max_results=2))
        self.assertEqual(len(blobs), 2)
    
    def test_get_blob(self):
        """Test getting a blob."""
        self.bucket.blob('test-file.txt').upload_from_string('content')
        
        blob = self.bucket.get_blob('test-file.txt')
        self.assertIsNotNone(blob)
        self.assertEqual(blob.name, 'test-file.txt')
    
    def test_get_nonexistent_blob(self):
        """Test getting non-existent blob returns None."""
        blob = self.bucket.get_blob('nonexistent.txt')
        self.assertIsNone(blob)
    
    def test_make_public(self):
        """Test making blob public."""
        blob = self.bucket.blob('test-file.txt')
        blob.upload_from_string('content')
        blob.make_public()
        
        metadata = _gcs_blob_metadata['test-bucket']['test-file.txt']
        self.assertTrue(metadata.get('public', False))
    
    def test_make_private(self):
        """Test making blob private."""
        blob = self.bucket.blob('test-file.txt')
        blob.upload_from_string('content')
        blob.make_public()
        blob.make_private()
        
        metadata = _gcs_blob_metadata['test-bucket']['test-file.txt']
        self.assertFalse(metadata.get('public', False))


class TestBlobFileOperations(unittest.TestCase):
    """Test blob file upload/download operations."""
    
    def setUp(self):
        """Clean storage before each test."""
        _gcs_buckets.clear()
        _gcs_blobs.clear()
        _gcs_blob_metadata.clear()
        self.client = Client(project='test-project')
        self.bucket = self.client.create_bucket('test-bucket')
    
    def test_upload_from_file(self):
        """Test uploading from file object."""
        blob = self.bucket.blob('test-file.txt')
        file_obj = io.BytesIO(b'File content')
        
        blob.upload_from_file(file_obj)
        
        self.assertTrue(blob.exists())
        self.assertEqual(blob.download_as_bytes(), b'File content')
    
    def test_download_to_file(self):
        """Test downloading to file object."""
        blob = self.bucket.blob('test-file.txt')
        blob.upload_from_string('File content')
        
        file_obj = io.BytesIO()
        blob.download_to_file(file_obj)
        
        file_obj.seek(0)
        self.assertEqual(file_obj.read(), b'File content')
    
    def test_upload_from_filename(self):
        """Test uploading from filename."""
        # Create a temporary file
        temp_file = '/tmp/test_upload.txt'
        with open(temp_file, 'w') as f:
            f.write('File from disk')
        
        blob = self.bucket.blob('test-file.txt')
        blob.upload_from_filename(temp_file)
        
        self.assertTrue(blob.exists())
        self.assertEqual(blob.download_as_string(), 'File from disk')
        
        # Clean up
        os.remove(temp_file)
    
    def test_download_to_filename(self):
        """Test downloading to filename."""
        blob = self.bucket.blob('test-file.txt')
        blob.upload_from_string('Download this')
        
        temp_file = '/tmp/test_download.txt'
        blob.download_to_filename(temp_file)
        
        with open(temp_file, 'r') as f:
            content = f.read()
        
        self.assertEqual(content, 'Download this')
        
        # Clean up
        os.remove(temp_file)


class TestBlobMetadata(unittest.TestCase):
    """Test blob metadata operations."""
    
    def setUp(self):
        """Clean storage before each test."""
        _gcs_buckets.clear()
        _gcs_blobs.clear()
        _gcs_blob_metadata.clear()
        self.client = Client(project='test-project')
        self.bucket = self.client.create_bucket('test-bucket')
    
    def test_custom_metadata(self):
        """Test setting and getting custom metadata."""
        blob = self.bucket.blob('test-file.txt')
        blob.upload_from_string('content', metadata={'key1': 'value1', 'key2': 'value2'})
        
        self.assertEqual(blob.metadata['key1'], 'value1')
        self.assertEqual(blob.metadata['key2'], 'value2')
    
    def test_update_metadata(self):
        """Test updating blob metadata."""
        blob = self.bucket.blob('test-file.txt')
        blob.upload_from_string('content')
        
        blob.metadata = {'new_key': 'new_value'}
        
        self.assertEqual(blob.metadata['new_key'], 'new_value')


class TestBucketCopyOperations(unittest.TestCase):
    """Test bucket copy operations."""
    
    def setUp(self):
        """Clean storage before each test."""
        _gcs_buckets.clear()
        _gcs_blobs.clear()
        _gcs_blob_metadata.clear()
        self.client = Client(project='test-project')
        self.source_bucket = self.client.create_bucket('source-bucket')
        self.dest_bucket = self.client.create_bucket('dest-bucket')
    
    def test_copy_blob(self):
        """Test copying a blob between buckets."""
        source_blob = self.source_bucket.blob('original.txt')
        source_blob.upload_from_string('Original content')
        
        new_blob = self.source_bucket.copy_blob(
            source_blob,
            self.dest_bucket,
            'copied.txt'
        )
        
        self.assertTrue(new_blob.exists())
        self.assertEqual(new_blob.download_as_string(), 'Original content')
        self.assertEqual(new_blob.name, 'copied.txt')
    
    def test_copy_blob_same_name(self):
        """Test copying blob with same name."""
        source_blob = self.source_bucket.blob('file.txt')
        source_blob.upload_from_string('Content')
        
        new_blob = self.source_bucket.copy_blob(
            source_blob,
            self.dest_bucket
        )
        
        self.assertEqual(new_blob.name, 'file.txt')


class TestSignedURL(unittest.TestCase):
    """Test signed URL generation."""
    
    def setUp(self):
        """Clean storage before each test."""
        _gcs_buckets.clear()
        _gcs_blobs.clear()
        _gcs_blob_metadata.clear()
        self.client = Client(project='test-project')
        self.bucket = self.client.create_bucket('test-bucket')
    
    def test_generate_signed_url(self):
        """Test generating signed URL."""
        blob = self.bucket.blob('test-file.txt')
        blob.upload_from_string('content')
        
        url = blob.generate_signed_url(expiration=3600)
        
        self.assertIn('storage.googleapis.com', url)
        self.assertIn('test-bucket', url)
        self.assertIn('test-file.txt', url)
        self.assertIn('token=', url)


class TestIntegrationScenarios(unittest.TestCase):
    """Test complete usage scenarios."""
    
    def setUp(self):
        """Clean storage before each test."""
        _gcs_buckets.clear()
        _gcs_blobs.clear()
        _gcs_blob_metadata.clear()
        self.client = Client(project='my-project')
    
    def test_complete_workflow(self):
        """Test complete upload/download workflow."""
        # Create bucket
        bucket = self.client.create_bucket('my-data-bucket', location='US')
        self.assertTrue(bucket.exists())
        
        # Upload files
        blob1 = bucket.blob('data/file1.txt')
        blob1.upload_from_string('File 1 content')
        
        blob2 = bucket.blob('data/file2.txt')
        blob2.upload_from_string('File 2 content')
        
        # List files
        blobs = list(bucket.list_blobs(prefix='data/'))
        self.assertEqual(len(blobs), 2)
        
        # Download file
        content = blob1.download_as_string()
        self.assertEqual(content, 'File 1 content')
        
        # Delete file
        blob1.delete()
        self.assertFalse(blob1.exists())
        
        # Verify remaining files
        blobs = list(bucket.list_blobs(prefix='data/'))
        self.assertEqual(len(blobs), 1)
    
    def test_static_website_hosting(self):
        """Test static website hosting scenario."""
        # Create bucket for website
        bucket = self.client.create_bucket('my-website-bucket')
        
        # Upload HTML files
        index_blob = bucket.blob('index.html')
        index_blob.upload_from_string('<html><body>Home</body></html>', content_type='text/html')
        
        about_blob = bucket.blob('about.html')
        about_blob.upload_from_string('<html><body>About</body></html>', content_type='text/html')
        
        # Make files public
        index_blob.make_public()
        about_blob.make_public()
        
        # Verify public URLs
        self.assertIn('my-website-bucket', index_blob.public_url)
        self.assertIn('index.html', index_blob.public_url)
    
    def test_data_backup_scenario(self):
        """Test data backup scenario."""
        # Create source and backup buckets
        source = self.client.create_bucket('source-data')
        backup = self.client.create_bucket('backup-data')
        
        # Create some files
        for i in range(5):
            blob = source.blob(f'file{i}.txt')
            blob.upload_from_string(f'Content {i}')
        
        # Backup files
        for blob in source.list_blobs():
            source.copy_blob(blob, backup, blob.name)
        
        # Verify backup
        backup_files = list(backup.list_blobs())
        self.assertEqual(len(backup_files), 5)


if __name__ == '__main__':
    unittest.main()
