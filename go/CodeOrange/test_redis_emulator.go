package main

// Developed by PowerShield, as an alternative to Redis (Go client)
import (
	"fmt"
	"time"
)

func main() {
	fmt.Println("=== Redis Emulator Test Suite ===\n")
	
	// Test 1: Client creation
	fmt.Println("Test 1: Client Creation")
	client := NewClient(&Options{
		Addr: "localhost:6379",
		DB:   0,
	})
	fmt.Println("✓ Redis client created")
	
	// Test 2: Ping
	fmt.Println("\nTest 2: Ping")
	pong, err := client.Ping()
	if err == nil && pong == "PONG" {
		fmt.Printf("✓ Ping successful: %s\n", pong)
	} else {
		fmt.Println("❌ Ping failed")
	}
	
	// Test 3: Set and Get
	fmt.Println("\nTest 3: Set and Get")
	client.Set("name", "Alice", 0)
	value, err := client.Get("name")
	if err == nil && value == "Alice" {
		fmt.Printf("✓ Set/Get works: %s\n", value)
	} else {
		fmt.Printf("❌ Expected Alice, got %s\n", value)
	}
	
	// Test 4: Set with expiration
	fmt.Println("\nTest 4: Set with Expiration")
	client.Set("temp", "expires soon", 2*time.Second)
	value, err = client.Get("temp")
	if err == nil && value == "expires soon" {
		fmt.Printf("✓ Key set with expiration: %s\n", value)
	}
	
	time.Sleep(3 * time.Second)
	value, err = client.Get("temp")
	if err != nil {
		fmt.Println("✓ Key expired successfully")
	} else {
		fmt.Println("❌ Key should have expired")
	}
	
	// Test 5: Delete
	fmt.Println("\nTest 5: Delete")
	client.Set("delete_me", "goodbye", 0)
	count, _ := client.Del("delete_me")
	if count == 1 {
		fmt.Printf("✓ Deleted %d key(s)\n", count)
	}
	
	// Test 6: Exists
	fmt.Println("\nTest 6: Exists")
	client.Set("key1", "value1", 0)
	client.Set("key2", "value2", 0)
	count, _ = client.Exists("key1", "key2", "key3")
	if count == 2 {
		fmt.Printf("✓ Found %d existing keys\n", count)
	} else {
		fmt.Printf("❌ Expected 2 keys, found %d\n", count)
	}
	
	// Test 7: Increment
	fmt.Println("\nTest 7: Increment")
	client.Set("counter", "10", 0)
	newVal, _ := client.Incr("counter")
	if newVal == 11 {
		fmt.Printf("✓ Incremented to %d\n", newVal)
	}
	
	newVal, _ = client.IncrBy("counter", 5)
	if newVal == 16 {
		fmt.Printf("✓ Incremented by 5 to %d\n", newVal)
	}
	
	// Test 8: Decrement
	fmt.Println("\nTest 8: Decrement")
	newVal, _ = client.Decr("counter")
	if newVal == 15 {
		fmt.Printf("✓ Decremented to %d\n", newVal)
	}
	
	newVal, _ = client.DecrBy("counter", 5)
	if newVal == 10 {
		fmt.Printf("✓ Decremented by 5 to %d\n", newVal)
	}
	
	// Test 9: List operations (LPUSH, RPUSH)
	fmt.Println("\nTest 9: List Operations - Push")
	client.LPush("mylist", "world")
	client.LPush("mylist", "hello")
	client.RPush("mylist", "!")
	
	items, _ := client.LRange("mylist", 0, -1)
	if len(items) == 3 && items[0] == "hello" && items[2] == "!" {
		fmt.Printf("✓ List created: %v\n", items)
	} else {
		fmt.Printf("❌ List issue: %v\n", items)
	}
	
	// Test 10: List Pop
	fmt.Println("\nTest 10: List Operations - Pop")
	first, _ := client.LPop("mylist")
	if first == "hello" {
		fmt.Printf("✓ LPOP returned: %s\n", first)
	}
	
	last, _ := client.RPop("mylist")
	if last == "!" {
		fmt.Printf("✓ RPOP returned: %s\n", last)
	}
	
	// Test 11: List Length
	fmt.Println("\nTest 11: List Length")
	length, _ := client.LLen("mylist")
	if length == 1 {
		fmt.Printf("✓ List length: %d\n", length)
	}
	
	// Test 12: Set operations (SADD)
	fmt.Println("\nTest 12: Set Operations - Add")
	client.SAdd("myset", "apple", "banana", "cherry")
	client.SAdd("myset", "apple") // duplicate
	
	card, _ := client.SCard("myset")
	if card == 3 {
		fmt.Printf("✓ Set has %d unique members\n", card)
	}
	
	// Test 13: Set Membership
	fmt.Println("\nTest 13: Set Membership")
	isMember, _ := client.SIsMember("myset", "apple")
	if isMember {
		fmt.Println("✓ apple is a member")
	}
	
	isMember, _ = client.SIsMember("myset", "grape")
	if !isMember {
		fmt.Println("✓ grape is not a member")
	}
	
	// Test 14: Set Members
	fmt.Println("\nTest 14: Set Members")
	members, _ := client.SMembers("myset")
	if len(members) == 3 {
		fmt.Printf("✓ Set members: %v\n", members)
	}
	
	// Test 15: Set Remove
	fmt.Println("\nTest 15: Set Remove")
	removed, _ := client.SRem("myset", "banana")
	if removed == 1 {
		fmt.Printf("✓ Removed %d member(s)\n", removed)
	}
	
	// Test 16: Hash operations
	fmt.Println("\nTest 16: Hash Operations")
	client.HSet("user:1", "name", "Alice")
	client.HSet("user:1", "age", "25")
	client.HSet("user:1", "email", "alice@example.com")
	
	name, _ := client.HGet("user:1", "name")
	if name == "Alice" {
		fmt.Printf("✓ Hash field retrieved: %s\n", name)
	}
	
	// Test 17: Hash GetAll
	fmt.Println("\nTest 17: Hash GetAll")
	hash, _ := client.HGetAll("user:1")
	if len(hash) == 3 && hash["name"] == "Alice" {
		fmt.Printf("✓ Hash has %d fields\n", len(hash))
	}
	
	// Test 18: Hash Length and Exists
	fmt.Println("\nTest 18: Hash Length and Exists")
	hlen, _ := client.HLen("user:1")
	if hlen == 3 {
		fmt.Printf("✓ Hash length: %d\n", hlen)
	}
	
	exists, _ := client.HExists("user:1", "name")
	if exists {
		fmt.Println("✓ Field exists")
	}
	
	// Test 19: Sorted Set operations
	fmt.Println("\nTest 19: Sorted Set Operations")
	client.ZAdd("leaderboard", 100, "Alice", 85, "Bob", 120, "Charlie")
	
	card, _ = client.ZCard("leaderboard")
	if card == 3 {
		fmt.Printf("✓ Sorted set has %d members\n", card)
	}
	
	// Test 20: Sorted Set Range
	fmt.Println("\nTest 20: Sorted Set Range")
	members, _ = client.ZRange("leaderboard", 0, -1)
	if len(members) == 3 && members[0] == "Bob" && members[2] == "Charlie" {
		fmt.Printf("✓ Sorted set members (by score): %v\n", members)
	} else {
		fmt.Printf("Members: %v\n", members)
	}
	
	// Test 21: Sorted Set Score
	fmt.Println("\nTest 21: Sorted Set Score")
	score, err := client.ZScore("leaderboard", "Alice")
	if err == nil && score == 100 {
		fmt.Printf("✓ Alice's score: %.0f\n", score)
	}
	
	// Test 22: Keys pattern matching
	fmt.Println("\nTest 22: Keys Pattern Matching")
	client.Set("user:1:name", "Alice", 0)
	client.Set("user:2:name", "Bob", 0)
	client.Set("product:1", "Laptop", 0)
	
	keys, _ := client.Keys("user:*")
	if len(keys) >= 2 {
		fmt.Printf("✓ Found %d keys matching 'user:*'\n", len(keys))
	}
	
	// Test 23: TTL
	fmt.Println("\nTest 23: TTL")
	client.Set("expiring", "soon", 10*time.Second)
	ttl, _ := client.TTL("expiring")
	if ttl > 0 && ttl <= 10*time.Second {
		fmt.Printf("✓ TTL: %v\n", ttl.Round(time.Second))
	}
	
	// Test 24: FlushDB
	fmt.Println("\nTest 24: FlushDB")
	client.FlushDB()
	keys, _ = client.Keys("*")
	if len(keys) == 0 {
		fmt.Println("✓ Database flushed successfully")
	}
	
	fmt.Println("\n=== All Tests Completed ===")
}
