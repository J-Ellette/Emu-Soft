package main

// Developed by PowerShield, as an alternative to Gin
import (
	"encoding/json"
	"fmt"
	"net/url"
	"strings"
)

// Context represents the context of an HTTP request in Gin
type Context struct {
	Request  *Request
	Response *Response
	Params   map[string]string
	handlers []HandlerFunc
	index    int
}

// Request represents an HTTP request
type Request struct {
	Method  string
	Path    string
	Headers map[string]string
	Body    []byte
	Query   url.Values
}

// Response represents an HTTP response
type Response struct {
	StatusCode int
	Headers    map[string]string
	Body       []byte
}

// HandlerFunc defines the handler function type
type HandlerFunc func(*Context)

// Engine is the core of the Gin framework
type Engine struct {
	routes     map[string]map[string][]HandlerFunc // method -> path -> handlers
	middleware []HandlerFunc
}

// RouterGroup is used for grouping routes
type RouterGroup struct {
	engine      *Engine
	prefix      string
	middleware  []HandlerFunc
}

// H is a shortcut for map[string]interface{}
type H map[string]interface{}

// New creates a new Engine instance
func New() *Engine {
	return &Engine{
		routes:     make(map[string]map[string][]HandlerFunc),
		middleware: []HandlerFunc{},
	}
}

// Default creates an Engine with default middleware
func Default() *Engine {
	engine := New()
	engine.Use(Logger(), Recovery())
	return engine
}

// Use adds global middleware
func (e *Engine) Use(middleware ...HandlerFunc) {
	e.middleware = append(e.middleware, middleware...)
}

// Group creates a new router group
func (e *Engine) Group(prefix string, handlers ...HandlerFunc) *RouterGroup {
	return &RouterGroup{
		engine:     e,
		prefix:     prefix,
		middleware: handlers,
	}
}

// GET registers a GET route
func (e *Engine) GET(path string, handlers ...HandlerFunc) {
	e.addRoute("GET", path, handlers)
}

// POST registers a POST route
func (e *Engine) POST(path string, handlers ...HandlerFunc) {
	e.addRoute("POST", path, handlers)
}

// PUT registers a PUT route
func (e *Engine) PUT(path string, handlers ...HandlerFunc) {
	e.addRoute("PUT", path, handlers)
}

// DELETE registers a DELETE route
func (e *Engine) DELETE(path string, handlers ...HandlerFunc) {
	e.addRoute("DELETE", path, handlers)
}

// PATCH registers a PATCH route
func (e *Engine) PATCH(path string, handlers ...HandlerFunc) {
	e.addRoute("PATCH", path, handlers)
}

// addRoute adds a route to the engine
func (e *Engine) addRoute(method, path string, handlers []HandlerFunc) {
	if e.routes[method] == nil {
		e.routes[method] = make(map[string][]HandlerFunc)
	}
	// Combine global middleware with route handlers
	allHandlers := append(e.middleware, handlers...)
	e.routes[method][path] = allHandlers
}

// ServeHTTP simulates handling an HTTP request
func (e *Engine) ServeHTTP(method, path string, body []byte, headers map[string]string) *Response {
	// Parse query string from path
	pathParts := strings.SplitN(path, "?", 2)
	cleanPath := pathParts[0]
	queryString := ""
	if len(pathParts) > 1 {
		queryString = pathParts[1]
	}

	queryValues, _ := url.ParseQuery(queryString)

	// Create context
	ctx := &Context{
		Request: &Request{
			Method:  method,
			Path:    cleanPath,
			Headers: headers,
			Body:    body,
			Query:   queryValues,
		},
		Response: &Response{
			StatusCode: 200,
			Headers:    make(map[string]string),
			Body:       []byte{},
		},
		Params:   make(map[string]string),
		handlers: []HandlerFunc{},
		index:    -1,
	}

	// Find matching route
	if routes, ok := e.routes[method]; ok {
		for routePath, handlers := range routes {
			params := matchRoute(routePath, cleanPath)
			if params != nil {
				ctx.Params = params
				ctx.handlers = handlers
				ctx.Next()
				return ctx.Response
			}
		}
	}

	// No route found
	ctx.Response.StatusCode = 404
	ctx.Response.Body = []byte("404 Not Found")
	return ctx.Response
}

// matchRoute checks if a route pattern matches a path and extracts parameters
func matchRoute(pattern, path string) map[string]string {
	patternParts := strings.Split(pattern, "/")
	pathParts := strings.Split(path, "/")

	if len(patternParts) != len(pathParts) {
		return nil
	}

	params := make(map[string]string)
	for i, part := range patternParts {
		if strings.HasPrefix(part, ":") {
			// This is a parameter
			paramName := part[1:]
			params[paramName] = pathParts[i]
		} else if part != pathParts[i] {
			// Literal part doesn't match
			return nil
		}
	}

	return params
}

// RouterGroup methods

// Group creates a sub-group
func (rg *RouterGroup) Group(prefix string, handlers ...HandlerFunc) *RouterGroup {
	return &RouterGroup{
		engine:     rg.engine,
		prefix:     rg.prefix + prefix,
		middleware: append(rg.middleware, handlers...),
	}
}

// Use adds middleware to the group
func (rg *RouterGroup) Use(middleware ...HandlerFunc) {
	rg.middleware = append(rg.middleware, middleware...)
}

// GET registers a GET route in the group
func (rg *RouterGroup) GET(path string, handlers ...HandlerFunc) {
	rg.handle("GET", path, handlers)
}

// POST registers a POST route in the group
func (rg *RouterGroup) POST(path string, handlers ...HandlerFunc) {
	rg.handle("POST", path, handlers)
}

// PUT registers a PUT route in the group
func (rg *RouterGroup) PUT(path string, handlers ...HandlerFunc) {
	rg.handle("PUT", path, handlers)
}

// DELETE registers a DELETE route in the group
func (rg *RouterGroup) DELETE(path string, handlers ...HandlerFunc) {
	rg.handle("DELETE", path, handlers)
}

// PATCH registers a PATCH route in the group
func (rg *RouterGroup) PATCH(path string, handlers ...HandlerFunc) {
	rg.handle("PATCH", path, handlers)
}

// handle registers a route with the group's prefix and middleware
func (rg *RouterGroup) handle(method, path string, handlers []HandlerFunc) {
	fullPath := rg.prefix + path
	allHandlers := append(rg.middleware, handlers...)
	rg.engine.addRoute(method, fullPath, allHandlers)
}

// Context methods

// Next executes the next handler in the chain
func (c *Context) Next() {
	c.index++
	for c.index < len(c.handlers) {
		c.handlers[c.index](c)
		c.index++
	}
}

// Abort prevents pending handlers from being called
func (c *Context) Abort() {
	c.index = len(c.handlers)
}

// AbortWithStatus aborts with a status code
func (c *Context) AbortWithStatus(code int) {
	c.Response.StatusCode = code
	c.Abort()
}

// Param returns a URL parameter value
func (c *Context) Param(key string) string {
	return c.Params[key]
}

// Query returns a query parameter value
func (c *Context) Query(key string) string {
	return c.Request.Query.Get(key)
}

// DefaultQuery returns a query parameter with a default value
func (c *Context) DefaultQuery(key, defaultValue string) string {
	value := c.Request.Query.Get(key)
	if value == "" {
		return defaultValue
	}
	return value
}

// GetHeader returns a request header value
func (c *Context) GetHeader(key string) string {
	return c.Request.Headers[key]
}

// Status sets the HTTP status code
func (c *Context) Status(code int) {
	c.Response.StatusCode = code
}

// Header sets a response header
func (c *Context) Header(key, value string) {
	c.Response.Headers[key] = value
}

// JSON sends a JSON response
func (c *Context) JSON(code int, obj interface{}) {
	c.Response.StatusCode = code
	c.Response.Headers["Content-Type"] = "application/json"
	data, err := json.Marshal(obj)
	if err != nil {
		c.Response.StatusCode = 500
		c.Response.Body = []byte(`{"error":"Failed to marshal JSON"}`)
		return
	}
	c.Response.Body = data
}

// String sends a string response
func (c *Context) String(code int, format string, values ...interface{}) {
	c.Response.StatusCode = code
	c.Response.Headers["Content-Type"] = "text/plain"
	c.Response.Body = []byte(fmt.Sprintf(format, values...))
}

// Data sends raw data response
func (c *Context) Data(code int, contentType string, data []byte) {
	c.Response.StatusCode = code
	c.Response.Headers["Content-Type"] = contentType
	c.Response.Body = data
}

// BindJSON binds the request body to a struct
func (c *Context) BindJSON(obj interface{}) error {
	return json.Unmarshal(c.Request.Body, obj)
}

// Set stores a value in the context
func (c *Context) Set(key string, value interface{}) {
	// In a real implementation, this would use a map
	// For this emulator, we'll keep it simple
}

// Get retrieves a value from the context
func (c *Context) Get(key string) (interface{}, bool) {
	// In a real implementation, this would retrieve from a map
	return nil, false
}

// Middleware

// Logger returns a logging middleware
func Logger() HandlerFunc {
	return func(c *Context) {
		fmt.Printf("[GIN] %s %s\n", c.Request.Method, c.Request.Path)
		c.Next()
	}
}

// Recovery returns a recovery middleware that recovers from panics
func Recovery() HandlerFunc {
	return func(c *Context) {
		defer func() {
			if err := recover(); err != nil {
				fmt.Printf("[GIN] Recovery from panic: %v\n", err)
				c.AbortWithStatus(500)
			}
		}()
		c.Next()
	}
}

// Run starts the server (simulated in this emulator)
func (e *Engine) Run(addr ...string) error {
	address := ":8080"
	if len(addr) > 0 {
		address = addr[0]
	}
	fmt.Printf("[GIN] Listening and serving HTTP on %s\n", address)
	fmt.Println("[GIN] This is an emulator - server is not actually running")
	return nil
}
