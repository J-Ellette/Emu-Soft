package main

import (
	"fmt"
	"os"
)

// Helper function to run a test
func runTest(name string, testFunc func() bool) {
	result := "PASS"
	if !testFunc() {
		result = "FAIL"
	}
	fmt.Printf("[%s] %s\n", result, name)
}

// Test Set and Get
func testSetAndGet() bool {
	v := New()
	v.Set("name", "Alice")
	return v.Get("name") == "Alice"
}

// Test GetString
func testGetString() bool {
	v := New()
	v.Set("name", "Bob")
	return v.GetString("name") == "Bob"
}

// Test GetInt
func testGetInt() bool {
	v := New()
	v.Set("count", 42)
	return v.GetInt("count") == 42
}

// Test GetBool
func testGetBool() bool {
	v := New()
	v.Set("enabled", true)
	return v.GetBool("enabled") == true
}

// Test GetFloat64
func testGetFloat64() bool {
	v := New()
	v.Set("price", 19.99)
	return v.GetFloat64("price") == 19.99
}

// Test GetStringSlice
func testGetStringSlice() bool {
	v := New()
	v.Set("tags", []string{"go", "config", "viper"})
	tags := v.GetStringSlice("tags")
	return len(tags) == 3 && tags[0] == "go"
}

// Test GetStringMap
func testGetStringMap() bool {
	v := New()
	m := map[string]interface{}{
		"host": "localhost",
		"port": 8080,
	}
	v.Set("server", m)
	result := v.GetStringMap("server")
	return result["host"] == "localhost"
}

// Test SetDefault
func testSetDefault() bool {
	v := New()
	v.SetDefault("port", 8080)
	return v.GetInt("port") == 8080
}

// Test default override
func testDefaultOverride() bool {
	v := New()
	v.SetDefault("port", 8080)
	v.Set("port", 3000)
	return v.GetInt("port") == 3000
}

// Test IsSet
func testIsSet() bool {
	v := New()
	v.Set("name", "test")
	return v.IsSet("name") && !v.IsSet("nonexistent")
}

// Test AllKeys
func testAllKeys() bool {
	v := New()
	v.Set("key1", "value1")
	v.Set("key2", "value2")
	keys := v.AllKeys()
	return len(keys) == 2
}

// Test AllSettings
func testAllSettings() bool {
	v := New()
	v.Set("name", "Alice")
	v.Set("age", 30)
	settings := v.AllSettings()
	return len(settings) == 2 && settings["name"] == "Alice"
}

// Test Sub
func testSub() bool {
	v := New()
	v.Set("database", map[string]interface{}{
		"host": "localhost",
		"port": 5432,
	})
	sub := v.Sub("database")
	return sub != nil && sub.GetString("host") == "localhost"
}

// Test BindEnv
func testBindEnv() bool {
	v := New()
	os.Setenv("TEST_VAR", "test_value")
	defer os.Unsetenv("TEST_VAR")
	
	v.BindEnv("mykey", "TEST_VAR")
	return v.GetString("mykey") == "test_value"
}

// Test config file write and read
func testWriteAndReadConfig() bool {
	v := New()
	v.Set("name", "TestApp")
	v.Set("version", "1.0.0")
	v.SetConfigFile("/tmp/test_config.json")
	v.SetConfigType("json")
	
	// Write config
	err := v.WriteConfig()
	if err != nil {
		fmt.Printf("Write error: %v\n", err)
		return false
	}
	
	// Read config in new instance
	v2 := New()
	v2.SetConfigFile("/tmp/test_config.json")
	v2.SetConfigType("json")
	err = v2.ReadInConfig()
	if err != nil {
		fmt.Printf("Read error: %v\n", err)
		return false
	}
	
	// Clean up
	os.Remove("/tmp/test_config.json")
	
	return v2.GetString("name") == "TestApp" && v2.GetString("version") == "1.0.0"
}

// Test WriteConfigAs
func testWriteConfigAs() bool {
	v := New()
	v.Set("app", "MyApp")
	
	err := v.WriteConfigAs("/tmp/test_config2.json")
	if err != nil {
		return false
	}
	
	// Read back
	v2 := New()
	v2.SetConfigFile("/tmp/test_config2.json")
	v2.SetConfigType("json")
	v2.ReadInConfig()
	
	// Clean up
	os.Remove("/tmp/test_config2.json")
	
	return v2.GetString("app") == "MyApp"
}

// Test SafeWriteConfig
func testSafeWriteConfig() bool {
	v := New()
	v.Set("test", "value")
	v.SetConfigFile("/tmp/safe_test.json")
	v.SetConfigType("json")
	
	// First write should succeed
	err := v.SafeWriteConfig()
	if err != nil {
		os.Remove("/tmp/safe_test.json")
		return false
	}
	
	// Second write should fail (file exists)
	err = v.SafeWriteConfig()
	shouldFail := err != nil
	
	// Clean up
	os.Remove("/tmp/safe_test.json")
	
	return shouldFail
}

// Test Unmarshal
func testUnmarshal() bool {
	v := New()
	v.Set("name", "Alice")
	v.Set("age", float64(30)) // JSON unmarshals numbers as float64
	v.Set("admin", true)
	
	type Config struct {
		Name  string  `json:"name"`
		Age   float64 `json:"age"`
		Admin bool    `json:"admin"`
	}
	
	var config Config
	err := v.Unmarshal(&config)
	if err != nil {
		fmt.Printf("Unmarshal error: %v\n", err)
		return false
	}
	
	return config.Name == "Alice" && config.Age == 30 && config.Admin == true
}

// Test UnmarshalKey
func testUnmarshalKey() bool {
	v := New()
	v.Set("database", map[string]interface{}{
		"host": "localhost",
		"port": float64(5432),
	})
	
	type Database struct {
		Host string  `json:"host"`
		Port float64 `json:"port"`
	}
	
	var db Database
	err := v.UnmarshalKey("database", &db)
	if err != nil {
		return false
	}
	
	return db.Host == "localhost" && db.Port == 5432
}

// Test Reset
func testReset() bool {
	v := New()
	v.Set("key1", "value1")
	v.Set("key2", "value2")
	v.Reset()
	return !v.IsSet("key1") && !v.IsSet("key2")
}

// Test global functions
func testGlobalFunctions() bool {
	Reset() // Clear any previous state
	Set("global_key", "global_value")
	result := GetString("global_key") == "global_value"
	Reset() // Clean up
	return result
}

// Test type conversions
func testTypeConversions() bool {
	v := New()
	
	// String to int
	v.Set("count", "42")
	if v.GetInt("count") != 42 {
		return false
	}
	
	// Float to int
	v.Set("number", 42.7)
	if v.GetInt("number") != 42 {
		return false
	}
	
	// String to bool
	v.Set("flag", "true")
	if !v.GetBool("flag") {
		return false
	}
	
	return true
}

// Test nested config
func testNestedConfig() bool {
	v := New()
	v.Set("server", map[string]interface{}{
		"host": "localhost",
		"port": 8080,
		"database": map[string]interface{}{
			"name": "mydb",
			"user": "admin",
		},
	})
	
	server := v.GetStringMap("server")
	if server["host"] != "localhost" {
		return false
	}
	
	sub := v.Sub("server")
	if sub == nil {
		return false
	}
	
	db := sub.GetStringMap("database")
	return db["name"] == "mydb"
}

// Test multiple types
func testMultipleTypes() bool {
	v := New()
	v.Set("string", "text")
	v.Set("int", 42)
	v.Set("float", 3.14)
	v.Set("bool", true)
	v.Set("slice", []string{"a", "b", "c"})
	
	return v.GetString("string") == "text" &&
		v.GetInt("int") == 42 &&
		v.GetFloat64("float") == 3.14 &&
		v.GetBool("bool") == true &&
		len(v.GetStringSlice("slice")) == 3
}

// Test config precedence
func testConfigPrecedence() bool {
	v := New()
	
	// Set default
	v.SetDefault("port", 8080)
	if v.GetInt("port") != 8080 {
		return false
	}
	
	// Set explicit value (should override default)
	v.Set("port", 3000)
	if v.GetInt("port") != 3000 {
		return false
	}
	
	// Set env var (should override config)
	os.Setenv("APP_PORT", "9000")
	defer os.Unsetenv("APP_PORT")
	v.BindEnv("port", "APP_PORT")
	if v.GetInt("port") != 9000 {
		return false
	}
	
	return true
}

// Test GetViper
func testGetViper() bool {
	v := GetViper()
	return v != nil
}

func main() {
	fmt.Println("Running Viper Emulator Tests...")
	fmt.Println("==============================")

	runTest("Set and Get", testSetAndGet)
	runTest("GetString", testGetString)
	runTest("GetInt", testGetInt)
	runTest("GetBool", testGetBool)
	runTest("GetFloat64", testGetFloat64)
	runTest("GetStringSlice", testGetStringSlice)
	runTest("GetStringMap", testGetStringMap)
	runTest("SetDefault", testSetDefault)
	runTest("Default Override", testDefaultOverride)
	runTest("IsSet", testIsSet)
	runTest("AllKeys", testAllKeys)
	runTest("AllSettings", testAllSettings)
	runTest("Sub", testSub)
	runTest("BindEnv", testBindEnv)
	runTest("Write and Read Config", testWriteAndReadConfig)
	runTest("WriteConfigAs", testWriteConfigAs)
	runTest("SafeWriteConfig", testSafeWriteConfig)
	runTest("Unmarshal", testUnmarshal)
	runTest("UnmarshalKey", testUnmarshalKey)
	runTest("Reset", testReset)
	runTest("Global Functions", testGlobalFunctions)
	runTest("Type Conversions", testTypeConversions)
	runTest("Nested Config", testNestedConfig)
	runTest("Multiple Types", testMultipleTypes)
	runTest("Config Precedence", testConfigPrecedence)
	runTest("GetViper", testGetViper)

	fmt.Println("==============================")
	fmt.Println("All tests completed!")
}
