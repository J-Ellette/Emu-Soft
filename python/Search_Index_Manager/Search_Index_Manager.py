"""
Elasticsearch-py Emulator - Elasticsearch Client for Python

This module emulates the elasticsearch-py library, which is the official
low-level Python client for Elasticsearch. It provides a straightforward
interface to interact with Elasticsearch clusters for indexing, searching,
and managing documents.

Developed by PowerShield
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
import copy


class ElasticsearchException(Exception):
    """Base exception for Elasticsearch errors."""
    pass


class NotFoundError(ElasticsearchException):
    """Exception raised when a document or index is not found."""
    pass


class ConflictError(ElasticsearchException):
    """Exception raised when there's a version conflict."""
    pass


class RequestError(ElasticsearchException):
    """Exception raised for bad requests."""
    pass


@dataclass
class Document:
    """Represents an Elasticsearch document."""
    index: str
    id: str
    source: Dict[str, Any]
    version: int = 1
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    def to_dict(self):
        """Convert to dictionary format."""
        return {
            '_index': self.index,
            '_id': self.id,
            '_version': self.version,
            '_source': copy.deepcopy(self.source),
        }


@dataclass
class Index:
    """Represents an Elasticsearch index."""
    name: str
    settings: Dict[str, Any] = field(default_factory=lambda: {
        'number_of_shards': 1,
        'number_of_replicas': 1
    })
    mappings: Dict[str, Any] = field(default_factory=dict)
    aliases: Dict[str, Any] = field(default_factory=dict)
    documents: Dict[str, Document] = field(default_factory=dict)
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class Elasticsearch:
    """
    Elasticsearch client for interacting with an Elasticsearch cluster.
    
    This emulates the elasticsearch-py.Elasticsearch class which provides
    access to all Elasticsearch APIs including document operations, search,
    and cluster management.
    """
    
    def __init__(self, hosts=None, **kwargs):
        """Initialize the Elasticsearch client."""
        self.hosts = hosts or ['localhost:9200']
        self.timeout = kwargs.get('timeout', 10)
        self.max_retries = kwargs.get('max_retries', 3)
        self.retry_on_timeout = kwargs.get('retry_on_timeout', False)
        
        # In-memory storage
        self._indices: Dict[str, Index] = {}
        self._bulk_queue = []
        
    def ping(self, **kwargs):
        """Test connectivity to the cluster."""
        return True
    
    def info(self, **kwargs):
        """Get cluster information."""
        return {
            'name': 'elasticsearch-emulator',
            'cluster_name': 'emulator-cluster',
            'cluster_uuid': 'test-uuid-12345',
            'version': {
                'number': '7.10.0',
                'build_flavor': 'default',
                'build_type': 'docker',
                'build_hash': 'abc123',
                'build_date': '2021-01-01T00:00:00.000000Z',
                'build_snapshot': False,
                'lucene_version': '8.7.0',
                'minimum_wire_compatibility_version': '6.8.0',
                'minimum_index_compatibility_version': '6.0.0-beta1'
            },
            'tagline': 'You Know, for Search'
        }
    
    # Index operations
    def indices_create(self, index, body=None, **kwargs):
        """Create an index."""
        if index in self._indices:
            raise RequestError(f"Index {index} already exists")
        
        settings = {}
        mappings = {}
        aliases = {}
        
        if body:
            settings = body.get('settings', {})
            mappings = body.get('mappings', {})
            aliases = body.get('aliases', {})
        
        self._indices[index] = Index(
            name=index,
            settings=settings or {
                'number_of_shards': 1,
                'number_of_replicas': 1
            },
            mappings=mappings,
            aliases=aliases
        )
        
        return {
            'acknowledged': True,
            'shards_acknowledged': True,
            'index': index
        }
    
    def indices_delete(self, index, **kwargs):
        """Delete an index."""
        if index not in self._indices:
            raise NotFoundError(f"Index {index} not found")
        
        del self._indices[index]
        return {'acknowledged': True}
    
    def indices_exists(self, index, **kwargs):
        """Check if an index exists."""
        return index in self._indices
    
    def indices_get(self, index, **kwargs):
        """Get index information."""
        if index not in self._indices:
            raise NotFoundError(f"Index {index} not found")
        
        idx = self._indices[index]
        return {
            index: {
                'aliases': idx.aliases,
                'mappings': idx.mappings,
                'settings': {
                    'index': idx.settings
                }
            }
        }
    
    def indices_put_mapping(self, index, body, **kwargs):
        """Update index mapping."""
        if index not in self._indices:
            raise NotFoundError(f"Index {index} not found")
        
        self._indices[index].mappings.update(body)
        return {'acknowledged': True}
    
    def indices_get_mapping(self, index=None, **kwargs):
        """Get index mapping."""
        if index and index not in self._indices:
            raise NotFoundError(f"Index {index} not found")
        
        if index:
            return {
                index: {
                    'mappings': self._indices[index].mappings
                }
            }
        else:
            # Return all mappings
            return {
                idx_name: {'mappings': idx.mappings}
                for idx_name, idx in self._indices.items()
            }
    
    def indices_refresh(self, index=None, **kwargs):
        """Refresh an index."""
        return {'_shards': {'total': 2, 'successful': 2, 'failed': 0}}
    
    def indices_flush(self, index=None, **kwargs):
        """Flush an index."""
        return {'_shards': {'total': 2, 'successful': 2, 'failed': 0}}
    
    def indices_stats(self, index=None, **kwargs):
        """Get index statistics."""
        if index and index not in self._indices:
            raise NotFoundError(f"Index {index} not found")
        
        indices_to_check = [index] if index else list(self._indices.keys())
        
        stats = {
            '_shards': {'total': 2, 'successful': 2, 'failed': 0},
            '_all': {'primaries': {}, 'total': {}},
            'indices': {}
        }
        
        for idx_name in indices_to_check:
            if idx_name in self._indices:
                doc_count = len(self._indices[idx_name].documents)
                stats['indices'][idx_name] = {
                    'primaries': {'docs': {'count': doc_count}},
                    'total': {'docs': {'count': doc_count}}
                }
        
        return stats
    
    # Document operations
    def index(self, index, body, id=None, **kwargs):
        """Index a document."""
        # Create index if it doesn't exist
        if index not in self._indices:
            self.indices_create(index)
        
        # Generate ID if not provided
        if not id:
            import random
            # Use 20-character ID consistent with Elasticsearch defaults
            id = ''.join(random.choices('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_', k=20))
        
        # Check if document exists for versioning
        existing_doc = self._indices[index].documents.get(id)
        version = existing_doc.version + 1 if existing_doc else 1
        
        # Create/update document
        doc = Document(
            index=index,
            id=id,
            source=copy.deepcopy(body),
            version=version
        )
        self._indices[index].documents[id] = doc
        
        result = 'updated' if existing_doc else 'created'
        
        return {
            '_index': index,
            '_id': id,
            '_version': version,
            'result': result,
            '_shards': {'total': 2, 'successful': 1, 'failed': 0},
            '_seq_no': version,
            '_primary_term': 1
        }
    
    def get(self, index, id, **kwargs):
        """Get a document by ID."""
        if index not in self._indices:
            raise NotFoundError(f"Index {index} not found")
        
        if id not in self._indices[index].documents:
            raise NotFoundError(f"Document {id} not found in index {index}")
        
        doc = self._indices[index].documents[id]
        return {
            '_index': index,
            '_id': id,
            '_version': doc.version,
            '_seq_no': doc.version,
            '_primary_term': 1,
            'found': True,
            '_source': copy.deepcopy(doc.source)
        }
    
    def exists(self, index, id, **kwargs):
        """Check if a document exists."""
        if index not in self._indices:
            return False
        return id in self._indices[index].documents
    
    def delete(self, index, id, **kwargs):
        """Delete a document."""
        if index not in self._indices:
            raise NotFoundError(f"Index {index} not found")
        
        if id not in self._indices[index].documents:
            raise NotFoundError(f"Document {id} not found in index {index}")
        
        doc = self._indices[index].documents[id]
        del self._indices[index].documents[id]
        
        return {
            '_index': index,
            '_id': id,
            '_version': doc.version + 1,
            'result': 'deleted',
            '_shards': {'total': 2, 'successful': 1, 'failed': 0},
            '_seq_no': doc.version + 1,
            '_primary_term': 1
        }
    
    def update(self, index, id, body, **kwargs):
        """Update a document."""
        if index not in self._indices:
            raise NotFoundError(f"Index {index} not found")
        
        if id not in self._indices[index].documents:
            raise NotFoundError(f"Document {id} not found in index {index}")
        
        doc = self._indices[index].documents[id]
        
        # Handle different update formats
        if 'doc' in body:
            # Partial document update
            doc.source.update(body['doc'])
        elif 'script' in body:
            # Script update (simplified)
            # In real ES, this would execute a script
            pass
        
        doc.version += 1
        
        return {
            '_index': index,
            '_id': id,
            '_version': doc.version,
            'result': 'updated',
            '_shards': {'total': 2, 'successful': 1, 'failed': 0},
            '_seq_no': doc.version,
            '_primary_term': 1
        }
    
    # Search operations
    def search(self, index=None, body=None, **kwargs):
        """Search for documents."""
        # Determine which indices to search
        if index:
            if isinstance(index, str):
                indices = [index] if index in self._indices else []
            else:
                indices = [i for i in index if i in self._indices]
        else:
            indices = list(self._indices.keys())
        
        # Collect all documents
        all_docs = []
        for idx_name in indices:
            for doc in self._indices[idx_name].documents.values():
                all_docs.append(doc)
        
        # Apply query filtering (simplified)
        filtered_docs = all_docs
        if body and 'query' in body:
            query = body['query']
            
            if 'match_all' in query:
                # Match all documents
                pass
            elif 'match' in query:
                # Simple text match
                field, value = list(query['match'].items())[0]
                filtered_docs = [
                    doc for doc in all_docs
                    if field in doc.source and str(value).lower() in str(doc.source[field]).lower()
                ]
            elif 'term' in query:
                # Exact term match
                field, value = list(query['term'].items())[0]
                filtered_docs = [
                    doc for doc in all_docs
                    if field in doc.source and doc.source[field] == value
                ]
            elif 'range' in query:
                # Range query
                field, conditions = list(query['range'].items())[0]
                filtered_docs = []
                for doc in all_docs:
                    if field not in doc.source:
                        continue
                    val = doc.source[field]
                    match = True
                    if 'gte' in conditions and val < conditions['gte']:
                        match = False
                    if 'gt' in conditions and val <= conditions['gt']:
                        match = False
                    if 'lte' in conditions and val > conditions['lte']:
                        match = False
                    if 'lt' in conditions and val >= conditions['lt']:
                        match = False
                    if match:
                        filtered_docs.append(doc)
        
        # Apply size limit
        size = kwargs.get('size', body.get('size', 10) if body else 10)
        from_param = kwargs.get('from_', body.get('from', 0) if body else 0)
        
        # Paginate results
        paginated_docs = filtered_docs[from_param:from_param + size]
        
        # Build response
        hits = []
        for doc in paginated_docs:
            hit = {
                '_index': doc.index,
                '_id': doc.id,
                '_score': 1.0,
                '_source': copy.deepcopy(doc.source)
            }
            hits.append(hit)
        
        return {
            'took': 5,
            'timed_out': False,
            '_shards': {'total': 5, 'successful': 5, 'skipped': 0, 'failed': 0},
            'hits': {
                'total': {'value': len(filtered_docs), 'relation': 'eq'},
                'max_score': 1.0 if hits else None,
                'hits': hits
            }
        }
    
    def count(self, index=None, body=None, **kwargs):
        """Count documents matching a query."""
        search_result = self.search(index=index, body=body, size=0, **kwargs)
        return {
            'count': search_result['hits']['total']['value'],
            '_shards': {'total': 5, 'successful': 5, 'skipped': 0, 'failed': 0}
        }
    
    # Bulk operations
    def bulk(self, body, index=None, **kwargs):
        """Perform bulk operations."""
        if isinstance(body, str):
            # Parse NDJSON format
            lines = body.strip().split('\n')
        else:
            lines = body
        
        results = []
        errors = False
        
        i = 0
        while i < len(lines):
            # Get action line
            if isinstance(lines[i], str):
                action_line = json.loads(lines[i])
            else:
                action_line = lines[i]
            
            action_type = list(action_line.keys())[0]
            action_meta = action_line[action_type]
            
            idx = action_meta.get('_index', index)
            doc_id = action_meta.get('_id')
            
            result = {}
            
            try:
                if action_type == 'index':
                    # Get document
                    i += 1
                    if isinstance(lines[i], str):
                        doc_body = json.loads(lines[i])
                    else:
                        doc_body = lines[i]
                    
                    # Index the document
                    response = self.index(index=idx, id=doc_id, body=doc_body)
                    result = {
                        'index': {
                            '_index': idx,
                            '_id': response['_id'],
                            '_version': response['_version'],
                            'result': response['result'],
                            'status': 201 if response['result'] == 'created' else 200
                        }
                    }
                
                elif action_type == 'create':
                    # Get document
                    i += 1
                    if isinstance(lines[i], str):
                        doc_body = json.loads(lines[i])
                    else:
                        doc_body = lines[i]
                    
                    # Check if document exists
                    if idx in self._indices and doc_id in self._indices[idx].documents:
                        raise ConflictError(f"Document {doc_id} already exists")
                    
                    response = self.index(index=idx, id=doc_id, body=doc_body)
                    result = {
                        'create': {
                            '_index': idx,
                            '_id': response['_id'],
                            '_version': response['_version'],
                            'result': 'created',
                            'status': 201
                        }
                    }
                
                elif action_type == 'update':
                    # Get update body
                    i += 1
                    if isinstance(lines[i], str):
                        update_body = json.loads(lines[i])
                    else:
                        update_body = lines[i]
                    
                    response = self.update(index=idx, id=doc_id, body=update_body)
                    result = {
                        'update': {
                            '_index': idx,
                            '_id': doc_id,
                            '_version': response['_version'],
                            'result': 'updated',
                            'status': 200
                        }
                    }
                
                elif action_type == 'delete':
                    # Delete the document
                    response = self.delete(index=idx, id=doc_id)
                    result = {
                        'delete': {
                            '_index': idx,
                            '_id': doc_id,
                            '_version': response['_version'],
                            'result': 'deleted',
                            'status': 200
                        }
                    }
            
            except Exception as e:
                errors = True
                result = {
                    action_type: {
                        '_index': idx,
                        '_id': doc_id,
                        'status': 400 if isinstance(e, RequestError) else 404,
                        'error': {
                            'type': type(e).__name__,
                            'reason': str(e)
                        }
                    }
                }
            
            results.append(result)
            i += 1
        
        return {
            'took': 10,
            'errors': errors,
            'items': results
        }
    
    # Aggregation helper
    def _perform_aggregation(self, agg_name, agg_body, documents):
        """Perform an aggregation on documents."""
        agg_type = list(agg_body.keys())[0]
        agg_config = agg_body[agg_type]
        
        if agg_type == 'terms':
            # Terms aggregation
            field = agg_config['field']
            buckets = {}
            
            for doc in documents:
                if field in doc.source:
                    key = doc.source[field]
                    if key not in buckets:
                        buckets[key] = 0
                    buckets[key] += 1
            
            return {
                agg_name: {
                    'doc_count_error_upper_bound': 0,
                    'sum_other_doc_count': 0,
                    'buckets': [
                        {'key': k, 'doc_count': v}
                        for k, v in sorted(buckets.items(), key=lambda x: x[1], reverse=True)
                    ]
                }
            }
        
        return {agg_name: {}}
    
    # Cleanup
    def close(self):
        """Close the client and release resources."""
        pass


# Convenience function
def connect(**kwargs):
    """Create and return an Elasticsearch client."""
    return Elasticsearch(**kwargs)


# Module exports
__all__ = [
    'Elasticsearch',
    'connect',
    'ElasticsearchException',
    'NotFoundError',
    'ConflictError',
    'RequestError',
]
