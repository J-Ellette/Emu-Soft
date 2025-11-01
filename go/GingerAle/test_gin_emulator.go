package main

// Developed by PowerShield, as an alternative to Gin
import (
	"encoding/json"
	"fmt"
)

// Helper function to run a test
func runTest(name string, testFunc func() bool) {
	result := "PASS"
	if !testFunc() {
		result = "FAIL"
	}
	fmt.Printf("[%s] %s\n", result, name)
}

// Test basic routing
func testBasicRouting() bool {
	r := New()
	r.GET("/hello", func(c *Context) {
		c.String(200, "Hello World")
	})

	resp := r.ServeHTTP("GET", "/hello", nil, map[string]string{})
	return resp.StatusCode == 200 && string(resp.Body) == "Hello World"
}

// Test JSON response
func testJSONResponse() bool {
	r := New()
	r.GET("/json", func(c *Context) {
		c.JSON(200, H{
			"message": "success",
			"code":    200,
		})
	})

	resp := r.ServeHTTP("GET", "/json", nil, map[string]string{})
	if resp.StatusCode != 200 {
		return false
	}

	var result map[string]interface{}
	err := json.Unmarshal(resp.Body, &result)
	if err != nil {
		return false
	}

	return result["message"] == "success"
}

// Test URL parameters
func testURLParameters() bool {
	r := New()
	r.GET("/users/:id", func(c *Context) {
		id := c.Param("id")
		c.JSON(200, H{"userId": id})
	})

	resp := r.ServeHTTP("GET", "/users/123", nil, map[string]string{})
	if resp.StatusCode != 200 {
		return false
	}

	var result map[string]interface{}
	json.Unmarshal(resp.Body, &result)
	return result["userId"] == "123"
}

// Test query parameters
func testQueryParameters() bool {
	r := New()
	r.GET("/search", func(c *Context) {
		q := c.Query("q")
		limit := c.DefaultQuery("limit", "10")
		c.JSON(200, H{
			"query": q,
			"limit": limit,
		})
	})

	resp := r.ServeHTTP("GET", "/search?q=test&limit=20", nil, map[string]string{})
	if resp.StatusCode != 200 {
		return false
	}

	var result map[string]interface{}
	json.Unmarshal(resp.Body, &result)
	return result["query"] == "test" && result["limit"] == "20"
}

// Test default query parameters
func testDefaultQueryParameters() bool {
	r := New()
	r.GET("/search", func(c *Context) {
		limit := c.DefaultQuery("limit", "10")
		c.String(200, limit)
	})

	resp := r.ServeHTTP("GET", "/search", nil, map[string]string{})
	return resp.StatusCode == 200 && string(resp.Body) == "10"
}

// Test POST request
func testPOSTRequest() bool {
	r := New()
	r.POST("/users", func(c *Context) {
		var user map[string]interface{}
		err := c.BindJSON(&user)
		if err != nil {
			c.JSON(400, H{"error": "Invalid JSON"})
			return
		}
		c.JSON(201, H{
			"id":   1,
			"name": user["name"],
		})
	})

	body := []byte(`{"name":"John Doe"}`)
	resp := r.ServeHTTP("POST", "/users", body, map[string]string{})
	
	if resp.StatusCode != 201 {
		return false
	}

	var result map[string]interface{}
	json.Unmarshal(resp.Body, &result)
	return result["name"] == "John Doe"
}

// Test middleware
func testMiddleware() bool {
	r := New()
	
	executed := false
	r.Use(func(c *Context) {
		executed = true
		c.Next()
	})

	r.GET("/test", func(c *Context) {
		c.String(200, "OK")
	})

	r.ServeHTTP("GET", "/test", nil, map[string]string{})
	return executed
}

// Test middleware order
func testMiddlewareOrder() bool {
	r := New()
	
	order := ""
	r.Use(func(c *Context) {
		order += "1"
		c.Next()
		order += "4"
	})

	r.Use(func(c *Context) {
		order += "2"
		c.Next()
		order += "3"
	})

	r.GET("/test", func(c *Context) {
		// Handler executes between middleware
	})

	r.ServeHTTP("GET", "/test", nil, map[string]string{})
	return order == "1234"
}

// Test abort in middleware
func testAbort() bool {
	r := New()
	
	handlerExecuted := false
	r.Use(func(c *Context) {
		c.AbortWithStatus(401)
	})

	r.GET("/test", func(c *Context) {
		handlerExecuted = true
		c.String(200, "OK")
	})

	resp := r.ServeHTTP("GET", "/test", nil, map[string]string{})
	return resp.StatusCode == 401 && !handlerExecuted
}

// Test router group
func testRouterGroup() bool {
	r := New()
	
	api := r.Group("/api")
	api.GET("/users", func(c *Context) {
		c.String(200, "Users")
	})

	resp := r.ServeHTTP("GET", "/api/users", nil, map[string]string{})
	return resp.StatusCode == 200 && string(resp.Body) == "Users"
}

// Test nested router groups
func testNestedRouterGroups() bool {
	r := New()
	
	api := r.Group("/api")
	v1 := api.Group("/v1")
	v1.GET("/users", func(c *Context) {
		c.String(200, "V1 Users")
	})

	resp := r.ServeHTTP("GET", "/api/v1/users", nil, map[string]string{})
	return resp.StatusCode == 200 && string(resp.Body) == "V1 Users"
}

// Test group middleware
func testGroupMiddleware() bool {
	r := New()
	
	executed := false
	api := r.Group("/api", func(c *Context) {
		executed = true
		c.Next()
	})
	
	api.GET("/test", func(c *Context) {
		c.String(200, "OK")
	})

	r.ServeHTTP("GET", "/api/test", nil, map[string]string{})
	return executed
}

// Test multiple HTTP methods
func testMultipleHTTPMethods() bool {
	r := New()
	
	r.GET("/resource", func(c *Context) {
		c.String(200, "GET")
	})
	
	r.POST("/resource", func(c *Context) {
		c.String(201, "POST")
	})
	
	r.PUT("/resource", func(c *Context) {
		c.String(200, "PUT")
	})
	
	r.DELETE("/resource", func(c *Context) {
		c.String(204, "DELETE")
	})

	getResp := r.ServeHTTP("GET", "/resource", nil, map[string]string{})
	postResp := r.ServeHTTP("POST", "/resource", nil, map[string]string{})
	putResp := r.ServeHTTP("PUT", "/resource", nil, map[string]string{})
	deleteResp := r.ServeHTTP("DELETE", "/resource", nil, map[string]string{})

	return getResp.StatusCode == 200 &&
		postResp.StatusCode == 201 &&
		putResp.StatusCode == 200 &&
		deleteResp.StatusCode == 204
}

// Test 404 handling
func test404Handling() bool {
	r := New()
	r.GET("/exists", func(c *Context) {
		c.String(200, "OK")
	})

	resp := r.ServeHTTP("GET", "/notfound", nil, map[string]string{})
	return resp.StatusCode == 404
}

// Test response headers
func testResponseHeaders() bool {
	r := New()
	r.GET("/test", func(c *Context) {
		c.Header("X-Custom-Header", "CustomValue")
		c.String(200, "OK")
	})

	resp := r.ServeHTTP("GET", "/test", nil, map[string]string{})
	return resp.Headers["X-Custom-Header"] == "CustomValue"
}

// Test request headers
func testRequestHeaders() bool {
	r := New()
	r.GET("/test", func(c *Context) {
		auth := c.GetHeader("Authorization")
		c.String(200, auth)
	})

	headers := map[string]string{
		"Authorization": "Bearer token123",
	}
	resp := r.ServeHTTP("GET", "/test", nil, headers)
	return string(resp.Body) == "Bearer token123"
}

// Test Default engine with middleware
func testDefaultEngine() bool {
	r := Default()
	r.GET("/test", func(c *Context) {
		c.String(200, "OK")
	})

	resp := r.ServeHTTP("GET", "/test", nil, map[string]string{})
	return resp.StatusCode == 200
}

// Test RESTful API pattern
func testRESTfulAPI() bool {
	r := New()
	
	users := make(map[string]interface{})
	
	// Create user
	r.POST("/users", func(c *Context) {
		var user map[string]interface{}
		c.BindJSON(&user)
		users[user["id"].(string)] = user
		c.JSON(201, user)
	})
	
	// Get user
	r.GET("/users/:id", func(c *Context) {
		id := c.Param("id")
		if user, exists := users[id]; exists {
			c.JSON(200, user)
		} else {
			c.JSON(404, H{"error": "User not found"})
		}
	})
	
	// Create a user
	createBody := []byte(`{"id":"1","name":"Alice"}`)
	createResp := r.ServeHTTP("POST", "/users", createBody, map[string]string{})
	
	if createResp.StatusCode != 201 {
		return false
	}
	
	// Get the user
	getResp := r.ServeHTTP("GET", "/users/1", nil, map[string]string{})
	if getResp.StatusCode != 200 {
		return false
	}
	
	var result map[string]interface{}
	json.Unmarshal(getResp.Body, &result)
	return result["name"] == "Alice"
}

// Test complex URL parameter patterns
func testComplexURLParameters() bool {
	r := New()
	r.GET("/api/:version/users/:id/posts/:postId", func(c *Context) {
		version := c.Param("version")
		userId := c.Param("id")
		postId := c.Param("postId")
		c.JSON(200, H{
			"version": version,
			"userId":  userId,
			"postId":  postId,
		})
	})

	resp := r.ServeHTTP("GET", "/api/v1/users/123/posts/456", nil, map[string]string{})
	if resp.StatusCode != 200 {
		return false
	}

	var result map[string]interface{}
	json.Unmarshal(resp.Body, &result)
	return result["version"] == "v1" && result["userId"] == "123" && result["postId"] == "456"
}

// Test content type headers
func testContentTypeHeaders() bool {
	r := New()
	r.GET("/json", func(c *Context) {
		c.JSON(200, H{"type": "json"})
	})
	
	r.GET("/text", func(c *Context) {
		c.String(200, "text")
	})

	jsonResp := r.ServeHTTP("GET", "/json", nil, map[string]string{})
	textResp := r.ServeHTTP("GET", "/text", nil, map[string]string{})

	return jsonResp.Headers["Content-Type"] == "application/json" &&
		textResp.Headers["Content-Type"] == "text/plain"
}

func main() {
	fmt.Println("Running Gin Emulator Tests...")
	fmt.Println("==============================")

	runTest("Basic Routing", testBasicRouting)
	runTest("JSON Response", testJSONResponse)
	runTest("URL Parameters", testURLParameters)
	runTest("Query Parameters", testQueryParameters)
	runTest("Default Query Parameters", testDefaultQueryParameters)
	runTest("POST Request", testPOSTRequest)
	runTest("Middleware", testMiddleware)
	runTest("Middleware Order", testMiddlewareOrder)
	runTest("Abort in Middleware", testAbort)
	runTest("Router Group", testRouterGroup)
	runTest("Nested Router Groups", testNestedRouterGroups)
	runTest("Group Middleware", testGroupMiddleware)
	runTest("Multiple HTTP Methods", testMultipleHTTPMethods)
	runTest("404 Handling", test404Handling)
	runTest("Response Headers", testResponseHeaders)
	runTest("Request Headers", testRequestHeaders)
	runTest("Default Engine", testDefaultEngine)
	runTest("RESTful API Pattern", testRESTfulAPI)
	runTest("Complex URL Parameters", testComplexURLParameters)
	runTest("Content Type Headers", testContentTypeHeaders)

	fmt.Println("==============================")
	fmt.Println("All tests completed!")
}
