# Gin Emulator - Web Framework for Go

**Developed by PowerShield, as an alternative to Gin**


This module emulates the **Gin** framework, which is a high-performance HTTP web framework written in Go. Gin is known for its speed, minimalism, and powerful routing capabilities.

## What is Gin?

Gin is a web framework written in Go that features a martini-like API with performance up to 40 times faster than Martini. It is designed to be:
- Fast and efficient with a radix tree-based router
- Lightweight with minimal memory footprint
- Crash-free with built-in recovery middleware
- JSON-friendly with easy validation
- Routes grouping for better organization
- Middleware support for extensibility

## Features

This emulator implements core Gin functionality:

### Routing
- **HTTP Method Handlers**: GET, POST, PUT, DELETE, PATCH
- **URL Parameters**: Dynamic path segments (e.g., `/users/:id`)
- **Query String Parsing**: Automatic parsing of URL query parameters
- **Route Matching**: Efficient route matching with parameter extraction
- **Router Groups**: Organize routes with common prefixes and middleware

### Middleware System
- **Global Middleware**: Apply middleware to all routes
- **Route-Specific Middleware**: Apply middleware to individual routes
- **Group Middleware**: Apply middleware to route groups
- **Built-in Middleware**: Logger and Recovery middleware included
- **Middleware Chain**: Execute multiple middleware in sequence
- **Abort Control**: Stop middleware chain execution

### Context Object
- **Request Access**: Method, path, headers, body, query parameters
- **Response Building**: Status codes, headers, body content
- **Parameter Extraction**: URL parameters and query strings
- **JSON Handling**: Marshal and unmarshal JSON data
- **Header Management**: Set and get request/response headers

### Response Methods
- **JSON**: Send JSON responses with automatic marshaling
- **String**: Send plain text responses with formatting
- **Data**: Send raw data with custom content type
- **Status**: Set HTTP status codes

## Usage Examples

### Basic Application

```go
package main

import "gin_emulator"

func main() {
    r := gin.Default()

    r.GET("/ping", func(c *gin.Context) {
        c.JSON(200, gin.H{
            "message": "pong",
        })
    })

    r.Run() // Listen on 0.0.0.0:8080
}
```

### URL Parameters

```go
package main

import "gin_emulator"

func main() {
    r := gin.New()

    r.GET("/users/:id", func(c *gin.Context) {
        id := c.Param("id")
        c.JSON(200, gin.H{"userId": id})
    })

    // Simulated request to /users/123
    resp := r.ServeHTTP("GET", "/users/123", nil, map[string]string{})
}
```

### Query Parameters

```go
package main

import "gin_emulator"

func main() {
    r := gin.New()

    r.GET("/search", func(c *gin.Context) {
        query := c.Query("q")
        limit := c.DefaultQuery("limit", "10")
        c.JSON(200, gin.H{
            "query": query,
            "limit": limit,
        })
    })

    // Access with: /search?q=golang&limit=20
}
```

### POST Request with JSON

```go
package main

import "gin_emulator"

type User struct {
    Name  string `json:"name"`
    Email string `json:"email"`
}

func main() {
    r := gin.New()

    r.POST("/users", func(c *gin.Context) {
        var user User
        if err := c.BindJSON(&user); err != nil {
            c.JSON(400, gin.H{"error": err.Error()})
            return
        }
        
        c.JSON(201, gin.H{
            "id":    1,
            "name":  user.Name,
            "email": user.Email,
        })
    })
}
```

### Middleware

```go
package main

import (
    "fmt"
    "gin_emulator"
)

func main() {
    r := gin.New()

    // Global middleware
    r.Use(func(c *gin.Context) {
        fmt.Println("Before request")
        c.Next()
        fmt.Println("After request")
    })

    // Authentication middleware
    r.Use(func(c *gin.Context) {
        auth := c.GetHeader("Authorization")
        if auth == "" {
            c.AbortWithStatus(401)
            return
        }
        c.Next()
    })

    r.GET("/protected", func(c *gin.Context) {
        c.JSON(200, gin.H{"message": "Protected resource"})
    })
}
```

### Router Groups

```go
package main

import "gin_emulator"

func main() {
    r := gin.New()

    // API v1 group
    v1 := r.Group("/api/v1")
    {
        v1.GET("/users", listUsers)
        v1.GET("/users/:id", getUser)
        v1.POST("/users", createUser)
        v1.PUT("/users/:id", updateUser)
        v1.DELETE("/users/:id", deleteUser)
    }

    // API v2 group
    v2 := r.Group("/api/v2")
    {
        v2.GET("/users", listUsersV2)
        v2.GET("/users/:id", getUserV2)
    }
}

func listUsers(c *gin.Context) {
    c.JSON(200, gin.H{"users": []string{"Alice", "Bob"}})
}

func getUser(c *gin.Context) {
    id := c.Param("id")
    c.JSON(200, gin.H{"id": id, "name": "Alice"})
}

func createUser(c *gin.Context) {
    c.JSON(201, gin.H{"id": 1, "status": "created"})
}

func updateUser(c *gin.Context) {
    id := c.Param("id")
    c.JSON(200, gin.H{"id": id, "status": "updated"})
}

func deleteUser(c *gin.Context) {
    c.Status(204)
}

func listUsersV2(c *gin.Context) {
    c.JSON(200, gin.H{"version": "2", "users": []string{}})
}

func getUserV2(c *gin.Context) {
    c.JSON(200, gin.H{"version": "2"})
}
```

### Nested Router Groups

```go
package main

import "gin_emulator"

func main() {
    r := gin.New()

    api := r.Group("/api")
    {
        v1 := api.Group("/v1")
        {
            users := v1.Group("/users")
            {
                users.GET("", listUsers)
                users.GET("/:id", getUser)
                users.POST("", createUser)
            }
        }
    }

    // Routes available:
    // GET /api/v1/users
    // GET /api/v1/users/:id
    // POST /api/v1/users
}
```

### Group Middleware

```go
package main

import (
    "fmt"
    "gin_emulator"
)

func main() {
    r := gin.New()

    // Admin routes with authentication
    admin := r.Group("/admin", func(c *gin.Context) {
        // Authentication middleware
        token := c.GetHeader("Authorization")
        if token != "admin-token" {
            c.AbortWithStatus(401)
            return
        }
        c.Next()
    })

    admin.GET("/dashboard", func(c *gin.Context) {
        c.String(200, "Admin Dashboard")
    })

    admin.GET("/users", func(c *gin.Context) {
        c.JSON(200, gin.H{"users": []string{}})
    })
}
```

### RESTful API Example

```go
package main

import "gin_emulator"

type User struct {
    ID    int    `json:"id"`
    Name  string `json:"name"`
    Email string `json:"email"`
}

var users = []User{
    {ID: 1, Name: "Alice", Email: "alice@example.com"},
    {ID: 2, Name: "Bob", Email: "bob@example.com"},
}

func main() {
    r := gin.Default()

    // List all users
    r.GET("/users", func(c *gin.Context) {
        c.JSON(200, users)
    })

    // Get single user
    r.GET("/users/:id", func(c *gin.Context) {
        id := c.Param("id")
        for _, user := range users {
            if fmt.Sprintf("%d", user.ID) == id {
                c.JSON(200, user)
                return
            }
        }
        c.JSON(404, gin.H{"error": "User not found"})
    })

    // Create user
    r.POST("/users", func(c *gin.Context) {
        var newUser User
        if err := c.BindJSON(&newUser); err != nil {
            c.JSON(400, gin.H{"error": err.Error()})
            return
        }
        newUser.ID = len(users) + 1
        users = append(users, newUser)
        c.JSON(201, newUser)
    })

    // Update user
    r.PUT("/users/:id", func(c *gin.Context) {
        id := c.Param("id")
        var updatedUser User
        if err := c.BindJSON(&updatedUser); err != nil {
            c.JSON(400, gin.H{"error": err.Error()})
            return
        }

        for i, user := range users {
            if fmt.Sprintf("%d", user.ID) == id {
                users[i].Name = updatedUser.Name
                users[i].Email = updatedUser.Email
                c.JSON(200, users[i])
                return
            }
        }
        c.JSON(404, gin.H{"error": "User not found"})
    })

    // Delete user
    r.DELETE("/users/:id", func(c *gin.Context) {
        id := c.Param("id")
        for i, user := range users {
            if fmt.Sprintf("%d", user.ID) == id {
                users = append(users[:i], users[i+1:]...)
                c.Status(204)
                return
            }
        }
        c.JSON(404, gin.H{"error": "User not found"})
    })

    r.Run(":8080")
}
```

### Custom Response Headers

```go
package main

import "gin_emulator"

func main() {
    r := gin.New()

    r.GET("/custom", func(c *gin.Context) {
        c.Header("X-Custom-Header", "CustomValue")
        c.Header("X-Request-ID", "12345")
        c.JSON(200, gin.H{"message": "Response with custom headers"})
    })
}
```

### Multiple Route Parameters

```go
package main

import "gin_emulator"

func main() {
    r := gin.New()

    r.GET("/api/:version/users/:userId/posts/:postId", func(c *gin.Context) {
        version := c.Param("version")
        userId := c.Param("userId")
        postId := c.Param("postId")

        c.JSON(200, gin.H{
            "version": version,
            "userId":  userId,
            "postId":  postId,
        })
    })

    // Access: /api/v1/users/123/posts/456
}
```

## Testing

Run the comprehensive test suite:

```bash
go run test_gin_emulator.go
```

Tests cover:
- Basic routing (GET, POST, PUT, DELETE, PATCH)
- URL parameters (single and multiple)
- Query parameters with defaults
- POST requests with JSON body
- Middleware execution and order
- Aborting middleware chains
- Router groups and nested groups
- Group-specific middleware
- 404 handling
- Request and response headers
- Content type handling
- RESTful API patterns
- Complex routing scenarios

Total: 20 tests

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for Gin in development and testing:

```go
// Instead of:
// import "github.com/gin-gonic/gin"

// Use:
// import "gin_emulator"

// The rest of your code remains largely unchanged
func main() {
    r := gin.Default()
    
    r.GET("/", func(c *gin.Context) {
        c.String(200, "Hello World")
    })
    
    r.Run()
}
```

## Use Cases

Perfect for:
- **Local Development**: Develop web applications without external dependencies
- **Testing**: Test HTTP handlers and API endpoints
- **Learning**: Understand web framework patterns in Go
- **Prototyping**: Quickly prototype REST APIs
- **Education**: Teach web development concepts
- **CI/CD**: Run API tests without network dependencies

## Limitations

This is an emulator for development and testing purposes:
- No actual HTTP server (simulated requests/responses)
- No actual network I/O
- Simplified middleware chain (no async)
- No template rendering
- No static file serving from filesystem
- No WebSocket support
- No TLS/HTTPS support
- No request validation beyond JSON binding
- Simplified context storage

## Supported Features

### Core Features
- ✅ Application creation
- ✅ HTTP method routing (GET, POST, PUT, DELETE, PATCH)
- ✅ URL parameters (`:param`)
- ✅ Query string parsing
- ✅ Middleware pipeline
- ✅ Router groups and nesting
- ✅ Context object
- ✅ Request/Response handling

### Context Methods
- ✅ Param() - Get URL parameter
- ✅ Query() - Get query parameter
- ✅ DefaultQuery() - Get query with default
- ✅ GetHeader() - Get request header
- ✅ Status() - Set status code
- ✅ Header() - Set response header
- ✅ JSON() - Send JSON response
- ✅ String() - Send string response
- ✅ Data() - Send raw data
- ✅ BindJSON() - Parse JSON body
- ✅ Next() - Execute next handler
- ✅ Abort() - Stop handler chain
- ✅ AbortWithStatus() - Abort with status

### Engine Methods
- ✅ New() - Create new engine
- ✅ Default() - Create with default middleware
- ✅ Use() - Add global middleware
- ✅ Group() - Create router group
- ✅ GET/POST/PUT/DELETE/PATCH() - Route registration
- ✅ Run() - Start server (simulated)
- ✅ ServeHTTP() - Handle requests

### Built-in Middleware
- ✅ Logger() - Request logging
- ✅ Recovery() - Panic recovery

## Real-World Web Framework Concepts

This emulator teaches the following concepts:

1. **HTTP Routing**: Mapping URLs to handler functions
2. **RESTful APIs**: Building resource-oriented APIs
3. **Middleware Pattern**: Composable request processing pipeline
4. **URL Parameters**: Dynamic URL segments
5. **Query Parameters**: Parsing URL parameters
6. **JSON Handling**: Marshaling and unmarshaling JSON
7. **Request/Response Cycle**: Understanding HTTP flow
8. **Status Codes**: Using appropriate HTTP status codes
9. **Header Management**: Setting and reading HTTP headers
10. **Route Organization**: Grouping related routes
11. **Error Handling**: Managing errors in web applications

## Compatibility

Emulates core features of:
- Gin v1.x API patterns
- Common Go web framework conventions
- Standard HTTP semantics

## License

Part of the Emu-Soft project. See main repository LICENSE.
