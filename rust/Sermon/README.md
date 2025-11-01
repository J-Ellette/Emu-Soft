# Serde Emulator - Serialization Framework for Rust

**Developed by PowerShield, as an alternative to Serde**


This module emulates **Serde**, which is Rust's most widely-used serialization/deserialization framework. Serde provides a powerful, efficient, and generic way to convert Rust data structures to and from different formats like JSON, YAML, TOML, etc.

## What is Serde?

Serde is a framework for serializing and deserializing Rust data structures efficiently and generically. It:
- **Serializes**: Converts Rust data structures to various formats (JSON, YAML, MessagePack, etc.)
- **Deserializes**: Converts data from formats back into Rust data structures
- **Zero-cost abstraction**: Compile-time code generation with no runtime overhead
- **Type-safe**: Leverages Rust's type system for correctness
- **Generic**: Works with any data format through traits
- **Derive macros**: Automatic implementation for custom types

## Features

This emulator implements core Serde functionality:

### Serialization
- **Basic Types**: bool, integers (i32, i64), floats (f64), strings
- **Compound Types**: Vec, HashMap, Option
- **Custom Structs**: Serializable custom data structures
- **Nested Structures**: Support for nested collections and types

### Traits
- **Serialize Trait**: Types implement this to be serializable
- **Serializer Trait**: Formats implement this to serialize data
- **SerializeSeq**: For serializing sequences (arrays, vectors)
- **SerializeMap**: For serializing key-value pairs (maps, structs)

### JSON Serialization
- **JSON Serializer**: Converts Rust types to JSON strings
- **Proper Formatting**: Handles quotes, brackets, commas
- **Type Support**: Full support for all basic and compound types

### Macros
- **derive_serialize!**: Macro for automatically implementing Serialize for structs

## Usage Examples

### Serializing Basic Types

```rust
use serde_emulator::*;

fn main() {
    // Serialize bool
    let json = to_json(&true).unwrap();
    println!("{}", json); // true
    
    // Serialize integer
    let json = to_json(&42).unwrap();
    println!("{}", json); // 42
    
    // Serialize float
    let json = to_json(&3.14159).unwrap();
    println!("{}", json); // 3.14159
    
    // Serialize string
    let json = to_json(&"Hello, World!").unwrap();
    println!("{}", json); // "Hello, World!"
}
```

### Serializing Option Types

```rust
use serde_emulator::*;

fn main() {
    // Some value
    let some_value: Option<i32> = Some(42);
    let json = to_json(&some_value).unwrap();
    println!("{}", json); // 42
    
    // None value
    let none_value: Option<i32> = None;
    let json = to_json(&none_value).unwrap();
    println!("{}", json); // null
}
```

### Serializing Vectors

```rust
use serde_emulator::*;

fn main() {
    // Vector of integers
    let numbers = vec![1, 2, 3, 4, 5];
    let json = to_json(&numbers).unwrap();
    println!("{}", json); // [1, 2, 3, 4, 5]
    
    // Vector of strings
    let fruits = vec!["apple", "banana", "cherry"];
    let json = to_json(&fruits).unwrap();
    println!("{}", json); // ["apple", "banana", "cherry"]
    
    // Empty vector
    let empty: Vec<i32> = vec![];
    let json = to_json(&empty).unwrap();
    println!("{}", json); // []
}
```

### Serializing HashMaps

```rust
use serde_emulator::*;
use std::collections::HashMap;

fn main() {
    let mut scores = HashMap::new();
    scores.insert("Alice", 95);
    scores.insert("Bob", 87);
    scores.insert("Charlie", 92);
    
    let json = to_json(&scores).unwrap();
    println!("{}", json);
    // {"Alice": 95, "Bob": 87, "Charlie": 92}
}
```

### Serializing Custom Structs

```rust
use serde_emulator::*;

pub struct Person {
    pub name: String,
    pub age: i32,
    pub email: String,
}

// Use the derive macro to implement Serialize
derive_serialize!(Person { name, age, email });

fn main() {
    let person = Person {
        name: "Alice".to_string(),
        age: 30,
        email: "alice@example.com".to_string(),
    };
    
    let json = to_json(&person).unwrap();
    println!("{}", json);
    // {"name": "Alice", "age": 30, "email": "alice@example.com"}
}
```

### Nested Structures

```rust
use serde_emulator::*;

fn main() {
    // Nested vectors
    let matrix = vec![
        vec![1, 2, 3],
        vec![4, 5, 6],
        vec![7, 8, 9],
    ];
    
    let json = to_json(&matrix).unwrap();
    println!("{}", json);
    // [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
}
```

### Multiple Structs Example

```rust
use serde_emulator::*;

pub struct Point {
    pub x: i32,
    pub y: i32,
}

derive_serialize!(Point { x, y });

pub struct User {
    pub id: i32,
    pub username: String,
    pub active: bool,
}

derive_serialize!(User { id, username, active });

fn main() {
    let point = Point { x: 10, y: 20 };
    println!("Point: {}", to_json(&point).unwrap());
    // Point: {"x": 10, "y": 20}
    
    let user = User {
        id: 1,
        username: "alice".to_string(),
        active: true,
    };
    println!("User: {}", to_json(&user).unwrap());
    // User: {"id": 1, "username": "alice", "active": true}
}
```

### Implementing Serialize Manually

```rust
use serde_emulator::*;

pub struct CustomType {
    pub value: i32,
}

impl Serialize for CustomType {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        let mut map = serializer.serialize_map(Some(1))?;
        map.serialize_entry(&"value", &self.value)?;
        map.end()
    }
}

fn main() {
    let custom = CustomType { value: 42 };
    let json = to_json(&custom).unwrap();
    println!("{}", json); // {"value": 42}
}
```

### Working with Serializers

```rust
use serde_emulator::*;

fn serialize_custom<S: Serializer>(value: &i32, serializer: S) -> Result<S::Ok, S::Error> {
    serializer.serialize_i32(*value)
}

fn main() {
    let value = 42;
    let json = to_json(&value).unwrap();
    println!("{}", json); // 42
}
```

### Complex Data Structures

```rust
use serde_emulator::*;
use std::collections::HashMap;

fn main() {
    // Vector of HashMaps
    let mut data = Vec::new();
    
    let mut item1 = HashMap::new();
    item1.insert("name".to_string(), "Item 1".to_string());
    item1.insert("type".to_string(), "A".to_string());
    
    let mut item2 = HashMap::new();
    item2.insert("name".to_string(), "Item 2".to_string());
    item2.insert("type".to_string(), "B".to_string());
    
    data.push(item1);
    data.push(item2);
    
    let json = to_json(&data).unwrap();
    println!("{}", json);
}
```

### Optional Fields Pattern

```rust
use serde_emulator::*;

pub struct Config {
    pub host: String,
    pub port: Option<i32>,
}

derive_serialize!(Config { host, port });

fn main() {
    // With port
    let config1 = Config {
        host: "localhost".to_string(),
        port: Some(8080),
    };
    println!("Config with port: {}", to_json(&config1).unwrap());
    
    // Without port (null)
    let config2 = Config {
        host: "localhost".to_string(),
        port: None,
    };
    println!("Config without port: {}", to_json(&config2).unwrap());
}
```

## Testing

Run the comprehensive test suite:

```bash
cargo run --bin test
```

Or directly with rustc:

```bash
rustc test_serde_emulator.rs && ./test_serde_emulator
```

Tests cover:
- Serialization of basic types (bool, integers, floats, strings)
- Option types (Some, None)
- Vec serialization (integers, strings, nested)
- HashMap serialization
- Custom struct serialization
- Nested data structures
- Edge cases (empty collections, negative numbers, zero)

Total: 20 tests

## Integration with Existing Code

This emulator demonstrates Serde patterns:

```rust
// Define your data structure
pub struct MyData {
    pub field1: String,
    pub field2: i32,
}

// Implement Serialize
derive_serialize!(MyData { field1, field2 });

// Use it
fn main() {
    let data = MyData {
        field1: "value".to_string(),
        field2: 42,
    };
    
    let json = to_json(&data).unwrap();
    println!("{}", json);
}
```

## Use Cases

Perfect for:
- **Data Serialization**: Convert Rust types to JSON
- **API Development**: Serialize response data
- **Configuration Files**: Export settings to JSON
- **Data Exchange**: Share data between systems
- **Learning Serde**: Understand serialization patterns
- **Testing**: Test serialization logic without dependencies

## Limitations

This is an emulator for development and testing purposes:
- Only JSON serialization (no YAML, TOML, MessagePack, etc.)
- No deserialization implementation
- Simplified derive macro (not a proc macro)
- No support for enums with variants
- No field attributes (rename, skip, etc.)
- No custom serialization formats
- No zero-copy deserialization
- HashMap order not guaranteed in output
- No support for borrowed data in serialization

## Supported Features

### Serialization
- ✅ Basic types (bool, i32, i64, f64, str, String)
- ✅ Option<T>
- ✅ Vec<T>
- ✅ HashMap<K, V>
- ✅ Custom structs
- ✅ Nested structures
- ✅ Manual Serialize implementation
- ✅ derive_serialize! macro

### Traits
- ✅ Serialize trait
- ✅ Serializer trait
- ✅ SerializeSeq trait
- ✅ SerializeMap trait
- ✅ Error handling

### Formats
- ✅ JSON serialization
- ❌ Deserialization (not implemented)
- ❌ Other formats (YAML, TOML, etc.)

## Real-World Serialization Concepts

This emulator teaches the following concepts:

1. **Trait-based Design**: Generic serialization through traits
2. **Visitor Pattern**: Type-driven serialization/deserialization
3. **Zero-cost Abstractions**: Compile-time polymorphism
4. **Type Safety**: Leveraging Rust's type system
5. **Separation of Concerns**: Data format independent of data structure
6. **Composability**: Build complex serializers from simple ones
7. **Error Handling**: Proper error propagation
8. **Generic Programming**: Working with generic types

## Compatibility

Emulates core concepts of:
- Serde 1.x trait design
- JSON serialization patterns
- Rust serialization best practices

## License

Part of the Emu-Soft project. See main repository LICENSE.
