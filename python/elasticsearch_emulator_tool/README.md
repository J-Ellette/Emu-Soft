# Elasticsearch-py Emulator - Elasticsearch Client for Python

This module emulates the **elasticsearch-py** library, which is the official low-level Python client for Elasticsearch. It provides a straightforward interface to interact with Elasticsearch clusters for indexing, searching, and managing documents and indices.

## What is elasticsearch-py?

elasticsearch-py is the official Python client for Elasticsearch. It provides:
- Low-level client for all Elasticsearch REST APIs
- Connection pooling and automatic node discovery
- Persistent connections and connection reuse
- Pluggable serializers with JSON by default
- Helpers for common operations like bulk indexing
- Comprehensive support for all Elasticsearch operations

## Features

This emulator implements core functionality for Elasticsearch operations:

### Cluster Operations
- Client initialization and configuration
- Cluster connectivity testing (ping)
- Cluster information retrieval
- Connection management

### Index Management
- Create, delete, and check index existence
- Get index information and settings
- Update index mappings
- Index refresh and flush
- Index statistics

### Document Operations
- Index documents (create/update)
- Get documents by ID
- Check document existence
- Delete documents
- Update existing documents
- Version control

### Search and Query
- Full-text search with match queries
- Exact term matching
- Range queries
- Match all queries
- Multi-index search
- Pagination (size and from parameters)
- Document counting

### Bulk Operations
- Bulk indexing
- Bulk updates
- Bulk deletes
- Mixed bulk operations
- Error handling in bulk

## Usage Examples

### Creating a Client

```python
from elasticsearch_emulator import Elasticsearch, connect

# Create client with default settings
es = Elasticsearch()

# Create client with custom hosts
es = Elasticsearch(hosts=['localhost:9200'])

# Create client with multiple hosts
es = Elasticsearch(
    hosts=['host1:9200', 'host2:9200'],
    timeout=30,
    max_retries=3
)

# Using connect convenience function
es = connect()

# Test connection
if es.ping():
    print("Connected to Elasticsearch")
```

### Cluster Information

```python
# Get cluster info
info = es.info()
print(f"Cluster: {info['cluster_name']}")
print(f"Version: {info['version']['number']}")
```

### Working with Indices

#### Creating Indices

```python
# Create a simple index
es.indices_create(index='my-index')

# Create index with settings and mappings
es.indices_create(
    index='products',
    body={
        'settings': {
            'number_of_shards': 2,
            'number_of_replicas': 1
        },
        'mappings': {
            'properties': {
                'name': {'type': 'text'},
                'price': {'type': 'float'},
                'quantity': {'type': 'integer'},
                'created_at': {'type': 'date'}
            }
        }
    }
)
```

#### Managing Indices

```python
# Check if index exists
if es.indices_exists(index='my-index'):
    print("Index exists")

# Get index information
info = es.indices_get(index='my-index')

# Update mapping
es.indices_put_mapping(
    index='my-index',
    body={
        'properties': {
            'description': {'type': 'text'},
            'tags': {'type': 'keyword'}
        }
    }
)

# Get mapping
mapping = es.indices_get_mapping(index='my-index')

# Refresh index
es.indices_refresh(index='my-index')

# Get index statistics
stats = es.indices_stats(index='my-index')
doc_count = stats['indices']['my-index']['total']['docs']['count']

# Delete index
es.indices_delete(index='my-index')
```

### Working with Documents

#### Indexing Documents

```python
# Index a document with explicit ID
es.index(
    index='products',
    id='1',
    body={
        'name': 'Laptop',
        'price': 999.99,
        'quantity': 50,
        'category': 'electronics'
    }
)

# Index a document with auto-generated ID
result = es.index(
    index='products',
    body={
        'name': 'Mouse',
        'price': 29.99,
        'quantity': 100
    }
)
print(f"Document ID: {result['_id']}")

# The index is created automatically if it doesn't exist
es.index(
    index='logs',
    body={
        'timestamp': '2024-01-01T10:00:00Z',
        'level': 'INFO',
        'message': 'Application started'
    }
)
```

#### Reading Documents

```python
# Get a document by ID
doc = es.get(index='products', id='1')
print(f"Product: {doc['_source']['name']}")
print(f"Price: ${doc['_source']['price']}")

# Check if document exists
if es.exists(index='products', id='1'):
    print("Document exists")
```

#### Updating Documents

```python
# Update a document (partial update)
es.update(
    index='products',
    id='1',
    body={
        'doc': {
            'price': 899.99,
            'on_sale': True
        }
    }
)

# Get the updated document
doc = es.get(index='products', id='1')
print(f"New price: ${doc['_source']['price']}")
```

#### Deleting Documents

```python
# Delete a document
es.delete(index='products', id='1')

# Verify deletion
exists = es.exists(index='products', id='1')
print(f"Document exists: {exists}")  # False
```

### Searching

#### Basic Search

```python
# Search all documents
result = es.search(
    index='products',
    body={
        'query': {
            'match_all': {}
        }
    }
)

for hit in result['hits']['hits']:
    print(f"Product: {hit['_source']['name']}")
```

#### Full-Text Search

```python
# Search with match query
result = es.search(
    index='products',
    body={
        'query': {
            'match': {
                'name': 'laptop computer'
            }
        }
    }
)

print(f"Found {result['hits']['total']['value']} products")
for hit in result['hits']['hits']:
    print(f"- {hit['_source']['name']}")
```

#### Term Queries

```python
# Exact term match
result = es.search(
    index='products',
    body={
        'query': {
            'term': {
                'category': 'electronics'
            }
        }
    }
)
```

#### Range Queries

```python
# Search for products in a price range
result = es.search(
    index='products',
    body={
        'query': {
            'range': {
                'price': {
                    'gte': 100,
                    'lte': 500
                }
            }
        }
    }
)
```

#### Search with Pagination

```python
# Get first page (10 results)
result = es.search(
    index='products',
    body={
        'query': {'match_all': {}},
        'size': 10,
        'from': 0
    }
)

# Get second page
result = es.search(
    index='products',
    body={
        'query': {'match_all': {}},
        'size': 10,
        'from': 10
    }
)
```

#### Multi-Index Search

```python
# Search across multiple indices
result = es.search(
    index=['products', 'inventory', 'catalog'],
    body={
        'query': {'match_all': {}}
    }
)

# Search all indices
result = es.search(
    body={
        'query': {'match_all': {}}
    }
)
```

### Counting Documents

```python
# Count all documents
result = es.count(index='products')
print(f"Total products: {result['count']}")

# Count with query
result = es.count(
    index='products',
    body={
        'query': {
            'range': {
                'price': {'gte': 1000}
            }
        }
    }
)
print(f"Expensive products: {result['count']}")
```

### Bulk Operations

#### Bulk Indexing

```python
# Prepare bulk operations
operations = []

for i in range(100):
    # Action metadata
    operations.append({'index': {'_index': 'products', '_id': str(i)}})
    # Document
    operations.append({
        'name': f'Product {i}',
        'price': i * 10.0,
        'quantity': i * 5
    })

# Perform bulk operation
result = es.bulk(body=operations)

if not result['errors']:
    print(f"Successfully indexed {len(result['items'])} documents")
```

#### Mixed Bulk Operations

```python
operations = [
    # Index a new document
    {'index': {'_index': 'products', '_id': '1'}},
    {'name': 'New Product', 'price': 99.99},
    
    # Update existing document
    {'update': {'_index': 'products', '_id': '2'}},
    {'doc': {'price': 149.99}},
    
    # Delete a document
    {'delete': {'_index': 'products', '_id': '3'}},
    
    # Create (fails if exists)
    {'create': {'_index': 'products', '_id': '4'}},
    {'name': 'Another Product', 'price': 199.99},
]

result = es.bulk(body=operations)

# Check for errors
if result['errors']:
    for item in result['items']:
        if 'error' in list(item.values())[0]:
            print(f"Error: {item}")
```

## Real-World Use Cases

### Application Logging

```python
from elasticsearch_emulator import Elasticsearch
from datetime import datetime

es = Elasticsearch()

def log_event(level, message, **kwargs):
    """Log an event to Elasticsearch."""
    doc = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'level': level,
        'message': message,
        **kwargs
    }
    
    es.index(
        index=f'logs-{datetime.utcnow().strftime("%Y-%m-%d")}',
        body=doc
    )

# Usage
log_event('INFO', 'Application started', component='web-server')
log_event('ERROR', 'Database connection failed', component='database', error_code=500)

# Search logs
errors = es.search(
    index='logs-*',
    body={
        'query': {'term': {'level': 'ERROR'}},
        'size': 100
    }
)
```

### Product Search Engine

```python
from elasticsearch_emulator import Elasticsearch

es = Elasticsearch()

# Create product index with mappings
es.indices_create(
    index='products',
    body={
        'mappings': {
            'properties': {
                'name': {'type': 'text'},
                'description': {'type': 'text'},
                'category': {'type': 'keyword'},
                'price': {'type': 'float'},
                'in_stock': {'type': 'boolean'},
                'tags': {'type': 'keyword'}
            }
        }
    }
)

# Add products
products = [
    {
        'name': 'Wireless Mouse',
        'description': 'Ergonomic wireless mouse with 6 buttons',
        'category': 'electronics',
        'price': 29.99,
        'in_stock': True,
        'tags': ['wireless', 'ergonomic', 'computer']
    },
    # ... more products
]

# Bulk index products
operations = []
for i, product in enumerate(products):
    operations.append({'index': {'_index': 'products', '_id': str(i)}})
    operations.append(product)

es.bulk(body=operations)

# Search function
def search_products(query_text, category=None, min_price=None, max_price=None):
    query = {'bool': {'must': []}}
    
    if query_text:
        query['bool']['must'].append({
            'match': {'name': query_text}
        })
    
    if category:
        query['bool']['must'].append({
            'term': {'category': category}
        })
    
    if min_price or max_price:
        range_query = {}
        if min_price:
            range_query['gte'] = min_price
        if max_price:
            range_query['lte'] = max_price
        query['bool']['must'].append({
            'range': {'price': range_query}
        })
    
    result = es.search(
        index='products',
        body={'query': query}
    )
    
    return [hit['_source'] for hit in result['hits']['hits']]

# Search for products
results = search_products('mouse', category='electronics', max_price=50)
```

### Analytics and Metrics

```python
from elasticsearch_emulator import Elasticsearch
from datetime import datetime, timedelta

es = Elasticsearch()

# Store metrics
def store_metric(name, value, tags=None):
    es.index(
        index='metrics',
        body={
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'name': name,
            'value': value,
            'tags': tags or {}
        }
    )

# Query metrics
def get_metrics(name, hours=24):
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + 'Z'
    
    result = es.search(
        index='metrics',
        body={
            'query': {
                'bool': {
                    'must': [
                        {'term': {'name': name}},
                        {'range': {'timestamp': {'gte': cutoff}}}
                    ]
                }
            },
            'size': 1000,
            'sort': [{'timestamp': 'desc'}]
        }
    )
    
    return [(hit['_source']['timestamp'], hit['_source']['value']) 
            for hit in result['hits']['hits']]
```

## API Compatibility

This emulator provides compatibility with elasticsearch-py core API:

- ✅ `Elasticsearch()` - Client creation
- ✅ `ping()` - Test connectivity
- ✅ `info()` - Cluster information
- ✅ Index operations (create, delete, exists, get, refresh, stats)
- ✅ Mapping operations (put, get)
- ✅ Document operations (index, get, exists, delete, update)
- ✅ Search operations (match, term, range, match_all)
- ✅ Count operations
- ✅ Bulk operations (index, create, update, delete)
- ✅ Multi-index operations
- ✅ Pagination support

## Emulated Concepts

### Inverted Index
Simulates Elasticsearch's inverted index structure for full-text search capabilities.

### Document Versioning
Tracks document versions for optimistic concurrency control.

### Index Management
Emulates index creation, deletion, and configuration management.

### Query DSL
Implements a subset of Elasticsearch's Query DSL for document retrieval.

### Bulk API
Simulates efficient bulk operations for high-throughput scenarios.

## Implementation Notes

- **In-Memory Storage**: All indices and documents stored in memory
- **ID Generation**: Auto-generates document IDs when not provided
- **Version Control**: Tracks document versions for updates
- **Simplified Search**: Implements basic query types (match, term, range)
- **Bulk Processing**: Supports bulk operations with error handling
- **Index Auto-Creation**: Automatically creates indices when indexing documents

## Testing

Run the test suite:

```bash
python test_elasticsearch_emulator.py
```

The test suite covers:
- Client creation and cluster operations
- Index management (create, delete, mapping, stats)
- Document CRUD operations
- Search operations (match, term, range, pagination)
- Bulk operations
- Multi-index search

## Emulates

This module emulates the **elasticsearch-py** library (PyPI package: `elasticsearch`):
- Repository: https://github.com/elastic/elasticsearch-py
- Documentation: https://elasticsearch-py.readthedocs.io/
- License: Apache 2.0

## Educational Purpose

This is an educational reimplementation created for the CIV-ARCOS project. It demonstrates:
- REST API client design patterns
- Search engine architecture concepts
- Document-oriented database operations
- Bulk data processing
- Query DSL implementation
- Full-text search mechanics

For production use with real Elasticsearch clusters, please use the official elasticsearch-py library.
