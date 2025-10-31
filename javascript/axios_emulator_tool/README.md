# Axios Emulator - HTTP Client for JavaScript

This module emulates the **axios** library, which is a promise-based HTTP client for the browser and Node.js. It provides an easy-to-use API for making HTTP requests and handling responses.

## What is Axios?

Axios is one of the most popular HTTP client libraries for JavaScript. It is designed to:
- Make XMLHttpRequests from the browser
- Make HTTP requests from Node.js
- Support the Promise API
- Intercept request and response
- Transform request and response data
- Cancel requests
- Automatic JSON data transformation

## Features

This emulator implements core axios functionality:

### HTTP Methods
- **GET**: Retrieve data
- **POST**: Submit data
- **PUT**: Update data (full replacement)
- **PATCH**: Update data (partial)
- **DELETE**: Delete data
- **HEAD**: Get headers only
- **OPTIONS**: Get supported methods

### Request Configuration
- **baseURL**: Base URL for requests
- **timeout**: Request timeout
- **headers**: Custom headers
- **params**: URL query parameters
- **validateStatus**: Custom status validation

### Instances
- **create()**: Create custom axios instances
- **defaults**: Default configuration
- **Independent instances**: Multiple instances with different configs

### Interceptors
- **Request interceptors**: Modify requests before sending
- **Response interceptors**: Transform responses
- **Error interceptors**: Handle errors globally
- **Eject**: Remove interceptors

### Cancel Tokens
- **CancelToken**: Cancel pending requests
- **source()**: Create cancel token source
- **isCancel()**: Check if error is cancellation

### Utilities
- **all()**: Handle concurrent requests
- **spread()**: Spread response array
- **isAxiosError()**: Check if error is from axios

### Response Structure
- **data**: Response data
- **status**: HTTP status code
- **statusText**: HTTP status message
- **headers**: Response headers
- **config**: Request configuration

## Usage Examples

### Basic Requests

```javascript
const axios = require('./axios_emulator');

// GET request
axios.get('/api/users')
    .then(response => {
        console.log(response.data);
    })
    .catch(error => {
        console.error(error);
    });

// POST request
axios.post('/api/users', {
    name: 'John Doe',
    email: 'john@example.com'
})
    .then(response => {
        console.log('User created:', response.data);
    });

// PUT request
axios.put('/api/users/1', {
    name: 'John Updated'
})
    .then(response => {
        console.log('User updated:', response.data);
    });

// DELETE request
axios.delete('/api/users/1')
    .then(response => {
        console.log('User deleted');
    });
```

### Async/Await

```javascript
const axios = require('./axios_emulator');

async function getUsers() {
    try {
        const response = await axios.get('/api/users');
        return response.data;
    } catch (error) {
        console.error('Error fetching users:', error);
        throw error;
    }
}

async function createUser(userData) {
    const response = await axios.post('/api/users', userData);
    return response.data;
}
```

### Request Configuration

```javascript
const axios = require('./axios_emulator');

// With query parameters
axios.get('/api/users', {
    params: {
        page: 1,
        limit: 10,
        sort: 'name'
    }
});

// With custom headers
axios.get('/api/protected', {
    headers: {
        'Authorization': 'Bearer token123',
        'X-Custom-Header': 'value'
    }
});

// With timeout
axios.get('/api/slow-endpoint', {
    timeout: 5000  // 5 seconds
});

// With base URL
axios.get('/users', {
    baseURL: 'https://api.example.com'
});
// Requests to: https://api.example.com/users
```

### Creating Instances

```javascript
const axios = require('./axios_emulator');

// Create instance with default config
const api = axios.create({
    baseURL: 'https://api.example.com',
    timeout: 10000,
    headers: {
        'X-API-Key': 'your-api-key'
    }
});

// Use the instance
api.get('/users');           // GET https://api.example.com/users
api.post('/users', data);    // POST https://api.example.com/users

// Multiple instances for different APIs
const apiV1 = axios.create({ baseURL: 'https://api.example.com/v1' });
const apiV2 = axios.create({ baseURL: 'https://api.example.com/v2' });
```

### Request Interceptors

```javascript
const axios = require('./axios_emulator');

const api = axios.create();

// Add request interceptor
api.interceptors.request.use(
    config => {
        // Add auth token to every request
        const token = localStorage.getItem('token');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        
        // Log request
        console.log('Request:', config.method, config.url);
        
        return config;
    },
    error => {
        return Promise.reject(error);
    }
);

// Use the api instance
api.get('/api/protected-resource');
```

### Response Interceptors

```javascript
const axios = require('./axios_emulator');

const api = axios.create();

// Add response interceptor
api.interceptors.response.use(
    response => {
        // Transform response data
        response.data.timestamp = Date.now();
        
        // Log response
        console.log('Response:', response.status, response.data);
        
        return response;
    },
    error => {
        // Handle errors globally
        if (error.response) {
            console.error('Response error:', error.response.status);
            
            // Handle specific status codes
            if (error.response.status === 401) {
                // Redirect to login
                window.location.href = '/login';
            }
        }
        
        return Promise.reject(error);
    }
);
```

### Eject Interceptors

```javascript
const axios = require('./axios_emulator');

const api = axios.create();

// Add interceptor and save ID
const interceptorId = api.interceptors.request.use(
    config => {
        config.headers['X-Temporary'] = 'value';
        return config;
    }
);

// Later, remove the interceptor
api.interceptors.request.eject(interceptorId);
```

### Cancel Tokens

```javascript
const axios = require('./axios_emulator');

// Using CancelToken.source
const source = axios.CancelToken.source();

axios.get('/api/data', {
    cancelToken: source.token
}).catch(error => {
    if (axios.isCancel(error)) {
        console.log('Request canceled:', error.message);
    }
});

// Cancel the request
source.cancel('Operation canceled by user');

// Using CancelToken constructor
let cancel;
axios.get('/api/data', {
    cancelToken: new axios.CancelToken(c => {
        cancel = c;
    })
});

// Cancel the request
cancel('User clicked cancel button');
```

### Concurrent Requests

```javascript
const axios = require('./axios_emulator');

// Execute multiple requests concurrently
axios.all([
    axios.get('/api/users'),
    axios.get('/api/posts'),
    axios.get('/api/comments')
])
.then(axios.spread((users, posts, comments) => {
    console.log('Users:', users.data);
    console.log('Posts:', posts.data);
    console.log('Comments:', comments.data);
}))
.catch(error => {
    console.error('One or more requests failed:', error);
});

// Alternative with async/await
async function fetchAll() {
    try {
        const [users, posts, comments] = await axios.all([
            axios.get('/api/users'),
            axios.get('/api/posts'),
            axios.get('/api/comments')
        ]);
        
        return {
            users: users.data,
            posts: posts.data,
            comments: comments.data
        };
    } catch (error) {
        console.error('Error:', error);
    }
}
```

### Error Handling

```javascript
const axios = require('./axios_emulator');

// Using try-catch with async/await
async function fetchUser(id) {
    try {
        const response = await axios.get(`/api/users/${id}`);
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error)) {
            // Axios error
            if (error.response) {
                // Server responded with error status
                console.error('Status:', error.response.status);
                console.error('Data:', error.response.data);
            } else if (error.request) {
                // Request was made but no response
                console.error('No response received');
            } else {
                // Error setting up request
                console.error('Request error:', error.message);
            }
        }
        throw error;
    }
}

// Using .catch()
axios.get('/api/users/999')
    .then(response => {
        console.log(response.data);
    })
    .catch(error => {
        if (error.response) {
            console.error('Error response:', error.response.status);
        }
    });
```

### Complete RESTful API Example

```javascript
const axios = require('./axios_emulator');

class UserService {
    constructor() {
        this.api = axios.create({
            baseURL: 'https://api.example.com',
            timeout: 5000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // Add auth interceptor
        this.api.interceptors.request.use(config => {
            const token = this.getToken();
            if (token) {
                config.headers['Authorization'] = `Bearer ${token}`;
            }
            return config;
        });
        
        // Add error handling interceptor
        this.api.interceptors.response.use(
            response => response,
            error => {
                if (error.response?.status === 401) {
                    this.handleUnauthorized();
                }
                return Promise.reject(error);
            }
        );
    }
    
    getToken() {
        return localStorage.getItem('authToken');
    }
    
    handleUnauthorized() {
        localStorage.removeItem('authToken');
        window.location.href = '/login';
    }
    
    // Get all users
    async getUsers(params = {}) {
        const response = await this.api.get('/users', { params });
        return response.data;
    }
    
    // Get single user
    async getUser(id) {
        const response = await this.api.get(`/users/${id}`);
        return response.data;
    }
    
    // Create user
    async createUser(userData) {
        const response = await this.api.post('/users', userData);
        return response.data;
    }
    
    // Update user
    async updateUser(id, userData) {
        const response = await this.api.put(`/users/${id}`, userData);
        return response.data;
    }
    
    // Partial update
    async patchUser(id, updates) {
        const response = await this.api.patch(`/users/${id}`, updates);
        return response.data;
    }
    
    // Delete user
    async deleteUser(id) {
        await this.api.delete(`/users/${id}`);
    }
    
    // Search users
    async searchUsers(query) {
        const response = await this.api.get('/users/search', {
            params: { q: query }
        });
        return response.data;
    }
}

// Usage
const userService = new UserService();

async function main() {
    try {
        // Get all users
        const users = await userService.getUsers({ page: 1, limit: 10 });
        console.log('Users:', users);
        
        // Create new user
        const newUser = await userService.createUser({
            name: 'Alice Johnson',
            email: 'alice@example.com'
        });
        console.log('Created:', newUser);
        
        // Update user
        const updated = await userService.updateUser(newUser.id, {
            name: 'Alice Smith'
        });
        console.log('Updated:', updated);
        
        // Delete user
        await userService.deleteUser(newUser.id);
        console.log('Deleted');
    } catch (error) {
        console.error('Error:', error.message);
    }
}
```

## Testing

Run the comprehensive test suite:

```bash
node test_axios_emulator.js
```

Tests cover:
- Basic HTTP methods (GET, POST, PUT, DELETE, PATCH)
- Request configuration (baseURL, params, headers, timeout)
- Custom instances
- Request and response interceptors
- Error handling
- Cancel tokens
- Mock responses
- Utilities (all, spread, isAxiosError)
- Response structure
- Integration scenarios

Total: 28 tests, all passing

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for axios in development and testing:

```javascript
// Instead of:
// const axios = require('axios');

// Use:
const axios = require('./axios_emulator');

// The rest of your code remains unchanged
const response = await axios.get('/api/users');
```

## Use Cases

Perfect for:
- **Local Development**: Develop without real HTTP servers
- **Testing**: Test HTTP client logic without network requests
- **Learning**: Understand HTTP client patterns
- **Prototyping**: Quickly prototype API interactions
- **Education**: Teach HTTP and async programming
- **CI/CD**: Run tests without external dependencies

## Limitations

This is an emulator for development and testing purposes:
- No actual network requests (simulated responses)
- Limited error types compared to real axios
- No browser-specific features (XMLHttpRequest)
- No automatic retry logic (can be added with interceptors)
- No upload/download progress events
- Simplified response transformation

## Supported Features

### Core Features
- ✅ HTTP method shortcuts (get, post, put, delete, patch, head, options)
- ✅ Promise-based API
- ✅ Request configuration
- ✅ Response structure
- ✅ Custom instances

### Advanced Features
- ✅ Request interceptors
- ✅ Response interceptors
- ✅ Interceptor ejection
- ✅ Cancel tokens
- ✅ Concurrent requests (all, spread)
- ✅ Error identification (isAxiosError, isCancel)

### Configuration Options
- ✅ baseURL
- ✅ timeout
- ✅ headers
- ✅ params
- ✅ validateStatus

## Real-World HTTP Client Concepts

This emulator teaches the following concepts:

1. **Promise-based APIs**: Async request/response handling
2. **HTTP Methods**: RESTful API patterns
3. **Request Configuration**: Headers, params, timeout
4. **Interceptors**: Request/response transformation
5. **Error Handling**: Try-catch and promise rejection
6. **Cancellation**: Aborting pending requests
7. **Concurrent Requests**: Handling multiple async operations
8. **Instance Management**: Multiple configured clients

## Compatibility

Emulates core features of:
- Axios 0.x and 1.x API patterns
- Promise-based HTTP client patterns
- RESTful API client conventions

## License

Part of the Emu-Soft project. See main repository LICENSE.
