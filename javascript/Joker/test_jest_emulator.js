/**
 * Developed by PowerShield, as an alternative to Jest
 */

/**
 * Test Suite for Jest Emulator
 * 
 * This file tests the Jest emulator implementation to ensure all features
 * work correctly including test definitions, assertions, mocking, and hooks.
 */

const { describe, test, it, expect, beforeEach, afterEach, beforeAll, afterAll, jest, runTests, clearTestState } = require('./jest_emulator');

// Test 1: Basic assertions
describe('Basic Assertions', () => {
    test('toBe works with primitives', () => {
        expect(1).toBe(1);
        expect('hello').toBe('hello');
        expect(true).toBe(true);
    });

    test('toEqual works with objects and arrays', () => {
        expect({ a: 1, b: 2 }).toEqual({ a: 1, b: 2 });
        expect([1, 2, 3]).toEqual([1, 2, 3]);
    });

    test('toBeTruthy and toBeFalsy work', () => {
        expect(true).toBeTruthy();
        expect(1).toBeTruthy();
        expect('hello').toBeTruthy();
        
        expect(false).toBeFalsy();
        expect(0).toBeFalsy();
        expect('').toBeFalsy();
    });

    test('toBeNull and toBeUndefined work', () => {
        expect(null).toBeNull();
        expect(undefined).toBeUndefined();
    });

    test('toBeDefined works', () => {
        const value = 'defined';
        expect(value).toBeDefined();
    });
});

// Test 2: Negation with .not
describe('Negation with .not', () => {
    test('not.toBe works', () => {
        expect(1).not.toBe(2);
        expect('hello').not.toBe('world');
    });

    test('not.toEqual works', () => {
        expect({ a: 1 }).not.toEqual({ a: 2 });
        expect([1, 2]).not.toEqual([1, 3]);
    });

    test('not.toBeTruthy works', () => {
        expect(false).not.toBeTruthy();
        expect(0).not.toBeTruthy();
    });

    test('not.toBeNull works', () => {
        expect('value').not.toBeNull();
        expect(0).not.toBeNull();
    });
});

// Test 3: Comparison matchers
describe('Comparison Matchers', () => {
    test('toBeGreaterThan works', () => {
        expect(10).toBeGreaterThan(5);
        expect(100).toBeGreaterThan(50);
    });

    test('toBeLessThan works', () => {
        expect(5).toBeLessThan(10);
        expect(50).toBeLessThan(100);
    });
});

// Test 4: Array and string matchers
describe('Array and String Matchers', () => {
    test('toContain works with arrays', () => {
        expect([1, 2, 3, 4]).toContain(3);
        expect(['apple', 'banana', 'orange']).toContain('banana');
    });

    test('toContain works with strings', () => {
        expect('hello world').toContain('world');
        expect('JavaScript').toContain('Script');
    });

    test('toHaveLength works', () => {
        expect([1, 2, 3]).toHaveLength(3);
        expect('hello').toHaveLength(5);
    });
});

// Test 5: Object matchers
describe('Object Matchers', () => {
    test('toHaveProperty checks property existence', () => {
        const obj = { name: 'Alice', age: 30 };
        expect(obj).toHaveProperty('name');
        expect(obj).toHaveProperty('age');
    });

    test('toHaveProperty checks property value', () => {
        const obj = { name: 'Alice', age: 30 };
        expect(obj).toHaveProperty('name', 'Alice');
        expect(obj).toHaveProperty('age', 30);
    });
});

// Test 6: Exception testing
describe('Exception Testing', () => {
    test('toThrow detects thrown errors', () => {
        const throwError = () => {
            throw new Error('Something went wrong');
        };
        
        expect(throwError).toThrow();
        expect(throwError).toThrow('went wrong');
    });

    test('toThrow detects specific error types', () => {
        const throwTypeError = () => {
            throw new TypeError('Type error occurred');
        };
        
        expect(throwTypeError).toThrow(TypeError);
    });
});

// Test 7: Pattern matching
describe('Pattern Matching', () => {
    test('toMatch works with strings', () => {
        expect('hello world').toMatch('world');
        expect('test@example.com').toMatch('example');
    });

    test('toMatch works with regex', () => {
        expect('hello123').toMatch(/\d+/);
        expect('test@example.com').toMatch(/^\w+@\w+\.\w+$/);
    });
});

// Test 8: Mock functions
describe('Mock Functions', () => {
    test('jest.fn creates a mock function', () => {
        const mockFn = jest.fn();
        mockFn();
        expect(mockFn.mock.calls).toHaveLength(1);
    });

    test('mock functions track calls', () => {
        const mockFn = jest.fn();
        mockFn('arg1', 'arg2');
        mockFn('arg3');
        
        expect(mockFn.mock.calls).toHaveLength(2);
        expect(mockFn.mock.calls[0]).toEqual(['arg1', 'arg2']);
        expect(mockFn.mock.calls[1]).toEqual(['arg3']);
    });

    test('mockReturnValue sets return value', () => {
        const mockFn = jest.fn().mockReturnValue(42);
        const result = mockFn();
        
        expect(result).toBe(42);
    });

    test('mockImplementation sets custom implementation', () => {
        const mockFn = jest.fn().mockImplementation((x, y) => x + y);
        const result = mockFn(2, 3);
        
        expect(result).toBe(5);
    });

    test('mockClear clears call history', () => {
        const mockFn = jest.fn();
        mockFn();
        mockFn();
        
        expect(mockFn.mock.calls).toHaveLength(2);
        
        mockFn.mockClear();
        expect(mockFn.mock.calls).toHaveLength(0);
    });
});

// Test 9: Spy functions
describe('Spy Functions', () => {
    test('spyOn tracks method calls', () => {
        const calculator = {
            add: (a, b) => a + b
        };
        
        const spy = jest.spyOn(calculator, 'add');
        calculator.add(2, 3);
        
        expect(spy.mock.calls).toHaveLength(1);
        expect(spy.mock.calls[0]).toEqual([2, 3]);
    });

    test('spyOn can be restored', () => {
        const calculator = {
            add: (a, b) => a + b
        };
        
        const originalAdd = calculator.add;
        const spy = jest.spyOn(calculator, 'add');
        spy.mockRestore();
        
        expect(calculator.add).toBe(originalAdd);
    });
});

// Test 10: Setup and teardown hooks
describe('Setup and Teardown Hooks', () => {
    let counter = 0;
    
    beforeAll(() => {
        counter = 0;
    });
    
    beforeEach(() => {
        counter++;
    });
    
    afterEach(() => {
        // Clean up after each test
    });
    
    afterAll(() => {
        // Final cleanup
    });
    
    test('first test increments counter', () => {
        expect(counter).toBe(1);
    });
    
    test('second test has counter at 2', () => {
        expect(counter).toBe(2);
    });
});

// Test 11: Nested describe blocks
describe('Nested Describe Blocks', () => {
    describe('Inner Suite 1', () => {
        test('test in inner suite 1', () => {
            expect(true).toBe(true);
        });
    });
    
    describe('Inner Suite 2', () => {
        test('test in inner suite 2', () => {
            expect(1 + 1).toBe(2);
        });
        
        describe('Deeply Nested Suite', () => {
            test('test in deeply nested suite', () => {
                expect('nested').toHaveLength(6);
            });
        });
    });
});

// Test 12: Async testing
describe('Async Testing', () => {
    test('async test with promises', async () => {
        const promise = Promise.resolve(42);
        const result = await promise;
        expect(result).toBe(42);
    });

    test('async test with async function', async () => {
        const asyncFunction = async () => {
            return 'hello';
        };
        
        const result = await asyncFunction();
        expect(result).toBe('hello');
    });
});

// Test 13: Real-world example - testing a calculator
describe('Calculator Tests', () => {
    const calculator = {
        add: (a, b) => a + b,
        subtract: (a, b) => a - b,
        multiply: (a, b) => a * b,
        divide: (a, b) => {
            if (b === 0) throw new Error('Division by zero');
            return a / b;
        }
    };
    
    test('adds two numbers correctly', () => {
        expect(calculator.add(2, 3)).toBe(5);
        expect(calculator.add(-1, 1)).toBe(0);
    });
    
    test('subtracts two numbers correctly', () => {
        expect(calculator.subtract(5, 3)).toBe(2);
        expect(calculator.subtract(0, 5)).toBe(-5);
    });
    
    test('multiplies two numbers correctly', () => {
        expect(calculator.multiply(3, 4)).toBe(12);
        expect(calculator.multiply(5, 0)).toBe(0);
    });
    
    test('divides two numbers correctly', () => {
        expect(calculator.divide(10, 2)).toBe(5);
        expect(calculator.divide(9, 3)).toBe(3);
    });
    
    test('throws error on division by zero', () => {
        expect(() => calculator.divide(10, 0)).toThrow('Division by zero');
    });
});

// Test 14: Real-world example - testing user service
describe('User Service Tests', () => {
    let userService;
    let mockDatabase;
    
    beforeEach(() => {
        mockDatabase = {
            findUser: jest.fn(),
            saveUser: jest.fn(),
            deleteUser: jest.fn()
        };
        
        userService = {
            getUser: (id) => mockDatabase.findUser(id),
            createUser: (userData) => mockDatabase.saveUser(userData),
            removeUser: (id) => mockDatabase.deleteUser(id)
        };
    });
    
    test('getUser calls database with correct id', () => {
        mockDatabase.findUser.mockReturnValue({ id: 1, name: 'Alice' });
        
        const user = userService.getUser(1);
        
        expect(mockDatabase.findUser.mock.calls).toHaveLength(1);
        expect(mockDatabase.findUser.mock.calls[0]).toEqual([1]);
        expect(user).toEqual({ id: 1, name: 'Alice' });
    });
    
    test('createUser calls database with user data', () => {
        const userData = { name: 'Bob', email: 'bob@example.com' };
        mockDatabase.saveUser.mockReturnValue({ id: 2, ...userData });
        
        const result = userService.createUser(userData);
        
        expect(mockDatabase.saveUser.mock.calls).toHaveLength(1);
        expect(result).toHaveProperty('id');
    });
    
    test('removeUser calls database with correct id', () => {
        userService.removeUser(5);
        
        expect(mockDatabase.deleteUser.mock.calls).toHaveLength(1);
        expect(mockDatabase.deleteUser.mock.calls[0]).toEqual([5]);
    });
});

// Run all tests
console.log('Running Jest Emulator Tests...\n');
runTests().then(results => {
    if (results.failed === 0) {
        console.log('✓ All tests passed!');
        process.exit(0);
    } else {
        console.log(`✗ ${results.failed} test(s) failed.`);
        process.exit(1);
    }
}).catch(error => {
    console.error('Error running tests:', error);
    process.exit(1);
});
