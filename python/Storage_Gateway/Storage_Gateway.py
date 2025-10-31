"""
Google Cloud Storage Emulator - Object Storage for Google Cloud

This module emulates the google-cloud-storage library, which is the official
Google Cloud client library for Cloud Storage, an object storage service for
storing and accessing data on Google Cloud Platform.

Key Features:
- Bucket management (create, delete, list, get)
- Blob (object) operations (upload, download, delete, copy)
- Blob metadata and properties
- Access control lists (ACLs)
- Batch operations
- Signed URLs for temporary access
- Blob versioning
- Storage classes


Developed by PowerShield
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union, Iterator, BinaryIO
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
import uuid
import os
import io


class CloudStorageError(Exception):
    """Base exception for Google Cloud Storage errors."""
    pass


class NotFound(CloudStorageError):
    """Raised when a resource is not found."""
    pass


class Conflict(CloudStorageError):
    """Raised when a resource already exists."""
    pass


class Forbidden(CloudStorageError):
    """Raised when access is forbidden."""
    pass


# In-memory storage for emulated Google Cloud Storage
_gcs_buckets: Dict[str, Dict[str, Any]] = {}
_gcs_blobs: Dict[str, Dict[str, bytes]] = defaultdict(dict)  # bucket_name -> {blob_name: data}
_gcs_blob_metadata: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)  # bucket_name -> {blob_name: metadata}


class Client:
    """Google Cloud Storage client."""
    
    def __init__(
        self,
        project: Optional[str] = None,
        credentials: Optional[Any] = None,
        _http: Optional[Any] = None,
        client_info: Optional[Any] = None,
        client_options: Optional[Any] = None
    ):
        """
        Initialize Google Cloud Storage client.
        
        Args:
            project: Project ID or project number
            credentials: OAuth2 credentials
            _http: HTTP client for making requests
            client_info: Client information for user agent
            client_options: Client options
        """
        self.project = project or 'emulated-project'
        self.credentials = credentials
        self._http = _http
        self.client_info = client_info
        self.client_options = client_options
    
    def bucket(self, bucket_name: str) -> Bucket:
        """
        Get a bucket by name.
        
        Args:
            bucket_name: Name of the bucket
        
        Returns:
            Bucket instance
        """
        return Bucket(self, bucket_name)
    
    def create_bucket(
        self,
        bucket_or_name: Union[Bucket, str],
        project: Optional[str] = None,
        **kwargs
    ) -> Bucket:
        """
        Create a new bucket.
        
        Args:
            bucket_or_name: Bucket instance or bucket name
            project: Project ID (uses client's project if not specified)
            **kwargs: Additional bucket configuration
        
        Returns:
            Created bucket
        """
        if isinstance(bucket_or_name, str):
            bucket = Bucket(self, bucket_or_name)
        else:
            bucket = bucket_or_name
        
        bucket.create(project=project or self.project, **kwargs)
        return bucket
    
    def list_buckets(
        self,
        project: Optional[str] = None,
        max_results: Optional[int] = None,
        page_token: Optional[str] = None,
        prefix: Optional[str] = None
    ) -> Iterator[Bucket]:
        """
        List buckets in a project.
        
        Args:
            project: Project ID (uses client's project if not specified)
            max_results: Maximum number of results to return
            page_token: Token for pagination
            prefix: Prefix to filter bucket names
        
        Yields:
            Bucket instances
        """
        project = project or self.project
        count = 0
        
        for bucket_name, bucket_data in _gcs_buckets.items():
            if prefix and not bucket_name.startswith(prefix):
                continue
            
            if bucket_data.get('project') == project:
                yield Bucket(self, bucket_name)
                count += 1
                
                if max_results and count >= max_results:
                    break
    
    def get_bucket(self, bucket_name: str) -> Bucket:
        """
        Get a bucket by name (raises NotFound if doesn't exist).
        
        Args:
            bucket_name: Name of the bucket
        
        Returns:
            Bucket instance
        
        Raises:
            NotFound: If bucket doesn't exist
        """
        if bucket_name not in _gcs_buckets:
            raise NotFound(f"Bucket {bucket_name} not found")
        return Bucket(self, bucket_name)


class Bucket:
    """Google Cloud Storage bucket."""
    
    def __init__(
        self,
        client: Client,
        name: str,
        user_project: Optional[str] = None
    ):
        """
        Initialize a bucket.
        
        Args:
            client: Cloud Storage client
            name: Bucket name
            user_project: Project to bill for requests
        """
        self.client = client
        self.name = name
        self.user_project = user_project
    
    def create(
        self,
        project: Optional[str] = None,
        location: str = 'US',
        storage_class: str = 'STANDARD',
        **kwargs
    ) -> None:
        """
        Create the bucket.
        
        Args:
            project: Project ID
            location: Bucket location
            storage_class: Storage class
            **kwargs: Additional bucket configuration
        """
        if self.name in _gcs_buckets:
            raise Conflict(f"Bucket {self.name} already exists")
        
        _gcs_buckets[self.name] = {
            'name': self.name,
            'project': project or self.client.project,
            'location': location,
            'storage_class': storage_class,
            'created': datetime.utcnow(),
            'versioning_enabled': kwargs.get('versioning_enabled', False),
            'labels': kwargs.get('labels', {}),
            'lifecycle_rules': kwargs.get('lifecycle_rules', [])
        }
    
    def delete(self, force: bool = False) -> None:
        """
        Delete the bucket.
        
        Args:
            force: If True, delete all blobs first
        
        Raises:
            NotFound: If bucket doesn't exist
            Conflict: If bucket is not empty and force=False
        """
        if self.name not in _gcs_buckets:
            raise NotFound(f"Bucket {self.name} not found")
        
        if _gcs_blobs[self.name] and not force:
            raise Conflict(f"Bucket {self.name} is not empty")
        
        # Delete all blobs if force=True
        if force:
            _gcs_blobs[self.name].clear()
            _gcs_blob_metadata[self.name].clear()
        
        del _gcs_buckets[self.name]
    
    def exists(self) -> bool:
        """Check if the bucket exists."""
        return self.name in _gcs_buckets
    
    def reload(self) -> None:
        """Reload bucket metadata from the server."""
        if not self.exists():
            raise NotFound(f"Bucket {self.name} not found")
    
    def blob(self, blob_name: str, **kwargs) -> Blob:
        """
        Get a blob in this bucket.
        
        Args:
            blob_name: Name of the blob
            **kwargs: Additional blob configuration
        
        Returns:
            Blob instance
        """
        return Blob(blob_name, self, **kwargs)
    
    def get_blob(self, blob_name: str) -> Optional[Blob]:
        """
        Get a blob by name (returns None if doesn't exist).
        
        Args:
            blob_name: Name of the blob
        
        Returns:
            Blob instance or None
        """
        if blob_name in _gcs_blobs[self.name]:
            return Blob(blob_name, self)
        return None
    
    def list_blobs(
        self,
        prefix: Optional[str] = None,
        delimiter: Optional[str] = None,
        max_results: Optional[int] = None,
        page_token: Optional[str] = None
    ) -> Iterator[Blob]:
        """
        List blobs in the bucket.
        
        Args:
            prefix: Filter to blobs with this prefix
            delimiter: Delimiter for directory-like listing
            max_results: Maximum number of results
            page_token: Token for pagination
        
        Yields:
            Blob instances
        """
        count = 0
        
        for blob_name in sorted(_gcs_blobs[self.name].keys()):
            if prefix and not blob_name.startswith(prefix):
                continue
            
            if delimiter:
                # Simplified directory-like listing
                after_prefix = blob_name[len(prefix):] if prefix else blob_name
                if delimiter in after_prefix:
                    # This is in a "subdirectory", skip it
                    continue
            
            yield Blob(blob_name, self)
            count += 1
            
            if max_results and count >= max_results:
                break
    
    def copy_blob(
        self,
        blob: Blob,
        destination_bucket: Bucket,
        new_name: Optional[str] = None
    ) -> Blob:
        """
        Copy a blob to another bucket.
        
        Args:
            blob: Source blob
            destination_bucket: Destination bucket
            new_name: New name for the blob (uses original name if not provided)
        
        Returns:
            New blob instance
        """
        new_name = new_name or blob.name
        
        if blob.name not in _gcs_blobs[self.name]:
            raise NotFound(f"Blob {blob.name} not found")
        
        # Copy data
        _gcs_blobs[destination_bucket.name][new_name] = _gcs_blobs[self.name][blob.name]
        
        # Copy metadata
        if blob.name in _gcs_blob_metadata[self.name]:
            _gcs_blob_metadata[destination_bucket.name][new_name] = (
                _gcs_blob_metadata[self.name][blob.name].copy()
            )
        
        return Blob(new_name, destination_bucket)
    
    @property
    def location(self) -> str:
        """Get bucket location."""
        if self.name in _gcs_buckets:
            return _gcs_buckets[self.name]['location']
        return 'US'
    
    @property
    def storage_class(self) -> str:
        """Get bucket storage class."""
        if self.name in _gcs_buckets:
            return _gcs_buckets[self.name]['storage_class']
        return 'STANDARD'
    
    @property
    def versioning_enabled(self) -> bool:
        """Check if versioning is enabled."""
        if self.name in _gcs_buckets:
            return _gcs_buckets[self.name].get('versioning_enabled', False)
        return False


class Blob:
    """Google Cloud Storage blob (object)."""
    
    def __init__(
        self,
        name: str,
        bucket: Bucket,
        chunk_size: Optional[int] = None,
        encryption_key: Optional[bytes] = None,
        kms_key_name: Optional[str] = None,
        generation: Optional[int] = None
    ):
        """
        Initialize a blob.
        
        Args:
            name: Blob name
            bucket: Parent bucket
            chunk_size: Chunk size for resumable uploads
            encryption_key: Customer-supplied encryption key
            kms_key_name: KMS key name for encryption
            generation: Specific generation of the blob
        """
        self.name = name
        self.bucket = bucket
        self.chunk_size = chunk_size
        self.encryption_key = encryption_key
        self.kms_key_name = kms_key_name
        self.generation = generation
    
    def upload_from_string(
        self,
        data: Union[str, bytes],
        content_type: str = 'text/plain',
        **kwargs
    ) -> None:
        """
        Upload data from a string or bytes.
        
        Args:
            data: Data to upload
            content_type: MIME type of the data
            **kwargs: Additional upload options
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        _gcs_blobs[self.bucket.name][self.name] = data
        
        # Store metadata
        _gcs_blob_metadata[self.bucket.name][self.name] = {
            'name': self.name,
            'bucket': self.bucket.name,
            'size': len(data),
            'content_type': content_type,
            'md5_hash': hashlib.md5(data).hexdigest(),
            'crc32c': str(hash(data) & 0xFFFFFFFF),
            'created': datetime.utcnow(),
            'updated': datetime.utcnow(),
            'generation': kwargs.get('generation', 1),
            'metageneration': 1,
            'metadata': kwargs.get('metadata', {})
        }
    
    def upload_from_file(
        self,
        file_obj: BinaryIO,
        content_type: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Upload data from a file-like object.
        
        Args:
            file_obj: File-like object to read from
            content_type: MIME type of the data
            **kwargs: Additional upload options
        """
        data = file_obj.read()
        self.upload_from_string(data, content_type=content_type or 'application/octet-stream', **kwargs)
    
    def upload_from_filename(
        self,
        filename: str,
        content_type: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Upload data from a file.
        
        Args:
            filename: Path to file to upload
            content_type: MIME type of the data
            **kwargs: Additional upload options
        """
        with open(filename, 'rb') as f:
            self.upload_from_file(f, content_type=content_type, **kwargs)
    
    def download_as_bytes(self) -> bytes:
        """
        Download blob content as bytes.
        
        Returns:
            Blob content as bytes
        
        Raises:
            NotFound: If blob doesn't exist
        """
        if self.name not in _gcs_blobs[self.bucket.name]:
            raise NotFound(f"Blob {self.name} not found")
        
        return _gcs_blobs[self.bucket.name][self.name]
    
    def download_as_string(self) -> str:
        """
        Download blob content as string.
        
        Returns:
            Blob content as string
        
        Raises:
            NotFound: If blob doesn't exist
        """
        return self.download_as_bytes().decode('utf-8')
    
    def download_to_file(self, file_obj: BinaryIO) -> None:
        """
        Download blob content to a file-like object.
        
        Args:
            file_obj: File-like object to write to
        
        Raises:
            NotFound: If blob doesn't exist
        """
        data = self.download_as_bytes()
        file_obj.write(data)
    
    def download_to_filename(self, filename: str) -> None:
        """
        Download blob content to a file.
        
        Args:
            filename: Path to file to write to
        
        Raises:
            NotFound: If blob doesn't exist
        """
        with open(filename, 'wb') as f:
            self.download_to_file(f)
    
    def delete(self) -> None:
        """Delete the blob."""
        if self.name not in _gcs_blobs[self.bucket.name]:
            raise NotFound(f"Blob {self.name} not found")
        
        del _gcs_blobs[self.bucket.name][self.name]
        _gcs_blob_metadata[self.bucket.name].pop(self.name, None)
    
    def exists(self) -> bool:
        """Check if the blob exists."""
        return self.name in _gcs_blobs[self.bucket.name]
    
    def reload(self) -> None:
        """Reload blob metadata from the server."""
        if not self.exists():
            raise NotFound(f"Blob {self.name} not found")
    
    def make_public(self) -> None:
        """Make the blob publicly accessible."""
        if self.name in _gcs_blob_metadata[self.bucket.name]:
            _gcs_blob_metadata[self.bucket.name][self.name]['public'] = True
    
    def make_private(self) -> None:
        """Make the blob private."""
        if self.name in _gcs_blob_metadata[self.bucket.name]:
            _gcs_blob_metadata[self.bucket.name][self.name]['public'] = False
    
    def generate_signed_url(
        self,
        expiration: Union[datetime, timedelta, int],
        method: str = 'GET',
        **kwargs
    ) -> str:
        """
        Generate a signed URL for temporary access.
        
        NOTE: This is a simplified emulation that returns a URL with a token.
        This is NOT cryptographically secure and should only be used for
        development and testing. In production, use the actual google-cloud-storage
        library which implements proper signed URL generation with cryptographic
        signatures.
        
        Args:
            expiration: Expiration time (datetime, timedelta, or seconds)
            method: HTTP method
            **kwargs: Additional parameters
        
        Returns:
            Signed URL string (emulated, not cryptographically secure)
        """
        # Simplified signed URL (not cryptographically secure)
        token = uuid.uuid4().hex
        return f"https://storage.googleapis.com/{self.bucket.name}/{self.name}?token={token}"
    
    @property
    def size(self) -> Optional[int]:
        """Get blob size in bytes."""
        if self.name in _gcs_blob_metadata[self.bucket.name]:
            return _gcs_blob_metadata[self.bucket.name][self.name]['size']
        return None
    
    @property
    def content_type(self) -> Optional[str]:
        """Get blob content type."""
        if self.name in _gcs_blob_metadata[self.bucket.name]:
            return _gcs_blob_metadata[self.bucket.name][self.name]['content_type']
        return None
    
    @property
    def md5_hash(self) -> Optional[str]:
        """Get blob MD5 hash."""
        if self.name in _gcs_blob_metadata[self.bucket.name]:
            return _gcs_blob_metadata[self.bucket.name][self.name]['md5_hash']
        return None
    
    @property
    def crc32c(self) -> Optional[str]:
        """Get blob CRC32C checksum."""
        if self.name in _gcs_blob_metadata[self.bucket.name]:
            return _gcs_blob_metadata[self.bucket.name][self.name]['crc32c']
        return None
    
    @property
    def public_url(self) -> str:
        """Get public URL for the blob."""
        return f"https://storage.googleapis.com/{self.bucket.name}/{self.name}"
    
    @property
    def metadata(self) -> Dict[str, str]:
        """Get custom metadata."""
        if self.name in _gcs_blob_metadata[self.bucket.name]:
            return _gcs_blob_metadata[self.bucket.name][self.name].get('metadata', {})
        return {}
    
    @metadata.setter
    def metadata(self, value: Dict[str, str]) -> None:
        """Set custom metadata."""
        if self.name in _gcs_blob_metadata[self.bucket.name]:
            _gcs_blob_metadata[self.bucket.name][self.name]['metadata'] = value


class Batch:
    """Batch context manager for efficient operations."""
    
    def __init__(self, client: Client):
        """
        Initialize batch.
        
        Args:
            client: Cloud Storage client
        """
        self.client = client
        self._operations = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.finish()
    
    def finish(self) -> None:
        """Execute all batched operations."""
        for operation in self._operations:
            operation()
        self._operations = []


# Constants for storage classes
STANDARD = 'STANDARD'
NEARLINE = 'NEARLINE'
COLDLINE = 'COLDLINE'
ARCHIVE = 'ARCHIVE'

# Constants for predefined ACLs
PRIVATE = 'private'
PUBLIC_READ = 'publicRead'
PUBLIC_READ_WRITE = 'publicReadWrite'
AUTHENTICATED_READ = 'authenticatedRead'
BUCKET_OWNER_READ = 'bucketOwnerRead'
BUCKET_OWNER_FULL_CONTROL = 'bucketOwnerFullControl'
