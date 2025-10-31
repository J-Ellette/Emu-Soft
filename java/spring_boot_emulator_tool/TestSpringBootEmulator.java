/**
 * Test suite for Spring Boot Emulator
 * This file contains comprehensive tests for the Spring Boot web framework emulator
 */

import java.util.*;

class TestSpringBootEmulator {
    
    private static int testsRun = 0;
    private static int testsPassed = 0;
    private static int testsFailed = 0;
    
    // Test helper methods
    private static void assertTrue(boolean condition, String message) {
        testsRun++;
        if (condition) {
            testsPassed++;
            System.out.println("✓ PASS: " + message);
        } else {
            testsFailed++;
            System.out.println("✗ FAIL: " + message);
        }
    }
    
    private static void assertEquals(Object expected, Object actual, String message) {
        testsRun++;
        if (Objects.equals(expected, actual)) {
            testsPassed++;
            System.out.println("✓ PASS: " + message);
        } else {
            testsFailed++;
            System.out.println("✗ FAIL: " + message + " (expected: " + expected + ", got: " + actual + ")");
        }
    }
    
    private static void assertNotNull(Object obj, String message) {
        testsRun++;
        if (obj != null) {
            testsPassed++;
            System.out.println("✓ PASS: " + message);
        } else {
            testsFailed++;
            System.out.println("✗ FAIL: " + message + " (object was null)");
        }
    }
    
    // Test HttpRequest
    private static void testHttpRequest() {
        System.out.println("\n=== Testing HttpRequest ===");
        
        SpringBootEmulator.HttpRequest request = new SpringBootEmulator.HttpRequest("GET", "/api/users");
        
        assertEquals("GET", request.getMethod(), "Request method should be GET");
        assertEquals("/api/users", request.getPath(), "Request path should be /api/users");
        
        request.addParam("page", "1");
        request.addParam("size", "10");
        assertTrue(request.getParams().containsKey("page"), "Request should have page parameter");
        assertEquals("1", request.getParams().get("page"), "Page parameter should be 1");
        
        request.addHeader("Content-Type", "application/json");
        assertTrue(request.getHeaders().containsKey("Content-Type"), "Request should have Content-Type header");
        
        request.setBody("{\"name\":\"John\"}");
        assertEquals("{\"name\":\"John\"}", request.getBody(), "Request body should match");
    }
    
    // Test HttpResponse
    private static void testHttpResponse() {
        System.out.println("\n=== Testing HttpResponse ===");
        
        SpringBootEmulator.HttpResponse response = new SpringBootEmulator.HttpResponse();
        
        assertEquals(200, response.getStatus(), "Default status should be 200");
        
        response.status(404).body("Not Found");
        assertEquals(404, response.getStatus(), "Status should be 404");
        assertEquals("Not Found", response.getBody(), "Body should be 'Not Found'");
        
        response.header("X-Custom-Header", "test-value");
        assertTrue(response.getHeaders().containsKey("X-Custom-Header"), "Response should have custom header");
    }
    
    // Test ResponseEntity
    private static void testResponseEntity() {
        System.out.println("\n=== Testing ResponseEntity ===");
        
        SpringBootEmulator.ResponseEntity<String> okResponse = SpringBootEmulator.ResponseEntity.ok("Success");
        assertEquals(200, okResponse.getStatusCode(), "OK response should have status 200");
        assertEquals("Success", okResponse.getBody(), "OK response body should match");
        
        SpringBootEmulator.ResponseEntity<String> createdResponse = SpringBootEmulator.ResponseEntity.created("Created");
        assertEquals(201, createdResponse.getStatusCode(), "Created response should have status 201");
        
        SpringBootEmulator.ResponseEntity<String> badRequestResponse = SpringBootEmulator.ResponseEntity.badRequest("Bad Request");
        assertEquals(400, badRequestResponse.getStatusCode(), "Bad request should have status 400");
        
        SpringBootEmulator.ResponseEntity<String> notFoundResponse = SpringBootEmulator.ResponseEntity.notFound();
        assertEquals(404, notFoundResponse.getStatusCode(), "Not found should have status 404");
        
        SpringBootEmulator.ResponseEntity<String> errorResponse = SpringBootEmulator.ResponseEntity.internalServerError("Error");
        assertEquals(500, errorResponse.getStatusCode(), "Internal server error should have status 500");
    }
    
    // Test Route
    private static void testRoute() {
        System.out.println("\n=== Testing Route ===");
        
        SpringBootEmulator.Route route = new SpringBootEmulator.Route(
            "GET", 
            "/api/users",
            req -> "User list"
        );
        
        assertEquals("GET", route.getMethod(), "Route method should be GET");
        assertEquals("/api/users", route.getPath(), "Route path should be /api/users");
        
        assertTrue(route.matches("GET", "/api/users"), "Route should match GET /api/users");
        assertTrue(!route.matches("POST", "/api/users"), "Route should not match POST");
        assertTrue(!route.matches("GET", "/api/posts"), "Route should not match different path");
    }
    
    // Test Route with path variables
    private static void testRouteWithPathVariables() {
        System.out.println("\n=== Testing Route with Path Variables ===");
        
        SpringBootEmulator.Route route = new SpringBootEmulator.Route(
            "GET",
            "/api/users/{id}",
            req -> "User " + req.pathVariables.get("id")
        );
        
        assertTrue(route.matches("GET", "/api/users/123"), "Route should match with path variable");
        assertTrue(!route.matches("GET", "/api/users/123/posts"), "Route should not match longer path");
        
        Map<String, String> vars = route.extractPathVariables("/api/users/456");
        assertEquals("456", vars.get("id"), "Path variable 'id' should be extracted");
    }
    
    // Test ApplicationContext
    private static void testApplicationContext() {
        System.out.println("\n=== Testing ApplicationContext ===");
        
        SpringBootEmulator.ApplicationContext context = new SpringBootEmulator.ApplicationContext();
        
        String testBean = "Test Bean";
        context.registerBean(String.class, testBean);
        
        assertTrue(context.hasBean(String.class), "Context should have String bean");
        assertEquals(testBean, context.getBean(String.class), "Retrieved bean should match");
        
        assertTrue(!context.hasBean(Integer.class), "Context should not have Integer bean");
    }
    
    // Test SpringApplication routing
    private static void testSpringApplicationRouting() {
        System.out.println("\n=== Testing SpringApplication Routing ===");
        
        SpringBootEmulator.SpringApplication app = new SpringBootEmulator.SpringApplication();
        
        // Add routes
        app.addRoute("GET", "/", req -> "Home");
        app.addRoute("GET", "/api/users", req -> "User List");
        app.addRoute("POST", "/api/users", req -> "User Created");
        app.addRoute("GET", "/api/users/{id}", req -> "User " + req.pathVariables.get("id"));
        
        // Test home route
        SpringBootEmulator.HttpRequest homeRequest = new SpringBootEmulator.HttpRequest("GET", "/");
        SpringBootEmulator.HttpResponse homeResponse = app.handleRequest(homeRequest);
        assertEquals(200, homeResponse.getStatus(), "Home route should return 200");
        assertEquals("Home", homeResponse.getBody(), "Home route should return 'Home'");
        
        // Test user list route
        SpringBootEmulator.HttpRequest listRequest = new SpringBootEmulator.HttpRequest("GET", "/api/users");
        SpringBootEmulator.HttpResponse listResponse = app.handleRequest(listRequest);
        assertEquals(200, listResponse.getStatus(), "User list should return 200");
        assertEquals("User List", listResponse.getBody(), "User list body should match");
        
        // Test POST route
        SpringBootEmulator.HttpRequest postRequest = new SpringBootEmulator.HttpRequest("POST", "/api/users");
        SpringBootEmulator.HttpResponse postResponse = app.handleRequest(postRequest);
        assertEquals(200, postResponse.getStatus(), "POST should return 200");
        assertEquals("User Created", postResponse.getBody(), "POST body should match");
        
        // Test path variable route
        SpringBootEmulator.HttpRequest varRequest = new SpringBootEmulator.HttpRequest("GET", "/api/users/123");
        SpringBootEmulator.HttpResponse varResponse = app.handleRequest(varRequest);
        assertEquals(200, varResponse.getStatus(), "Path variable route should return 200");
        assertEquals("User 123", varResponse.getBody(), "Path variable should be extracted");
        
        // Test 404
        SpringBootEmulator.HttpRequest notFoundRequest = new SpringBootEmulator.HttpRequest("GET", "/not/found");
        SpringBootEmulator.HttpResponse notFoundResponse = app.handleRequest(notFoundRequest);
        assertEquals(404, notFoundResponse.getStatus(), "Unknown route should return 404");
        assertEquals("Not Found", notFoundResponse.getBody(), "404 response body should be 'Not Found'");
    }
    
    // Test SpringApplication with ResponseEntity
    private static void testSpringApplicationWithResponseEntity() {
        System.out.println("\n=== Testing SpringApplication with ResponseEntity ===");
        
        SpringBootEmulator.SpringApplication app = new SpringBootEmulator.SpringApplication();
        
        app.addRoute("GET", "/api/success", req -> SpringBootEmulator.ResponseEntity.ok("OK"));
        app.addRoute("POST", "/api/create", req -> SpringBootEmulator.ResponseEntity.created("Created"));
        app.addRoute("GET", "/api/error", req -> SpringBootEmulator.ResponseEntity.badRequest("Error"));
        
        SpringBootEmulator.HttpRequest okRequest = new SpringBootEmulator.HttpRequest("GET", "/api/success");
        SpringBootEmulator.HttpResponse okResponse = app.handleRequest(okRequest);
        assertEquals(200, okResponse.getStatus(), "ResponseEntity.ok should return 200");
        
        SpringBootEmulator.HttpRequest createRequest = new SpringBootEmulator.HttpRequest("POST", "/api/create");
        SpringBootEmulator.HttpResponse createResponse = app.handleRequest(createRequest);
        assertEquals(201, createResponse.getStatus(), "ResponseEntity.created should return 201");
        
        SpringBootEmulator.HttpRequest errorRequest = new SpringBootEmulator.HttpRequest("GET", "/api/error");
        SpringBootEmulator.HttpResponse errorResponse = app.handleRequest(errorRequest);
        assertEquals(400, errorResponse.getStatus(), "ResponseEntity.badRequest should return 400");
    }
    
    // Test ConfigurationProperties
    private static void testConfigurationProperties() {
        System.out.println("\n=== Testing ConfigurationProperties ===");
        
        SpringBootEmulator.ConfigurationProperties config = new SpringBootEmulator.ConfigurationProperties();
        
        config.setProperty("server.port", "8080");
        config.setProperty("app.name", "MyApp");
        
        assertEquals("8080", config.getProperty("server.port"), "Property should be retrieved");
        assertEquals("MyApp", config.getProperty("app.name"), "Property should be retrieved");
        assertEquals("default", config.getProperty("missing.prop", "default"), "Default value should be returned");
    }
    
    // Test ApiResponse
    private static void testApiResponse() {
        System.out.println("\n=== Testing ApiResponse ===");
        
        SpringBootEmulator.ApiResponse successResponse = SpringBootEmulator.ApiResponse.success("data");
        assertTrue(successResponse.toString().contains("\"success\":true"), "Success response should have success=true");
        
        SpringBootEmulator.ApiResponse errorResponse = SpringBootEmulator.ApiResponse.error("Error message");
        assertTrue(errorResponse.toString().contains("\"success\":false"), "Error response should have success=false");
        assertTrue(errorResponse.toString().contains("Error message"), "Error response should contain message");
    }
    
    // Test complete REST API workflow
    private static void testCompleteRestApiWorkflow() {
        System.out.println("\n=== Testing Complete REST API Workflow ===");
        
        SpringBootEmulator.SpringApplication app = new SpringBootEmulator.SpringApplication();
        
        // Simulate a user management API
        Map<String, String> users = new HashMap<>();
        
        // GET all users
        app.addRoute("GET", "/api/users", req -> {
            return SpringBootEmulator.ResponseEntity.ok(SpringBootEmulator.ApiResponse.success(users));
        });
        
        // GET user by ID
        app.addRoute("GET", "/api/users/{id}", req -> {
            String id = req.pathVariables.get("id");
            if (users.containsKey(id)) {
                return SpringBootEmulator.ResponseEntity.ok(users.get(id));
            } else {
                return SpringBootEmulator.ResponseEntity.notFound();
            }
        });
        
        // POST create user
        app.addRoute("POST", "/api/users", req -> {
            // In real implementation, would parse JSON body
            String id = String.valueOf(users.size() + 1);
            users.put(id, "User " + id);
            return SpringBootEmulator.ResponseEntity.created("User created with ID: " + id);
        });
        
        // PUT update user
        app.addRoute("PUT", "/api/users/{id}", req -> {
            String id = req.pathVariables.get("id");
            if (users.containsKey(id)) {
                users.put(id, "Updated User " + id);
                return SpringBootEmulator.ResponseEntity.ok("User updated");
            } else {
                return SpringBootEmulator.ResponseEntity.notFound();
            }
        });
        
        // DELETE user
        app.addRoute("DELETE", "/api/users/{id}", req -> {
            String id = req.pathVariables.get("id");
            if (users.containsKey(id)) {
                users.remove(id);
                return SpringBootEmulator.ResponseEntity.ok("User deleted");
            } else {
                return SpringBootEmulator.ResponseEntity.notFound();
            }
        });
        
        // Test workflow
        // 1. GET empty list
        SpringBootEmulator.HttpRequest getEmpty = new SpringBootEmulator.HttpRequest("GET", "/api/users");
        SpringBootEmulator.HttpResponse emptyResponse = app.handleRequest(getEmpty);
        assertEquals(200, emptyResponse.getStatus(), "GET empty list should return 200");
        
        // 2. POST create user
        SpringBootEmulator.HttpRequest postUser = new SpringBootEmulator.HttpRequest("POST", "/api/users");
        SpringBootEmulator.HttpResponse createResponse = app.handleRequest(postUser);
        assertEquals(201, createResponse.getStatus(), "POST should return 201");
        
        // 3. GET user by ID
        SpringBootEmulator.HttpRequest getUser = new SpringBootEmulator.HttpRequest("GET", "/api/users/1");
        SpringBootEmulator.HttpResponse getUserResponse = app.handleRequest(getUser);
        assertEquals(200, getUserResponse.getStatus(), "GET user should return 200");
        
        // 4. PUT update user
        SpringBootEmulator.HttpRequest putUser = new SpringBootEmulator.HttpRequest("PUT", "/api/users/1");
        SpringBootEmulator.HttpResponse updateResponse = app.handleRequest(putUser);
        assertEquals(200, updateResponse.getStatus(), "PUT should return 200");
        
        // 5. DELETE user
        SpringBootEmulator.HttpRequest deleteUser = new SpringBootEmulator.HttpRequest("DELETE", "/api/users/1");
        SpringBootEmulator.HttpResponse deleteResponse = app.handleRequest(deleteUser);
        assertEquals(200, deleteResponse.getStatus(), "DELETE should return 200");
        
        // 6. GET deleted user (should be 404)
        SpringBootEmulator.HttpRequest getDeleted = new SpringBootEmulator.HttpRequest("GET", "/api/users/1");
        SpringBootEmulator.HttpResponse notFoundResponse = app.handleRequest(getDeleted);
        assertEquals(404, notFoundResponse.getStatus(), "GET deleted user should return 404");
    }
    
    // Main test runner
    public static void main(String[] args) {
        System.out.println("Running Spring Boot Emulator Tests...\n");
        
        testHttpRequest();
        testHttpResponse();
        testResponseEntity();
        testRoute();
        testRouteWithPathVariables();
        testApplicationContext();
        testSpringApplicationRouting();
        testSpringApplicationWithResponseEntity();
        testConfigurationProperties();
        testApiResponse();
        testCompleteRestApiWorkflow();
        
        System.out.println("\n" + "=".repeat(50));
        System.out.println("Test Results:");
        System.out.println("  Total:  " + testsRun);
        System.out.println("  Passed: " + testsPassed);
        System.out.println("  Failed: " + testsFailed);
        System.out.println("=".repeat(50));
        
        if (testsFailed == 0) {
            System.out.println("\n✓ All tests passed!");
            System.exit(0);
        } else {
            System.out.println("\n✗ Some tests failed!");
            System.exit(1);
        }
    }
}
