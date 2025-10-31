"""
Test suite for Elasticsearch-py Emulator

Tests the core functionality of the elasticsearch-py emulator including:
- Client creation and connection
- Index operations
- Document CRUD operations
- Search operations
- Bulk operations
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from elasticsearch_emulator import (
    Elasticsearch,
    connect,
    ElasticsearchException,
    NotFoundError,
    ConflictError,
    RequestError,
)


def test_client_creation():
    """Test creating Elasticsearch clients."""
    print("Testing client creation...")
    
    # Create client with default settings
    es = Elasticsearch()
    assert es is not None
    assert es.ping() == True
    
    # Create client with custom hosts
    es2 = Elasticsearch(hosts=['localhost:9200'])
    assert es2 is not None
    
    # Create client using connect function
    es3 = connect()
    assert es3 is not None
    
    print("  ✓ Client creation works")


def test_cluster_info():
    """Test getting cluster information."""
    print("Testing cluster info...")
    
    es = Elasticsearch()
    
    # Get cluster info
    info = es.info()
    assert 'version' in info
    assert 'cluster_name' in info
    assert info['version']['number'] == '7.10.0'
    
    print("  ✓ Cluster info works")


def test_index_creation():
    """Test creating indices."""
    print("Testing index creation...")
    
    es = Elasticsearch()
    
    # Create a simple index
    result = es.indices_create(index='test-index')
    assert result['acknowledged'] == True
    assert result['index'] == 'test-index'
    
    # Create index with settings
    result = es.indices_create(
        index='test-index-2',
        body={
            'settings': {
                'number_of_shards': 2,
                'number_of_replicas': 0
            },
            'mappings': {
                'properties': {
                    'title': {'type': 'text'},
                    'timestamp': {'type': 'date'}
                }
            }
        }
    )
    assert result['acknowledged'] == True
    
    print("  ✓ Index creation works")


def test_index_exists():
    """Test checking index existence."""
    print("Testing index exists...")
    
    es = Elasticsearch()
    
    # Create an index
    es.indices_create(index='exists-test')
    
    # Check if it exists
    assert es.indices_exists(index='exists-test') == True
    
    # Check non-existent index
    assert es.indices_exists(index='non-existent') == False
    
    print("  ✓ Index exists works")


def test_index_get():
    """Test getting index information."""
    print("Testing index get...")
    
    es = Elasticsearch()
    
    # Create an index with settings
    es.indices_create(
        index='get-test',
        body={
            'settings': {'number_of_shards': 3},
            'mappings': {'properties': {'name': {'type': 'keyword'}}}
        }
    )
    
    # Get index info
    info = es.indices_get(index='get-test')
    assert 'get-test' in info
    assert 'settings' in info['get-test']
    assert 'mappings' in info['get-test']
    
    print("  ✓ Index get works")


def test_index_delete():
    """Test deleting indices."""
    print("Testing index delete...")
    
    es = Elasticsearch()
    
    # Create and delete an index
    es.indices_create(index='delete-test')
    result = es.indices_delete(index='delete-test')
    assert result['acknowledged'] == True
    
    # Verify it's deleted
    assert es.indices_exists(index='delete-test') == False
    
    # Try to delete non-existent index
    try:
        es.indices_delete(index='non-existent')
        assert False, "Should have raised NotFoundError"
    except NotFoundError:
        pass
    
    print("  ✓ Index delete works")


def test_index_mapping():
    """Test index mapping operations."""
    print("Testing index mapping...")
    
    es = Elasticsearch()
    
    # Create an index
    es.indices_create(index='mapping-test')
    
    # Put mapping
    result = es.indices_put_mapping(
        index='mapping-test',
        body={
            'properties': {
                'title': {'type': 'text'},
                'count': {'type': 'integer'}
            }
        }
    )
    assert result['acknowledged'] == True
    
    # Get mapping
    mapping = es.indices_get_mapping(index='mapping-test')
    assert 'mapping-test' in mapping
    assert 'title' in mapping['mapping-test']['mappings']['properties']
    
    print("  ✓ Index mapping works")


def test_document_index():
    """Test indexing documents."""
    print("Testing document index...")
    
    es = Elasticsearch()
    
    # Index a document with ID
    result = es.index(
        index='docs',
        id='1',
        body={'title': 'Test Document', 'content': 'Hello World'}
    )
    assert result['result'] == 'created'
    assert result['_id'] == '1'
    assert result['_version'] == 1
    
    # Index a document without ID (auto-generated)
    result = es.index(
        index='docs',
        body={'title': 'Auto ID Document'}
    )
    assert result['result'] == 'created'
    assert len(result['_id']) > 0
    
    # Update existing document
    result = es.index(
        index='docs',
        id='1',
        body={'title': 'Updated Document', 'content': 'Updated Content'}
    )
    assert result['result'] == 'updated'
    assert result['_version'] == 2
    
    print("  ✓ Document index works")


def test_document_get():
    """Test getting documents."""
    print("Testing document get...")
    
    es = Elasticsearch()
    
    # Index a document
    es.index(
        index='docs',
        id='get-1',
        body={'title': 'Get Test', 'value': 42}
    )
    
    # Get the document
    doc = es.get(index='docs', id='get-1')
    assert doc['found'] == True
    assert doc['_source']['title'] == 'Get Test'
    assert doc['_source']['value'] == 42
    
    # Try to get non-existent document
    try:
        es.get(index='docs', id='non-existent')
        assert False, "Should have raised NotFoundError"
    except NotFoundError:
        pass
    
    print("  ✓ Document get works")


def test_document_exists():
    """Test checking document existence."""
    print("Testing document exists...")
    
    es = Elasticsearch()
    
    # Index a document
    es.index(index='docs', id='exists-1', body={'test': 'data'})
    
    # Check if it exists
    assert es.exists(index='docs', id='exists-1') == True
    
    # Check non-existent document
    assert es.exists(index='docs', id='non-existent') == False
    
    # Check in non-existent index
    assert es.exists(index='non-existent', id='exists-1') == False
    
    print("  ✓ Document exists works")


def test_document_delete():
    """Test deleting documents."""
    print("Testing document delete...")
    
    es = Elasticsearch()
    
    # Index a document
    es.index(index='docs', id='delete-1', body={'test': 'data'})
    
    # Delete the document
    result = es.delete(index='docs', id='delete-1')
    assert result['result'] == 'deleted'
    
    # Verify it's deleted
    assert es.exists(index='docs', id='delete-1') == False
    
    # Try to delete non-existent document
    try:
        es.delete(index='docs', id='non-existent')
        assert False, "Should have raised NotFoundError"
    except NotFoundError:
        pass
    
    print("  ✓ Document delete works")


def test_document_update():
    """Test updating documents."""
    print("Testing document update...")
    
    es = Elasticsearch()
    
    # Index a document
    es.index(
        index='docs',
        id='update-1',
        body={'title': 'Original', 'count': 1}
    )
    
    # Update the document
    result = es.update(
        index='docs',
        id='update-1',
        body={'doc': {'count': 2, 'status': 'updated'}}
    )
    assert result['result'] == 'updated'
    assert result['_version'] == 2
    
    # Get updated document
    doc = es.get(index='docs', id='update-1')
    assert doc['_source']['title'] == 'Original'
    assert doc['_source']['count'] == 2
    assert doc['_source']['status'] == 'updated'
    
    print("  ✓ Document update works")


def test_search_match_all():
    """Test search with match_all query."""
    print("Testing search match_all...")
    
    es = Elasticsearch()
    
    # Index some documents
    for i in range(5):
        es.index(
            index='search-test',
            id=str(i),
            body={'title': f'Document {i}', 'value': i}
        )
    
    # Search all documents
    result = es.search(
        index='search-test',
        body={'query': {'match_all': {}}}
    )
    assert result['hits']['total']['value'] == 5
    assert len(result['hits']['hits']) == 5
    
    print("  ✓ Search match_all works")


def test_search_match():
    """Test search with match query."""
    print("Testing search match...")
    
    es = Elasticsearch()
    
    # Index documents
    es.index(index='search-test', id='1', body={'title': 'Python Programming'})
    es.index(index='search-test', id='2', body={'title': 'Java Programming'})
    es.index(index='search-test', id='3', body={'title': 'Python Data Science'})
    
    # Search for Python
    result = es.search(
        index='search-test',
        body={'query': {'match': {'title': 'Python'}}}
    )
    assert result['hits']['total']['value'] == 2
    
    print("  ✓ Search match works")


def test_search_term():
    """Test search with term query."""
    print("Testing search term...")
    
    es = Elasticsearch()
    
    # Index documents
    es.index(index='search-test', id='1', body={'status': 'active', 'count': 10})
    es.index(index='search-test', id='2', body={'status': 'inactive', 'count': 20})
    es.index(index='search-test', id='3', body={'status': 'active', 'count': 30})
    
    # Search for exact term
    result = es.search(
        index='search-test',
        body={'query': {'term': {'status': 'active'}}}
    )
    assert result['hits']['total']['value'] == 2
    
    print("  ✓ Search term works")


def test_search_range():
    """Test search with range query."""
    print("Testing search range...")
    
    es = Elasticsearch()
    
    # Index documents with numeric values
    for i in range(10):
        es.index(
            index='search-test',
            id=str(i),
            body={'value': i * 10}
        )
    
    # Search for range
    result = es.search(
        index='search-test',
        body={'query': {'range': {'value': {'gte': 30, 'lte': 60}}}}
    )
    assert result['hits']['total']['value'] == 4  # 30, 40, 50, 60
    
    print("  ✓ Search range works")


def test_search_pagination():
    """Test search pagination."""
    print("Testing search pagination...")
    
    es = Elasticsearch()
    
    # Index documents
    for i in range(20):
        es.index(index='search-test', id=str(i), body={'value': i})
    
    # First page
    result = es.search(
        index='search-test',
        body={'query': {'match_all': {}}, 'size': 5, 'from': 0}
    )
    assert len(result['hits']['hits']) == 5
    
    # Second page
    result = es.search(
        index='search-test',
        body={'query': {'match_all': {}}, 'size': 5, 'from': 5}
    )
    assert len(result['hits']['hits']) == 5
    
    print("  ✓ Search pagination works")


def test_search_multiple_indices():
    """Test searching across multiple indices."""
    print("Testing search multiple indices...")
    
    es = Elasticsearch()
    
    # Index documents in different indices
    es.index(index='index-1', id='1', body={'text': 'Document 1'})
    es.index(index='index-2', id='2', body={'text': 'Document 2'})
    es.index(index='index-3', id='3', body={'text': 'Document 3'})
    
    # Search all indices
    result = es.search(body={'query': {'match_all': {}}})
    assert result['hits']['total']['value'] >= 3
    
    # Search specific indices
    result = es.search(
        index=['index-1', 'index-2'],
        body={'query': {'match_all': {}}}
    )
    assert result['hits']['total']['value'] >= 2
    
    print("  ✓ Search multiple indices works")


def test_count():
    """Test document count."""
    print("Testing count...")
    
    es = Elasticsearch()
    
    # Index documents
    for i in range(15):
        es.index(
            index='count-test',
            id=str(i),
            body={'status': 'active' if i % 2 == 0 else 'inactive'}
        )
    
    # Count all documents
    result = es.count(index='count-test')
    assert result['count'] == 15
    
    # Count with query
    result = es.count(
        index='count-test',
        body={'query': {'term': {'status': 'active'}}}
    )
    assert result['count'] == 8
    
    print("  ✓ Count works")


def test_bulk_index():
    """Test bulk indexing."""
    print("Testing bulk index...")
    
    es = Elasticsearch()
    
    # Prepare bulk operations
    operations = [
        {'index': {'_index': 'bulk-test', '_id': '1'}},
        {'title': 'Document 1', 'value': 10},
        {'index': {'_index': 'bulk-test', '_id': '2'}},
        {'title': 'Document 2', 'value': 20},
        {'index': {'_index': 'bulk-test', '_id': '3'}},
        {'title': 'Document 3', 'value': 30},
    ]
    
    # Perform bulk operation
    result = es.bulk(body=operations)
    assert result['errors'] == False
    assert len(result['items']) == 3
    
    # Verify documents were indexed
    doc = es.get(index='bulk-test', id='1')
    assert doc['_source']['title'] == 'Document 1'
    
    print("  ✓ Bulk index works")


def test_bulk_mixed_operations():
    """Test bulk operations with mixed actions."""
    print("Testing bulk mixed operations...")
    
    es = Elasticsearch()
    
    # Index initial documents
    es.index(index='bulk-test', id='1', body={'title': 'Doc 1'})
    es.index(index='bulk-test', id='2', body={'title': 'Doc 2'})
    
    # Prepare mixed bulk operations
    operations = [
        {'update': {'_index': 'bulk-test', '_id': '1'}},
        {'doc': {'title': 'Updated Doc 1'}},
        {'delete': {'_index': 'bulk-test', '_id': '2'}},
        {'create': {'_index': 'bulk-test', '_id': '3'}},
        {'title': 'New Doc 3'},
    ]
    
    # Perform bulk operation
    result = es.bulk(body=operations)
    assert len(result['items']) == 3
    
    # Verify results
    doc1 = es.get(index='bulk-test', id='1')
    assert doc1['_source']['title'] == 'Updated Doc 1'
    
    assert es.exists(index='bulk-test', id='2') == False
    
    doc3 = es.get(index='bulk-test', id='3')
    assert doc3['_source']['title'] == 'New Doc 3'
    
    print("  ✓ Bulk mixed operations work")


def test_index_refresh():
    """Test index refresh."""
    print("Testing index refresh...")
    
    es = Elasticsearch()
    
    # Create and refresh index
    es.indices_create(index='refresh-test')
    result = es.indices_refresh(index='refresh-test')
    assert result['_shards']['successful'] > 0
    
    print("  ✓ Index refresh works")


def test_index_stats():
    """Test index statistics."""
    print("Testing index stats...")
    
    es = Elasticsearch()
    
    # Create index and add documents
    es.indices_create(index='stats-test')
    for i in range(5):
        es.index(index='stats-test', id=str(i), body={'value': i})
    
    # Get stats
    stats = es.indices_stats(index='stats-test')
    assert 'stats-test' in stats['indices']
    assert stats['indices']['stats-test']['total']['docs']['count'] == 5
    
    print("  ✓ Index stats works")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Elasticsearch-py Emulator Test Suite")
    print("=" * 60)
    
    tests = [
        test_client_creation,
        test_cluster_info,
        test_index_creation,
        test_index_exists,
        test_index_get,
        test_index_delete,
        test_index_mapping,
        test_document_index,
        test_document_get,
        test_document_exists,
        test_document_delete,
        test_document_update,
        test_search_match_all,
        test_search_match,
        test_search_term,
        test_search_range,
        test_search_pagination,
        test_search_multiple_indices,
        test_count,
        test_bulk_index,
        test_bulk_mixed_operations,
        test_index_refresh,
        test_index_stats,
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
