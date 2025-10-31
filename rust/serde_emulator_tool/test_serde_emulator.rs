#[path = "serde_emulator.rs"]
mod serde_emulator;

use serde_emulator::*;
use std::collections::HashMap;

struct TestResult {
    name: String,
    passed: bool,
    error: Option<String>,
}

fn test_runner<F>(name: &str, test_fn: F) -> TestResult
where
    F: FnOnce() -> Result<(), String>,
{
    match test_fn() {
        Ok(_) => TestResult {
            name: name.to_string(),
            passed: true,
            error: None,
        },
        Err(e) => TestResult {
            name: name.to_string(),
            passed: false,
            error: Some(e),
        },
    }
}

fn main() {
    println!("Running Serde Emulator Tests");
    println!("============================\n");
    
    let mut results = Vec::new();
    
    // Test 1: Serialize bool
    results.push(test_runner("Serialize bool", || {
        let result = to_json(&true).map_err(|e| e.to_string())?;
        if result == "true" {
            Ok(())
        } else {
            Err(format!("Expected 'true', got '{}'", result))
        }
    }));
    
    // Test 2: Serialize i32
    results.push(test_runner("Serialize i32", || {
        let result = to_json(&42).map_err(|e| e.to_string())?;
        if result == "42" {
            Ok(())
        } else {
            Err(format!("Expected '42', got '{}'", result))
        }
    }));
    
    // Test 3: Serialize i64
    results.push(test_runner("Serialize i64", || {
        let result = to_json(&9223372036854775807i64).map_err(|e| e.to_string())?;
        if result == "9223372036854775807" {
            Ok(())
        } else {
            Err(format!("Expected '9223372036854775807', got '{}'", result))
        }
    }));
    
    // Test 4: Serialize f64
    results.push(test_runner("Serialize f64", || {
        let result = to_json(&3.14).map_err(|e| e.to_string())?;
        if result.starts_with("3.14") {
            Ok(())
        } else {
            Err(format!("Expected value starting with '3.14', got '{}'", result))
        }
    }));
    
    // Test 5: Serialize string
    results.push(test_runner("Serialize string", || {
        let result = to_json(&"Hello".to_string()).map_err(|e| e.to_string())?;
        if result == "\"Hello\"" {
            Ok(())
        } else {
            Err(format!("Expected '\"Hello\"', got '{}'", result))
        }
    }));
    
    // Test 6: Serialize String
    results.push(test_runner("Serialize String", || {
        let s = String::from("World");
        let result = to_json(&s).map_err(|e| e.to_string())?;
        if result == "\"World\"" {
            Ok(())
        } else {
            Err(format!("Expected '\"World\"', got '{}'", result))
        }
    }));
    
    // Test 7: Serialize Some
    results.push(test_runner("Serialize Some", || {
        let opt: Option<i32> = Some(42);
        let result = to_json(&opt).map_err(|e| e.to_string())?;
        if result == "42" {
            Ok(())
        } else {
            Err(format!("Expected '42', got '{}'", result))
        }
    }));
    
    // Test 8: Serialize None
    results.push(test_runner("Serialize None", || {
        let opt: Option<i32> = None;
        let result = to_json(&opt).map_err(|e| e.to_string())?;
        if result == "null" {
            Ok(())
        } else {
            Err(format!("Expected 'null', got '{}'", result))
        }
    }));
    
    // Test 9: Serialize Vec of integers
    results.push(test_runner("Serialize Vec<i32>", || {
        let vec = vec![1, 2, 3, 4, 5];
        let result = to_json(&vec).map_err(|e| e.to_string())?;
        if result == "[1, 2, 3, 4, 5]" {
            Ok(())
        } else {
            Err(format!("Expected '[1, 2, 3, 4, 5]', got '{}'", result))
        }
    }));
    
    // Test 10: Serialize Vec of strings
    results.push(test_runner("Serialize Vec<String>", || {
        let vec = vec!["a".to_string(), "b".to_string(), "c".to_string()];
        let result = to_json(&vec).map_err(|e| e.to_string())?;
        if result == "[\"a\", \"b\", \"c\"]" {
            Ok(())
        } else {
            Err(format!("Expected '[\"a\", \"b\", \"c\"]', got '{}'", result))
        }
    }));
    
    // Test 11: Serialize empty Vec
    results.push(test_runner("Serialize empty Vec", || {
        let vec: Vec<i32> = vec![];
        let result = to_json(&vec).map_err(|e| e.to_string())?;
        if result == "[]" {
            Ok(())
        } else {
            Err(format!("Expected '[]', got '{}'", result))
        }
    }));
    
    // Test 12: Serialize HashMap
    results.push(test_runner("Serialize HashMap", || {
        let mut map = HashMap::new();
        map.insert("key1".to_string(), 100);
        map.insert("key2".to_string(), 200);
        let result = to_json(&map).map_err(|e| e.to_string())?;
        // HashMap order is not guaranteed, so check both possible orders
        let valid = result == "{\"key1\": 100, \"key2\": 200}" || 
                    result == "{\"key2\": 200, \"key1\": 100}";
        if valid {
            Ok(())
        } else {
            Err(format!("Invalid HashMap serialization: '{}'", result))
        }
    }));
    
    // Test 13: Serialize empty HashMap
    results.push(test_runner("Serialize empty HashMap", || {
        let map: HashMap<String, i32> = HashMap::new();
        let result = to_json(&map).map_err(|e| e.to_string())?;
        if result == "{}" {
            Ok(())
        } else {
            Err(format!("Expected '{{}}', got '{}'", result))
        }
    }));
    
    // Test 14: Serialize nested Vec
    results.push(test_runner("Serialize nested Vec", || {
        let vec = vec![vec![1, 2], vec![3, 4]];
        let result = to_json(&vec).map_err(|e| e.to_string())?;
        if result == "[[1, 2], [3, 4]]" {
            Ok(())
        } else {
            Err(format!("Expected '[[1, 2], [3, 4]]', got '{}'", result))
        }
    }));
    
    // Test 15: Serialize Person struct
    results.push(test_runner("Serialize Person struct", || {
        let person = Person {
            name: "Alice".to_string(),
            age: 30,
            email: "alice@example.com".to_string(),
        };
        let result = to_json(&person).map_err(|e| e.to_string())?;
        // Check that all fields are present
        let has_name = result.contains("\"name\": \"Alice\"");
        let has_age = result.contains("\"age\": 30");
        let has_email = result.contains("\"email\": \"alice@example.com\"");
        
        if has_name && has_age && has_email {
            Ok(())
        } else {
            Err(format!("Missing fields in Person serialization: '{}'", result))
        }
    }));
    
    // Test 16: Serialize Point struct
    results.push(test_runner("Serialize Point struct", || {
        let point = Point { x: 10, y: 20 };
        let result = to_json(&point).map_err(|e| e.to_string())?;
        let has_x = result.contains("\"x\": 10");
        let has_y = result.contains("\"y\": 20");
        
        if has_x && has_y {
            Ok(())
        } else {
            Err(format!("Missing fields in Point serialization: '{}'", result))
        }
    }));
    
    // Test 17: Serialize Vec of Options
    results.push(test_runner("Serialize Vec<Option<i32>>", || {
        let vec = vec![Some(1), None, Some(3)];
        let result = to_json(&vec).map_err(|e| e.to_string())?;
        if result == "[1, null, 3]" {
            Ok(())
        } else {
            Err(format!("Expected '[1, null, 3]', got '{}'", result))
        }
    }));
    
    // Test 18: Serialize HashMap with string values
    results.push(test_runner("Serialize HashMap<String, String>", || {
        let mut map = HashMap::new();
        map.insert("first".to_string(), "Alice".to_string());
        map.insert("last".to_string(), "Smith".to_string());
        let result = to_json(&map).map_err(|e| e.to_string())?;
        let has_first = result.contains("\"first\": \"Alice\"");
        let has_last = result.contains("\"last\": \"Smith\"");
        
        if has_first && has_last {
            Ok(())
        } else {
            Err(format!("Missing fields in HashMap serialization: '{}'", result))
        }
    }));
    
    // Test 19: Serialize negative numbers
    results.push(test_runner("Serialize negative numbers", || {
        let result = to_json(&-42).map_err(|e| e.to_string())?;
        if result == "-42" {
            Ok(())
        } else {
            Err(format!("Expected '-42', got '{}'", result))
        }
    }));
    
    // Test 20: Serialize zero
    results.push(test_runner("Serialize zero", || {
        let result = to_json(&0).map_err(|e| e.to_string())?;
        if result == "0" {
            Ok(())
        } else {
            Err(format!("Expected '0', got '{}'", result))
        }
    }));
    
    // Print results
    println!("\n=== Test Results ===");
    let mut passed = 0;
    for result in &results {
        if result.passed {
            println!("✓ {}", result.name);
            passed += 1;
        } else {
            println!("✗ {}: {}", result.name, result.error.as_ref().unwrap());
        }
    }
    
    println!("\nPassed: {}/{}", passed, results.len());
}
