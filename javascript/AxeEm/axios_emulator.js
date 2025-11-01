/**
 * Developed by PowerShield, as an alternative to Axios
 */

/**
 * Axios Emulator - HTTP Client for JavaScript
 * 
 * This module emulates the axios library, which is a promise-based HTTP client
 * for the browser and Node.js. It provides an easy-to-use API for making HTTP
 * requests and handling responses.
 * 
 * Key Features:
 * - Promise-based API
 * - Request/Response interceptors
 * - Automatic JSON transformation
 * - Request cancellation
 * - HTTP method shortcuts (get, post, put, delete, etc.)
 * - Custom instances with default configuration
 */

/**
 * Simulated HTTP response
 */
class AxiosResponse {
    constructor(data, status = 200, statusText = 'OK', headers = {}, config = {}) {
        this.data = data;
        this.status = status;
        this.statusText = statusText;
        this.headers = headers;
        this.config = config;
    }
}

/**
 * Axios error class
 */
class AxiosError extends Error {
    constructor(message, code, config, request, response) {
        super(message);
        this.name = 'AxiosError';
        this.code = code;
        this.config = config;
        this.request = request;
        this.response = response;
        this.isAxiosError = true;
    }
}

/**
 * Cancel token for request cancellation
 */
class CancelToken {
    constructor(executor) {
        this.promise = new Promise(resolve => {
            this._resolve = resolve;
        });
        
        this.reason = null;
        
        if (executor) {
            executor(reason => this.cancel(reason));
        }
    }
    
    cancel(reason = 'Operation canceled') {
        if (this.reason) return;
        this.reason = new Cancel(reason);
        this._resolve(this.reason);
    }
    
    static source() {
        let cancel;
        const token = new CancelToken(c => {
            cancel = c;
        });
        return { token, cancel };
    }
}

/**
 * Cancel error
 */
class Cancel {
    constructor(message) {
        this.message = message;
    }
    
    toString() {
        return `Cancel${this.message ? ': ' + this.message : ''}`;
    }
}

/**
 * Main Axios class
 */
class Axios {
    constructor(config = {}) {
        this.defaults = {
            baseURL: '',
            timeout: 0,
            headers: {
                common: {
                    'Accept': 'application/json, text/plain, */*'
                },
                get: {},
                post: { 'Content-Type': 'application/json' },
                put: { 'Content-Type': 'application/json' },
                patch: { 'Content-Type': 'application/json' },
                delete: {}
            },
            transformRequest: [],
            transformResponse: [],
            validateStatus: (status) => status >= 200 && status < 300,
            ...config
        };
        
        this.interceptors = {
            request: new InterceptorManager(),
            response: new InterceptorManager()
        };
        
        // Mock response storage for testing
        this._mockResponses = new Map();
    }
    
    /**
     * Make a request with the given config
     */
    async request(config) {
        // Merge config with defaults
        config = this._mergeConfig(this.defaults, config);
        
        // Apply request interceptors
        for (const interceptor of this.interceptors.request.handlers) {
            if (interceptor) {
                config = await interceptor.fulfilled(config);
            }
        }
        
        // Check for cancellation
        if (config.cancelToken && config.cancelToken.reason) {
            throw config.cancelToken.reason;
        }
        
        // Build full URL
        const url = this._buildURL(config.baseURL, config.url, config.params);
        
        // Simulate HTTP request
        let response;
        try {
            response = await this._makeRequest(url, config);
        } catch (error) {
            // Apply response error interceptors
            for (const interceptor of this.interceptors.response.handlers) {
                if (interceptor && interceptor.rejected) {
                    error = await interceptor.rejected(error);
                }
            }
            throw error;
        }
        
        // Apply response interceptors
        for (const interceptor of this.interceptors.response.handlers) {
            if (interceptor && interceptor.fulfilled) {
                response = await interceptor.fulfilled(response);
            }
        }
        
        return response;
    }
    
    /**
     * Make the actual HTTP request (simulated)
     */
    async _makeRequest(url, config) {
        // Check if we have a mock response for this URL/method
        const mockKey = `${config.method.toUpperCase()}:${url}`;
        if (this._mockResponses.has(mockKey)) {
            const mockData = this._mockResponses.get(mockKey);
            
            if (mockData.error) {
                throw new AxiosError(
                    mockData.message || 'Request failed',
                    mockData.code || 'ERR_BAD_REQUEST',
                    config,
                    null,
                    mockData.response
                );
            }
            
            return new AxiosResponse(
                mockData.data,
                mockData.status || 200,
                mockData.statusText || 'OK',
                mockData.headers || {},
                config
            );
        }
        
        // Simulate network delay
        if (config.timeout) {
            await new Promise(resolve => setTimeout(resolve, Math.min(config.timeout / 10, 10)));
        }
        
        // Simulate successful response
        const responseData = this._transformResponseData(config);
        const status = 200;
        const statusText = 'OK';
        const headers = { 'content-type': 'application/json' };
        
        const response = new AxiosResponse(responseData, status, statusText, headers, config);
        
        // Validate status
        if (!config.validateStatus(status)) {
            throw new AxiosError(
                `Request failed with status code ${status}`,
                'ERR_BAD_REQUEST',
                config,
                null,
                response
            );
        }
        
        return response;
    }
    
    /**
     * Transform response data
     */
    _transformResponseData(config) {
        // For simulated responses, echo back the request data or return a default
        if (config.data) {
            return { echo: config.data, method: config.method };
        }
        return { success: true, method: config.method };
    }
    
    /**
     * Build full URL with params
     */
    _buildURL(baseURL, url, params) {
        let fullURL = baseURL ? baseURL + url : url;
        
        if (params) {
            const queryString = Object.keys(params)
                .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
                .join('&');
            fullURL += (fullURL.includes('?') ? '&' : '?') + queryString;
        }
        
        return fullURL;
    }
    
    /**
     * Merge configurations
     */
    _mergeConfig(defaults, config) {
        return {
            ...defaults,
            ...config,
            headers: {
                ...defaults.headers.common,
                ...(defaults.headers[config.method?.toLowerCase()] || {}),
                ...(config.headers || {})
            }
        };
    }
    
    /**
     * Mock a response for testing
     */
    _mock(method, url, response) {
        const key = `${method.toUpperCase()}:${url}`;
        this._mockResponses.set(key, response);
    }
    
    /**
     * Clear all mocks
     */
    _clearMocks() {
        this._mockResponses.clear();
    }
    
    // HTTP method shortcuts
    get(url, config = {}) {
        return this.request({ ...config, method: 'GET', url });
    }
    
    delete(url, config = {}) {
        return this.request({ ...config, method: 'DELETE', url });
    }
    
    head(url, config = {}) {
        return this.request({ ...config, method: 'HEAD', url });
    }
    
    options(url, config = {}) {
        return this.request({ ...config, method: 'OPTIONS', url });
    }
    
    post(url, data, config = {}) {
        return this.request({ ...config, method: 'POST', url, data });
    }
    
    put(url, data, config = {}) {
        return this.request({ ...config, method: 'PUT', url, data });
    }
    
    patch(url, data, config = {}) {
        return this.request({ ...config, method: 'PATCH', url, data });
    }
}

/**
 * Interceptor manager
 */
class InterceptorManager {
    constructor() {
        this.handlers = [];
    }
    
    use(fulfilled, rejected) {
        this.handlers.push({ fulfilled, rejected });
        return this.handlers.length - 1;
    }
    
    eject(id) {
        if (this.handlers[id]) {
            this.handlers[id] = null;
        }
    }
}

/**
 * Create a new instance of Axios
 */
function createInstance(config) {
    const instance = new Axios(config);
    
    // Bind request method to instance
    const axios = instance.request.bind(instance);
    
    // Copy properties from instance to axios function
    Object.setPrototypeOf(axios, instance);
    Object.assign(axios, instance);
    
    return axios;
}

// Create default instance
const axios = createInstance();

// Expose class constructors
axios.Axios = Axios;
axios.Cancel = Cancel;
axios.CancelToken = CancelToken;
axios.isCancel = (value) => value instanceof Cancel;
axios.AxiosError = AxiosError;

// Create method
axios.create = function(config) {
    return createInstance(config);
};

// Spread method (for concurrent requests)
axios.all = function(promises) {
    return Promise.all(promises);
};

axios.spread = function(callback) {
    return function(arr) {
        return callback.apply(null, arr);
    };
};

// Helper to check if axios error
axios.isAxiosError = function(error) {
    return error && error.isAxiosError === true;
};

module.exports = axios;
