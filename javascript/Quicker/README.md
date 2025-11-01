# Express.js Emulator - Web Framework for Node.js

**Developed by PowerShield, as an alternative to Express.js**


This module emulates the **Express.js** library, which is a minimal and flexible Node.js web application framework that provides a robust set of features for web and mobile applications.

## What is Express.js?

Express.js is the most popular Node.js web framework. It is designed to be:
- Minimal and unopinionated
- Fast and flexible
- Easy to use with a simple API
- Extensible through middleware
- Ideal for building web applications and APIs

## Features

This emulator implements core Express.js functionality:

### Application & Routing
- **HTTP Method Handlers**: GET, POST, PUT, DELETE, PATCH, and ALL
- **Route Parameters**: Dynamic path segments (e.g., `/users/:id`)
- **Query String Parsing**: Automatic parsing of URL query parameters
- **Route Matching**: Pattern-based route matching
- **Router**: Modular route handlers and sub-routers

### Middleware System
- **Middleware Pipeline**: Chain multiple middleware functions
- **Path-based Middleware**: Apply middleware to specific paths
- **Built-in Middleware**: JSON and URL-encoded body parsing
- **Static File Serving**: Serve static assets

### Request Object
- **URL Information**: Path, query parameters, original URL
- **Headers**: Access to request headers
- **Parameters**: Route parameters and query strings
- **Body**: Request body (with middleware parsing)
- **Method**: HTTP method

### Response Object
- **Status Codes**: Set HTTP status codes
- **Headers**: Set response headers
- **Body Content**: Send text, JSON, or other content
- **Redirects**: HTTP redirects
- **Cookies**: Set and clear cookies
- **Method Chaining**: Fluent API for building responses

## Usage Examples

### Basic Application

```javascript
const express = require('./express_emulator');

const app = express();

app.get('/', (req, res) => {
    res.send('Hello World!');
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
```

### Route Parameters

```javascript
const express = require('./express_emulator');
const app = express();

app.get('/users/:userId', (req, res) => {
    const userId = req.params.userId;
    res.json({ userId: userId, name: 'John Doe' });
});

// Access with: /users/123
```

### Query Parameters

```javascript
app.get('/search', (req, res) => {
    const query = req.query.q;
    const limit = req.query.limit || 10;
    res.json({ 
        query: query, 
        limit: limit,
        results: []
    });
});

// Access with: /search?q=express&limit=20
```

### POST Requests with JSON

```javascript
const express = require('./express_emulator');
const app = express();

app.use(express.json());

app.post('/api/users', (req, res) => {
    const user = req.body;
    // Process user data
    res.status(201).json({ 
        id: 1, 
        ...user 
    });
});
```

### Middleware

```javascript
const express = require('./express_emulator');
const app = express();

// Logging middleware
app.use((req, res, next) => {
    console.log(`${req.method} ${req.path}`);
    next();
});

// Authentication middleware
app.use('/admin', (req, res, next) => {
    if (!req.headers.authorization) {
        res.status(401).send('Unauthorized');
        return;
    }
    next();
});

app.get('/admin/dashboard', (req, res) => {
    res.send('Admin Dashboard');
});
```

### Router

```javascript
const express = require('./express_emulator');
const app = express();
const router = express.Router();

// Define routes on the router
router.get('/users', (req, res) => {
    res.json([{ id: 1, name: 'Alice' }]);
});

router.get('/users/:id', (req, res) => {
    res.json({ id: req.params.id, name: 'Alice' });
});

router.post('/users', (req, res) => {
    res.status(201).json({ id: 2, name: 'Bob' });
});

// Mount the router
app.use('/api', router);

// Routes available at:
// GET /api/users
// GET /api/users/:id
// POST /api/users
```

### Response Methods

```javascript
const express = require('./express_emulator');
const app = express();

// Send text
app.get('/text', (req, res) => {
    res.send('Plain text response');
});

// Send JSON
app.get('/json', (req, res) => {
    res.json({ message: 'JSON response' });
});

// Set status and send
app.get('/created', (req, res) => {
    res.status(201).send('Resource created');
});

// Send status only
app.delete('/resource/:id', (req, res) => {
    res.sendStatus(204);
});

// Redirect
app.get('/old-path', (req, res) => {
    res.redirect('/new-path');
});

// Set headers
app.get('/custom', (req, res) => {
    res.set('X-Custom-Header', 'Value');
    res.send('Response with custom header');
});

// Set cookies
app.get('/login', (req, res) => {
    res.cookie('session', 'abc123');
    res.send('Logged in');
});
```

### RESTful API Example

```javascript
const express = require('./express_emulator');
const app = express();

app.use(express.json());

let users = [
    { id: 1, name: 'Alice', email: 'alice@example.com' },
    { id: 2, name: 'Bob', email: 'bob@example.com' }
];

// List all users
app.get('/api/users', (req, res) => {
    res.json(users);
});

// Get single user
app.get('/api/users/:id', (req, res) => {
    const user = users.find(u => u.id === parseInt(req.params.id));
    if (!user) {
        res.status(404).json({ error: 'User not found' });
        return;
    }
    res.json(user);
});

// Create user
app.post('/api/users', (req, res) => {
    const newUser = {
        id: users.length + 1,
        name: req.body.name,
        email: req.body.email
    };
    users.push(newUser);
    res.status(201).json(newUser);
});

// Update user
app.put('/api/users/:id', (req, res) => {
    const user = users.find(u => u.id === parseInt(req.params.id));
    if (!user) {
        res.status(404).json({ error: 'User not found' });
        return;
    }
    user.name = req.body.name || user.name;
    user.email = req.body.email || user.email;
    res.json(user);
});

// Delete user
app.delete('/api/users/:id', (req, res) => {
    const index = users.findIndex(u => u.id === parseInt(req.params.id));
    if (index === -1) {
        res.status(404).json({ error: 'User not found' });
        return;
    }
    users.splice(index, 1);
    res.sendStatus(204);
});

app.listen(3000);
```

### Application Settings

```javascript
const express = require('./express_emulator');
const app = express();

// Set application settings
app.set('view engine', 'pug');
app.set('views', './views');
app.set('trust proxy', true);

// Get application settings
const viewEngine = app.get('view engine');
console.log(viewEngine); // 'pug'
```

### Static Files

```javascript
const express = require('./express_emulator');
const app = express();

// Serve static files from 'public' directory
app.use(express.static('public'));

// Now files in public/ directory are accessible
// e.g., public/style.css -> http://localhost:3000/style.css
```

## Testing

Run the comprehensive test suite:

```bash
node test_express_emulator.js
```

Tests cover:
- Request object functionality
- Response object methods
- Application routing (GET, POST, PUT, DELETE, PATCH)
- Route parameters and query strings
- Middleware execution
- Router and sub-routers
- Built-in middleware (JSON, URL-encoded, static)
- Error handling
- Integration scenarios (RESTful APIs)

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for Express.js in development and testing:

```javascript
// Instead of:
// const express = require('express');

// Use:
const express = require('./express_emulator');

// The rest of your code remains unchanged
const app = express();

app.get('/', (req, res) => {
    res.send('Hello World');
});
```

## Use Cases

Perfect for:
- **Local Development**: Develop web applications without Node.js
- **Testing**: Test HTTP handlers without a real server
- **Learning**: Understand web framework patterns
- **Prototyping**: Quickly prototype REST APIs
- **Education**: Teach web development concepts
- **CI/CD**: Run API tests without external dependencies

## Limitations

This is an emulator for development and testing purposes:
- No actual HTTP server (simulated requests/responses)
- No async middleware chain (simplified)
- No template rendering engines
- No advanced routing patterns (regex routes)
- No compression or security middleware
- No WebSocket support
- Single-threaded execution model

## Supported Features

### Core Features
- ✅ Application creation
- ✅ HTTP method routing (GET, POST, PUT, DELETE, PATCH, ALL)
- ✅ Route parameters (`:param`)
- ✅ Query string parsing
- ✅ Middleware pipeline
- ✅ Router and sub-routers
- ✅ Request object
- ✅ Response object
- ✅ Method chaining

### Response Methods
- ✅ res.send()
- ✅ res.json()
- ✅ res.status()
- ✅ res.sendStatus()
- ✅ res.redirect()
- ✅ res.set()
- ✅ res.get()
- ✅ res.cookie()
- ✅ res.clearCookie()
- ✅ res.type()

### Request Properties
- ✅ req.params
- ✅ req.query
- ✅ req.body
- ✅ req.headers
- ✅ req.method
- ✅ req.path
- ✅ req.url

### Built-in Middleware
- ✅ express.json()
- ✅ express.urlencoded()
- ✅ express.static()

## Real-World Web Framework Concepts

This emulator teaches the following concepts:

1. **Request-Response Cycle**: Understanding HTTP request/response flow
2. **Routing**: Mapping URLs to handler functions
3. **Middleware**: Composable request processing pipeline
4. **RESTful APIs**: Building resource-oriented APIs
5. **Error Handling**: Managing errors in web applications
6. **Route Parameters**: Dynamic URL segments
7. **Query Strings**: Parsing URL parameters
8. **HTTP Status Codes**: Using appropriate response codes

## Compatibility

Emulates core features of:
- Express.js 4.x API patterns
- Common routing and middleware patterns
- Standard RESTful API conventions

## License

Part of the Emu-Soft project. See main repository LICENSE.
