# Go-kit Emulator - Microservices Toolkit for Go

This module emulates **Go-kit**, which is a programming toolkit for building microservices (or elegant monoliths) in Go. Go-kit provides guidance and solutions for most common distributed systems problems, helping you focus on delivering business value.

## What is Go-kit?

Go-kit is a toolkit for microservices that emphasizes:
- **Separation of concerns**: Transport, endpoint, and service layers
- **Explicit dependencies**: No global state or hidden dependencies
- **Clean architecture**: Interfaces and dependency injection
- **Testability**: Easy to test each component in isolation
- **Observability**: Built-in support for logging, metrics, and tracing
- **Resilience**: Circuit breakers, rate limiting, and retries

## Features

This emulator implements core Go-kit functionality:

### Endpoint Layer
- **Endpoint Definition**: RPC-style request/response abstraction
- **Endpoint Middleware**: Chainable behavior modification
- **Request/Response Types**: Structured data handling
- **Error Handling**: Explicit error propagation

### Transport Layer
- **HTTP Server**: HTTP transport implementation
- **Request Decoding**: Transform transport data to domain objects
- **Response Encoding**: Transform domain objects to transport data
- **Transport Abstraction**: Clean separation from business logic

### Middleware System
- **Logging Middleware**: Request/response logging
- **Circuit Breaker**: Prevent cascading failures
- **Rate Limiting**: Throttle request rates
- **Timeout**: Add timeouts to endpoints
- **Middleware Chaining**: Compose multiple middleware

### Service Layer
- **Service Interface**: Business logic definition
- **Service Implementation**: Pure business logic
- **Service Middleware**: Service-level concerns

## Usage Examples

### Basic Service and Endpoint

```go
package main

import (
    "context"
    "errors"
)

// Define service interface
type StringService interface {
    Uppercase(ctx context.Context, s string) (string, error)
    Count(ctx context.Context, s string) (int, error)
}

// Implement service
type stringService struct{}

func (stringService) Uppercase(ctx context.Context, s string) (string, error) {
    if s == "" {
        return "", errors.New("empty string")
    }
    return strings.ToUpper(s), nil
}

func (stringService) Count(ctx context.Context, s string) (int, error) {
    return len(s), nil
}

func NewStringService() StringService {
    return stringService{}
}
```

### Creating Endpoints

```go
package main

import "context"

// Define request/response types
type UppercaseRequest struct {
    S string `json:"s"`
}

type UppercaseResponse struct {
    V   string `json:"v"`
    Err string `json:"err,omitempty"`
}

// Create endpoint
func MakeUppercaseEndpoint(svc StringService) Endpoint {
    return func(ctx context.Context, request interface{}) (interface{}, error) {
        req := request.(UppercaseRequest)
        v, err := svc.Uppercase(ctx, req.S)
        if err != nil {
            return UppercaseResponse{V: v, Err: err.Error()}, nil
        }
        return UppercaseResponse{V: v}, nil
    }
}

// Use endpoint
func main() {
    svc := NewStringService()
    endpoint := MakeUppercaseEndpoint(svc)
    
    ctx := context.Background()
    req := UppercaseRequest{S: "hello"}
    resp, err := endpoint(ctx, req)
    
    // resp will be UppercaseResponse{V: "HELLO"}
}
```

### HTTP Transport

```go
package main

import "context"

func main() {
    svc := NewStringService()
    endpoint := MakeUppercaseEndpoint(svc)
    
    // Create HTTP server
    server := NewServer(
        endpoint,
        decodeUppercaseRequest,
        encodeResponse,
    )
    
    // Handle request
    request := UppercaseRequest{S: "hello"}
    response, err := server.ServeHTTP(request)
}

func decodeUppercaseRequest(ctx context.Context, r interface{}) (interface{}, error) {
    return r, nil
}

func encodeResponse(ctx context.Context, w interface{}, response interface{}) error {
    return JSONEncoder(ctx, w, response)
}
```

### Logging Middleware

```go
package main

import "context"

func main() {
    svc := NewStringService()
    endpoint := MakeUppercaseEndpoint(svc)
    
    // Add logging middleware
    logger := &SimpleLogger{}
    endpoint = LoggingMiddleware(logger)(endpoint)
    
    ctx := context.Background()
    req := UppercaseRequest{S: "hello"}
    
    // This will log the request and response
    resp, err := endpoint(ctx, req)
}
```

### Circuit Breaker Middleware

```go
package main

import "context"

func main() {
    svc := NewStringService()
    endpoint := MakeUppercaseEndpoint(svc)
    
    // Add circuit breaker (opens after 3 failures)
    endpoint = CircuitBreakerMiddleware(3)(endpoint)
    
    ctx := context.Background()
    req := UppercaseRequest{S: ""}
    
    // After 3 failures, circuit breaker will open
    // and return "circuit breaker is open" error
    for i := 0; i < 5; i++ {
        resp, err := endpoint(ctx, req)
        if err != nil {
            fmt.Printf("Error: %v\n", err)
        }
    }
}
```

### Rate Limiting Middleware

```go
package main

import "context"

func main() {
    svc := NewStringService()
    endpoint := MakeUppercaseEndpoint(svc)
    
    // Allow max 10 concurrent requests
    endpoint = RateLimitMiddleware(10)(endpoint)
    
    ctx := context.Background()
    req := UppercaseRequest{S: "hello"}
    
    // 11th concurrent request will be rejected
    resp, err := endpoint(ctx, req)
}
```

### Chaining Multiple Middleware

```go
package main

import "context"

func main() {
    svc := NewStringService()
    endpoint := MakeUppercaseEndpoint(svc)
    
    logger := &SimpleLogger{}
    
    // Chain multiple middleware
    endpoint = Chain(
        LoggingMiddleware(logger),
        RateLimitMiddleware(100),
        CircuitBreakerMiddleware(5),
    )(endpoint)
    
    ctx := context.Background()
    req := UppercaseRequest{S: "hello"}
    resp, err := endpoint(ctx, req)
}
```

### Endpoint Set Pattern

```go
package main

import "context"

// Create endpoint set for entire service
func main() {
    svc := NewStringService()
    logger := &SimpleLogger{}
    
    // Create endpoint set with middleware
    endpoints := NewEndpointSet(
        svc,
        LoggingMiddleware(logger),
        RateLimitMiddleware(100),
    )
    
    ctx := context.Background()
    
    // Use uppercase endpoint
    uppercaseResp, _ := endpoints.UppercaseEndpoint(
        ctx,
        UppercaseRequest{S: "hello"},
    )
    
    // Use count endpoint
    countResp, _ := endpoints.CountEndpoint(
        ctx,
        CountRequest{S: "hello"},
    )
}
```

### Complete Microservice Example

```go
package main

import (
    "context"
    "errors"
    "strings"
)

// Service definition
type CalculatorService interface {
    Add(ctx context.Context, a, b int) (int, error)
    Multiply(ctx context.Context, a, b int) (int, error)
}

type calculatorService struct{}

func (calculatorService) Add(ctx context.Context, a, b int) (int, error) {
    return a + b, nil
}

func (calculatorService) Multiply(ctx context.Context, a, b int) (int, error) {
    return a * b, nil
}

func NewCalculatorService() CalculatorService {
    return calculatorService{}
}

// Request/Response types
type AddRequest struct {
    A int `json:"a"`
    B int `json:"b"`
}

type AddResponse struct {
    Result int    `json:"result"`
    Err    string `json:"err,omitempty"`
}

// Endpoints
func MakeAddEndpoint(svc CalculatorService) Endpoint {
    return func(ctx context.Context, request interface{}) (interface{}, error) {
        req := request.(AddRequest)
        result, err := svc.Add(ctx, req.A, req.B)
        if err != nil {
            return AddResponse{Err: err.Error()}, nil
        }
        return AddResponse{Result: result}, nil
    }
}

// Main application
func main() {
    svc := NewCalculatorService()
    logger := &SimpleLogger{}
    
    // Create endpoint with middleware
    addEndpoint := MakeAddEndpoint(svc)
    addEndpoint = LoggingMiddleware(logger)(addEndpoint)
    addEndpoint = RateLimitMiddleware(100)(addEndpoint)
    addEndpoint = CircuitBreakerMiddleware(5)(addEndpoint)
    
    // Create HTTP transport
    server := NewServer(
        addEndpoint,
        func(ctx context.Context, r interface{}) (interface{}, error) {
            return r, nil
        },
        JSONEncoder,
    )
    
    // Handle request
    req := AddRequest{A: 5, B: 3}
    resp, err := server.ServeHTTP(req)
    
    if err != nil {
        fmt.Printf("Error: %v\n", err)
    } else {
        addResp := resp.(AddResponse)
        fmt.Printf("Result: %d\n", addResp.Result)
    }
}
```

### Error Handling Pattern

```go
package main

import (
    "context"
    "errors"
)

type Response struct {
    Value string
    Err   string
}

// Implement Failer interface
func (r Response) Failed() error {
    if r.Err != "" {
        return errors.New(r.Err)
    }
    return nil
}

func MakeEndpointWithErrorHandling(svc Service) Endpoint {
    return func(ctx context.Context, request interface{}) (interface{}, error) {
        // Business logic
        value, err := svc.DoSomething(ctx, request)
        
        if err != nil {
            // Return error in response
            return Response{Err: err.Error()}, nil
        }
        
        return Response{Value: value}, nil
    }
}
```

### Custom Middleware Example

```go
package main

import (
    "context"
    "fmt"
    "time"
)

// Custom timing middleware
func TimingMiddleware() Middleware {
    return func(next Endpoint) Endpoint {
        return func(ctx context.Context, request interface{}) (interface{}, error) {
            start := time.Now()
            response, err := next(ctx, request)
            duration := time.Since(start)
            
            fmt.Printf("Request took %v\n", duration)
            return response, err
        }
    }
}

// Custom authentication middleware
func AuthMiddleware(token string) Middleware {
    return func(next Endpoint) Endpoint {
        return func(ctx context.Context, request interface{}) (interface{}, error) {
            // Check authentication
            if token != "valid-token" {
                return nil, errors.New("unauthorized")
            }
            return next(ctx, request)
        }
    }
}

func main() {
    endpoint := MakeSomeEndpoint(svc)
    endpoint = TimingMiddleware()(endpoint)
    endpoint = AuthMiddleware("valid-token")(endpoint)
    
    resp, err := endpoint(ctx, request)
}
```

### Multiple Transport Support

```go
package main

import "context"

// HTTP Transport
type HTTPTransport struct {
    Endpoint Endpoint
    Decoder  DecodeRequestFunc
    Encoder  EncodeResponseFunc
}

func (t *HTTPTransport) MakeHandler() interface{} {
    return NewServer(t.Endpoint, t.Decoder, t.Encoder)
}

// Use with multiple transports
func main() {
    svc := NewStringService()
    endpoint := MakeUppercaseEndpoint(svc)
    
    // HTTP transport
    httpTransport := &HTTPTransport{
        Endpoint: endpoint,
        Decoder:  JSONDecoder,
        Encoder:  JSONEncoder,
    }
    
    httpHandler := httpTransport.MakeHandler()
    
    // Could also create gRPC, Thrift, or other transports
}
```

## Testing

Run the comprehensive test suite:

```bash
go run test_gokit_emulator.go
```

Tests cover:
- Basic endpoint creation and execution
- Endpoint error handling
- Logging middleware
- Circuit breaker middleware
- Rate limit middleware
- Middleware chaining
- String service implementation (Uppercase, Count)
- HTTP server and transport
- JSON encoding/decoding
- Endpoint set creation
- Multiple middleware application
- Failer interface
- Context propagation
- HTTP transport creation

Total: 20 tests

## Integration with Existing Code

This emulator is designed to demonstrate Go-kit patterns:

```go
// Service layer - pure business logic
type MyService interface {
    DoSomething(ctx context.Context, input string) (string, error)
}

// Endpoint layer - request/response conversion
func MakeDoSomethingEndpoint(svc MyService) Endpoint {
    return func(ctx context.Context, request interface{}) (interface{}, error) {
        req := request.(DoSomethingRequest)
        result, err := svc.DoSomething(ctx, req.Input)
        if err != nil {
            return DoSomethingResponse{Err: err.Error()}, nil
        }
        return DoSomethingResponse{Result: result}, nil
    }
}

// Transport layer - HTTP, gRPC, etc.
func main() {
    svc := NewMyService()
    endpoint := MakeDoSomethingEndpoint(svc)
    endpoint = LoggingMiddleware(logger)(endpoint)
    
    server := NewServer(endpoint, decoder, encoder)
}
```

## Use Cases

Perfect for:
- **Microservices Architecture**: Build distributed systems with clean separation
- **Learning Go-kit Patterns**: Understand endpoint, transport, and service layers
- **Testing**: Test business logic independently from transport
- **Prototyping**: Quickly prototype microservice architectures
- **Education**: Teach microservice patterns and clean architecture
- **Development**: Develop without external dependencies

## Limitations

This is an emulator for development and testing purposes:
- No actual network I/O (simulated)
- Simplified HTTP server (no real HTTP)
- No gRPC or Thrift transports
- No distributed tracing implementation
- No metrics collection (Prometheus, etc.)
- No service discovery
- Simplified circuit breaker (no half-open state)
- No request context cancellation
- No streaming support

## Supported Features

### Core Features
- ✅ Endpoint abstraction
- ✅ Middleware pattern
- ✅ Transport layer separation
- ✅ Service layer definition
- ✅ Request/Response types
- ✅ Error handling

### Middleware
- ✅ Logging middleware
- ✅ Circuit breaker middleware
- ✅ Rate limiting middleware
- ✅ Timeout middleware (placeholder)
- ✅ Middleware chaining
- ✅ Custom middleware support

### Transport
- ✅ HTTP server abstraction
- ✅ Request decoding
- ✅ Response encoding
- ✅ JSON encoding/decoding
- ✅ Transport interface

### Patterns
- ✅ Endpoint set pattern
- ✅ Failer interface
- ✅ Context propagation
- ✅ Clean architecture
- ✅ Dependency injection

## Real-World Microservices Concepts

This emulator teaches the following concepts:

1. **Clean Architecture**: Separation of transport, endpoint, and service
2. **Middleware Pattern**: Composable cross-cutting concerns
3. **Request/Response Pattern**: Explicit API contracts
4. **Error Handling**: Explicit error propagation and handling
5. **Circuit Breaker**: Preventing cascading failures
6. **Rate Limiting**: Protecting services from overload
7. **Observability**: Logging and monitoring
8. **Testability**: Testing each layer independently
9. **Dependency Injection**: Explicit dependencies
10. **Interface-based Design**: Programming to interfaces

## Compatibility

Emulates core concepts of:
- Go-kit v0.x patterns
- Microservices best practices
- Clean architecture principles
- Hexagonal architecture pattern

## License

Part of the Emu-Soft project. See main repository LICENSE.
