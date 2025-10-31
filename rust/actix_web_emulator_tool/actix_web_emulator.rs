use std::collections::HashMap;

// HttpRequest represents an HTTP request
#[derive(Clone)]
pub struct HttpRequest {
    pub method: String,
    pub path: String,
    pub headers: HashMap<String, String>,
    pub body: Vec<u8>,
    pub query_params: HashMap<String, String>,
    pub path_params: HashMap<String, String>,
}

impl HttpRequest {
    pub fn new(method: &str, path: &str) -> Self {
        HttpRequest {
            method: method.to_string(),
            path: path.to_string(),
            headers: HashMap::new(),
            body: Vec::new(),
            query_params: HashMap::new(),
            path_params: HashMap::new(),
        }
    }

    pub fn header(&self, name: &str) -> Option<&String> {
        self.headers.get(name)
    }

    pub fn match_info(&self) -> &HashMap<String, String> {
        &self.path_params
    }

    pub fn query_string(&self) -> String {
        self.query_params
            .iter()
            .map(|(k, v)| format!("{}={}", k, v))
            .collect::<Vec<_>>()
            .join("&")
    }
}

// HttpResponse represents an HTTP response
pub struct HttpResponse {
    pub status_code: u16,
    pub headers: HashMap<String, String>,
    pub body: Vec<u8>,
}

impl HttpResponse {
    pub fn new(status_code: u16) -> Self {
        HttpResponse {
            status_code,
            headers: HashMap::new(),
            body: Vec::new(),
        }
    }

    pub fn Ok() -> HttpResponseBuilder {
        HttpResponseBuilder::new(200)
    }

    pub fn Created() -> HttpResponseBuilder {
        HttpResponseBuilder::new(201)
    }

    pub fn BadRequest() -> HttpResponseBuilder {
        HttpResponseBuilder::new(400)
    }

    pub fn NotFound() -> HttpResponseBuilder {
        HttpResponseBuilder::new(404)
    }

    pub fn InternalServerError() -> HttpResponseBuilder {
        HttpResponseBuilder::new(500)
    }
}

// HttpResponseBuilder for building responses
pub struct HttpResponseBuilder {
    response: HttpResponse,
}

impl HttpResponseBuilder {
    pub fn new(status_code: u16) -> Self {
        HttpResponseBuilder {
            response: HttpResponse::new(status_code),
        }
    }

    pub fn header(mut self, key: &str, value: &str) -> Self {
        self.response.headers.insert(key.to_string(), value.to_string());
        self
    }

    pub fn body(mut self, body: impl Into<Vec<u8>>) -> HttpResponse {
        self.response.body = body.into();
        self.response
    }

    pub fn json<T: serde::Serialize>(mut self, data: &T) -> HttpResponse {
        let json_str = serde_json::to_string(data).unwrap_or_else(|_| "{}".to_string());
        self.response.headers.insert("Content-Type".to_string(), "application/json".to_string());
        self.response.body = json_str.into_bytes();
        self.response
    }

    pub fn finish(self) -> HttpResponse {
        self.response
    }
}

// Handler function type
pub type Handler = fn(HttpRequest) -> HttpResponse;

// Route structure
struct Route {
    method: String,
    path: String,
    handler: Handler,
}

impl Route {
    fn matches(&self, method: &str, path: &str) -> Option<HashMap<String, String>> {
        if self.method != method {
            return None;
        }

        let route_parts: Vec<&str> = self.path.split('/').filter(|s| !s.is_empty()).collect();
        let path_parts: Vec<&str> = path.split('/').filter(|s| !s.is_empty()).collect();

        if route_parts.len() != path_parts.len() {
            return None;
        }

        let mut params = HashMap::new();

        for (route_part, path_part) in route_parts.iter().zip(path_parts.iter()) {
            if route_part.starts_with('{') && route_part.ends_with('}') {
                let param_name = &route_part[1..route_part.len() - 1];
                params.insert(param_name.to_string(), path_part.to_string());
            } else if route_part != path_part {
                return None;
            }
        }

        Some(params)
    }
}

// App structure representing the web application
pub struct App {
    routes: Vec<Route>,
    middleware: Vec<Box<dyn Fn(&mut HttpRequest) -> Option<HttpResponse>>>,
}

impl App {
    pub fn new() -> Self {
        App {
            routes: Vec::new(),
            middleware: Vec::new(),
        }
    }

    pub fn route(mut self, path: &str, method: &str, handler: Handler) -> Self {
        self.routes.push(Route {
            method: method.to_string(),
            path: path.to_string(),
            handler,
        });
        self
    }

    pub fn wrap<F>(mut self, middleware: F) -> Self
    where
        F: Fn(&mut HttpRequest) -> Option<HttpResponse> + 'static,
    {
        self.middleware.push(Box::new(middleware));
        self
    }

    pub fn handle_request(&self, mut req: HttpRequest) -> HttpResponse {
        // Apply middleware
        for mw in &self.middleware {
            if let Some(response) = mw(&mut req) {
                return response;
            }
        }

        // Find matching route
        for route in &self.routes {
            if let Some(params) = route.matches(&req.method, &req.path) {
                req.path_params = params;
                return (route.handler)(req);
            }
        }

        // No route found
        HttpResponse::NotFound().body("Not Found")
    }

    pub fn run(self, bind_addr: &str) -> Result<(), String> {
        println!("Server running at {}", bind_addr);
        println!("(Simulated - no actual server started)");
        Ok(())
    }
}

// JSON extraction helper
pub struct Json<T> {
    pub inner: T,
}

impl<T: serde::de::DeserializeOwned> Json<T> {
    pub fn from_request(req: &HttpRequest) -> Result<Self, String> {
        let json_str = String::from_utf8(req.body.clone())
            .map_err(|_| "Invalid UTF-8".to_string())?;
        
        let data: T = serde_json::from_str(&json_str)
            .map_err(|e| format!("JSON parse error: {}", e))?;
        
        Ok(Json { inner: data })
    }

    pub fn into_inner(self) -> T {
        self.inner
    }
}

// Path parameter extraction
pub struct Path<T> {
    pub inner: T,
}

impl Path<String> {
    pub fn from_request(req: &HttpRequest, param_name: &str) -> Result<Self, String> {
        req.path_params
            .get(param_name)
            .map(|s| Path { inner: s.clone() })
            .ok_or_else(|| format!("Path parameter '{}' not found", param_name))
    }
}

// Query parameter extraction
pub struct Query<T> {
    pub inner: T,
}

impl Query<HashMap<String, String>> {
    pub fn from_request(req: &HttpRequest) -> Self {
        Query {
            inner: req.query_params.clone(),
        }
    }
}

// Web module for common utilities
pub mod web {
    use super::*;

    pub fn get() -> String {
        "GET".to_string()
    }

    pub fn post() -> String {
        "POST".to_string()
    }

    pub fn put() -> String {
        "PUT".to_string()
    }

    pub fn delete() -> String {
        "DELETE".to_string()
    }

    pub fn patch() -> String {
        "PATCH".to_string()
    }

    pub fn resource(path: &str) -> String {
        path.to_string()
    }
}

// Middleware helpers
pub mod middleware {
    use super::*;

    pub fn logger() -> impl Fn(&mut HttpRequest) -> Option<HttpResponse> {
        move |req: &mut HttpRequest| {
            println!("{} {}", req.method, req.path);
            None
        }
    }

    pub fn cors() -> impl Fn(&mut HttpRequest) -> Option<HttpResponse> {
        move |_req: &mut HttpRequest| {
            // CORS handling would go here
            None
        }
    }
}

// Macro-like helpers for routing
pub fn scope(prefix: &str) -> Scope {
    Scope {
        prefix: prefix.to_string(),
        routes: Vec::new(),
    }
}

pub struct Scope {
    prefix: String,
    routes: Vec<(String, String, Handler)>,
}

impl Scope {
    pub fn route(mut self, path: &str, method: &str, handler: Handler) -> Self {
        let full_path = format!("{}{}", self.prefix, path);
        self.routes.push((full_path, method.to_string(), handler));
        self
    }

    pub fn service(mut self, nested_scope: Scope) -> Self {
        for (path, method, handler) in nested_scope.routes {
            let full_path = format!("{}{}", self.prefix, path);
            self.routes.push((full_path, method, handler));
        }
        self
    }
}

// HttpServer for running the application
pub struct HttpServer;

impl HttpServer {
    pub fn new<F>(_factory: F) -> Self
    where
        F: Fn() -> App + 'static,
    {
        HttpServer
    }

    pub fn bind(self, addr: &str) -> Result<Self, String> {
        println!("Binding to {}", addr);
        Ok(self)
    }

    pub fn run(self) -> Result<(), String> {
        println!("Server started (simulated)");
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_routing() {
        let app = App::new()
            .route("/", "GET", |_req| {
                HttpResponse::Ok().body("Hello World")
            });

        let req = HttpRequest::new("GET", "/");
        let resp = app.handle_request(req);
        
        assert_eq!(resp.status_code, 200);
        assert_eq!(String::from_utf8_lossy(&resp.body), "Hello World");
    }

    #[test]
    fn test_path_parameters() {
        let app = App::new()
            .route("/users/{id}", "GET", |req| {
                let id = req.path_params.get("id").unwrap();
                HttpResponse::Ok().body(format!("User {}", id))
            });

        let req = HttpRequest::new("GET", "/users/123");
        let resp = app.handle_request(req);
        
        assert_eq!(resp.status_code, 200);
        assert_eq!(String::from_utf8_lossy(&resp.body), "User 123");
    }

    #[test]
    fn test_not_found() {
        let app = App::new()
            .route("/", "GET", |_req| {
                HttpResponse::Ok().body("Home")
            });

        let req = HttpRequest::new("GET", "/notfound");
        let resp = app.handle_request(req);
        
        assert_eq!(resp.status_code, 404);
    }
}
