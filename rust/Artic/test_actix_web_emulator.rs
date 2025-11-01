// Developed by PowerShield, as an alternative to Actix-web

mod actix_web_emulator;

use actix_web_emulator::*;

fn main() {
    println!("=== Actix-web Emulator Test Suite ===\n");

    // Test 1: Basic GET request
    println!("Test 1: Basic GET Request");
    let app = App::new()
        .route("/", "GET", |_req| {
            HttpResponse::Ok().body("Hello, World!")
        });

    let req = HttpRequest::new("GET", "/");
    let resp = app.handle_request(req);
    
    if resp.status_code == 200 && String::from_utf8_lossy(&resp.body) == "Hello, World!" {
        println!("✓ Basic GET request works");
    } else {
        println!("❌ Basic GET request failed");
    }

    // Test 2: JSON response
    println!("\nTest 2: JSON Response");
    #[derive(serde::Serialize)]
    struct User {
        id: u32,
        name: String,
    }

    let app = App::new()
        .route("/user", "GET", |_req| {
            let user = User {
                id: 1,
                name: "Alice".to_string(),
            };
            HttpResponse::Ok().json(&user)
        });

    let req = HttpRequest::new("GET", "/user");
    let resp = app.handle_request(req);
    
    if resp.status_code == 200 && resp.headers.get("Content-Type").unwrap() == "application/json" {
        println!("✓ JSON response works");
        println!("  Body: {}", String::from_utf8_lossy(&resp.body));
    } else {
        println!("❌ JSON response failed");
    }

    // Test 3: Path parameters
    println!("\nTest 3: Path Parameters");
    let app = App::new()
        .route("/users/{id}", "GET", |req| {
            if let Some(id) = req.path_params.get("id") {
                HttpResponse::Ok().body(format!("User ID: {}", id))
            } else {
                HttpResponse::BadRequest().body("Missing ID")
            }
        });

    let req = HttpRequest::new("GET", "/users/123");
    let resp = app.handle_request(req);
    
    if resp.status_code == 200 && String::from_utf8_lossy(&resp.body) == "User ID: 123" {
        println!("✓ Path parameters work");
    } else {
        println!("❌ Path parameters failed");
    }

    // Test 4: Multiple path parameters
    println!("\nTest 4: Multiple Path Parameters");
    let app = App::new()
        .route("/api/{version}/users/{id}", "GET", |req| {
            let version = req.path_params.get("version").unwrap();
            let id = req.path_params.get("id").unwrap();
            HttpResponse::Ok().body(format!("API v{}, User {}", version, id))
        });

    let req = HttpRequest::new("GET", "/api/v1/users/456");
    let resp = app.handle_request(req);
    
    if resp.status_code == 200 && String::from_utf8_lossy(&resp.body).contains("v1") && 
       String::from_utf8_lossy(&resp.body).contains("456") {
        println!("✓ Multiple path parameters work");
    } else {
        println!("❌ Multiple path parameters failed");
    }

    // Test 5: POST request
    println!("\nTest 5: POST Request");
    let app = App::new()
        .route("/users", "POST", |_req| {
            HttpResponse::Created().body("User created")
        });

    let req = HttpRequest::new("POST", "/users");
    let resp = app.handle_request(req);
    
    if resp.status_code == 201 && String::from_utf8_lossy(&resp.body) == "User created" {
        println!("✓ POST request works");
    } else {
        println!("❌ POST request failed");
    }

    // Test 6: PUT request
    println!("\nTest 6: PUT Request");
    let app = App::new()
        .route("/users/{id}", "PUT", |req| {
            let id = req.path_params.get("id").unwrap();
            HttpResponse::Ok().body(format!("User {} updated", id))
        });

    let req = HttpRequest::new("PUT", "/users/789");
    let resp = app.handle_request(req);
    
    if resp.status_code == 200 && String::from_utf8_lossy(&resp.body).contains("789") {
        println!("✓ PUT request works");
    } else {
        println!("❌ PUT request failed");
    }

    // Test 7: DELETE request
    println!("\nTest 7: DELETE Request");
    let app = App::new()
        .route("/users/{id}", "DELETE", |req| {
            let id = req.path_params.get("id").unwrap();
            HttpResponse::Ok().body(format!("User {} deleted", id))
        });

    let req = HttpRequest::new("DELETE", "/users/999");
    let resp = app.handle_request(req);
    
    if resp.status_code == 200 && String::from_utf8_lossy(&resp.body).contains("999") {
        println!("✓ DELETE request works");
    } else {
        println!("❌ DELETE request failed");
    }

    // Test 8: 404 Not Found
    println!("\nTest 8: 404 Not Found");
    let app = App::new()
        .route("/", "GET", |_req| {
            HttpResponse::Ok().body("Home")
        });

    let req = HttpRequest::new("GET", "/notfound");
    let resp = app.handle_request(req);
    
    if resp.status_code == 404 {
        println!("✓ 404 Not Found works");
    } else {
        println!("❌ 404 Not Found failed, got status: {}", resp.status_code);
    }

    // Test 9: Custom headers
    println!("\nTest 9: Custom Headers");
    let app = App::new()
        .route("/headers", "GET", |_req| {
            HttpResponse::Ok()
                .header("X-Custom-Header", "CustomValue")
                .header("X-Request-ID", "12345")
                .body("Headers set")
        });

    let req = HttpRequest::new("GET", "/headers");
    let resp = app.handle_request(req);
    
    if resp.headers.get("X-Custom-Header").unwrap() == "CustomValue" {
        println!("✓ Custom headers work");
    } else {
        println!("❌ Custom headers failed");
    }

    // Test 10: Middleware
    println!("\nTest 10: Middleware");
    let app = App::new()
        .wrap(|_req| {
            println!("  Middleware executed");
            None // Continue to handler
        })
        .route("/test", "GET", |_req| {
            HttpResponse::Ok().body("Success")
        });

    let req = HttpRequest::new("GET", "/test");
    let resp = app.handle_request(req);
    
    if resp.status_code == 200 {
        println!("✓ Middleware works");
    } else {
        println!("❌ Middleware failed");
    }

    // Test 11: Error responses
    println!("\nTest 11: Error Responses");
    let app = App::new()
        .route("/error", "GET", |_req| {
            HttpResponse::InternalServerError().body("Server Error")
        });

    let req = HttpRequest::new("GET", "/error");
    let resp = app.handle_request(req);
    
    if resp.status_code == 500 {
        println!("✓ Error responses work");
    } else {
        println!("❌ Error responses failed");
    }

    // Test 12: BadRequest response
    println!("\nTest 12: BadRequest Response");
    let app = App::new()
        .route("/validate", "POST", |_req| {
            HttpResponse::BadRequest().body("Invalid data")
        });

    let req = HttpRequest::new("POST", "/validate");
    let resp = app.handle_request(req);
    
    if resp.status_code == 400 {
        println!("✓ BadRequest response works");
    } else {
        println!("❌ BadRequest response failed");
    }

    // Test 13: Multiple routes
    println!("\nTest 13: Multiple Routes");
    let app = App::new()
        .route("/", "GET", |_req| HttpResponse::Ok().body("Home"))
        .route("/about", "GET", |_req| HttpResponse::Ok().body("About"))
        .route("/contact", "GET", |_req| HttpResponse::Ok().body("Contact"));

    let req1 = HttpRequest::new("GET", "/");
    let resp1 = app.handle_request(req1);
    
    let req2 = HttpRequest::new("GET", "/about");
    let resp2 = app.handle_request(req2);
    
    if resp1.status_code == 200 && resp2.status_code == 200 {
        println!("✓ Multiple routes work");
    } else {
        println!("❌ Multiple routes failed");
    }

    // Test 14: Query parameters (setup)
    println!("\nTest 14: Query Parameters");
    let app = App::new()
        .route("/search", "GET", |req| {
            if let Some(q) = req.query_params.get("q") {
                HttpResponse::Ok().body(format!("Searching for: {}", q))
            } else {
                HttpResponse::Ok().body("No query")
            }
        });

    let mut req = HttpRequest::new("GET", "/search");
    req.query_params.insert("q".to_string(), "rust".to_string());
    let resp = app.handle_request(req);
    
    if resp.status_code == 200 && String::from_utf8_lossy(&resp.body).contains("rust") {
        println!("✓ Query parameters work");
    } else {
        println!("❌ Query parameters failed");
    }

    // Test 15: Request headers
    println!("\nTest 15: Request Headers");
    let app = App::new()
        .route("/auth", "GET", |req| {
            if let Some(token) = req.header("Authorization") {
                HttpResponse::Ok().body(format!("Authorized: {}", token))
            } else {
                HttpResponse::Ok().body("No authorization")
            }
        });

    let mut req = HttpRequest::new("GET", "/auth");
    req.headers.insert("Authorization".to_string(), "Bearer token123".to_string());
    let resp = app.handle_request(req);
    
    if resp.status_code == 200 && String::from_utf8_lossy(&resp.body).contains("token123") {
        println!("✓ Request headers work");
    } else {
        println!("❌ Request headers failed");
    }

    println!("\n=== All Tests Completed ===");
}
