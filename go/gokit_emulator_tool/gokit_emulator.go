package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
)

// Endpoint represents a single RPC method
type Endpoint func(ctx context.Context, request interface{}) (response interface{}, err error)

// Middleware is a chainable behavior modifier for endpoints
type Middleware func(Endpoint) Endpoint

// Service interface represents a microservice
type Service interface{}

// Server represents a transport server
type Server interface {
	ServeHTTP(request interface{}) (interface{}, error)
}

// HTTPServer implements HTTP transport
type HTTPServer struct {
	endpoint Endpoint
	decoder  DecodeRequestFunc
	encoder  EncodeResponseFunc
}

// DecodeRequestFunc extracts a user-domain request object from an HTTP request
type DecodeRequestFunc func(ctx context.Context, r interface{}) (request interface{}, err error)

// EncodeResponseFunc encodes the passed response object to the HTTP response writer
type EncodeResponseFunc func(ctx context.Context, w interface{}, response interface{}) error

// NewServer constructs a new HTTP server
func NewServer(
	e Endpoint,
	dec DecodeRequestFunc,
	enc EncodeResponseFunc,
) *HTTPServer {
	return &HTTPServer{
		endpoint: e,
		decoder:  dec,
		encoder:  enc,
	}
}

// ServeHTTP implements the Server interface
func (s *HTTPServer) ServeHTTP(request interface{}) (interface{}, error) {
	ctx := context.Background()
	
	// Decode request
	req, err := s.decoder(ctx, request)
	if err != nil {
		return nil, err
	}
	
	// Call endpoint
	response, err := s.endpoint(ctx, req)
	if err != nil {
		return nil, err
	}
	
	// Encode response
	err = s.encoder(ctx, nil, response)
	if err != nil {
		return nil, err
	}
	
	return response, nil
}

// Chain is a helper function for composing middlewares
func Chain(outer Middleware, others ...Middleware) Middleware {
	return func(next Endpoint) Endpoint {
		for i := len(others) - 1; i >= 0; i-- {
			next = others[i](next)
		}
		return outer(next)
	}
}

// Logging middleware example
type Logger interface {
	Log(keyvals ...interface{}) error
}

// LoggingMiddleware logs endpoint requests and responses
func LoggingMiddleware(logger Logger) Middleware {
	return func(next Endpoint) Endpoint {
		return func(ctx context.Context, request interface{}) (interface{}, error) {
			logger.Log("msg", "calling endpoint", "request", request)
			response, err := next(ctx, request)
			if err != nil {
				logger.Log("msg", "endpoint error", "err", err)
				return nil, err
			}
			logger.Log("msg", "endpoint success", "response", response)
			return response, nil
		}
	}
}

// SimpleLogger implements Logger interface
type SimpleLogger struct{}

func (l *SimpleLogger) Log(keyvals ...interface{}) error {
	for i := 0; i < len(keyvals); i += 2 {
		if i+1 < len(keyvals) {
			fmt.Printf("%v=%v ", keyvals[i], keyvals[i+1])
		}
	}
	fmt.Println()
	return nil
}

// CircuitBreakerMiddleware implements circuit breaker pattern
func CircuitBreakerMiddleware(maxFailures int) Middleware {
	failures := 0
	
	return func(next Endpoint) Endpoint {
		return func(ctx context.Context, request interface{}) (interface{}, error) {
			if failures >= maxFailures {
				return nil, errors.New("circuit breaker is open")
			}
			
			response, err := next(ctx, request)
			if err != nil {
				failures++
				return nil, err
			}
			
			failures = 0
			return response, nil
		}
	}
}

// RateLimitMiddleware implements rate limiting
func RateLimitMiddleware(maxRequests int) Middleware {
	requests := 0
	
	return func(next Endpoint) Endpoint {
		return func(ctx context.Context, request interface{}) (interface{}, error) {
			requests++
			if requests > maxRequests {
				return nil, errors.New("rate limit exceeded")
			}
			
			response, err := next(ctx, request)
			
			return response, err
		}
	}
}

// TimeoutMiddleware adds timeout to endpoints
func TimeoutMiddleware() Middleware {
	return func(next Endpoint) Endpoint {
		return func(ctx context.Context, request interface{}) (interface{}, error) {
			// In a real implementation, this would use context.WithTimeout
			// For this emulator, we just pass through
			return next(ctx, request)
		}
	}
}

// JSONEncoder encodes responses as JSON
func JSONEncoder(ctx context.Context, w interface{}, response interface{}) error {
	data, err := json.Marshal(response)
	if err != nil {
		return err
	}
	
	// In a real implementation, this would write to http.ResponseWriter
	// For emulation, we just verify it can be marshaled
	_ = data
	return nil
}

// JSONDecoder decodes JSON requests
func JSONDecoder(ctx context.Context, r interface{}) (interface{}, error) {
	// In a real implementation, this would read from http.Request
	// For emulation, we assume r is already the decoded object
	return r, nil
}

// MakeEndpoint creates an endpoint from a service method
func MakeEndpoint(svc Service, method func(ctx context.Context, request interface{}) (interface{}, error)) Endpoint {
	return func(ctx context.Context, request interface{}) (interface{}, error) {
		return method(ctx, request)
	}
}

// Transport layer abstractions
type Transport interface {
	MakeHandler() interface{}
}

// HTTPTransport implements HTTP-based transport
type HTTPTransport struct {
	Endpoint Endpoint
	Decoder  DecodeRequestFunc
	Encoder  EncodeResponseFunc
}

func (t *HTTPTransport) MakeHandler() interface{} {
	return NewServer(t.Endpoint, t.Decoder, t.Encoder)
}

// Request/Response types for common patterns
type Request struct {
	Data map[string]interface{}
}

type Response struct {
	Data   map[string]interface{}
	Err    string
}

// ErrorEncoder encodes errors
func ErrorEncoder(ctx context.Context, err error, w interface{}) {
	// In a real implementation, this would write error to response
	fmt.Printf("Error: %v\n", err)
}

// ServiceMiddleware wraps entire services
type ServiceMiddleware func(Service) Service

// Example service implementation
type StringService interface {
	Uppercase(ctx context.Context, s string) (string, error)
	Count(ctx context.Context, s string) (int, error)
}

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

// Request/Response types for string service
type UppercaseRequest struct {
	S string `json:"s"`
}

type UppercaseResponse struct {
	V   string `json:"v"`
	Err string `json:"err,omitempty"`
}

type CountRequest struct {
	S string `json:"s"`
}

type CountResponse struct {
	V int `json:"v"`
}

// Endpoints for string service
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

func MakeCountEndpoint(svc StringService) Endpoint {
	return func(ctx context.Context, request interface{}) (interface{}, error) {
		req := request.(CountRequest)
		v, err := svc.Count(ctx, req.S)
		if err != nil {
			return CountResponse{}, err
		}
		return CountResponse{V: v}, nil
	}
}

// Failer is an interface that should be implemented by response types
type Failer interface {
	Failed() error
}

func (r UppercaseResponse) Failed() error {
	if r.Err != "" {
		return errors.New(r.Err)
	}
	return nil
}

// EndpointSet holds all service endpoints
type EndpointSet struct {
	UppercaseEndpoint Endpoint
	CountEndpoint     Endpoint
}

// NewEndpointSet creates endpoint set from service
func NewEndpointSet(svc StringService, middlewares ...Middleware) EndpointSet {
	uppercaseEndpoint := MakeUppercaseEndpoint(svc)
	countEndpoint := MakeCountEndpoint(svc)
	
	// Apply middleware
	for _, mw := range middlewares {
		uppercaseEndpoint = mw(uppercaseEndpoint)
		countEndpoint = mw(countEndpoint)
	}
	
	return EndpointSet{
		UppercaseEndpoint: uppercaseEndpoint,
		CountEndpoint:     countEndpoint,
	}
}

func main() {
	fmt.Println("Go-kit Microservices Toolkit Emulator")
	fmt.Println("======================================")
	fmt.Println()
	
	// Create a service
	svc := NewStringService()
	
	// Create logger
	logger := &SimpleLogger{}
	
	// Create endpoint with middleware
	endpoint := MakeUppercaseEndpoint(svc)
	endpoint = LoggingMiddleware(logger)(endpoint)
	endpoint = CircuitBreakerMiddleware(3)(endpoint)
	
	// Test the endpoint
	ctx := context.Background()
	
	// Test 1: Success case
	req1 := UppercaseRequest{S: "hello"}
	resp1, err1 := endpoint(ctx, req1)
	if err1 != nil {
		fmt.Printf("Error: %v\n", err1)
	} else {
		fmt.Printf("Response: %+v\n", resp1)
	}
	
	fmt.Println()
	
	// Test 2: Empty string (error case)
	req2 := UppercaseRequest{S: ""}
	resp2, err2 := endpoint(ctx, req2)
	fmt.Printf("Response: %+v, Error: %v\n", resp2, err2)
	
	fmt.Println()
	
	// Test 3: Count endpoint
	countEndpoint := MakeCountEndpoint(svc)
	countReq := CountRequest{S: "hello world"}
	countResp, _ := countEndpoint(ctx, countReq)
	fmt.Printf("Count Response: %+v\n", countResp)
	
	fmt.Println()
	
	// Test 4: HTTP Server
	server := NewServer(
		MakeUppercaseEndpoint(svc),
		func(ctx context.Context, r interface{}) (interface{}, error) {
			return r, nil
		},
		JSONEncoder,
	)
	
	serverResp, serverErr := server.ServeHTTP(UppercaseRequest{S: "test"})
	fmt.Printf("Server Response: %+v, Error: %v\n", serverResp, serverErr)
	
	fmt.Println()
	
	// Test 5: Middleware chain
	chainedEndpoint := Chain(
		LoggingMiddleware(logger),
		RateLimitMiddleware(5),
		CircuitBreakerMiddleware(3),
	)(MakeUppercaseEndpoint(svc))
	
	chainResp, _ := chainedEndpoint(ctx, UppercaseRequest{S: "chained"})
	fmt.Printf("Chained Response: %+v\n", chainResp)
	
	fmt.Println("\n✓ Go-kit emulator demonstration complete")
	fmt.Println()
	
	// Run tests
	runTests()
}
