package main

// Developed by PowerShield, as an alternative to Redis (Go client)
import (
	"errors"
	"fmt"
	"sort"
	"strconv"
	"strings"
	"time"
)

// Client represents a Redis client connection
type Client struct {
	data     map[string]string
	lists    map[string][]string
	sets     map[string]map[string]bool
	hashes   map[string]map[string]string
	sortedSets map[string]map[string]float64
	expires  map[string]time.Time
}

// NewClient creates a new Redis client
func NewClient(options *Options) *Client {
	return &Client{
		data:       make(map[string]string),
		lists:      make(map[string][]string),
		sets:       make(map[string]map[string]bool),
		hashes:     make(map[string]map[string]string),
		sortedSets: make(map[string]map[string]float64),
		expires:    make(map[string]time.Time),
	}
}

// Options represents Redis connection options
type Options struct {
	Addr     string
	Password string
	DB       int
}

// String Commands

// Set sets a key to hold a string value
func (c *Client) Set(key string, value interface{}, expiration time.Duration) error {
	c.data[key] = fmt.Sprintf("%v", value)
	if expiration > 0 {
		c.expires[key] = time.Now().Add(expiration)
	}
	return nil
}

// Get retrieves the value of a key
func (c *Client) Get(key string) (string, error) {
	if c.isExpired(key) {
		delete(c.data, key)
		delete(c.expires, key)
		return "", errors.New("redis: nil")
	}
	
	value, exists := c.data[key]
	if !exists {
		return "", errors.New("redis: nil")
	}
	return value, nil
}

// Del deletes one or more keys
func (c *Client) Del(keys ...string) (int, error) {
	count := 0
	for _, key := range keys {
		if _, exists := c.data[key]; exists {
			delete(c.data, key)
			delete(c.expires, key)
			count++
		}
		if _, exists := c.lists[key]; exists {
			delete(c.lists, key)
			count++
		}
		if _, exists := c.sets[key]; exists {
			delete(c.sets, key)
			count++
		}
		if _, exists := c.hashes[key]; exists {
			delete(c.hashes, key)
			count++
		}
		if _, exists := c.sortedSets[key]; exists {
			delete(c.sortedSets, key)
			count++
		}
	}
	return count, nil
}

// Exists checks if keys exist
func (c *Client) Exists(keys ...string) (int, error) {
	count := 0
	for _, key := range keys {
		if c.isExpired(key) {
			c.Del(key)
			continue
		}
		if _, exists := c.data[key]; exists {
			count++
		} else if _, exists := c.lists[key]; exists {
			count++
		} else if _, exists := c.sets[key]; exists {
			count++
		} else if _, exists := c.hashes[key]; exists {
			count++
		} else if _, exists := c.sortedSets[key]; exists {
			count++
		}
	}
	return count, nil
}

// Expire sets a timeout on a key
func (c *Client) Expire(key string, expiration time.Duration) error {
	c.expires[key] = time.Now().Add(expiration)
	return nil
}

// TTL returns the remaining time to live of a key
func (c *Client) TTL(key string) (time.Duration, error) {
	expireTime, exists := c.expires[key]
	if !exists {
		return -1, nil
	}
	
	ttl := time.Until(expireTime)
	if ttl < 0 {
		return -2, nil
	}
	return ttl, nil
}

// Incr increments the integer value of a key by one
func (c *Client) Incr(key string) (int64, error) {
	return c.IncrBy(key, 1)
}

// IncrBy increments the integer value of a key by the given amount
func (c *Client) IncrBy(key string, value int64) (int64, error) {
	current, err := c.Get(key)
	if err != nil {
		current = "0"
	}
	
	intVal, err := strconv.ParseInt(current, 10, 64)
	if err != nil {
		return 0, errors.New("value is not an integer")
	}
	
	newVal := intVal + value
	c.Set(key, newVal, 0)
	return newVal, nil
}

// Decr decrements the integer value of a key by one
func (c *Client) Decr(key string) (int64, error) {
	return c.DecrBy(key, 1)
}

// DecrBy decrements the integer value of a key by the given amount
func (c *Client) DecrBy(key string, value int64) (int64, error) {
	return c.IncrBy(key, -value)
}

// List Commands

// LPush inserts values at the head of the list
func (c *Client) LPush(key string, values ...interface{}) (int, error) {
	if c.lists[key] == nil {
		c.lists[key] = []string{}
	}
	
	for i := len(values) - 1; i >= 0; i-- {
		c.lists[key] = append([]string{fmt.Sprintf("%v", values[i])}, c.lists[key]...)
	}
	
	return len(c.lists[key]), nil
}

// RPush inserts values at the tail of the list
func (c *Client) RPush(key string, values ...interface{}) (int, error) {
	if c.lists[key] == nil {
		c.lists[key] = []string{}
	}
	
	for _, value := range values {
		c.lists[key] = append(c.lists[key], fmt.Sprintf("%v", value))
	}
	
	return len(c.lists[key]), nil
}

// LPop removes and returns the first element of the list
func (c *Client) LPop(key string) (string, error) {
	list, exists := c.lists[key]
	if !exists || len(list) == 0 {
		return "", errors.New("redis: nil")
	}
	
	value := list[0]
	c.lists[key] = list[1:]
	return value, nil
}

// RPop removes and returns the last element of the list
func (c *Client) RPop(key string) (string, error) {
	list, exists := c.lists[key]
	if !exists || len(list) == 0 {
		return "", errors.New("redis: nil")
	}
	
	value := list[len(list)-1]
	c.lists[key] = list[:len(list)-1]
	return value, nil
}

// LRange returns a range of elements from the list
func (c *Client) LRange(key string, start, stop int) ([]string, error) {
	list, exists := c.lists[key]
	if !exists {
		return []string{}, nil
	}
	
	length := len(list)
	
	// Handle negative indices
	if start < 0 {
		start = length + start
	}
	if stop < 0 {
		stop = length + stop
	}
	
	// Clamp to bounds
	if start < 0 {
		start = 0
	}
	if stop >= length {
		stop = length - 1
	}
	
	if start > stop || start >= length {
		return []string{}, nil
	}
	
	return list[start : stop+1], nil
}

// LLen returns the length of the list
func (c *Client) LLen(key string) (int, error) {
	list, exists := c.lists[key]
	if !exists {
		return 0, nil
	}
	return len(list), nil
}

// Set Commands

// SAdd adds members to a set
func (c *Client) SAdd(key string, members ...interface{}) (int, error) {
	if c.sets[key] == nil {
		c.sets[key] = make(map[string]bool)
	}
	
	added := 0
	for _, member := range members {
		memberStr := fmt.Sprintf("%v", member)
		if !c.sets[key][memberStr] {
			c.sets[key][memberStr] = true
			added++
		}
	}
	
	return added, nil
}

// SMembers returns all members of the set
func (c *Client) SMembers(key string) ([]string, error) {
	set, exists := c.sets[key]
	if !exists {
		return []string{}, nil
	}
	
	members := []string{}
	for member := range set {
		members = append(members, member)
	}
	
	return members, nil
}

// SIsMember checks if a value is a member of the set
func (c *Client) SIsMember(key string, member interface{}) (bool, error) {
	set, exists := c.sets[key]
	if !exists {
		return false, nil
	}
	
	memberStr := fmt.Sprintf("%v", member)
	return set[memberStr], nil
}

// SRem removes members from a set
func (c *Client) SRem(key string, members ...interface{}) (int, error) {
	set, exists := c.sets[key]
	if !exists {
		return 0, nil
	}
	
	removed := 0
	for _, member := range members {
		memberStr := fmt.Sprintf("%v", member)
		if set[memberStr] {
			delete(set, memberStr)
			removed++
		}
	}
	
	return removed, nil
}

// SCard returns the number of members in the set
func (c *Client) SCard(key string) (int, error) {
	set, exists := c.sets[key]
	if !exists {
		return 0, nil
	}
	return len(set), nil
}

// Hash Commands

// HSet sets a field in the hash
func (c *Client) HSet(key, field string, value interface{}) error {
	if c.hashes[key] == nil {
		c.hashes[key] = make(map[string]string)
	}
	
	c.hashes[key][field] = fmt.Sprintf("%v", value)
	return nil
}

// HGet retrieves the value of a hash field
func (c *Client) HGet(key, field string) (string, error) {
	hash, exists := c.hashes[key]
	if !exists {
		return "", errors.New("redis: nil")
	}
	
	value, exists := hash[field]
	if !exists {
		return "", errors.New("redis: nil")
	}
	
	return value, nil
}

// HGetAll retrieves all fields and values in a hash
func (c *Client) HGetAll(key string) (map[string]string, error) {
	hash, exists := c.hashes[key]
	if !exists {
		return make(map[string]string), nil
	}
	
	result := make(map[string]string)
	for k, v := range hash {
		result[k] = v
	}
	
	return result, nil
}

// HDel deletes fields from a hash
func (c *Client) HDel(key string, fields ...string) (int, error) {
	hash, exists := c.hashes[key]
	if !exists {
		return 0, nil
	}
	
	deleted := 0
	for _, field := range fields {
		if _, exists := hash[field]; exists {
			delete(hash, field)
			deleted++
		}
	}
	
	return deleted, nil
}

// HExists checks if a field exists in the hash
func (c *Client) HExists(key, field string) (bool, error) {
	hash, exists := c.hashes[key]
	if !exists {
		return false, nil
	}
	
	_, exists = hash[field]
	return exists, nil
}

// HLen returns the number of fields in the hash
func (c *Client) HLen(key string) (int, error) {
	hash, exists := c.hashes[key]
	if !exists {
		return 0, nil
	}
	return len(hash), nil
}

// Sorted Set Commands

// ZAdd adds members with scores to a sorted set
func (c *Client) ZAdd(key string, members ...interface{}) (int, error) {
	if c.sortedSets[key] == nil {
		c.sortedSets[key] = make(map[string]float64)
	}
	
	added := 0
	for i := 0; i < len(members); i += 2 {
		if i+1 >= len(members) {
			break
		}
		
		score, err := parseFloat(members[i])
		if err != nil {
			continue
		}
		
		member := fmt.Sprintf("%v", members[i+1])
		if _, exists := c.sortedSets[key][member]; !exists {
			added++
		}
		c.sortedSets[key][member] = score
	}
	
	return added, nil
}

// ZRange returns a range of members in a sorted set by index
func (c *Client) ZRange(key string, start, stop int) ([]string, error) {
	zset, exists := c.sortedSets[key]
	if !exists {
		return []string{}, nil
	}
	
	// Sort members by score
	type scoredMember struct {
		member string
		score  float64
	}
	
	members := []scoredMember{}
	for member, score := range zset {
		members = append(members, scoredMember{member, score})
	}
	
	sort.Slice(members, func(i, j int) bool {
		if members[i].score == members[j].score {
			return members[i].member < members[j].member
		}
		return members[i].score < members[j].score
	})
	
	length := len(members)
	
	// Handle negative indices
	if start < 0 {
		start = length + start
	}
	if stop < 0 {
		stop = length + stop
	}
	
	// Clamp to bounds
	if start < 0 {
		start = 0
	}
	if stop >= length {
		stop = length - 1
	}
	
	if start > stop || start >= length {
		return []string{}, nil
	}
	
	result := []string{}
	for i := start; i <= stop; i++ {
		result = append(result, members[i].member)
	}
	
	return result, nil
}

// ZScore returns the score of a member in a sorted set
func (c *Client) ZScore(key, member string) (float64, error) {
	zset, exists := c.sortedSets[key]
	if !exists {
		return 0, errors.New("redis: nil")
	}
	
	score, exists := zset[member]
	if !exists {
		return 0, errors.New("redis: nil")
	}
	
	return score, nil
}

// ZRem removes members from a sorted set
func (c *Client) ZRem(key string, members ...interface{}) (int, error) {
	zset, exists := c.sortedSets[key]
	if !exists {
		return 0, nil
	}
	
	removed := 0
	for _, member := range members {
		memberStr := fmt.Sprintf("%v", member)
		if _, exists := zset[memberStr]; exists {
			delete(zset, memberStr)
			removed++
		}
	}
	
	return removed, nil
}

// ZCard returns the number of members in a sorted set
func (c *Client) ZCard(key string) (int, error) {
	zset, exists := c.sortedSets[key]
	if !exists {
		return 0, nil
	}
	return len(zset), nil
}

// Utility Commands

// Keys returns all keys matching the pattern
func (c *Client) Keys(pattern string) ([]string, error) {
	keys := []string{}
	
	// Simplified pattern matching (only supports * wildcard)
	for key := range c.data {
		if matchPattern(key, pattern) {
			keys = append(keys, key)
		}
	}
	for key := range c.lists {
		if matchPattern(key, pattern) {
			keys = append(keys, key)
		}
	}
	for key := range c.sets {
		if matchPattern(key, pattern) {
			keys = append(keys, key)
		}
	}
	for key := range c.hashes {
		if matchPattern(key, pattern) {
			keys = append(keys, key)
		}
	}
	for key := range c.sortedSets {
		if matchPattern(key, pattern) {
			keys = append(keys, key)
		}
	}
	
	return keys, nil
}

// FlushDB removes all keys from the current database
func (c *Client) FlushDB() error {
	c.data = make(map[string]string)
	c.lists = make(map[string][]string)
	c.sets = make(map[string]map[string]bool)
	c.hashes = make(map[string]map[string]string)
	c.sortedSets = make(map[string]map[string]float64)
	c.expires = make(map[string]time.Time)
	return nil
}

// Ping tests the connection
func (c *Client) Ping() (string, error) {
	return "PONG", nil
}

// Helper functions

func (c *Client) isExpired(key string) bool {
	expireTime, exists := c.expires[key]
	if !exists {
		return false
	}
	return time.Now().After(expireTime)
}

func matchPattern(key, pattern string) bool {
	if pattern == "*" {
		return true
	}
	
	if strings.Contains(pattern, "*") {
		parts := strings.Split(pattern, "*")
		if len(parts) == 2 {
			prefix := parts[0]
			suffix := parts[1]
			return strings.HasPrefix(key, prefix) && strings.HasSuffix(key, suffix)
		}
	}
	
	return key == pattern
}

func parseFloat(value interface{}) (float64, error) {
	switch v := value.(type) {
	case float64:
		return v, nil
	case float32:
		return float64(v), nil
	case int:
		return float64(v), nil
	case int64:
		return float64(v), nil
	case string:
		return strconv.ParseFloat(v, 64)
	default:
		str := fmt.Sprintf("%v", v)
		return strconv.ParseFloat(str, 64)
	}
}
