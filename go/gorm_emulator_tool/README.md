# GORM Emulator - ORM for Go

This module emulates **GORM** (Go Object-Relational Mapping), which is a popular ORM library for Go. GORM provides a developer-friendly way to interact with databases using Go structs and methods.

## What is GORM?

GORM is a full-featured ORM library for Go that provides:
- Association handling (Has One, Has Many, Belongs To, Many To Many, Polymorphism)
- Hooks (Before/After Create/Save/Update/Delete/Find)
- Preloading (Eager Loading)
- Transactions
- Auto Migrations
- SQL Builder
- Logger
- Composite Primary Key
- Index and Constraint support
- Database Resolver (multiple databases, read/write splitting)

## Features

This emulator implements core GORM functionality:

### Database Operations
- **Create**: Insert new records into the database
- **First**: Retrieve the first record matching conditions
- **Find**: Retrieve all records matching conditions
- **Save**: Update existing records or create new ones
- **Update**: Update a single column
- **Updates**: Update multiple columns
- **Delete**: Soft delete records
- **Count**: Count matching records

### Query Building
- **Where**: Add WHERE conditions
- **Limit**: Limit number of results
- **Offset**: Skip a number of results
- **Order**: Order results
- **Table**: Specify table name
- **Model**: Specify model for operations

### Model Features
- **Auto Migration**: Automatically create tables
- **Timestamps**: Automatic CreatedAt and UpdatedAt
- **Soft Deletes**: DeletedAt field for soft deletion
- **Primary Keys**: Auto-incrementing ID field

### Advanced Features
- **Method Chaining**: Chain multiple query methods
- **Transaction Support**: Begin, Commit, Rollback
- **Raw SQL**: Execute raw SQL queries
- **Error Handling**: Proper error propagation

## Usage Examples

### Basic Model Definition

```go
package main

import (
    "time"
)

type User struct {
    ID        uint      `gorm:"primaryKey"`
    CreatedAt time.Time
    UpdatedAt time.Time
    DeletedAt *time.Time `gorm:"index"`
    Name      string
    Email     string
    Age       int
}
```

### Database Connection

```go
package main

import "gorm_emulator"

func main() {
    // Connect to database
    db, err := Open("sqlite", "test.db")
    if err != nil {
        panic("failed to connect database")
    }

    // Auto migrate the schema
    db.AutoMigrate(&User{})
}
```

### Create Records

```go
package main

func main() {
    db, _ := Open("sqlite", "test.db")
    db.AutoMigrate(&User{})

    // Create a single record
    user := User{Name: "Alice", Email: "alice@example.com", Age: 25}
    db.Create(&user)
    
    // ID will be set automatically
    fmt.Printf("Created user with ID: %d\n", user.ID)
}
```

### Query Records

```go
package main

func main() {
    db, _ := Open("sqlite", "test.db")

    // Find first user
    var user User
    db.First(&user)

    // Find all users
    var users []User
    db.Find(&users)

    // Find with conditions
    db.Where("age > ?", 20).Find(&users)

    // Find specific user
    db.Where("id = ?", 1).First(&user)
}
```

### Update Records

```go
package main

func main() {
    db, _ := Open("sqlite", "test.db")

    // Update single field
    db.Model(&User{}).Where("id = ?", 1).Update("Age", 26)

    // Update multiple fields
    db.Model(&User{}).Where("id = ?", 1).Updates(map[string]interface{}{
        "Name": "Alice Smith",
        "Age":  27,
    })

    // Save model (update if exists, create if not)
    user := User{ID: 1, Name: "Alice", Email: "alice@example.com", Age: 28}
    db.Save(&user)
}
```

### Delete Records

```go
package main

func main() {
    db, _ := Open("sqlite", "test.db")

    // Soft delete (sets DeletedAt)
    db.Where("id = ?", 1).Delete(&User{})

    // Deleted records won't appear in queries
    var users []User
    db.Find(&users) // Won't include soft-deleted records
}
```

### Query Modifiers

```go
package main

func main() {
    db, _ := Open("sqlite", "test.db")

    // Limit and offset
    var users []User
    db.Limit(10).Offset(5).Find(&users)

    // Order by
    db.Order("age DESC").Find(&users)

    // Count
    var count int64
    db.Model(&User{}).Count(&count)

    // Chain multiple conditions
    db.Where("age > ?", 20).
       Where("name LIKE ?", "A%").
       Order("age DESC").
       Limit(10).
       Find(&users)
}
```

### Transaction Support

```go
package main

func main() {
    db, _ := Open("sqlite", "test.db")

    // Begin transaction
    tx := db.Begin()

    // Create records in transaction
    user1 := User{Name: "Alice", Email: "alice@example.com"}
    tx.Create(&user1)

    user2 := User{Name: "Bob", Email: "bob@example.com"}
    tx.Create(&user2)

    // Commit transaction
    tx.Commit()

    // Rollback on error
    tx2 := db.Begin()
    user3 := User{Name: "Charlie"}
    if err := tx2.Create(&user3).Error; err != nil {
        tx2.Rollback()
    } else {
        tx2.Commit()
    }
}
```

### Using Table Method

```go
package main

func main() {
    db, _ := Open("sqlite", "test.db")

    // Specify table name explicitly
    var users []User
    db.Table("users").Where("age > ?", 20).Find(&users)
}
```

### Error Handling

```go
package main

import "fmt"

func main() {
    db, _ := Open("sqlite", "test.db")

    var user User
    result := db.Where("id = ?", 999).First(&user)
    
    if result.Error != nil {
        fmt.Println("Error:", result.Error)
    }

    if result.RowsAffected == 0 {
        fmt.Println("No records found")
    }
}
```

### Multiple Models

```go
package main

type Product struct {
    ID        uint
    CreatedAt time.Time
    UpdatedAt time.Time
    DeletedAt *time.Time
    Name      string
    Price     float64
    Stock     int
}

func main() {
    db, _ := Open("sqlite", "test.db")

    // Migrate multiple models
    db.AutoMigrate(&User{}, &Product{})

    // Create records in different tables
    user := User{Name: "Alice", Email: "alice@example.com"}
    db.Create(&user)

    product := Product{Name: "Laptop", Price: 999.99, Stock: 10}
    db.Create(&product)

    // Query different tables
    var users []User
    db.Find(&users)

    var products []Product
    db.Find(&products)
}
```

### Model with Embedded Struct

```go
package main

import "time"

// Reusable Model struct
type Model struct {
    ID        uint      `gorm:"primaryKey"`
    CreatedAt time.Time
    UpdatedAt time.Time
    DeletedAt *time.Time `gorm:"index"`
}

// Embed Model in User
type User struct {
    Model
    Name  string
    Email string
    Age   int
}

func main() {
    db, _ := Open("sqlite", "test.db")
    db.AutoMigrate(&User{})

    user := User{Name: "Alice", Email: "alice@example.com", Age: 25}
    db.Create(&user)

    // Access embedded fields
    fmt.Println("ID:", user.ID)
    fmt.Println("Created:", user.CreatedAt)
}
```

### Complex Queries

```go
package main

func main() {
    db, _ := Open("sqlite", "test.db")

    var users []User

    // Multiple WHERE conditions
    db.Where("age > ?", 20).
       Where("email LIKE ?", "%@example.com").
       Find(&users)

    // Combining conditions
    db.Where("age BETWEEN ? AND ?", 20, 30).Find(&users)

    // Find with count
    var count int64
    db.Model(&User{}).
       Where("age > ?", 25).
       Count(&count)

    fmt.Printf("Found %d users over 25\n", count)
}
```

## Testing

Run the comprehensive test suite:

```bash
go run test_gorm_emulator.go
```

Tests cover:
- Database connection and initialization
- Auto migration
- Creating records with auto-generated IDs
- Finding first and all records
- WHERE clauses with parameters
- Updating single and multiple fields
- Save method (update or create)
- Counting records
- Limit and Offset
- Order by
- Soft delete functionality
- Multiple table support
- Method chaining
- RowsAffected tracking
- Error handling
- Automatic timestamps
- Transaction simulation
- Table method

Total: 20 tests

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for GORM in development and testing:

```go
// Instead of:
// import "gorm.io/gorm"
// import "gorm.io/driver/sqlite"

// Use:
// import "gorm_emulator"

// Most of your GORM code will work with minimal changes
func main() {
    db, err := Open("sqlite", "test.db")
    if err != nil {
        panic("failed to connect")
    }

    db.AutoMigrate(&User{})

    user := User{Name: "Alice"}
    db.Create(&user)
}
```

## Use Cases

Perfect for:
- **Local Development**: Develop database-driven applications without a real database
- **Testing**: Test database operations in memory
- **Learning**: Understand ORM patterns in Go
- **Prototyping**: Quickly prototype data models
- **Education**: Teach database concepts
- **CI/CD**: Run database tests without database infrastructure

## Limitations

This is an emulator for development and testing purposes:
- No actual database connection (in-memory storage)
- Simplified query parsing (basic WHERE conditions)
- No association support (Has One, Has Many, etc.)
- No hooks (Before/After callbacks)
- No preloading/eager loading
- No complex SQL parsing
- No database-specific features
- Simplified transaction handling
- No migration management
- No connection pooling
- Ordering is simplified (no actual sorting)

## Supported Features

### Core Operations
- ✅ Open database connection
- ✅ AutoMigrate
- ✅ Create records
- ✅ Find records (First, Find)
- ✅ Update records (Save, Update, Updates)
- ✅ Delete records (soft delete)
- ✅ Count records

### Query Building
- ✅ Where clauses
- ✅ Limit/Offset
- ✅ Order by (basic)
- ✅ Method chaining
- ✅ Table/Model specification

### Model Features
- ✅ Primary key (ID)
- ✅ Timestamps (CreatedAt, UpdatedAt)
- ✅ Soft delete (DeletedAt)
- ✅ Embedded Model struct

### Advanced
- ✅ Transaction methods (Begin, Commit, Rollback)
- ✅ Raw SQL (basic support)
- ✅ Error handling
- ✅ RowsAffected tracking

## Real-World ORM Concepts

This emulator teaches the following concepts:

1. **Object-Relational Mapping**: Mapping Go structs to database tables
2. **CRUD Operations**: Create, Read, Update, Delete
3. **Query Building**: Constructing database queries programmatically
4. **Model Definition**: Defining data structures with tags
5. **Migrations**: Automatic schema creation
6. **Soft Deletes**: Marking records as deleted without removing them
7. **Timestamps**: Automatic time tracking
8. **Transactions**: Grouping operations together
9. **Method Chaining**: Building complex queries fluently
10. **Error Handling**: Managing database errors

## Compatibility

Emulates core features of:
- GORM v1.x/v2.x API patterns
- Common ORM conventions
- Standard database operation semantics

## License

Part of the Emu-Soft project. See main repository LICENSE.
