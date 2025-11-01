package main

// Developed by PowerShield, as an alternative to Go-kit
import (
	"context"
	"errors"
	"fmt"
)

// Simple test framework
type Test struct {
	name   string
	passed bool
	err    error
}

var tests []Test

func TestRunner(name string, fn func() error) {
	err := fn()
	tests = append(tests, Test{
		name:   name,
		passed: err == nil,
		err:    err,
	})
}

func PrintResults() {
	fmt.Println("\n=== Test Results ===")
	passed := 0
	for _, t := range tests {
		if t.passed {
			fmt.Printf("✓ %s\n", t.name)
			passed++
		} else {
			fmt.Printf("✗ %s: %v\n", t.name, t.err)
		}
	}
	fmt.Printf("\nPassed: %d/%d\n", passed, len(tests))
}

func runTests() {
	fmt.Println("Running Go-kit Emulator Tests")
	fmt.Println("==============================\n")
	
	// Test 1: Basic endpoint creation
	TestRunner("Basic Endpoint Creation", func() error {
		endpoint := func(ctx context.Context, request interface{}) (interface{}, error) {
			return "response", nil
		}
		
		ctx := context.Background()
		resp, err := endpoint(ctx, "request")
		if err != nil {
			return err
		}
		if resp != "response" {
			return fmt.Errorf("expected 'response', got %v", resp)
		}
		return nil
	})
	
	// Test 2: Endpoint with error
	TestRunner("Endpoint With Error", func() error {
		endpoint := func(ctx context.Context, request interface{}) (interface{}, error) {
			return nil, errors.New("test error")
		}
		
		ctx := context.Background()
		_, err := endpoint(ctx, "request")
		if err == nil {
			return errors.New("expected error, got nil")
		}
		return nil
	})
	
	// Test 3: Logging middleware
	TestRunner("Logging Middleware", func() error {
		logger := &SimpleLogger{}
		
		baseEndpoint := func(ctx context.Context, request interface{}) (interface{}, error) {
			return "logged", nil
		}
		
		endpoint := LoggingMiddleware(logger)(baseEndpoint)
		ctx := context.Background()
		resp, err := endpoint(ctx, "request")
		
		if err != nil {
			return err
		}
		if resp != "logged" {
			return fmt.Errorf("expected 'logged', got %v", resp)
		}
		return nil
	})
	
	// Test 4: Circuit breaker middleware
	TestRunner("Circuit Breaker Middleware", func() error {
		failingEndpoint := func(ctx context.Context, request interface{}) (interface{}, error) {
			return nil, errors.New("failure")
		}
		
		endpoint := CircuitBreakerMiddleware(2)(failingEndpoint)
		ctx := context.Background()
		
		// First failure
		_, err1 := endpoint(ctx, "request")
		if err1 == nil {
			return errors.New("expected error on first call")
		}
		
		// Second failure
		_, err2 := endpoint(ctx, "request")
		if err2 == nil {
			return errors.New("expected error on second call")
		}
		
		// Third call should trip circuit breaker
		_, err3 := endpoint(ctx, "request")
		if err3 == nil {
			return errors.New("expected circuit breaker to open")
		}
		if err3.Error() != "circuit breaker is open" {
			return fmt.Errorf("expected 'circuit breaker is open', got %v", err3)
		}
		
		return nil
	})
	
	// Test 5: Rate limit middleware
	TestRunner("Rate Limit Middleware", func() error {
		baseEndpoint := func(ctx context.Context, request interface{}) (interface{}, error) {
			return "ok", nil
		}
		
		endpoint := RateLimitMiddleware(2)(baseEndpoint)
		ctx := context.Background()
		
		// First request
		_, err1 := endpoint(ctx, "request")
		if err1 != nil {
			return fmt.Errorf("first request failed: %v", err1)
		}
		
		// Second request
		_, err2 := endpoint(ctx, "request")
		if err2 != nil {
			return fmt.Errorf("second request failed: %v", err2)
		}
		
		// Third request should be rate limited
		_, err3 := endpoint(ctx, "request")
		if err3 == nil {
			return errors.New("expected rate limit error")
		}
		
		return nil
	})
	
	// Test 6: Middleware chain
	TestRunner("Middleware Chain", func() error {
		logger := &SimpleLogger{}
		
		baseEndpoint := func(ctx context.Context, request interface{}) (interface{}, error) {
			return "chained", nil
		}
		
		endpoint := Chain(
			LoggingMiddleware(logger),
			RateLimitMiddleware(10),
		)(baseEndpoint)
		
		ctx := context.Background()
		resp, err := endpoint(ctx, "request")
		
		if err != nil {
			return err
		}
		if resp != "chained" {
			return fmt.Errorf("expected 'chained', got %v", resp)
		}
		return nil
	})
	
	// Test 7: String service - Uppercase
	TestRunner("String Service Uppercase", func() error {
		svc := NewStringService()
		ctx := context.Background()
		
		result, err := svc.Uppercase(ctx, "hello")
		if err != nil {
			return err
		}
		if result != "HELLO" {
			return fmt.Errorf("expected 'HELLO', got %v", result)
		}
		return nil
	})
	
	// Test 8: String service - Uppercase with empty string
	TestRunner("String Service Uppercase Empty", func() error {
		svc := NewStringService()
		ctx := context.Background()
		
		_, err := svc.Uppercase(ctx, "")
		if err == nil {
			return errors.New("expected error for empty string")
		}
		return nil
	})
	
	// Test 9: String service - Count
	TestRunner("String Service Count", func() error {
		svc := NewStringService()
		ctx := context.Background()
		
		result, err := svc.Count(ctx, "hello")
		if err != nil {
			return err
		}
		if result != 5 {
			return fmt.Errorf("expected 5, got %v", result)
		}
		return nil
	})
	
	// Test 10: Uppercase endpoint
	TestRunner("Uppercase Endpoint", func() error {
		svc := NewStringService()
		endpoint := MakeUppercaseEndpoint(svc)
		ctx := context.Background()
		
		req := UppercaseRequest{S: "test"}
		resp, err := endpoint(ctx, req)
		if err != nil {
			return err
		}
		
		uppercaseResp := resp.(UppercaseResponse)
		if uppercaseResp.V != "TEST" {
			return fmt.Errorf("expected 'TEST', got %v", uppercaseResp.V)
		}
		return nil
	})
	
	// Test 11: Count endpoint
	TestRunner("Count Endpoint", func() error {
		svc := NewStringService()
		endpoint := MakeCountEndpoint(svc)
		ctx := context.Background()
		
		req := CountRequest{S: "hello world"}
		resp, err := endpoint(ctx, req)
		if err != nil {
			return err
		}
		
		countResp := resp.(CountResponse)
		if countResp.V != 11 {
			return fmt.Errorf("expected 11, got %v", countResp.V)
		}
		return nil
	})
	
	// Test 12: HTTP Server
	TestRunner("HTTP Server", func() error {
		svc := NewStringService()
		endpoint := MakeUppercaseEndpoint(svc)
		
		server := NewServer(
			endpoint,
			func(ctx context.Context, r interface{}) (interface{}, error) {
				return r, nil
			},
			JSONEncoder,
		)
		
		req := UppercaseRequest{S: "server"}
		resp, err := server.ServeHTTP(req)
		if err != nil {
			return err
		}
		
		uppercaseResp := resp.(UppercaseResponse)
		if uppercaseResp.V != "SERVER" {
			return fmt.Errorf("expected 'SERVER', got %v", uppercaseResp.V)
		}
		return nil
	})
	
	// Test 13: JSON Encoder
	TestRunner("JSON Encoder", func() error {
		ctx := context.Background()
		response := UppercaseResponse{V: "test"}
		
		err := JSONEncoder(ctx, nil, response)
		if err != nil {
			return err
		}
		return nil
	})
	
	// Test 14: JSON Decoder
	TestRunner("JSON Decoder", func() error {
		ctx := context.Background()
		request := UppercaseRequest{S: "test"}
		
		decoded, err := JSONDecoder(ctx, request)
		if err != nil {
			return err
		}
		
		decodedReq := decoded.(UppercaseRequest)
		if decodedReq.S != "test" {
			return fmt.Errorf("expected 'test', got %v", decodedReq.S)
		}
		return nil
	})
	
	// Test 15: Endpoint set creation
	TestRunner("Endpoint Set Creation", func() error {
		svc := NewStringService()
		logger := &SimpleLogger{}
		
		endpointSet := NewEndpointSet(svc, LoggingMiddleware(logger))
		
		ctx := context.Background()
		
		// Test uppercase endpoint
		uppercaseReq := UppercaseRequest{S: "hello"}
		uppercaseResp, err := endpointSet.UppercaseEndpoint(ctx, uppercaseReq)
		if err != nil {
			return err
		}
		
		resp := uppercaseResp.(UppercaseResponse)
		if resp.V != "HELLO" {
			return fmt.Errorf("expected 'HELLO', got %v", resp.V)
		}
		
		// Test count endpoint
		countReq := CountRequest{S: "world"}
		countResp, err := endpointSet.CountEndpoint(ctx, countReq)
		if err != nil {
			return err
		}
		
		count := countResp.(CountResponse)
		if count.V != 5 {
			return fmt.Errorf("expected 5, got %v", count.V)
		}
		
		return nil
	})
	
	// Test 16: Multiple middleware application
	TestRunner("Multiple Middleware", func() error {
		svc := NewStringService()
		logger := &SimpleLogger{}
		
		endpoint := MakeUppercaseEndpoint(svc)
		endpoint = LoggingMiddleware(logger)(endpoint)
		endpoint = RateLimitMiddleware(10)(endpoint)
		endpoint = CircuitBreakerMiddleware(5)(endpoint)
		
		ctx := context.Background()
		req := UppercaseRequest{S: "middleware"}
		resp, err := endpoint(ctx, req)
		
		if err != nil {
			return err
		}
		
		uppercaseResp := resp.(UppercaseResponse)
		if uppercaseResp.V != "MIDDLEWARE" {
			return fmt.Errorf("expected 'MIDDLEWARE', got %v", uppercaseResp.V)
		}
		
		return nil
	})
	
	// Test 17: Failer interface
	TestRunner("Failer Interface", func() error {
		resp := UppercaseResponse{V: "test", Err: "test error"}
		err := resp.Failed()
		
		if err == nil {
			return errors.New("expected error from Failed()")
		}
		if err.Error() != "test error" {
			return fmt.Errorf("expected 'test error', got %v", err)
		}
		
		return nil
	})
	
	// Test 18: Successful response has no error
	TestRunner("Successful Response No Error", func() error {
		resp := UppercaseResponse{V: "test"}
		err := resp.Failed()
		
		if err != nil {
			return fmt.Errorf("expected no error, got %v", err)
		}
		
		return nil
	})
	
	// Test 19: HTTP Transport creation
	TestRunner("HTTP Transport", func() error {
		svc := NewStringService()
		endpoint := MakeUppercaseEndpoint(svc)
		
		transport := &HTTPTransport{
			Endpoint: endpoint,
			Decoder:  JSONDecoder,
			Encoder:  JSONEncoder,
		}
		
		handler := transport.MakeHandler()
		if handler == nil {
			return errors.New("expected handler, got nil")
		}
		
		return nil
	})
	
	// Test 20: Context propagation
	TestRunner("Context Propagation", func() error {
		var contextReceived bool
		
		endpoint := func(ctx context.Context, request interface{}) (interface{}, error) {
			if ctx != nil {
				contextReceived = true
			}
			return "ok", nil
		}
		
		ctx := context.Background()
		_, err := endpoint(ctx, "request")
		if err != nil {
			return err
		}
		
		if !contextReceived {
			return errors.New("context not propagated")
		}
		
		return nil
	})
	
	PrintResults()
}
