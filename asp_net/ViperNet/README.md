# ViperNet - ASP.NET Core Web Framework Emulator

A lightweight emulation of **ASP.NET Core**, Microsoft's cross-platform, high-performance framework for building modern, cloud-based, Internet-connected applications.

## Features

This emulator implements core ASP.NET Core functionality:

### Web Application Builder
- **WebApplicationBuilder**: Fluent API for application configuration
- **Service Registration**: Dependency injection configuration
- **Configuration Management**: Application settings and configuration
- **Environment Detection**: Development, Staging, Production environments

### Middleware Pipeline
- **UseRouting**: Enable endpoint routing
- **UseAuthentication**: Authentication middleware
- **UseAuthorization**: Authorization middleware
- **UseCors**: Cross-Origin Resource Sharing
- **UseHttpsRedirection**: HTTPS redirection
- **UseStaticFiles**: Static file serving
- **Custom Middleware**: Build custom middleware components

### Routing and Endpoints
- **Minimal APIs**: MapGet, MapPost, MapPut, MapDelete
- **Endpoint Routing**: Pattern-based routing
- **Route Parameters**: Extract values from URLs
- **Query Strings**: Parse query parameters
- **Controller Routing**: MapControllers for MVC pattern

### Dependency Injection
- **Service Lifetimes**: Singleton, Scoped, Transient
- **Service Registration**: AddSingleton, AddScoped, AddTransient
- **Service Resolution**: Automatic dependency resolution
- **IServiceCollection**: Service container interface

### Controllers and Actions
- **ControllerBase**: Base class for API controllers
- **Action Results**: Ok, BadRequest, NotFound, Created, NoContent
- **HTTP Method Attributes**: HttpGet, HttpPost, HttpPut, HttpDelete
- **Routing Attributes**: Route, ApiController
- **Parameter Binding**: FromBody, FromQuery, FromRoute

### HTTP Context
- **Request**: HTTP request information (method, path, headers, body)
- **Response**: HTTP response (status code, headers, body)
- **User**: Authentication information
- **Items**: Request-scoped data storage
- **RequestServices**: Service provider for request scope

### Configuration
- **ConfigurationManager**: Key-value configuration
- **Connection Strings**: Database connection configuration
- **Section Binding**: Bind configuration to objects
- **Environment Variables**: Read from environment

### CORS Support
- **Policy-Based**: Named CORS policies
- **AllowAnyOrigin**: Accept requests from any origin
- **AllowAnyMethod**: Accept any HTTP method
- **AllowAnyHeader**: Accept any header

## What It Emulates

This tool emulates [ASP.NET Core](https://docs.microsoft.com/en-us/aspnet/core/), Microsoft's modern web framework used for building web applications, APIs, and microservices.

### Core Components Implemented

1. **WebApplication**
   - Application host and builder pattern
   - Startup configuration
   - Middleware pipeline
   - Endpoint routing

2. **Dependency Injection**
   - Built-in IoC container
   - Service lifetime management
   - Constructor injection

3. **Middleware**
   - Request/response pipeline
   - Order-dependent middleware
   - Custom middleware support

4. **MVC Controllers**
   - API controllers
   - Action methods
   - Action results
   - Model binding

5. **Routing**
   - Endpoint routing
   - Attribute routing
   - Route templates
   - Route parameters

## Example Usage

### Minimal API

```csharp
using ViperNet;

var builder = WebApplicationFactory.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/", async (HttpContext ctx) =>
{
    await ctx.Response.WriteAsync("Hello World!");
});

app.MapGet("/api/users/{id}", async (HttpContext ctx) =>
{
    await ctx.Response.WriteAsJsonAsync(new { id = 1, name = "John Doe" });
});

await app.RunAsync("http://localhost:5000");
```

### Controller-Based API

```csharp
using ViperNet;

var builder = WebApplicationFactory.CreateBuilder(args);

// Configure services
builder.Services.AddControllers();
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

var app = builder.Build();

// Configure middleware
app.UseRouting();
app.UseCors("AllowAll");
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();

await app.RunAsync();
```

### Example Controller

```csharp
using ViperNet;

[ApiController]
[Route("api/[controller]")]
public class UsersController : ControllerBase
{
    [HttpGet]
    public OkObjectResult GetAll()
    {
        var users = new[] 
        {
            new { id = 1, name = "Alice" },
            new { id = 2, name = "Bob" }
        };
        return Ok(users);
    }

    [HttpGet("{id}")]
    public ActionResult GetById([FromRoute] int id)
    {
        if (id > 0)
            return Ok(new { id, name = "Alice" });
        return NotFound();
    }

    [HttpPost]
    public CreatedResult Create([FromBody] object user)
    {
        return Created("/api/users/1", new { id = 1, name = "New User" });
    }

    [HttpPut("{id}")]
    public OkResult Update([FromRoute] int id, [FromBody] object user)
    {
        return Ok();
    }

    [HttpDelete("{id}")]
    public NoContentResult Delete([FromRoute] int id)
    {
        return NoContent();
    }
}
```

### Configuration

```csharp
using ViperNet;

var builder = WebApplicationFactory.CreateBuilder(args);

// Set configuration values
builder.Configuration["AppName"] = "My API";
builder.Configuration["ConnectionStrings:DefaultConnection"] = 
    "Server=localhost;Database=mydb";

var app = builder.Build();

// Read configuration
var appName = app.Configuration["AppName"];
var connectionString = app.Configuration.GetConnectionString("DefaultConnection");

await app.RunAsync();
```

### Dependency Injection

```csharp
using ViperNet;

public interface IUserService
{
    string GetUser(int id);
}

public class UserService : IUserService
{
    public string GetUser(int id)
    {
        return $"User {id}";
    }
}

var builder = WebApplicationFactory.CreateBuilder(args);

// Register services
builder.Services.AddSingleton<IUserService, UserService>();
builder.Services.AddScoped<IUserRepository, UserRepository>();
builder.Services.AddTransient<IEmailService, EmailService>();

var app = builder.Build();
await app.RunAsync();
```

## Testing

Run the test suite:

```bash
# Compile and run tests
csc ViperNet.cs TestViperNet.cs
./TestViperNet
```

## Key Differences from Real ASP.NET Core

This is an educational emulator focusing on core concepts:

1. **Simplified HTTP**: Does not implement actual HTTP server
2. **No Kestrel**: Real ASP.NET Core uses Kestrel web server
3. **Basic Routing**: Simplified routing without all pattern matching
4. **Limited Middleware**: Implements common middleware concepts
5. **Simple DI**: Basic dependency injection without full feature set
6. **No Database**: Does not include Entity Framework Core integration

## Real-World ASP.NET Core

In production applications, ASP.NET Core provides:

- **Kestrel Web Server**: High-performance cross-platform web server
- **IIS Integration**: Integration with IIS on Windows
- **Entity Framework Core**: Full-featured ORM
- **Identity Framework**: Complete authentication/authorization
- **Blazor**: WebAssembly and Server-side UI framework
- **gRPC**: High-performance RPC framework
- **SignalR**: Real-time communication
- **Health Checks**: Application health monitoring
- **Logging**: Built-in logging infrastructure
- **Caching**: Memory and distributed caching
- **Response Compression**: Automatic compression
- **Rate Limiting**: Request throttling

## Architecture

ASP.NET Core follows a modular architecture:

```
WebApplication
├── Builder Pattern
│   ├── WebApplicationBuilder
│   ├── ServiceCollection
│   └── ConfigurationManager
├── Middleware Pipeline
│   ├── Request Processing
│   ├── Response Processing
│   └── Custom Middleware
├── Routing
│   ├── Endpoint Routing
│   ├── Minimal APIs
│   └── Controller Routing
├── Dependency Injection
│   ├── Service Registration
│   ├── Service Resolution
│   └── Lifetime Management
└── HTTP Context
    ├── HttpRequest
    ├── HttpResponse
    └── User/Identity
```

## Use Cases

ASP.NET Core is ideal for:

1. **RESTful APIs**: Build web APIs with JSON/XML responses
2. **Microservices**: Create independently deployable services
3. **Web Applications**: Full-stack web apps with Razor Pages/MVC
4. **Real-Time Apps**: Chat, notifications with SignalR
5. **Cloud-Native**: Deploy to Azure, AWS, or any cloud
6. **Cross-Platform**: Run on Windows, Linux, macOS
7. **High-Performance**: Handle millions of requests per second
8. **Container-Based**: Docker and Kubernetes support

## Educational Value

This emulator demonstrates:

- **Modern Web Architecture**: Request/response pipeline
- **Dependency Injection**: Inversion of Control principles
- **Middleware Pattern**: Composable request processing
- **Builder Pattern**: Fluent API design
- **RESTful Design**: HTTP methods and status codes
- **MVC Pattern**: Model-View-Controller architecture
- **SOLID Principles**: Single Responsibility, Dependency Inversion

## References

- [ASP.NET Core Documentation](https://docs.microsoft.com/en-us/aspnet/core/)
- [Minimal APIs](https://docs.microsoft.com/en-us/aspnet/core/fundamentals/minimal-apis)
- [Dependency Injection](https://docs.microsoft.com/en-us/aspnet/core/fundamentals/dependency-injection)
- [Middleware](https://docs.microsoft.com/en-us/aspnet/core/fundamentals/middleware/)
- [Routing](https://docs.microsoft.com/en-us/aspnet/core/fundamentals/routing)
