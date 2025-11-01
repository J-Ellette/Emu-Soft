/**
 * Developed by PowerShield, as an alternative to Express.js
 */

/**
 * Tests for Express.js emulator
 * 
 * Comprehensive test suite for web framework emulator functionality.
 */

const express = require('./express_emulator');

// Simple test framework
class TestRunner {
    constructor() {
        this.tests = [];
        this.passed = 0;
        this.failed = 0;
    }

    test(name, fn) {
        this.tests.push({ name, fn });
    }

    async run() {
        console.log('Running Express.js Emulator Tests\n');
        console.log('='.repeat(50));
        
        for (const test of this.tests) {
            try {
                await test.fn();
                this.passed++;
                console.log(`✓ ${test.name}`);
            } catch (error) {
                this.failed++;
                console.log(`✗ ${test.name}`);
                console.log(`  Error: ${error.message}`);
            }
        }
        
        console.log('='.repeat(50));
        console.log(`\nTests: ${this.passed} passed, ${this.failed} failed, ${this.tests.length} total`);
        
        if (this.failed > 0) {
            process.exit(1);
        }
    }
}

function assert(condition, message = 'Assertion failed') {
    if (!condition) {
        throw new Error(message);
    }
}

function assertEqual(actual, expected, message) {
    if (actual !== expected) {
        throw new Error(message || `Expected ${expected}, got ${actual}`);
    }
}

function assertDeepEqual(actual, expected, message) {
    if (JSON.stringify(actual) !== JSON.stringify(expected)) {
        throw new Error(message || `Expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
    }
}

// Test suite
const runner = new TestRunner();

// Request tests
runner.test('Request - should parse query string', () => {
    const req = new express.Request('GET', '/search?q=test&limit=10');
    assertDeepEqual(req.query, { q: 'test', limit: '10' });
});

runner.test('Request - should extract path without query', () => {
    const req = new express.Request('GET', '/users?id=123');
    assertEqual(req.path, '/users');
});

runner.test('Request - should get headers', () => {
    const req = new express.Request('GET', '/', { 'content-type': 'application/json' });
    assertEqual(req.get('content-type'), 'application/json');
});

// Response tests
runner.test('Response - should set status code', () => {
    const res = new express.Response();
    res.status(404);
    assertEqual(res.statusCode, 404);
});

runner.test('Response - should send body', () => {
    const res = new express.Response();
    res.send('Hello World');
    assertEqual(res.body, 'Hello World');
    assert(res._sent);
});

runner.test('Response - should send JSON', () => {
    const res = new express.Response();
    res.json({ message: 'success' });
    assertEqual(res.body, '{"message":"success"}');
    assertEqual(res.headers['Content-Type'], 'application/json');
});

runner.test('Response - should chain status and send', () => {
    const res = new express.Response();
    res.status(201).send('Created');
    assertEqual(res.statusCode, 201);
    assertEqual(res.body, 'Created');
});

runner.test('Response - should set headers', () => {
    const res = new express.Response();
    res.set('X-Custom-Header', 'value');
    assertEqual(res.headers['X-Custom-Header'], 'value');
});

runner.test('Response - should set multiple headers', () => {
    const res = new express.Response();
    res.set({
        'X-Header-1': 'value1',
        'X-Header-2': 'value2'
    });
    assertEqual(res.headers['X-Header-1'], 'value1');
    assertEqual(res.headers['X-Header-2'], 'value2');
});

runner.test('Response - should handle redirect', () => {
    const res = new express.Response();
    res.redirect('/new-location');
    assertEqual(res.statusCode, 302);
    assertEqual(res.headers['Location'], '/new-location');
});

runner.test('Response - should set cookies', () => {
    const res = new express.Response();
    res.cookie('session', 'abc123');
    assert(res.headers['Set-Cookie'].includes('session=abc123'));
});

// Application tests
runner.test('Application - should create app instance', () => {
    const app = express();
    assert(app instanceof express.Application);
});

runner.test('Application - should handle GET request', () => {
    const app = express();
    app.get('/hello', (req, res) => {
        res.send('Hello World');
    });
    
    const res = app.request('GET', '/hello');
    assertEqual(res.body, 'Hello World');
    assertEqual(res.statusCode, 200);
});

runner.test('Application - should handle POST request', () => {
    const app = express();
    app.post('/data', (req, res) => {
        res.json({ received: true });
    });
    
    const res = app.request('POST', '/data');
    assertEqual(res.statusCode, 200);
    assert(res.body.includes('received'));
});

runner.test('Application - should handle PUT request', () => {
    const app = express();
    app.put('/update/:id', (req, res) => {
        res.send(`Updated ${req.params.id}`);
    });
    
    const res = app.request('PUT', '/update/123');
    assertEqual(res.body, 'Updated 123');
});

runner.test('Application - should handle DELETE request', () => {
    const app = express();
    app.delete('/items/:id', (req, res) => {
        res.sendStatus(204);
    });
    
    const res = app.request('DELETE', '/items/456');
    assertEqual(res.statusCode, 204);
});

runner.test('Application - should return 404 for unmatched routes', () => {
    const app = express();
    app.get('/hello', (req, res) => {
        res.send('Hello');
    });
    
    const res = app.request('GET', '/unknown');
    assertEqual(res.statusCode, 404);
    assertEqual(res.body, 'Not Found');
});

runner.test('Application - should parse route parameters', () => {
    const app = express();
    app.get('/users/:userId/posts/:postId', (req, res) => {
        res.json(req.params);
    });
    
    const res = app.request('GET', '/users/john/posts/42');
    const params = JSON.parse(res.body);
    assertEqual(params.userId, 'john');
    assertEqual(params.postId, '42');
});

runner.test('Application - should use middleware', () => {
    const app = express();
    let middlewareExecuted = false;
    
    app.use((req, res, next) => {
        middlewareExecuted = true;
        req.customProperty = 'value';
        next();
    });
    
    app.get('/test', (req, res) => {
        res.send(req.customProperty || 'no value');
    });
    
    const res = app.request('GET', '/test');
    assert(middlewareExecuted);
});

runner.test('Application - should handle query parameters', () => {
    const app = express();
    app.get('/search', (req, res) => {
        res.json(req.query);
    });
    
    const res = app.request('GET', '/search?name=John&age=30');
    const query = JSON.parse(res.body);
    assertEqual(query.name, 'John');
    assertEqual(query.age, '30');
});

runner.test('Application - should set and get settings', () => {
    const app = express();
    app.set('view engine', 'pug');
    assertEqual(app.get('view engine'), 'pug');
});

runner.test('Application - should handle all() method', () => {
    const app = express();
    app.all('/any-method', (req, res) => {
        res.send(`Method: ${req.method}`);
    });
    
    const getRes = app.request('GET', '/any-method');
    assert(getRes.body.includes('GET'));
    
    const postRes = app.request('POST', '/any-method');
    assert(postRes.body.includes('POST'));
});

// Router tests
runner.test('Router - should create router instance', () => {
    const router = express.Router();
    assert(router instanceof express.Router.RouterClass);
});

runner.test('Router - should add routes', () => {
    const router = express.Router();
    router.get('/test', (req, res) => {
        res.send('test');
    });
    
    assert(router.routes.length > 0);
});

runner.test('Router - should mount sub-router', () => {
    const app = express();
    const apiRouter = express.Router();
    
    apiRouter.get('/users', (req, res) => {
        res.json([{ id: 1, name: 'John' }]);
    });
    
    app.use('/api', apiRouter);
    
    const res = app.request('GET', '/api/users');
    const users = JSON.parse(res.body);
    assertEqual(users[0].name, 'John');
});

// Middleware tests
runner.test('Middleware - json() should parse JSON body', () => {
    const app = express();
    app.use(express.json());
    
    app.post('/data', (req, res) => {
        res.json({ received: req.body });
    });
    
    const res = app.request('POST', '/data', '{"name":"John"}', { 'content-type': 'application/json' });
    const data = JSON.parse(res.body);
    assertEqual(data.received.name, 'John');
});

runner.test('Middleware - urlencoded() should parse form data', () => {
    const app = express();
    app.use(express.urlencoded());
    
    app.post('/form', (req, res) => {
        res.json(req.body);
    });
    
    const res = app.request('POST', '/form', 'name=John&age=30', { 'content-type': 'application/x-www-form-urlencoded' });
    const data = JSON.parse(res.body);
    assertEqual(data.name, 'John');
    assertEqual(data.age, '30');
});

runner.test('Middleware - static() should serve static files', () => {
    const app = express();
    app.use(express.static('public'));
    
    app.get('/test', (req, res) => {
        res.send('dynamic');
    });
    
    const res = app.request('GET', '/any-file.html');
    assert(res.body.includes('Static file'));
});

// Integration tests
runner.test('Integration - RESTful API', () => {
    const app = express();
    const users = [
        { id: 1, name: 'Alice' },
        { id: 2, name: 'Bob' }
    ];
    
    app.get('/api/users', (req, res) => {
        res.json(users);
    });
    
    app.get('/api/users/:id', (req, res) => {
        const user = users.find(u => u.id === parseInt(req.params.id));
        if (user) {
            res.json(user);
        } else {
            res.status(404).json({ error: 'User not found' });
        }
    });
    
    // Test list
    const listRes = app.request('GET', '/api/users');
    const userList = JSON.parse(listRes.body);
    assertEqual(userList.length, 2);
    
    // Test get by ID
    const getRes = app.request('GET', '/api/users/1');
    const user = JSON.parse(getRes.body);
    assertEqual(user.name, 'Alice');
    
    // Test not found
    const notFoundRes = app.request('GET', '/api/users/999');
    assertEqual(notFoundRes.statusCode, 404);
});

runner.test('Integration - Error handling', () => {
    const app = express();
    
    app.get('/error', (req, res) => {
        throw new Error('Something went wrong');
    });
    
    const res = app.request('GET', '/error');
    assertEqual(res.statusCode, 500);
});

runner.test('Integration - Complex routing', () => {
    const app = express();
    
    app.get('/products', (req, res) => {
        res.send('All products');
    });
    
    app.get('/products/:category', (req, res) => {
        res.send(`Products in ${req.params.category}`);
    });
    
    app.get('/products/:category/:id', (req, res) => {
        res.json({
            category: req.params.category,
            id: req.params.id
        });
    });
    
    const res1 = app.request('GET', '/products');
    assert(res1.body.includes('All products'));
    
    const res2 = app.request('GET', '/products/electronics');
    assert(res2.body.includes('electronics'));
    
    const res3 = app.request('GET', '/products/electronics/123');
    const data = JSON.parse(res3.body);
    assertEqual(data.category, 'electronics');
    assertEqual(data.id, '123');
});

runner.test('Application - should listen on port', (done) => {
    const app = express();
    let callbackCalled = false;
    
    const server = app.listen(3000, () => {
        callbackCalled = true;
    });
    
    // Wait for async callback
    setTimeout(() => {
        assert(callbackCalled, 'Callback should be called');
        assertEqual(server.port, 3000);
        server.close();
    }, 10);
});

// Run all tests
runner.run().catch(console.error);
