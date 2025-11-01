# Jest Emulator - Testing Framework for JavaScript

**Developed by PowerShield, as an alternative to Jest**


This module emulates the **Jest** testing framework, which is a delightful JavaScript testing framework with a focus on simplicity. Jest works with projects using Babel, TypeScript, Node, React, Angular, Vue and more.

## What is Jest?

Jest is a JavaScript testing framework developed by Facebook. It is designed to:
- Provide a complete testing solution out of the box
- Require zero configuration for most projects
- Include powerful mocking capabilities
- Offer fast and parallel test execution
- Support snapshot testing
- Provide excellent error messages

## Features

This emulator implements core Jest functionality:

### Test Definition
- **describe**: Group related tests together
- **test/it**: Define individual test cases
- **Nested suites**: Support for nested describe blocks
- **Async tests**: Full support for async/await testing

### Assertions (Matchers)
- **Equality**: toBe, toEqual, toStrictEqual
- **Truthiness**: toBeTruthy, toBeFalsy, toBeNull, toBeUndefined, toBeDefined
- **Comparison**: toBeGreaterThan, toBeLessThan
- **Contains**: toContain, toHaveLength
- **Objects**: toHaveProperty
- **Exceptions**: toThrow
- **Patterns**: toMatch
- **Negation**: .not modifier for all matchers

### Mocking
- **jest.fn()**: Create mock functions
- **jest.spyOn()**: Spy on object methods
- **mockReturnValue**: Set return values
- **mockImplementation**: Custom implementations
- **mockResolvedValue/mockRejectedValue**: Async mocking
- **Call tracking**: Track all function calls and arguments

### Setup/Teardown Hooks
- **beforeAll**: Run once before all tests
- **afterAll**: Run once after all tests
- **beforeEach**: Run before each test
- **afterEach**: Run after each test

## Usage Examples

### Basic Test Suite

```javascript
const { describe, test, expect, runTests } = require('./jest_emulator');

describe('Math Operations', () => {
    test('addition works correctly', () => {
        expect(1 + 1).toBe(2);
        expect(2 + 3).toBe(5);
    });

    test('subtraction works correctly', () => {
        expect(5 - 3).toBe(2);
        expect(10 - 4).toBe(6);
    });

    test('multiplication works correctly', () => {
        expect(2 * 3).toBe(6);
        expect(5 * 5).toBe(25);
    });
});

// Run all tests
runTests();
```

### Using Matchers

```javascript
const { describe, test, expect } = require('./jest_emulator');

describe('Matchers Examples', () => {
    test('equality matchers', () => {
        expect(2 + 2).toBe(4);
        expect({ a: 1 }).toEqual({ a: 1 });
    });

    test('truthiness matchers', () => {
        expect(true).toBeTruthy();
        expect(false).toBeFalsy();
        expect(null).toBeNull();
        expect(undefined).toBeUndefined();
    });

    test('comparison matchers', () => {
        expect(10).toBeGreaterThan(5);
        expect(3).toBeLessThan(10);
    });

    test('array and string matchers', () => {
        expect([1, 2, 3]).toContain(2);
        expect('hello world').toContain('world');
        expect([1, 2, 3]).toHaveLength(3);
    });

    test('object matchers', () => {
        const user = { name: 'Alice', age: 30 };
        expect(user).toHaveProperty('name');
        expect(user).toHaveProperty('age', 30);
    });
});
```

### Negation with .not

```javascript
const { describe, test, expect } = require('./jest_emulator');

describe('Negation Examples', () => {
    test('using .not modifier', () => {
        expect(1).not.toBe(2);
        expect('hello').not.toBe('world');
        expect([1, 2]).not.toContain(3);
        expect(null).not.toBeTruthy();
    });
});
```

### Testing Exceptions

```javascript
const { describe, test, expect } = require('./jest_emulator');

describe('Exception Testing', () => {
    function throwError() {
        throw new Error('Something went wrong');
    }

    function divide(a, b) {
        if (b === 0) {
            throw new Error('Division by zero');
        }
        return a / b;
    }

    test('function throws an error', () => {
        expect(throwError).toThrow();
        expect(throwError).toThrow('went wrong');
        expect(throwError).toThrow(Error);
    });

    test('division by zero throws', () => {
        expect(() => divide(10, 0)).toThrow('Division by zero');
    });
});
```

### Mock Functions

```javascript
const { describe, test, expect, jest } = require('./jest_emulator');

describe('Mock Function Examples', () => {
    test('basic mock function', () => {
        const mockFn = jest.fn();
        
        mockFn('arg1', 'arg2');
        mockFn('arg3');
        
        // Check that function was called
        expect(mockFn.mock.calls).toHaveLength(2);
        
        // Check call arguments
        expect(mockFn.mock.calls[0]).toEqual(['arg1', 'arg2']);
        expect(mockFn.mock.calls[1]).toEqual(['arg3']);
    });

    test('mock with return value', () => {
        const mockFn = jest.fn().mockReturnValue(42);
        
        const result = mockFn();
        expect(result).toBe(42);
    });

    test('mock with custom implementation', () => {
        const add = jest.fn().mockImplementation((a, b) => a + b);
        
        expect(add(2, 3)).toBe(5);
        expect(add(10, 20)).toBe(30);
    });

    test('mock for async operations', async () => {
        const fetchData = jest.fn().mockResolvedValue({ data: 'test' });
        
        const result = await fetchData();
        expect(result).toEqual({ data: 'test' });
    });
});
```

### Spying on Methods

```javascript
const { describe, test, expect, jest } = require('./jest_emulator');

describe('Spy Examples', () => {
    test('spying on object methods', () => {
        const calculator = {
            add: (a, b) => a + b,
            multiply: (a, b) => a * b
        };
        
        const addSpy = jest.spyOn(calculator, 'add');
        
        calculator.add(2, 3);
        calculator.add(5, 7);
        
        // Verify the method was called
        expect(addSpy.mock.calls).toHaveLength(2);
        expect(addSpy.mock.calls[0]).toEqual([2, 3]);
        
        // Restore original implementation
        addSpy.mockRestore();
    });
});
```

### Setup and Teardown

```javascript
const { describe, test, expect, beforeEach, afterEach, beforeAll, afterAll } = require('./jest_emulator');

describe('Setup and Teardown Example', () => {
    let database;
    
    beforeAll(() => {
        // Runs once before all tests
        console.log('Setting up test database...');
    });
    
    afterAll(() => {
        // Runs once after all tests
        console.log('Tearing down test database...');
    });
    
    beforeEach(() => {
        // Runs before each test
        database = { users: [] };
    });
    
    afterEach(() => {
        // Runs after each test
        database = null;
    });
    
    test('can add user to database', () => {
        database.users.push({ name: 'Alice' });
        expect(database.users).toHaveLength(1);
    });
    
    test('database starts empty', () => {
        expect(database.users).toHaveLength(0);
    });
});
```

### Async Testing

```javascript
const { describe, test, expect } = require('./jest_emulator');

describe('Async Testing Examples', () => {
    test('async function with promise', async () => {
        const fetchUser = () => Promise.resolve({ name: 'Alice' });
        
        const user = await fetchUser();
        expect(user).toEqual({ name: 'Alice' });
    });

    test('async function with async/await', async () => {
        const getData = async () => {
            return { status: 'success' };
        };
        
        const result = await getData();
        expect(result).toHaveProperty('status', 'success');
    });
});
```

### Nested Describe Blocks

```javascript
const { describe, test, expect } = require('./jest_emulator');

describe('User Management', () => {
    describe('User Creation', () => {
        test('creates user with valid data', () => {
            const user = { name: 'Alice', email: 'alice@example.com' };
            expect(user).toHaveProperty('name');
            expect(user).toHaveProperty('email');
        });
    });
    
    describe('User Validation', () => {
        test('validates email format', () => {
            const email = 'test@example.com';
            expect(email).toMatch(/@/);
        });
    });
});
```

### Real-World Example: Testing an API Client

```javascript
const { describe, test, expect, jest, beforeEach } = require('./jest_emulator');

describe('API Client Tests', () => {
    let apiClient;
    let mockFetch;
    
    beforeEach(() => {
        mockFetch = jest.fn();
        
        apiClient = {
            fetch: mockFetch,
            getUser: function(userId) {
                return this.fetch(`/api/users/${userId}`);
            },
            createUser: function(userData) {
                return this.fetch('/api/users', {
                    method: 'POST',
                    body: JSON.stringify(userData)
                });
            }
        };
    });
    
    test('getUser calls fetch with correct URL', () => {
        mockFetch.mockResolvedValue({ id: 1, name: 'Alice' });
        
        apiClient.getUser(1);
        
        expect(mockFetch.mock.calls).toHaveLength(1);
        expect(mockFetch.mock.calls[0][0]).toBe('/api/users/1');
    });
    
    test('createUser sends POST request', () => {
        const userData = { name: 'Bob', email: 'bob@example.com' };
        mockFetch.mockResolvedValue({ id: 2, ...userData });
        
        apiClient.createUser(userData);
        
        expect(mockFetch.mock.calls).toHaveLength(1);
        expect(mockFetch.mock.calls[0][0]).toBe('/api/users');
        expect(mockFetch.mock.calls[0][1]).toHaveProperty('method', 'POST');
    });
});
```

### Real-World Example: Testing Business Logic

```javascript
const { describe, test, expect, beforeEach } = require('./jest_emulator');

describe('Shopping Cart', () => {
    let cart;
    
    beforeEach(() => {
        cart = {
            items: [],
            addItem: function(item) {
                this.items.push(item);
            },
            removeItem: function(itemId) {
                this.items = this.items.filter(item => item.id !== itemId);
            },
            getTotal: function() {
                return this.items.reduce((sum, item) => sum + item.price, 0);
            },
            isEmpty: function() {
                return this.items.length === 0;
            }
        };
    });
    
    test('starts empty', () => {
        expect(cart.isEmpty()).toBe(true);
        expect(cart.items).toHaveLength(0);
    });
    
    test('can add items', () => {
        cart.addItem({ id: 1, name: 'Book', price: 10 });
        cart.addItem({ id: 2, name: 'Pen', price: 2 });
        
        expect(cart.items).toHaveLength(2);
        expect(cart.isEmpty()).toBe(false);
    });
    
    test('can remove items', () => {
        cart.addItem({ id: 1, name: 'Book', price: 10 });
        cart.addItem({ id: 2, name: 'Pen', price: 2 });
        
        cart.removeItem(1);
        
        expect(cart.items).toHaveLength(1);
        expect(cart.items[0]).toHaveProperty('id', 2);
    });
    
    test('calculates total correctly', () => {
        cart.addItem({ id: 1, name: 'Book', price: 10 });
        cart.addItem({ id: 2, name: 'Pen', price: 2 });
        cart.addItem({ id: 3, name: 'Notebook', price: 5 });
        
        expect(cart.getTotal()).toBe(17);
    });
});
```

## Testing

Run the comprehensive test suite:

```bash
node test_jest_emulator.js
```

Tests cover:
- Basic assertions (5 tests)
- Negation with .not (4 tests)
- Comparison matchers (2 tests)
- Array and string matchers (3 tests)
- Object matchers (2 tests)
- Exception testing (2 tests)
- Pattern matching (2 tests)
- Mock functions (5 tests)
- Spy functions (2 tests)
- Setup and teardown hooks (2 tests)
- Nested describe blocks (3 tests)
- Async testing (2 tests)
- Calculator tests (5 tests)
- User service tests (3 tests)

Total: 42+ tests

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for Jest in development and testing:

```javascript
// Instead of:
// const { describe, test, expect } = require('@jest/globals');

// Use:
const { describe, test, expect, runTests } = require('./jest_emulator');

// Write your tests as normal
describe('My Tests', () => {
    test('example test', () => {
        expect(1 + 1).toBe(2);
    });
});

// Run the tests
runTests();
```

## Use Cases

Perfect for:
- **Local Development**: Develop tests without npm dependencies
- **Testing**: Test JavaScript code with a familiar API
- **Learning**: Understand testing framework patterns
- **Education**: Teach test-driven development
- **CI/CD**: Run tests in restricted environments
- **Prototyping**: Quickly prototype test suites
- **Understanding**: Learn how testing frameworks work internally

## Limitations

This is an emulator for development and testing purposes:
- No snapshot testing
- No code coverage reporting
- Simplified mock implementation
- No module mocking integration
- No test.only or test.skip
- No parallel test execution
- No watch mode
- Simplified async handling

## Supported Features

### Test Definition
- ✅ describe
- ✅ test/it
- ✅ Nested describe blocks
- ✅ Async test support

### Matchers
- ✅ toBe
- ✅ toEqual/toStrictEqual
- ✅ toBeTruthy/toBeFalsy
- ✅ toBeNull/toBeUndefined/toBeDefined
- ✅ toBeGreaterThan/toBeLessThan
- ✅ toContain
- ✅ toHaveLength
- ✅ toHaveProperty
- ✅ toThrow
- ✅ toMatch
- ✅ .not modifier

### Mocking
- ✅ jest.fn()
- ✅ jest.spyOn()
- ✅ mockReturnValue
- ✅ mockImplementation
- ✅ mockResolvedValue/mockRejectedValue
- ✅ mockClear/mockReset
- ✅ Call tracking

### Hooks
- ✅ beforeAll
- ✅ afterAll
- ✅ beforeEach
- ✅ afterEach

## Real-World Testing Concepts

This emulator teaches the following concepts:

1. **Test Organization**: Grouping related tests with describe
2. **Test Cases**: Writing individual test cases with test/it
3. **Assertions**: Using matchers to verify behavior
4. **Mocking**: Isolating code under test
5. **Spying**: Observing function calls
6. **Setup/Teardown**: Managing test state
7. **Async Testing**: Testing asynchronous code
8. **TDD**: Test-driven development workflow

## Compatibility

Emulates core features of:
- Jest 27.x+ API patterns
- Common testing patterns
- Standard assertion syntax

## License

Part of the Emu-Soft project. See main repository LICENSE.
