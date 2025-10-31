/**
 * Express.js Emulator - Web Framework for Node.js
 * 
 * This module emulates the Express.js library, which is a minimal and flexible
 * Node.js web application framework that provides a robust set of features for
 * web and mobile applications.
 * 
 * Key Features:
 * - Routing system (HTTP methods, path patterns)
 * - Middleware pipeline
 * - Request and Response object extensions
 * - Template engine support
 * - Static file serving
 * - Error handling
 */

class Request {
    /**
     * Represents an HTTP request with Express-like properties and methods.
     */
    constructor(method = 'GET', url = '/', headers = {}, body = null) {
        this.method = method.toUpperCase();
        this.url = url;
        this.originalUrl = url;
        this.path = url.split('?')[0];
        this.headers = headers;
        this.body = body;
        this.params = {};
        this.query = this._parseQuery(url);
        this.cookies = {};
    }

    _parseQuery(url) {
        const query = {};
        const queryString = url.split('?')[1];
        if (queryString) {
            queryString.split('&').forEach(pair => {
                const [key, value] = pair.split('=');
                query[decodeURIComponent(key)] = decodeURIComponent(value || '');
            });
        }
        return query;
    }

    get(header) {
        return this.headers[header.toLowerCase()];
    }

    header(name) {
        return this.get(name);
    }
}

class Response {
    /**
     * Represents an HTTP response with Express-like methods.
     */
    constructor() {
        this.statusCode = 200;
        this.headers = {};
        this.body = null;
        this._sent = false;
    }

    status(code) {
        this.statusCode = code;
        return this;
    }

    set(field, value) {
        if (typeof field === 'object') {
            Object.assign(this.headers, field);
        } else {
            this.headers[field] = value;
        }
        return this;
    }

    get(field) {
        return this.headers[field];
    }

    send(body) {
        if (this._sent) {
            throw new Error('Cannot send response multiple times');
        }
        this.body = body;
        this._sent = true;
        return this;
    }

    json(obj) {
        this.set('Content-Type', 'application/json');
        return this.send(JSON.stringify(obj));
    }

    sendStatus(statusCode) {
        this.statusCode = statusCode;
        return this.send(this._getStatusText(statusCode));
    }

    redirect(url) {
        this.statusCode = 302;
        this.set('Location', url);
        return this.send(`Redirecting to ${url}`);
    }

    type(contentType) {
        return this.set('Content-Type', contentType);
    }

    cookie(name, value, options = {}) {
        this.headers['Set-Cookie'] = `${name}=${value}`;
        return this;
    }

    clearCookie(name) {
        this.headers['Set-Cookie'] = `${name}=; Max-Age=0`;
        return this;
    }

    _getStatusText(code) {
        const statusTexts = {
            200: 'OK',
            201: 'Created',
            204: 'No Content',
            301: 'Moved Permanently',
            302: 'Found',
            304: 'Not Modified',
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            500: 'Internal Server Error',
            502: 'Bad Gateway',
            503: 'Service Unavailable'
        };
        return statusTexts[code] || 'Unknown Status';
    }
}

class Router {
    /**
     * Express Router for organizing route handlers.
     */
    constructor() {
        this.routes = [];
        this.middlewares = [];
    }

    use(...args) {
        if (typeof args[0] === 'function') {
            // Middleware without path
            this.middlewares.push({ path: '/', handler: args[0] });
        } else if (typeof args[0] === 'string' && typeof args[1] === 'function') {
            // Middleware with path
            this.middlewares.push({ path: args[0], handler: args[1] });
        } else if (typeof args[0] === 'string' && args[1] instanceof Router) {
            // Mount sub-router with path: app.use('/api', router)
            const basePath = args[0];
            const subRouter = args[1];
            subRouter.routes.forEach(route => {
                this.routes.push({
                    method: route.method,
                    path: basePath + route.path,
                    handler: route.handler
                });
            });
        } else if (args[0] instanceof Router) {
            // Mount sub-router without path: app.use(router)
            const subRouter = args[0];
            const basePath = '/';
            subRouter.routes.forEach(route => {
                this.routes.push({
                    method: route.method,
                    path: basePath === '/' ? route.path : basePath + route.path,
                    handler: route.handler
                });
            });
        }
        return this;
    }

    _addRoute(method, path, ...handlers) {
        handlers.forEach(handler => {
            this.routes.push({ method: method.toUpperCase(), path, handler });
        });
        return this;
    }

    get(path, ...handlers) {
        return this._addRoute('GET', path, ...handlers);
    }

    post(path, ...handlers) {
        return this._addRoute('POST', path, ...handlers);
    }

    put(path, ...handlers) {
        return this._addRoute('PUT', path, ...handlers);
    }

    delete(path, ...handlers) {
        return this._addRoute('DELETE', path, ...handlers);
    }

    patch(path, ...handlers) {
        return this._addRoute('PATCH', path, ...handlers);
    }

    all(path, ...handlers) {
        return this._addRoute('ALL', path, ...handlers);
    }

    _matchPath(pattern, path) {
        const paramNames = [];
        const regexPattern = pattern
            .replace(/:\w+/g, (match) => {
                paramNames.push(match.slice(1));
                return '([^/]+)';
            })
            .replace(/\*/g, '.*');
        
        const regex = new RegExp(`^${regexPattern}$`);
        const match = path.match(regex);
        
        if (match) {
            const params = {};
            paramNames.forEach((name, index) => {
                params[name] = match[index + 1];
            });
            return params;
        }
        return null;
    }

    handle(req, res) {
        // Execute middlewares
        for (const middleware of this.middlewares) {
            if (req.path.startsWith(middleware.path)) {
                try {
                    middleware.handler(req, res, () => {});
                    // Check if middleware sent response
                    if (res._sent) {
                        return;
                    }
                } catch (err) {
                    res.status(500).send('Internal Server Error');
                    return;
                }
            }
        }

        // Find and execute matching route
        for (const route of this.routes) {
            if (route.method === 'ALL' || route.method === req.method) {
                const params = this._matchPath(route.path, req.path);
                if (params !== null) {
                    req.params = params;
                    try {
                        route.handler(req, res);
                        return;
                    } catch (err) {
                        res.status(500).send('Internal Server Error');
                        return;
                    }
                }
            }
        }

        // No route matched
        res.status(404).send('Not Found');
    }
}

class Application extends Router {
    /**
     * Main Express application class.
     */
    constructor() {
        super();
        this.settings = {};
        this.engines = {};
        this.locals = {};
    }

    set(setting, value) {
        this.settings[setting] = value;
        return this;
    }

    get(setting) {
        if (typeof setting === 'string' && arguments.length === 1) {
            return this.settings[setting];
        }
        // Otherwise it's a route handler
        return super.get.apply(this, arguments);
    }

    engine(ext, fn) {
        this.engines[ext] = fn;
        return this;
    }

    listen(port, callback) {
        const server = {
            port,
            close: () => {
                if (callback) {
                    callback();
                }
            }
        };
        
        if (callback) {
            // Simulate async server start
            setTimeout(() => callback(), 0);
        }
        
        return server;
    }

    request(method, url, body = null, headers = {}) {
        const req = new Request(method, url, headers, body);
        const res = new Response();
        this.handle(req, res);
        return res;
    }
}

/**
 * Factory function to create an Express application.
 */
function express() {
    return new Application();
}

/**
 * Create a new Router.
 */
express.Router = function() {
    return new Router();
};

// Make Router class available for instanceof checks
express.Router.prototype = Router.prototype;

/**
 * Built-in middleware
 */
express.json = function(options = {}) {
    return function(req, res, next) {
        if (req.headers['content-type'] === 'application/json' && req.body) {
            try {
                req.body = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
            } catch (e) {
                res.status(400).send('Invalid JSON');
                return;
            }
        }
        next();
    };
};

express.urlencoded = function(options = {}) {
    return function(req, res, next) {
        if (req.headers['content-type'] === 'application/x-www-form-urlencoded' && req.body) {
            const parsed = {};
            req.body.split('&').forEach(pair => {
                const [key, value] = pair.split('=');
                parsed[decodeURIComponent(key)] = decodeURIComponent(value || '');
            });
            req.body = parsed;
        }
        next();
    };
};

express.static = function(root, options = {}) {
    return function(req, res, next) {
        // Simulated static file serving
        if (req.method === 'GET') {
            res.status(200).send(`Static file from ${root}`);
        } else {
            next();
        }
    };
};

// Export classes for testing
express.Request = Request;
express.Response = Response;
express.Router.RouterClass = Router;  // For instanceof checks
express.Application = Application;

module.exports = express;
