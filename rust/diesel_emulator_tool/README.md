# Diesel Emulator - ORM and Query Builder for Rust

This module emulates **Diesel**, a safe, extensible ORM (Object-Relational Mapping) and Query Builder for Rust. Diesel provides a type-safe way to interact with databases, preventing common errors at compile time.

## What is Diesel?

Diesel is a powerful ORM and query builder for Rust that provides:
- **Type-safe SQL queries** - Catch SQL errors at compile time
- **Query builder pattern** - Construct queries programmatically
- **Connection pooling** - Efficient database connection management
- **Migration system** - Database schema version control
- **Multiple database support** - PostgreSQL, MySQL, and SQLite
- **Raw SQL support** - Execute custom SQL when needed

Key features:
- Zero-cost abstractions for database operations
- Composable query building
- Automatic query generation
- Safe, compile-time verified queries
- No runtime overhead

## Features

This emulator implements core Diesel functionality:

### Connection Management
- **PostgreSQL connections** - Connect to PostgreSQL databases
- **MySQL connections** - Connect to MySQL databases
- **SQLite connections** - Connect to SQLite databases
- **Transaction support** - Begin, commit, and rollback transactions
- **Raw SQL execution** - Execute arbitrary SQL statements

### Query Builder
- **SELECT queries** - Flexible query construction with filters, ordering, limits
- **INSERT queries** - Insert records into tables
- **UPDATE queries** - Update existing records
- **DELETE queries** - Delete records from tables
- **Method chaining** - Build complex queries fluently

### Schema Management
- **Migrations** - Create and manage database schema changes
- **Table creation** - Define tables with columns and types
- **Column operations** - Add and remove columns
- **Table operations** - Create and drop tables

### Data Types
- **Integer values** - i32 integers
- **BigInt values** - i64 large integers
- **Text values** - String data
- **Float values** - f64 floating point numbers
- **Boolean values** - true/false values
- **NULL values** - Represent missing data

## Usage Examples

### Establishing Connections

```rust
use diesel_emulator::Connection;

// PostgreSQL connection
let pg_conn = Connection::establish_postgres(
    "postgres://user:password@localhost/mydb"
).expect("Failed to connect to PostgreSQL");

// MySQL connection
let mysql_conn = Connection::establish_mysql(
    "mysql://root:password@localhost/mydb"
).expect("Failed to connect to MySQL");

// SQLite connection (in-memory)
let sqlite_conn = Connection::establish_sqlite(":memory:")
    .expect("Failed to connect to SQLite");

// SQLite connection (file)
let file_conn = Connection::establish_sqlite("./mydb.sqlite")
    .expect("Failed to connect to SQLite file");
```

### SELECT Queries

#### Basic SELECT

```rust
use diesel_emulator::{Connection, SelectQuery};

let conn = Connection::establish_sqlite(":memory:").unwrap();

// Simple select all
let query = SelectQuery::new("users");
let results = query.load(&conn).unwrap();

for row in results {
    println!("User: {:?}", row);
}
```

#### SELECT with Columns

```rust
use diesel_emulator::SelectQuery;

let query = SelectQuery::new("users")
    .select(vec!["id", "name", "email"]);

let sql = query.to_sql();
// Output: SELECT id, name, email FROM users
```

#### SELECT with WHERE Clause

```rust
use diesel_emulator::SelectQuery;

let query = SelectQuery::new("users")
    .select(vec!["name", "email"])
    .filter("age >= 18");

let sql = query.to_sql();
// Output: SELECT name, email FROM users WHERE age >= 18
```

#### SELECT with ORDER BY

```rust
use diesel_emulator::SelectQuery;

let query = SelectQuery::new("posts")
    .select(vec!["title", "created_at"])
    .filter("published = true")
    .order_by("created_at", "DESC")
    .limit(10);

let sql = query.to_sql();
// Output: SELECT title, created_at FROM posts 
//         WHERE published = true ORDER BY created_at DESC LIMIT 10
```

#### SELECT with LIMIT and OFFSET (Pagination)

```rust
use diesel_emulator::SelectQuery;

let page = 2;
let per_page = 20;

let query = SelectQuery::new("products")
    .order_by("name", "ASC")
    .limit(per_page)
    .offset((page - 1) * per_page);

let results = query.load(&conn).unwrap();
```

#### Get First Result

```rust
use diesel_emulator::SelectQuery;

let query = SelectQuery::new("users")
    .filter("email = 'user@example.com'");

let user = query.first(&conn).unwrap();
match user {
    Some(row) => println!("Found user: {:?}", row),
    None => println!("User not found"),
}
```

### INSERT Queries

#### Basic INSERT

```rust
use diesel_emulator::{Connection, InsertQuery, Value};

let conn = Connection::establish_sqlite(":memory:").unwrap();

let result = InsertQuery::new("users")
    .value("name", Value::Text("Alice".to_string()))
    .value("email", Value::Text("alice@example.com".to_string()))
    .value("age", Value::Integer(30))
    .execute(&conn);

println!("Inserted {} row(s)", result.unwrap());
```

#### INSERT Multiple Values

```rust
use diesel_emulator::{InsertQuery, Value};

let query = InsertQuery::new("posts")
    .value("title", Value::Text("My First Post".to_string()))
    .value("content", Value::Text("Hello, world!".to_string()))
    .value("author_id", Value::Integer(1))
    .value("published", Value::Boolean(true));

let affected = query.execute(&conn).unwrap();
```

### UPDATE Queries

#### Basic UPDATE

```rust
use diesel_emulator::{Connection, UpdateQuery, Value};

let conn = Connection::establish_sqlite(":memory:").unwrap();

let result = UpdateQuery::new("users")
    .set("email", Value::Text("newemail@example.com".to_string()))
    .filter("id = 1")
    .execute(&conn);

println!("Updated {} row(s)", result.unwrap());
```

#### UPDATE Multiple Columns

```rust
use diesel_emulator::{UpdateQuery, Value};

let query = UpdateQuery::new("posts")
    .set("title", Value::Text("Updated Title".to_string()))
    .set("content", Value::Text("Updated content".to_string()))
    .set("updated_at", Value::Text("2024-01-15T10:30:00Z".to_string()))
    .filter("id = 5");

let sql = query.to_sql();
// Output: UPDATE posts SET title = Updated Title, content = Updated content, 
//         updated_at = 2024-01-15T10:30:00Z WHERE id = 5
```

#### Conditional UPDATE

```rust
use diesel_emulator::{UpdateQuery, Value};

// Activate all users who verified their email
let result = UpdateQuery::new("users")
    .set("status", Value::Text("active".to_string()))
    .filter("email_verified = true AND status = 'pending'")
    .execute(&conn)
    .unwrap();
```

### DELETE Queries

#### Basic DELETE

```rust
use diesel_emulator::{Connection, DeleteQuery};

let conn = Connection::establish_sqlite(":memory:").unwrap();

let result = DeleteQuery::new("users")
    .filter("id = 1")
    .execute(&conn);

println!("Deleted {} row(s)", result.unwrap());
```

#### DELETE with Complex Filter

```rust
use diesel_emulator::DeleteQuery;

// Delete old, inactive sessions
let query = DeleteQuery::new("sessions")
    .filter("last_active < '2024-01-01' AND user_id IS NULL");

let deleted = query.execute(&conn).unwrap();
println!("Cleaned up {} old sessions", deleted);
```

#### DELETE All Rows

```rust
use diesel_emulator::DeleteQuery;

// Clear all data from a table (use with caution!)
let query = DeleteQuery::new("temp_data");
let result = query.execute(&conn).unwrap();
```

### Transactions

#### Basic Transaction

```rust
use diesel_emulator::{Connection, InsertQuery, Value};

let conn = Connection::establish_postgres("postgres://localhost/mydb").unwrap();

let transaction = conn.begin_transaction().unwrap();

// Perform operations...
InsertQuery::new("users")
    .value("name", Value::Text("Bob".to_string()))
    .execute(&conn)
    .unwrap();

// Commit transaction
transaction.commit().unwrap();
```

#### Transaction with Rollback

```rust
use diesel_emulator::Connection;

let conn = Connection::establish_sqlite(":memory:").unwrap();

let transaction = conn.begin_transaction().unwrap();

// Perform some operations...

// If something goes wrong, rollback
if some_error_condition {
    transaction.rollback().unwrap();
} else {
    transaction.commit().unwrap();
}
```

### Schema Migrations

#### Creating Tables

```rust
use diesel_emulator::{Connection, Migration};

let conn = Connection::establish_sqlite(":memory:").unwrap();

let migration = Migration::new()
    .create_table("users", vec![
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("name", "TEXT NOT NULL"),
        ("email", "TEXT UNIQUE NOT NULL"),
        ("age", "INTEGER"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ]);

migration.run(&conn).unwrap();
```

#### Adding Columns

```rust
use diesel_emulator::Migration;

let migration = Migration::new()
    .add_column("users", "phone", "VARCHAR(20)")
    .add_column("users", "address", "TEXT");

migration.run(&conn).unwrap();
```

#### Removing Columns

```rust
use diesel_emulator::Migration;

let migration = Migration::new()
    .remove_column("users", "deprecated_field");

migration.run(&conn).unwrap();
```

#### Complex Migration

```rust
use diesel_emulator::Migration;

let migration = Migration::new()
    // Create new table
    .create_table("posts", vec![
        ("id", "INTEGER PRIMARY KEY"),
        ("title", "TEXT NOT NULL"),
        ("content", "TEXT"),
        ("author_id", "INTEGER"),
    ])
    // Add foreign key column to users
    .add_column("users", "role_id", "INTEGER")
    // Remove old table
    .drop_table("legacy_data");

migration.run(&conn).unwrap();
```

### Table DSL (Domain-Specific Language)

#### Using Table Interface

```rust
use diesel_emulator::{Connection, Table, Value};

let conn = Connection::establish_sqlite(":memory:").unwrap();
let users = Table::new("users");

// SELECT
let results = users.select()
    .filter("age > 18")
    .order_by("name", "ASC")
    .limit(10)
    .load(&conn)
    .unwrap();

// INSERT
users.insert()
    .value("name", Value::Text("Charlie".to_string()))
    .value("age", Value::Integer(25))
    .execute(&conn)
    .unwrap();

// UPDATE
users.update()
    .set("status", Value::Text("active".to_string()))
    .filter("id = 1")
    .execute(&conn)
    .unwrap();

// DELETE
users.delete()
    .filter("last_login < '2023-01-01'")
    .execute(&conn)
    .unwrap();

// COUNT
let total = users.count(&conn).unwrap();
println!("Total users: {}", total);
```

### Complete CRUD Example

```rust
use diesel_emulator::{Connection, Table, Value, Migration};

fn main() {
    // Setup
    let conn = Connection::establish_sqlite(":memory:").unwrap();
    
    // Create schema
    Migration::new()
        .create_table("products", vec![
            ("id", "INTEGER PRIMARY KEY"),
            ("name", "TEXT NOT NULL"),
            ("price", "REAL"),
            ("stock", "INTEGER"),
        ])
        .run(&conn)
        .unwrap();
    
    let products = Table::new("products");
    
    // CREATE
    products.insert()
        .value("name", Value::Text("Laptop".to_string()))
        .value("price", Value::Float(999.99))
        .value("stock", Value::Integer(10))
        .execute(&conn)
        .unwrap();
    
    products.insert()
        .value("name", Value::Text("Mouse".to_string()))
        .value("price", Value::Float(29.99))
        .value("stock", Value::Integer(50))
        .execute(&conn)
        .unwrap();
    
    // READ
    let all_products = products.select().load(&conn).unwrap();
    println!("All products: {:?}", all_products);
    
    let expensive = products.select()
        .filter("price > 100")
        .load(&conn)
        .unwrap();
    println!("Expensive products: {:?}", expensive);
    
    // UPDATE
    products.update()
        .set("stock", Value::Integer(8))
        .filter("name = 'Laptop'")
        .execute(&conn)
        .unwrap();
    
    // DELETE
    products.delete()
        .filter("stock = 0")
        .execute(&conn)
        .unwrap();
    
    // COUNT
    let total = products.count(&conn).unwrap();
    println!("Total products: {}", total);
}
```

### Working with Raw SQL

```rust
use diesel_emulator::Connection;

let conn = Connection::establish_postgres("postgres://localhost/mydb").unwrap();

// Execute raw SQL
conn.execute("CREATE INDEX idx_users_email ON users(email)").unwrap();
conn.execute("VACUUM ANALYZE users").unwrap();
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
cargo test

# Run with output
cargo test -- --nocapture

# Run specific test
cargo test test_select_query_builder
```

The test suite covers:
- Connection establishment for all database types
- Query builder operations (SELECT, INSERT, UPDATE, DELETE)
- Transaction management (commit and rollback)
- Migration operations
- Table DSL usage
- Value types and display
- Complex query chains
- Full CRUD cycles

## Use Cases

Perfect for:
- **Database-driven applications** - Build applications with database backends
- **REST APIs** - Create API servers with database persistence
- **Data processing** - Process and transform database data
- **Testing** - Test database code without actual database
- **Learning** - Learn Diesel patterns and ORM concepts
- **Prototyping** - Quickly prototype database schemas

## Limitations

This is an emulator for development and learning:
- In-memory storage only (data not persisted)
- Simplified query execution (no actual SQL parsing)
- Limited type checking compared to real Diesel
- Doesn't connect to real databases
- Subset of Diesel's full feature set

## Supported Operations

### Connection Operations
- ✅ establish_postgres
- ✅ establish_mysql
- ✅ establish_sqlite
- ✅ execute (raw SQL)
- ✅ begin_transaction

### Query Operations
- ✅ SELECT with columns, filters, ordering, limits, offsets
- ✅ INSERT with multiple values
- ✅ UPDATE with multiple columns and filters
- ✅ DELETE with filters
- ✅ Query builder pattern with method chaining
- ✅ first() to get single result

### Schema Operations
- ✅ create_table with columns and types
- ✅ drop_table
- ✅ add_column
- ✅ remove_column
- ✅ Migration runner

### Table DSL
- ✅ Table interface for all CRUD operations
- ✅ count() for row counting

## Compatibility

Emulates patterns from:
- Diesel 2.x API design
- Active Record pattern
- Query builder pattern
- Common ORM operations

## Integration

Use as a drop-in replacement for Diesel in development:

```rust
// Instead of:
// use diesel::prelude::*;

// Use:
use diesel_emulator::*;

// Your code works the same way
```

## License

Part of the Emu-Soft project. See main repository LICENSE.
