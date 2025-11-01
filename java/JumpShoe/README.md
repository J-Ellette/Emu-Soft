# Spring Boot Emulator - Enterprise Web Framework for Java

**Developed by PowerShield, as an alternative to Spring Boot**


This module emulates **Spring Boot**, a powerful framework for building production-ready Spring applications in Java. Spring Boot simplifies Spring development by providing opinionated defaults and auto-configuration.

## What is Spring Boot?

Spring Boot is an open-source Java-based framework developed by Pivotal Team (now part of VMware). It provides:
- **Auto-configuration** - Automatic configuration based on dependencies
- **Standalone applications** - Embedded server (Tomcat, Jetty, or Undertow)
- **Production-ready features** - Health checks, metrics, and monitoring
- **No XML configuration** - Convention over configuration
- **Microservices support** - Perfect for building microservices
- **Rich ecosystem** - Integration with Spring Data, Spring Security, etc.

Key features:
- Rapid application development
- Minimal boilerplate code
- Embedded web servers
- RESTful web services
- Dependency injection
- Built-in production features

## Features

This emulator implements core Spring Boot functionality:

### Web Framework
- **HTTP Request/Response** - Handle HTTP requests and responses
- **RESTful routing** - Map URLs to handler methods
- **Path variables** - Extract variables from URLs
- **Query parameters** - Handle URL query strings
- **Request/Response bodies** - Process JSON and other content

### Annotations (Emulated)
- **@SpringBootApplication** - Main application annotation
- **@RestController** - REST API controller
- **@GetMapping, @PostMapping, @PutMapping, @DeleteMapping** - HTTP method mappings
- **@PathVariable** - Extract path variables
- **@RequestParam** - Extract query parameters
- **@RequestBody** - Parse request body
- **@Autowired** - Dependency injection

### Application Features
- **Application context** - Dependency injection container
- **ResponseEntity** - Typed HTTP responses
- **Configuration properties** - Application configuration
- **API responses** - Structured JSON responses

## Usage Examples

### Basic Spring Boot Application

```java
import SpringBootEmulator.*;

public class MyApplication {
    public static void main(String[] args) {
        SpringApplication app = SpringApplication.run(MyApplication.class, args);
        
        // Application is now running
        // Access at http://localhost:8080
    }
}
```

### Creating a REST Controller

```java
import SpringBootEmulator.*;

public class UserController {
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication();
        
        // GET endpoint
        app.addRoute("GET", "/api/users", req -> {
            return ResponseEntity.ok("List of users");
        });
        
        // POST endpoint
        app.addRoute("POST", "/api/users", req -> {
            return ResponseEntity.created("User created");
        });
        
        app.run();
    }
}
```

### Path Variables

Extract values from URL paths:

```java
import SpringBootEmulator.*;

public class UserApi {
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication();
        
        // GET user by ID
        app.addRoute("GET", "/api/users/{id}", req -> {
            String userId = req.pathVariables.get("id");
            return ResponseEntity.ok("User ID: " + userId);
        });
        
        // GET user posts
        app.addRoute("GET", "/api/users/{userId}/posts/{postId}", req -> {
            String userId = req.pathVariables.get("userId");
            String postId = req.pathVariables.get("postId");
            return ResponseEntity.ok(
                "User " + userId + ", Post " + postId
            );
        });
        
        app.run();
    }
}
```

### Query Parameters

Handle URL query strings:

```java
import SpringBootEmulator.*;

public class SearchApi {
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication();
        
        app.addRoute("GET", "/api/search", req -> {
            String query = req.getParams().get("q");
            String page = req.getParams().getOrDefault("page", "1");
            String size = req.getParams().getOrDefault("size", "10");
            
            return ResponseEntity.ok(
                "Search: " + query + ", Page: " + page + ", Size: " + size
            );
        });
        
        app.run();
    }
}
```

### ResponseEntity

Return typed HTTP responses with status codes:

```java
import SpringBootEmulator.*;

public class ProductApi {
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication();
        Map<String, String> products = new HashMap<>();
        
        // GET - 200 OK
        app.addRoute("GET", "/api/products/{id}", req -> {
            String id = req.pathVariables.get("id");
            if (products.containsKey(id)) {
                return ResponseEntity.ok(products.get(id));
            } else {
                return ResponseEntity.notFound();  // 404
            }
        });
        
        // POST - 201 Created
        app.addRoute("POST", "/api/products", req -> {
            String id = String.valueOf(products.size() + 1);
            products.put(id, "Product " + id);
            return ResponseEntity.created("Product created with ID: " + id);
        });
        
        // PUT - 200 OK or 404
        app.addRoute("PUT", "/api/products/{id}", req -> {
            String id = req.pathVariables.get("id");
            if (products.containsKey(id)) {
                products.put(id, "Updated Product");
                return ResponseEntity.ok("Updated");
            } else {
                return ResponseEntity.notFound();
            }
        });
        
        // DELETE - 200 OK
        app.addRoute("DELETE", "/api/products/{id}", req -> {
            String id = req.pathVariables.get("id");
            products.remove(id);
            return ResponseEntity.ok("Deleted");
        });
        
        app.run();
    }
}
```

### Request Body

Handle JSON and other request bodies:

```java
import SpringBootEmulator.*;

public class UserRegistration {
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication();
        
        app.addRoute("POST", "/api/register", req -> {
            String body = req.getBody();
            // In real Spring Boot, this would be parsed to an object
            
            // Process registration...
            
            return ResponseEntity.created("User registered");
        });
        
        app.run();
    }
}
```

### Application Context (Dependency Injection)

Manage beans and dependencies:

```java
import SpringBootEmulator.*;

class UserService {
    public String getUser(String id) {
        return "User " + id;
    }
}

public class DIExample {
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication();
        
        // Register service bean
        UserService userService = new UserService();
        app.getContext().registerBean(UserService.class, userService);
        
        // Use in routes
        app.addRoute("GET", "/api/users/{id}", req -> {
            UserService service = app.getContext().getBean(UserService.class);
            String id = req.pathVariables.get("id");
            String user = service.getUser(id);
            return ResponseEntity.ok(user);
        });
        
        app.run();
    }
}
```

### Configuration Properties

Manage application configuration:

```java
import SpringBootEmulator.*;

public class ConfigExample {
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication();
        
        ConfigurationProperties config = new ConfigurationProperties();
        config.setProperty("server.port", "8080");
        config.setProperty("app.name", "MyApp");
        config.setProperty("app.version", "1.0.0");
        
        app.addRoute("GET", "/api/config", req -> {
            return ResponseEntity.ok(
                "App: " + config.getProperty("app.name") + 
                " v" + config.getProperty("app.version")
            );
        });
        
        app.run();
    }
}
```

### API Response Format

Use structured API responses:

```java
import SpringBootEmulator.*;

public class ApiExample {
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication();
        
        app.addRoute("GET", "/api/data", req -> {
            List<String> data = Arrays.asList("item1", "item2", "item3");
            return ResponseEntity.ok(ApiResponse.success(data));
        });
        
        app.addRoute("GET", "/api/error", req -> {
            return ResponseEntity.badRequest(
                ApiResponse.error("Invalid request")
            );
        });
        
        app.run();
    }
}
```

### Complete REST API Example

Full CRUD API for managing resources:

```java
import SpringBootEmulator.*;
import java.util.*;

public class BookstoreApi {
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication();
        
        // In-memory database
        Map<String, Map<String, String>> books = new HashMap<>();
        int nextId = 1;
        
        // GET /api/books - List all books
        app.addRoute("GET", "/api/books", req -> {
            return ResponseEntity.ok(ApiResponse.success(books));
        });
        
        // GET /api/books/{id} - Get specific book
        app.addRoute("GET", "/api/books/{id}", req -> {
            String id = req.pathVariables.get("id");
            
            if (books.containsKey(id)) {
                return ResponseEntity.ok(books.get(id));
            } else {
                return ResponseEntity.notFound();
            }
        });
        
        // POST /api/books - Create new book
        app.addRoute("POST", "/api/books", req -> {
            String body = req.getBody();
            // In real app, parse JSON body
            
            String id = String.valueOf(nextId++);
            Map<String, String> book = new HashMap<>();
            book.put("id", id);
            book.put("title", "Sample Book " + id);
            book.put("author", "Author " + id);
            
            books.put(id, book);
            
            return ResponseEntity.created(
                ApiResponse.success("Book created with ID: " + id)
            );
        });
        
        // PUT /api/books/{id} - Update book
        app.addRoute("PUT", "/api/books/{id}", req -> {
            String id = req.pathVariables.get("id");
            
            if (books.containsKey(id)) {
                Map<String, String> book = books.get(id);
                book.put("title", "Updated Title");
                
                return ResponseEntity.ok(
                    ApiResponse.success("Book updated")
                );
            } else {
                return ResponseEntity.notFound();
            }
        });
        
        // DELETE /api/books/{id} - Delete book
        app.addRoute("DELETE", "/api/books/{id}", req -> {
            String id = req.pathVariables.get("id");
            
            if (books.containsKey(id)) {
                books.remove(id);
                return ResponseEntity.ok(
                    ApiResponse.success("Book deleted")
                );
            } else {
                return ResponseEntity.notFound();
            }
        });
        
        // GET /api/books/search - Search books
        app.addRoute("GET", "/api/books/search", req -> {
            String query = req.getParams().get("q");
            String author = req.getParams().get("author");
            
            // Filter books based on query
            List<Map<String, String>> results = new ArrayList<>();
            for (Map<String, String> book : books.values()) {
                results.add(book);
            }
            
            return ResponseEntity.ok(ApiResponse.success(results));
        });
        
        System.out.println("Bookstore API is running!");
        System.out.println("Endpoints:");
        System.out.println("  GET    /api/books           - List all books");
        System.out.println("  GET    /api/books/{id}      - Get book by ID");
        System.out.println("  POST   /api/books           - Create new book");
        System.out.println("  PUT    /api/books/{id}      - Update book");
        System.out.println("  DELETE /api/books/{id}      - Delete book");
        System.out.println("  GET    /api/books/search    - Search books");
        
        app.run();
    }
}
```

### Testing the Application

```java
import SpringBootEmulator.*;

public class TestApi {
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication();
        
        app.addRoute("GET", "/api/test", req -> {
            return ResponseEntity.ok("Test successful");
        });
        
        // Simulate a request
        HttpRequest request = new HttpRequest("GET", "/api/test");
        HttpResponse response = app.handleRequest(request);
        
        System.out.println("Status: " + response.getStatus());
        System.out.println("Body: " + response.getBody());
    }
}
```

## Testing

Compile and run the test suite:

```bash
# Compile
javac SpringBootEmulator.java TestSpringBootEmulator.java

# Run tests
java TestSpringBootEmulator
```

The test suite covers:
- HTTP request and response handling
- ResponseEntity usage
- Route matching and path variables
- Application context (dependency injection)
- Configuration properties
- API response formatting
- Complete REST API workflows

## Use Cases

Perfect for:
- **REST APIs** - Build RESTful web services
- **Microservices** - Create microservice architectures
- **Web Applications** - Develop web applications
- **Enterprise Applications** - Build enterprise-grade systems
- **Learning** - Learn Spring Boot concepts
- **Prototyping** - Rapid application prototyping

## Best Practices

### Controller Organization

```java
// Good: Organize by resource
/api/users     -> UserController
/api/products  -> ProductController
/api/orders    -> OrderController

// Each controller handles one resource type
```

### Use ResponseEntity

```java
// Good: Use ResponseEntity for proper HTTP status codes
return ResponseEntity.ok(data);              // 200
return ResponseEntity.created(data);         // 201
return ResponseEntity.notFound();            // 404
return ResponseEntity.badRequest(error);     // 400

// Bad: Just returning strings
return "OK";  // No status code control
```

### Path Variables vs Query Parameters

```java
// Good: Use path variables for resource identification
GET /api/users/{id}           // Specific user
GET /api/users/{id}/posts     // User's posts

// Good: Use query parameters for filtering/sorting
GET /api/users?role=admin     // Filter users
GET /api/products?sort=price  // Sort products
GET /api/search?q=keyword     // Search query
```

### Service Layer

```java
// Good: Separate business logic into services
UserService userService = new UserService();
app.getContext().registerBean(UserService.class, userService);

// Controllers handle HTTP, services handle business logic
```

## Limitations

This is an emulator for development and learning:
- No actual HTTP server
- Simplified request handling
- No JSON parsing/serialization
- No database integration
- No Spring Security
- No transaction management
- Limited annotation processing

## Supported Features

### HTTP Methods
- ✅ GET
- ✅ POST
- ✅ PUT
- ✅ DELETE

### Request Handling
- ✅ Path variables
- ✅ Query parameters
- ✅ Request headers
- ✅ Request body

### Response Handling
- ✅ Response status codes
- ✅ Response body
- ✅ Response headers
- ✅ ResponseEntity

### Application Features
- ✅ Application context (DI container)
- ✅ Configuration properties
- ✅ Route matching
- ✅ API response formatting

## Compatibility

Emulates patterns from:
- Spring Boot 2.x/3.x
- Spring MVC
- Spring Web
- RESTful web services

## Integration

Use similar patterns to real Spring Boot:

```java
// Similar to Spring Boot annotations
@RestController
public class UserController {
    @GetMapping("/api/users/{id}")
    public ResponseEntity<User> getUser(@PathVariable String id) {
        // ...
    }
}

// In the emulator:
app.addRoute("GET", "/api/users/{id}", req -> {
    String id = req.pathVariables.get("id");
    // ...
});
```

## License

Part of the Emu-Soft project. See main repository LICENSE.
