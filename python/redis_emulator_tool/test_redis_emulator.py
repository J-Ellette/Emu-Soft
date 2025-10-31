"""
Tests for Redis emulator

Comprehensive test suite for Redis client emulator functionality.
"""

import unittest
import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from redis_emulator import (
    Redis, Pipeline, PubSub, ConnectionPool, Sentinel,
    RedisError, ConnectionError, ResponseError,
    from_url, StrictRedis,
    _redis_storage, _redis_hashes, _redis_lists, _redis_sets, 
    _redis_sorted_sets, _redis_expiry
)


class TestRedisBasics(unittest.TestCase):
    """Test basic Redis operations."""
    
    def setUp(self):
        """Clean storage before each test."""
        _redis_storage.clear()
        _redis_hashes.clear()
        _redis_lists.clear()
        _redis_sets.clear()
        _redis_sorted_sets.clear()
        _redis_expiry.clear()
        self.redis = Redis()
    
    def test_redis_creation(self):
        """Test Redis client creation."""
        r = Redis(host='localhost', port=6379, db=0)
        self.assertEqual(r.host, 'localhost')
        self.assertEqual(r.port, 6379)
        self.assertEqual(r.db, 0)
    
    def test_strict_redis_alias(self):
        """Test StrictRedis is an alias for Redis."""
        r = StrictRedis()
        self.assertIsInstance(r, Redis)


class TestStringOperations(unittest.TestCase):
    """Test Redis string operations."""
    
    def setUp(self):
        """Clean storage before each test."""
        _redis_storage.clear()
        _redis_expiry.clear()
        self.redis = Redis()
    
    def test_set_and_get(self):
        """Test basic set and get operations."""
        self.redis.set('key1', 'value1')
        self.assertEqual(self.redis.get('key1'), b'value1')
    
    def test_set_with_decode_responses(self):
        """Test set and get with decode_responses."""
        r = Redis(decode_responses=True)
        r.set('key1', 'value1')
        self.assertEqual(r.get('key1'), 'value1')
    
    def test_set_nx(self):
        """Test set with NX flag (only if not exists)."""
        self.assertTrue(self.redis.set('key1', 'value1', nx=True))
        self.assertFalse(self.redis.set('key1', 'value2', nx=True))
        self.assertEqual(self.redis.get('key1'), b'value1')
    
    def test_set_xx(self):
        """Test set with XX flag (only if exists)."""
        self.assertFalse(self.redis.set('key1', 'value1', xx=True))
        self.redis.set('key1', 'value1')
        self.assertTrue(self.redis.set('key1', 'value2', xx=True))
        self.assertEqual(self.redis.get('key1'), b'value2')
    
    def test_delete(self):
        """Test delete operation."""
        self.redis.set('key1', 'value1')
        self.redis.set('key2', 'value2')
        count = self.redis.delete('key1', 'key2', 'key3')
        self.assertEqual(count, 2)
        self.assertIsNone(self.redis.get('key1'))
    
    def test_exists(self):
        """Test exists operation."""
        self.redis.set('key1', 'value1')
        self.redis.set('key2', 'value2')
        self.assertEqual(self.redis.exists('key1'), 1)
        self.assertEqual(self.redis.exists('key1', 'key2'), 2)
        self.assertEqual(self.redis.exists('key3'), 0)
    
    def test_incr_decr(self):
        """Test increment and decrement operations."""
        self.redis.set('counter', '10')
        self.assertEqual(self.redis.incr('counter'), 11)
        self.assertEqual(self.redis.incr('counter', 5), 16)
        self.assertEqual(self.redis.decr('counter'), 15)
        self.assertEqual(self.redis.decr('counter', 5), 10)
    
    def test_incr_nonexistent(self):
        """Test increment on non-existent key."""
        self.assertEqual(self.redis.incr('new_counter'), 1)


class TestHashOperations(unittest.TestCase):
    """Test Redis hash operations."""
    
    def setUp(self):
        """Clean storage before each test."""
        _redis_hashes.clear()
        _redis_expiry.clear()
        self.redis = Redis()
    
    def test_hset_hget(self):
        """Test hash set and get."""
        self.redis.hset('myhash', 'field1', 'value1')
        self.assertEqual(self.redis.hget('myhash', 'field1'), b'value1')
    
    def test_hset_mapping(self):
        """Test hash set with mapping."""
        count = self.redis.hset('myhash', mapping={'field1': 'value1', 'field2': 'value2'})
        self.assertEqual(count, 2)
        self.assertEqual(self.redis.hget('myhash', 'field1'), b'value1')
        self.assertEqual(self.redis.hget('myhash', 'field2'), b'value2')
    
    def test_hgetall(self):
        """Test getting all hash fields."""
        self.redis.hset('myhash', mapping={'field1': 'value1', 'field2': 'value2'})
        result = self.redis.hgetall('myhash')
        self.assertEqual(len(result), 2)
        self.assertIn(b'field1', result)
    
    def test_hdel(self):
        """Test hash field deletion."""
        self.redis.hset('myhash', mapping={'field1': 'value1', 'field2': 'value2'})
        count = self.redis.hdel('myhash', 'field1')
        self.assertEqual(count, 1)
        self.assertIsNone(self.redis.hget('myhash', 'field1'))
    
    def test_hexists(self):
        """Test hash field existence check."""
        self.redis.hset('myhash', 'field1', 'value1')
        self.assertTrue(self.redis.hexists('myhash', 'field1'))
        self.assertFalse(self.redis.hexists('myhash', 'field2'))


class TestListOperations(unittest.TestCase):
    """Test Redis list operations."""
    
    def setUp(self):
        """Clean storage before each test."""
        _redis_lists.clear()
        _redis_expiry.clear()
        self.redis = Redis()
    
    def test_lpush_rpush(self):
        """Test list push operations."""
        self.redis.lpush('mylist', 'value1')
        self.redis.rpush('mylist', 'value2')
        self.assertEqual(self.redis.lrange('mylist', 0, -1), [b'value1', b'value2'])
    
    def test_lpop_rpop(self):
        """Test list pop operations."""
        self.redis.rpush('mylist', 'value1', 'value2', 'value3')
        self.assertEqual(self.redis.lpop('mylist'), b'value1')
        self.assertEqual(self.redis.rpop('mylist'), b'value3')
        self.assertEqual(self.redis.llen('mylist'), 1)
    
    def test_lrange(self):
        """Test list range operation."""
        self.redis.rpush('mylist', 'value1', 'value2', 'value3', 'value4')
        self.assertEqual(self.redis.lrange('mylist', 0, 1), [b'value1', b'value2'])
        self.assertEqual(self.redis.lrange('mylist', 1, 2), [b'value2', b'value3'])
    
    def test_llen(self):
        """Test list length operation."""
        self.redis.rpush('mylist', 'value1', 'value2', 'value3')
        self.assertEqual(self.redis.llen('mylist'), 3)


class TestSetOperations(unittest.TestCase):
    """Test Redis set operations."""
    
    def setUp(self):
        """Clean storage before each test."""
        _redis_sets.clear()
        _redis_expiry.clear()
        self.redis = Redis()
    
    def test_sadd_smembers(self):
        """Test set add and members operations."""
        count = self.redis.sadd('myset', 'member1', 'member2', 'member3')
        self.assertEqual(count, 3)
        members = self.redis.smembers('myset')
        self.assertEqual(len(members), 3)
        self.assertIn(b'member1', members)
    
    def test_sadd_duplicate(self):
        """Test adding duplicate to set."""
        self.redis.sadd('myset', 'member1')
        count = self.redis.sadd('myset', 'member1')
        self.assertEqual(count, 0)
    
    def test_srem(self):
        """Test set remove operation."""
        self.redis.sadd('myset', 'member1', 'member2', 'member3')
        count = self.redis.srem('myset', 'member1', 'member2')
        self.assertEqual(count, 2)
        self.assertEqual(self.redis.scard('myset'), 1)
    
    def test_sismember(self):
        """Test set membership check."""
        self.redis.sadd('myset', 'member1')
        self.assertTrue(self.redis.sismember('myset', 'member1'))
        self.assertFalse(self.redis.sismember('myset', 'member2'))
    
    def test_scard(self):
        """Test set cardinality."""
        self.redis.sadd('myset', 'member1', 'member2', 'member3')
        self.assertEqual(self.redis.scard('myset'), 3)


class TestSortedSetOperations(unittest.TestCase):
    """Test Redis sorted set operations."""
    
    def setUp(self):
        """Clean storage before each test."""
        _redis_sorted_sets.clear()
        _redis_expiry.clear()
        self.redis = Redis()
    
    def test_zadd_zrange(self):
        """Test sorted set add and range operations."""
        count = self.redis.zadd('myzset', {'member1': 1.0, 'member2': 2.0, 'member3': 3.0})
        self.assertEqual(count, 3)
        members = self.redis.zrange('myzset', 0, -1)
        self.assertEqual(members, [b'member1', b'member2', b'member3'])
    
    def test_zrange_with_scores(self):
        """Test sorted set range with scores."""
        self.redis.zadd('myzset', {'member1': 1.0, 'member2': 2.0})
        result = self.redis.zrange('myzset', 0, -1, withscores=True)
        self.assertEqual(result, [(b'member1', 1.0), (b'member2', 2.0)])
    
    def test_zscore(self):
        """Test getting score of member."""
        self.redis.zadd('myzset', {'member1': 1.5})
        score = self.redis.zscore('myzset', 'member1')
        self.assertEqual(score, 1.5)
    
    def test_zrem(self):
        """Test sorted set remove operation."""
        self.redis.zadd('myzset', {'member1': 1.0, 'member2': 2.0})
        count = self.redis.zrem('myzset', 'member1')
        self.assertEqual(count, 1)
        members = self.redis.zrange('myzset', 0, -1)
        self.assertEqual(members, [b'member2'])


class TestKeyOperations(unittest.TestCase):
    """Test Redis key operations."""
    
    def setUp(self):
        """Clean storage before each test."""
        _redis_storage.clear()
        _redis_expiry.clear()
        self.redis = Redis()
    
    def test_expire_ttl(self):
        """Test key expiration."""
        self.redis.set('key1', 'value1')
        self.assertTrue(self.redis.expire('key1', 2))
        ttl = self.redis.ttl('key1')
        self.assertGreater(ttl, 0)
        self.assertLessEqual(ttl, 2)
    
    def test_persist(self):
        """Test removing expiration."""
        self.redis.set('key1', 'value1', ex=10)
        self.assertTrue(self.redis.persist('key1'))
        self.assertEqual(self.redis.ttl('key1'), -1)
    
    def test_keys_pattern(self):
        """Test keys pattern matching."""
        self.redis.set('user:1', 'value1')
        self.redis.set('user:2', 'value2')
        self.redis.set('post:1', 'value3')
        
        keys = self.redis.keys('user:*')
        self.assertEqual(len(keys), 2)
        
        all_keys = self.redis.keys('*')
        self.assertEqual(len(all_keys), 3)
    
    def test_flushdb(self):
        """Test flushing database."""
        self.redis.set('key1', 'value1')
        self.redis.set('key2', 'value2')
        self.assertTrue(self.redis.flushdb())
        self.assertEqual(self.redis.exists('key1', 'key2'), 0)


class TestPipeline(unittest.TestCase):
    """Test Redis pipeline functionality."""
    
    def setUp(self):
        """Clean storage before each test."""
        _redis_storage.clear()
        self.redis = Redis()
    
    def test_pipeline_basic(self):
        """Test basic pipeline operations."""
        pipe = self.redis.pipeline()
        pipe.set('key1', 'value1')
        pipe.set('key2', 'value2')
        pipe.get('key1')
        results = pipe.execute()
        
        self.assertEqual(len(results), 3)
        self.assertTrue(results[0])  # set returns True
        self.assertTrue(results[1])
        self.assertEqual(results[2], b'value1')
    
    def test_pipeline_context_manager(self):
        """Test pipeline with context manager."""
        with self.redis.pipeline() as pipe:
            pipe.set('key1', 'value1')
            pipe.set('key2', 'value2')
        
        self.assertEqual(self.redis.get('key1'), b'value1')
        self.assertEqual(self.redis.get('key2'), b'value2')


class TestPubSub(unittest.TestCase):
    """Test Redis Pub/Sub functionality."""
    
    def setUp(self):
        """Clean storage before each test."""
        self.redis = Redis()
    
    def test_pubsub_creation(self):
        """Test creating PubSub instance."""
        pubsub = self.redis.pubsub()
        self.assertIsInstance(pubsub, PubSub)
    
    def test_subscribe(self):
        """Test channel subscription."""
        pubsub = self.redis.pubsub()
        pubsub.subscribe('channel1', 'channel2')
        self.assertIn('channel1', pubsub.channels)
        self.assertIn('channel2', pubsub.channels)
    
    def test_unsubscribe(self):
        """Test channel unsubscription."""
        pubsub = self.redis.pubsub()
        pubsub.subscribe('channel1')
        pubsub.unsubscribe('channel1')
        self.assertNotIn('channel1', pubsub.channels)
    
    def test_publish(self):
        """Test publishing messages."""
        count = self.redis.publish('channel1', 'message')
        self.assertEqual(count, 0)  # No subscribers


class TestConnectionPool(unittest.TestCase):
    """Test connection pool functionality."""
    
    def test_pool_creation(self):
        """Test creating connection pool."""
        pool = ConnectionPool(host='localhost', port=6379)
        self.assertEqual(pool.host, 'localhost')
        self.assertEqual(pool.port, 6379)
    
    def test_get_connection(self):
        """Test getting connection from pool."""
        pool = ConnectionPool()
        conn = pool.get_connection('GET')
        self.assertIsInstance(conn, Redis)


class TestSentinel(unittest.TestCase):
    """Test Sentinel functionality."""
    
    def test_sentinel_creation(self):
        """Test creating Sentinel instance."""
        sentinel = Sentinel([('localhost', 26379)])
        self.assertEqual(len(sentinel.sentinels), 1)
    
    def test_master_for(self):
        """Test getting master client."""
        sentinel = Sentinel([('localhost', 26379)])
        master = sentinel.master_for('mymaster')
        self.assertIsInstance(master, Redis)
    
    def test_slave_for(self):
        """Test getting slave client."""
        sentinel = Sentinel([('localhost', 26379)])
        slave = sentinel.slave_for('mymaster')
        self.assertIsInstance(slave, Redis)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""
    
    def test_from_url(self):
        """Test creating client from URL."""
        r = from_url('redis://localhost:6379/0')
        self.assertIsInstance(r, Redis)


class TestExpiration(unittest.TestCase):
    """Test key expiration functionality."""
    
    def setUp(self):
        """Clean storage before each test."""
        _redis_storage.clear()
        _redis_expiry.clear()
        self.redis = Redis()
    
    def test_set_with_ex(self):
        """Test set with expiration in seconds."""
        self.redis.set('key1', 'value1', ex=1)
        self.assertIsNotNone(self.redis.get('key1'))
        time.sleep(1.1)
        self.assertIsNone(self.redis.get('key1'))
    
    def test_set_with_px(self):
        """Test set with expiration in milliseconds."""
        self.redis.set('key1', 'value1', px=500)
        self.assertIsNotNone(self.redis.get('key1'))
        time.sleep(0.6)
        self.assertIsNone(self.redis.get('key1'))


class TestIntegrationScenarios(unittest.TestCase):
    """Test complete usage scenarios."""
    
    def setUp(self):
        """Clean storage before each test."""
        _redis_storage.clear()
        _redis_hashes.clear()
        _redis_lists.clear()
        _redis_sets.clear()
        _redis_sorted_sets.clear()
        _redis_expiry.clear()
        self.redis = Redis(decode_responses=True)
    
    def test_user_session_management(self):
        """Test user session management scenario."""
        # Store user session
        self.redis.hset('session:user123', mapping={
            'user_id': '123',
            'username': 'john_doe',
            'login_time': '2024-01-01T00:00:00Z'
        })
        
        # Set expiration
        self.redis.expire('session:user123', 3600)
        
        # Retrieve session
        session = self.redis.hgetall('session:user123')
        self.assertEqual(session['username'], 'john_doe')
    
    def test_leaderboard_scenario(self):
        """Test leaderboard using sorted sets."""
        # Add players with scores
        self.redis.zadd('leaderboard', {
            'player1': 100,
            'player2': 200,
            'player3': 150
        })
        
        # Get top 3 players
        top_players = self.redis.zrange('leaderboard', 0, 2, withscores=True)
        self.assertEqual(len(top_players), 3)
        self.assertEqual(top_players[2][0], 'player2')  # Highest score
        self.assertEqual(top_players[2][1], 200)
    
    def test_queue_scenario(self):
        """Test message queue using lists."""
        # Add jobs to queue
        self.redis.rpush('job_queue', 'job1', 'job2', 'job3')
        
        # Process jobs
        job1 = self.redis.lpop('job_queue')
        job2 = self.redis.lpop('job_queue')
        
        self.assertEqual(job1, 'job1')
        self.assertEqual(job2, 'job2')
        self.assertEqual(self.redis.llen('job_queue'), 1)
    
    def test_caching_scenario(self):
        """Test caching with expiration."""
        # Cache API response
        self.redis.set('cache:api:users', '{"users": []}', ex=60)
        
        # Check cache hit
        cached = self.redis.get('cache:api:users')
        self.assertIsNotNone(cached)
        
        # Check TTL
        ttl = self.redis.ttl('cache:api:users')
        self.assertGreater(ttl, 0)


if __name__ == '__main__':
    unittest.main()
