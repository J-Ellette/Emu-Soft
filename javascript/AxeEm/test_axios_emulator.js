/**
 * Developed by PowerShield, as an alternative to Axios
 */

/**
 * Tests for axios emulator
 * 
 * Comprehensive test suite for HTTP client emulator functionality.
 */

const axios = require('./axios_emulator');

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
        console.log('Running Axios Emulator Tests\n');
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

const runner = new TestRunner();

// ============================================================================
// BASIC REQUEST TESTS
// ============================================================================

runner.test('GET request - should make GET request', async () => {
    const response = await axios.get('/api/users');
    assertEqual(response.status, 200);
    assert(response.data.success === true);
    assertEqual(response.data.method, 'GET');
});

runner.test('POST request - should make POST request with data', async () => {
    const data = { name: 'John', email: 'john@example.com' };
    const response = await axios.post('/api/users', data);
    
    assertEqual(response.status, 200);
    assertDeepEqual(response.data.echo, data);
    assertEqual(response.data.method, 'POST');
});

runner.test('PUT request - should make PUT request', async () => {
    const data = { name: 'John Updated' };
    const response = await axios.put('/api/users/1', data);
    
    assertEqual(response.status, 200);
    assertEqual(response.data.method, 'PUT');
});

runner.test('DELETE request - should make DELETE request', async () => {
    const response = await axios.delete('/api/users/1');
    assertEqual(response.status, 200);
    assertEqual(response.data.method, 'DELETE');
});

runner.test('PATCH request - should make PATCH request', async () => {
    const data = { email: 'newemail@example.com' };
    const response = await axios.patch('/api/users/1', data);
    
    assertEqual(response.status, 200);
    assertEqual(response.data.method, 'PATCH');
});

// ============================================================================
// CONFIGURATION TESTS
// ============================================================================

runner.test('Config - should use baseURL', async () => {
    const instance = axios.create({
        baseURL: 'https://api.example.com'
    });
    
    const response = await instance.get('/users');
    assertEqual(response.status, 200);
});

runner.test('Config - should add query parameters', async () => {
    const response = await axios.get('/api/users', {
        params: { page: 1, limit: 10 }
    });
    
    assertEqual(response.status, 200);
});

runner.test('Config - should set custom headers', async () => {
    const response = await axios.get('/api/users', {
        headers: { 'X-Custom-Header': 'custom-value' }
    });
    
    assertEqual(response.status, 200);
    assertEqual(response.config.headers['X-Custom-Header'], 'custom-value');
});

runner.test('Config - should set timeout', async () => {
    const response = await axios.get('/api/users', {
        timeout: 5000
    });
    
    assertEqual(response.config.timeout, 5000);
});

// ============================================================================
// CUSTOM INSTANCE TESTS
// ============================================================================

runner.test('Instance - should create custom instance', async () => {
    const instance = axios.create({
        baseURL: 'https://api.example.com',
        timeout: 3000,
        headers: { 'X-API-Key': 'secret' }
    });
    
    assertEqual(instance.defaults.baseURL, 'https://api.example.com');
    assertEqual(instance.defaults.timeout, 3000);
});

runner.test('Instance - custom instance should work independently', async () => {
    const instance1 = axios.create({ baseURL: 'https://api1.com' });
    const instance2 = axios.create({ baseURL: 'https://api2.com' });
    
    assertEqual(instance1.defaults.baseURL, 'https://api1.com');
    assertEqual(instance2.defaults.baseURL, 'https://api2.com');
});

// ============================================================================
// INTERCEPTOR TESTS
// ============================================================================

runner.test('Interceptors - request interceptor should modify config', async () => {
    const instance = axios.create();
    
    instance.interceptors.request.use(config => {
        config.headers['Authorization'] = 'Bearer token123';
        return config;
    });
    
    const response = await instance.get('/api/users');
    assertEqual(response.config.headers['Authorization'], 'Bearer token123');
});

runner.test('Interceptors - response interceptor should modify response', async () => {
    const instance = axios.create();
    
    instance.interceptors.response.use(response => {
        response.data.intercepted = true;
        return response;
    });
    
    const response = await instance.get('/api/users');
    assert(response.data.intercepted === true);
});

runner.test('Interceptors - should be able to eject interceptor', async () => {
    const instance = axios.create();
    
    const id = instance.interceptors.request.use(config => {
        config.headers['X-Intercepted'] = 'yes';
        return config;
    });
    
    instance.interceptors.request.eject(id);
    
    const response = await instance.get('/api/users');
    assert(response.config.headers['X-Intercepted'] === undefined);
});

// ============================================================================
// ERROR HANDLING TESTS
// ============================================================================

runner.test('Errors - should handle mock error response', async () => {
    const instance = axios.create();
    instance._mock('GET', '/api/error', {
        error: true,
        message: 'Not Found',
        code: 'ERR_NOT_FOUND',
        response: { status: 404, statusText: 'Not Found' }
    });
    
    try {
        await instance.get('/api/error');
        assert(false, 'Should have thrown an error');
    } catch (error) {
        assert(axios.isAxiosError(error));
        assertEqual(error.code, 'ERR_NOT_FOUND');
    }
});

runner.test('Errors - response error interceptor should handle errors', async () => {
    const instance = axios.create();
    
    instance.interceptors.response.use(
        response => response,
        error => {
            error.handled = true;
            return Promise.reject(error);
        }
    );
    
    instance._mock('GET', '/api/error', {
        error: true,
        message: 'Server Error'
    });
    
    try {
        await instance.get('/api/error');
    } catch (error) {
        assert(error.handled === true);
    }
});

// ============================================================================
// CANCEL TOKEN TESTS
// ============================================================================

runner.test('CancelToken - should cancel request', async () => {
    const source = axios.CancelToken.source();
    
    // Cancel immediately
    source.cancel('Operation canceled by user');
    
    try {
        await axios.get('/api/users', {
            cancelToken: source.token
        });
        assert(false, 'Should have thrown cancel error');
    } catch (error) {
        assert(axios.isCancel(error));
        assertEqual(error.message, 'Operation canceled by user');
    }
});

runner.test('CancelToken - should create token with executor', async () => {
    let cancel;
    const token = new axios.CancelToken(c => {
        cancel = c;
    });
    
    cancel('User canceled');
    
    try {
        await axios.get('/api/users', { cancelToken: token });
        assert(false, 'Should have thrown cancel error');
    } catch (error) {
        assert(axios.isCancel(error));
    }
});

// ============================================================================
// MOCK RESPONSE TESTS
// ============================================================================

runner.test('Mock - should return mocked response', async () => {
    const instance = axios.create();
    instance._mock('GET', '/api/users', {
        data: [
            { id: 1, name: 'Alice' },
            { id: 2, name: 'Bob' }
        ],
        status: 200
    });
    
    const response = await instance.get('/api/users');
    assertEqual(response.data.length, 2);
    assertEqual(response.data[0].name, 'Alice');
});

runner.test('Mock - should clear mocks', async () => {
    const instance = axios.create();
    instance._mock('GET', '/api/test', { data: 'mocked' });
    instance._clearMocks();
    
    const response = await instance.get('/api/test');
    // Should return default response, not mocked data
    assert(response.data.success === true);
});

// ============================================================================
// UTILITY TESTS
// ============================================================================

runner.test('Utility - all() should handle multiple requests', async () => {
    const requests = [
        axios.get('/api/users'),
        axios.get('/api/posts'),
        axios.get('/api/comments')
    ];
    
    const responses = await axios.all(requests);
    assertEqual(responses.length, 3);
    responses.forEach(response => {
        assertEqual(response.status, 200);
    });
});

runner.test('Utility - spread() should spread response array', async () => {
    const requests = [
        axios.get('/api/users'),
        axios.get('/api/posts')
    ];
    
    await axios.all(requests).then(axios.spread((users, posts) => {
        assertEqual(users.status, 200);
        assertEqual(posts.status, 200);
    }));
});

runner.test('Utility - isAxiosError() should identify axios errors', () => {
    const axiosError = new axios.AxiosError('Error', 'ERR_BAD_REQUEST');
    const regularError = new Error('Regular error');
    
    assert(axios.isAxiosError(axiosError) === true);
    assert(axios.isAxiosError(regularError) === false);
});

// ============================================================================
// RESPONSE STRUCTURE TESTS
// ============================================================================

runner.test('Response - should have correct structure', async () => {
    const response = await axios.get('/api/users');
    
    assert(response.data !== undefined);
    assert(response.status !== undefined);
    assert(response.statusText !== undefined);
    assert(response.headers !== undefined);
    assert(response.config !== undefined);
});

runner.test('Response - should include request config', async () => {
    const config = {
        headers: { 'X-Custom': 'value' },
        params: { page: 1 }
    };
    
    const response = await axios.get('/api/users', config);
    assertEqual(response.config.headers['X-Custom'], 'value');
    assertDeepEqual(response.config.params, { page: 1 });
});

// ============================================================================
// INTEGRATION TESTS
// ============================================================================

runner.test('Integration - RESTful API workflow', async () => {
    const api = axios.create({
        baseURL: 'https://api.example.com'
    });
    
    // Mock responses
    api._mock('GET', 'https://api.example.com/users', {
        data: [{ id: 1, name: 'Alice' }]
    });
    
    api._mock('POST', 'https://api.example.com/users', {
        data: { id: 2, name: 'Bob' },
        status: 201
    });
    
    api._mock('PUT', 'https://api.example.com/users/2', {
        data: { id: 2, name: 'Bob Updated' }
    });
    
    api._mock('DELETE', 'https://api.example.com/users/2', {
        data: { success: true },
        status: 204
    });
    
    // GET all users
    const getResponse = await api.get('/users');
    assertEqual(getResponse.data.length, 1);
    
    // POST new user
    const postResponse = await api.post('/users', { name: 'Bob' });
    assertEqual(postResponse.status, 201);
    assertEqual(postResponse.data.name, 'Bob');
    
    // PUT update user
    const putResponse = await api.put('/users/2', { name: 'Bob Updated' });
    assertEqual(putResponse.data.name, 'Bob Updated');
    
    // DELETE user
    const deleteResponse = await api.delete('/users/2');
    assertEqual(deleteResponse.status, 204);
});

runner.test('Integration - with auth interceptor', async () => {
    const api = axios.create({
        baseURL: 'https://api.example.com'
    });
    
    // Add auth token to all requests
    api.interceptors.request.use(config => {
        config.headers['Authorization'] = 'Bearer mytoken';
        return config;
    });
    
    // Log all responses
    let responseLogged = false;
    api.interceptors.response.use(response => {
        responseLogged = true;
        return response;
    });
    
    const response = await api.get('/protected');
    assertEqual(response.config.headers['Authorization'], 'Bearer mytoken');
    assert(responseLogged === true);
});

runner.test('Integration - error handling with retry', async () => {
    const api = axios.create();
    let interceptorCalled = false;
    
    api.interceptors.response.use(
        response => response,
        async error => {
            interceptorCalled = true;
            // In real scenario, would retry the request
            return Promise.reject(error);
        }
    );
    
    api._mock('GET', '/api/flaky', {
        error: true,
        message: 'Temporary error'
    });
    
    try {
        await api.get('/api/flaky');
    } catch (error) {
        assert(interceptorCalled === true, 'Interceptor should be called');
        assert(axios.isAxiosError(error));
    }
});

// Run all tests
runner.run().catch(console.error);
