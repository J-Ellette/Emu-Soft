// Developed by PowerShield, as an alternative to Serde

use std::collections::HashMap;
use std::fmt;

// Serializer trait - converts Rust data structures to formats
pub trait Serializer {
    type Ok;
    type Error;
    
    fn serialize_bool(self, v: bool) -> Result<Self::Ok, Self::Error>;
    fn serialize_i32(self, v: i32) -> Result<Self::Ok, Self::Error>;
    fn serialize_i64(self, v: i64) -> Result<Self::Ok, Self::Error>;
    fn serialize_f64(self, v: f64) -> Result<Self::Ok, Self::Error>;
    fn serialize_str(self, v: &str) -> Result<Self::Ok, Self::Error>;
    fn serialize_none(self) -> Result<Self::Ok, Self::Error>;
    fn serialize_some<T: Serialize>(self, value: &T) -> Result<Self::Ok, Self::Error>;
    fn serialize_seq(self, len: Option<usize>) -> Result<Self::SerializeSeq, Self::Error>;
    fn serialize_map(self, len: Option<usize>) -> Result<Self::SerializeMap, Self::Error>;
    
    type SerializeSeq: SerializeSeq<Ok = Self::Ok, Error = Self::Error>;
    type SerializeMap: SerializeMap<Ok = Self::Ok, Error = Self::Error>;
}

// SerializeSeq trait for serializing sequences
pub trait SerializeSeq {
    type Ok;
    type Error;
    
    fn serialize_element<T: Serialize>(&mut self, value: &T) -> Result<(), Self::Error>;
    fn end(self) -> Result<Self::Ok, Self::Error>;
}

// SerializeMap trait for serializing maps
pub trait SerializeMap {
    type Ok;
    type Error;
    
    fn serialize_key<T: Serialize>(&mut self, key: &T) -> Result<(), Self::Error>;
    fn serialize_value<T: Serialize>(&mut self, value: &T) -> Result<(), Self::Error>;
    fn serialize_entry<K: Serialize, V: Serialize>(&mut self, key: &K, value: &V) -> Result<(), Self::Error> {
        self.serialize_key(key)?;
        self.serialize_value(value)?;
        Ok(())
    }
    fn end(self) -> Result<Self::Ok, Self::Error>;
}

// Serialize trait - types implement this to be serializable
pub trait Serialize {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error>;
}

// Deserializer trait - converts formats to Rust data structures
pub trait Deserializer<'de> {
    type Error;
    
    fn deserialize_any<V: Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error>;
    fn deserialize_bool<V: Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error>;
    fn deserialize_i32<V: Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error>;
    fn deserialize_i64<V: Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error>;
    fn deserialize_f64<V: Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error>;
    fn deserialize_str<V: Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error>;
    fn deserialize_string<V: Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error>;
    fn deserialize_option<V: Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error>;
    fn deserialize_seq<V: Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error>;
    fn deserialize_map<V: Visitor<'de>>(self, visitor: V) -> Result<V::Value, Self::Error>;
}

// Visitor trait for deserializing
pub trait Visitor<'de>: Sized {
    type Value;
    
    fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result;
    
    fn visit_bool<E>(self, v: bool) -> Result<Self::Value, E> {
        Err(self.invalid_type("boolean"))
    }
    
    fn visit_i32<E>(self, v: i32) -> Result<Self::Value, E> {
        Err(self.invalid_type("i32"))
    }
    
    fn visit_i64<E>(self, v: i64) -> Result<Self::Value, E> {
        Err(self.invalid_type("i64"))
    }
    
    fn visit_f64<E>(self, v: f64) -> Result<Self::Value, E> {
        Err(self.invalid_type("f64"))
    }
    
    fn visit_str<E>(self, v: &str) -> Result<Self::Value, E> {
        Err(self.invalid_type("string"))
    }
    
    fn visit_string<E>(self, v: String) -> Result<Self::Value, E> {
        self.visit_str(&v)
    }
    
    fn visit_none<E>(self) -> Result<Self::Value, E> {
        Err(self.invalid_type("none"))
    }
    
    fn visit_some<D: Deserializer<'de>>(self, deserializer: D) -> Result<Self::Value, D::Error> {
        Err(self.invalid_type("some"))
    }
    
    fn visit_seq<A: SeqAccess<'de>>(self, seq: A) -> Result<Self::Value, A::Error> {
        Err(self.invalid_type("sequence"))
    }
    
    fn visit_map<A: MapAccess<'de>>(self, map: A) -> Result<Self::Value, A::Error> {
        Err(self.invalid_type("map"))
    }
    
    fn invalid_type<E>(&self, type_name: &str) -> E {
        panic!("invalid type: expected {}", type_name)
    }
}

// SeqAccess for deserializing sequences
pub trait SeqAccess<'de> {
    type Error;
    
    fn next_element<T: Deserialize<'de>>(&mut self) -> Result<Option<T>, Self::Error>;
}

// MapAccess for deserializing maps
pub trait MapAccess<'de> {
    type Error;
    
    fn next_key<K: Deserialize<'de>>(&mut self) -> Result<Option<K>, Self::Error>;
    fn next_value<V: Deserialize<'de>>(&mut self) -> Result<V, Self::Error>;
    fn next_entry<K: Deserialize<'de>, V: Deserialize<'de>>(&mut self) -> Result<Option<(K, V)>, Self::Error> {
        match self.next_key()? {
            Some(key) => {
                let value = self.next_value()?;
                Ok(Some((key, value)))
            }
            None => Ok(None),
        }
    }
}

// Deserialize trait - types implement this to be deserializable
pub trait Deserialize<'de>: Sized {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error>;
}

// Error type for serialization/deserialization
#[derive(Debug)]
pub struct Error {
    message: String,
}

impl Error {
    pub fn custom(msg: String) -> Self {
        Error { message: msg }
    }
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.message)
    }
}

impl std::error::Error for Error {}

// JSON Serializer implementation
pub struct JsonSerializer {
    output: String,
}

impl JsonSerializer {
    pub fn new() -> Self {
        JsonSerializer {
            output: String::new(),
        }
    }
}

impl Serializer for JsonSerializer {
    type Ok = String;
    type Error = Error;
    type SerializeSeq = JsonSeqSerializer;
    type SerializeMap = JsonMapSerializer;
    
    fn serialize_bool(mut self, v: bool) -> Result<String, Error> {
        self.output = v.to_string();
        Ok(self.output)
    }
    
    fn serialize_i32(mut self, v: i32) -> Result<String, Error> {
        self.output = v.to_string();
        Ok(self.output)
    }
    
    fn serialize_i64(mut self, v: i64) -> Result<String, Error> {
        self.output = v.to_string();
        Ok(self.output)
    }
    
    fn serialize_f64(mut self, v: f64) -> Result<String, Error> {
        self.output = v.to_string();
        Ok(self.output)
    }
    
    fn serialize_str(mut self, v: &str) -> Result<String, Error> {
        self.output = format!("\"{}\"", v);
        Ok(self.output)
    }
    
    fn serialize_none(mut self) -> Result<String, Error> {
        self.output = "null".to_string();
        Ok(self.output)
    }
    
    fn serialize_some<T: Serialize>(self, value: &T) -> Result<String, Error> {
        value.serialize(self)
    }
    
    fn serialize_seq(self, _len: Option<usize>) -> Result<JsonSeqSerializer, Error> {
        Ok(JsonSeqSerializer {
            output: String::from("["),
            first: true,
        })
    }
    
    fn serialize_map(self, _len: Option<usize>) -> Result<JsonMapSerializer, Error> {
        Ok(JsonMapSerializer {
            output: String::from("{"),
            first: true,
            key: None,
        })
    }
}

pub struct JsonSeqSerializer {
    output: String,
    first: bool,
}

impl SerializeSeq for JsonSeqSerializer {
    type Ok = String;
    type Error = Error;
    
    fn serialize_element<T: Serialize>(&mut self, value: &T) -> Result<(), Error> {
        if !self.first {
            self.output.push_str(", ");
        }
        self.first = false;
        
        let serialized = to_json(value)?;
        self.output.push_str(&serialized);
        Ok(())
    }
    
    fn end(mut self) -> Result<String, Error> {
        self.output.push(']');
        Ok(self.output)
    }
}

pub struct JsonMapSerializer {
    output: String,
    first: bool,
    key: Option<String>,
}

impl SerializeMap for JsonMapSerializer {
    type Ok = String;
    type Error = Error;
    
    fn serialize_key<T: Serialize>(&mut self, key: &T) -> Result<(), Error> {
        if !self.first {
            self.output.push_str(", ");
        }
        self.first = false;
        
        let serialized = to_json(key)?;
        self.key = Some(serialized);
        Ok(())
    }
    
    fn serialize_value<T: Serialize>(&mut self, value: &T) -> Result<(), Error> {
        if let Some(key) = self.key.take() {
            self.output.push_str(&key);
            self.output.push_str(": ");
            let serialized = to_json(value)?;
            self.output.push_str(&serialized);
        }
        Ok(())
    }
    
    fn end(mut self) -> Result<String, Error> {
        self.output.push('}');
        Ok(self.output)
    }
}

// Helper function to serialize to JSON
pub fn to_json<T: Serialize>(value: &T) -> Result<String, Error> {
    value.serialize(JsonSerializer::new())
}

// Implement Serialize for common types
impl Serialize for bool {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        serializer.serialize_bool(*self)
    }
}

impl Serialize for i32 {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        serializer.serialize_i32(*self)
    }
}

impl Serialize for i64 {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        serializer.serialize_i64(*self)
    }
}

impl Serialize for f64 {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        serializer.serialize_f64(*self)
    }
}

impl Serialize for str {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        serializer.serialize_str(self)
    }
}

impl Serialize for String {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        serializer.serialize_str(self)
    }
}

impl<T: Serialize> Serialize for Option<T> {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        match self {
            Some(value) => serializer.serialize_some(value),
            None => serializer.serialize_none(),
        }
    }
}

impl<T: Serialize> Serialize for Vec<T> {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        let mut seq = serializer.serialize_seq(Some(self.len()))?;
        for element in self {
            seq.serialize_element(element)?;
        }
        seq.end()
    }
}

impl<K: Serialize, V: Serialize> Serialize for HashMap<K, V> {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        let mut map = serializer.serialize_map(Some(self.len()))?;
        for (key, value) in self {
            map.serialize_entry(key, value)?;
        }
        map.end()
    }
}

// Macro for deriving Serialize
#[macro_export]
macro_rules! derive_serialize {
    ($name:ident { $($field:ident),* }) => {
        impl Serialize for $name {
            fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
                let mut map = serializer.serialize_map(None)?;
                $(
                    map.serialize_entry(&stringify!($field).to_string(), &self.$field)?;
                )*
                map.end()
            }
        }
    };
}

// Example struct using the derive macro
pub struct Person {
    pub name: String,
    pub age: i32,
    pub email: String,
}

derive_serialize!(Person { name, age, email });

pub struct Point {
    pub x: i32,
    pub y: i32,
}

derive_serialize!(Point { x, y });

fn main() {
    println!("Serde Emulator - Serialization Framework");
    println!("=========================================\n");
    
    // Test basic types
    println!("=== Basic Types ===");
    println!("bool: {}", to_json(&true).unwrap());
    println!("i32: {}", to_json(&42).unwrap());
    println!("i64: {}", to_json(&9223372036854775807i64).unwrap());
    println!("f64: {}", to_json(&3.14159).unwrap());
    println!("string: {}", to_json(&"Hello, Serde!".to_string()).unwrap());
    println!();
    
    // Test Option
    println!("=== Option ===");
    let some_value: Option<i32> = Some(42);
    let none_value: Option<i32> = None;
    println!("Some: {}", to_json(&some_value).unwrap());
    println!("None: {}", to_json(&none_value).unwrap());
    println!();
    
    // Test Vec
    println!("=== Vec ===");
    let numbers = vec![1, 2, 3, 4, 5];
    println!("Vec<i32>: {}", to_json(&numbers).unwrap());
    
    let strings = vec!["apple".to_string(), "banana".to_string(), "cherry".to_string()];
    println!("Vec<String>: {}", to_json(&strings).unwrap());
    println!();
    
    // Test HashMap
    println!("=== HashMap ===");
    let mut scores = HashMap::new();
    scores.insert("Alice".to_string(), 95);
    scores.insert("Bob".to_string(), 87);
    println!("HashMap: {}", to_json(&scores).unwrap());
    println!();
    
    // Test nested structures
    println!("=== Nested Structures ===");
    let nested_vec = vec![vec![1, 2], vec![3, 4], vec![5, 6]];
    println!("Vec<Vec<i32>>: {}", to_json(&nested_vec).unwrap());
    println!();
    
    // Test struct
    println!("=== Structs ===");
    let person = Person {
        name: "Alice".to_string(),
        age: 30,
        email: "alice@example.com".to_string(),
    };
    println!("Person: {}", to_json(&person).unwrap());
    
    let point = Point { x: 10, y: 20 };
    println!("Point: {}", to_json(&point).unwrap());
    println!();
    
    println!("✓ Serde emulator demonstration complete");
}
