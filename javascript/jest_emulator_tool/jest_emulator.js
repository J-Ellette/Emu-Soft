/**
 * Jest Emulator - Testing Framework for JavaScript
 * 
 * This module emulates the Jest testing framework, which is a delightful
 * JavaScript testing framework with a focus on simplicity. It works with
 * projects using Babel, TypeScript, Node, React, Angular, Vue and more.
 * 
 * Key Features:
 * - Test suites and test cases
 * - Assertions (matchers)
 * - Mocking capabilities
 * - Setup and teardown hooks
 * - Async testing support
 */

// Global test state
const testState = {
    suites: [],
    currentSuite: null,
    testResults: [],
    beforeEachHooks: [],
    afterEachHooks: [],
    beforeAllHooks: [],
    afterAllHooks: []
};

/**
 * Define a test suite
 */
function describe(description, testSuite) {
    const suite = {
        description,
        tests: [],
        beforeEachHooks: [],
        afterEachHooks: [],
        beforeAllHooks: [],
        afterAllHooks: [],
        parentSuite: testState.currentSuite
    };
    
    if (testState.currentSuite) {
        testState.currentSuite.tests.push(suite);
    } else {
        testState.suites.push(suite);
    }
    
    const previousSuite = testState.currentSuite;
    testState.currentSuite = suite;
    testSuite();
    testState.currentSuite = previousSuite;
}

/**
 * Define a test case
 */
function test(description, testFunction) {
    if (!testState.currentSuite) {
        throw new Error('Tests must be inside a describe block');
    }
    
    testState.currentSuite.tests.push({
        description,
        testFunction,
        isTest: true
    });
}

// Alias for test
const it = test;

/**
 * Setup hooks
 */
function beforeEach(hookFunction) {
    if (!testState.currentSuite) {
        testState.beforeEachHooks.push(hookFunction);
    } else {
        testState.currentSuite.beforeEachHooks.push(hookFunction);
    }
}

function afterEach(hookFunction) {
    if (!testState.currentSuite) {
        testState.afterEachHooks.push(hookFunction);
    } else {
        testState.currentSuite.afterEachHooks.push(hookFunction);
    }
}

function beforeAll(hookFunction) {
    if (!testState.currentSuite) {
        testState.beforeAllHooks.push(hookFunction);
    } else {
        testState.currentSuite.beforeAllHooks.push(hookFunction);
    }
}

function afterAll(hookFunction) {
    if (!testState.currentSuite) {
        testState.afterAllHooks.push(hookFunction);
    } else {
        testState.currentSuite.afterAllHooks.push(hookFunction);
    }
}

/**
 * Expectation class for assertions
 */
class Expectation {
    constructor(actual) {
        this.actual = actual;
        this.isNot = false;
    }

    get not() {
        const newExpectation = new Expectation(this.actual);
        newExpectation.isNot = !this.isNot;
        return newExpectation;
    }

    toBe(expected) {
        const passed = this.isNot 
            ? this.actual !== expected 
            : this.actual === expected;
        
        if (!passed) {
            throw new Error(
                this.isNot 
                    ? `Expected ${this.actual} not to be ${expected}`
                    : `Expected ${this.actual} to be ${expected}`
            );
        }
    }

    toEqual(expected) {
        const passed = this.isNot
            ? !this._deepEqual(this.actual, expected)
            : this._deepEqual(this.actual, expected);
        
        if (!passed) {
            throw new Error(
                this.isNot
                    ? `Expected ${JSON.stringify(this.actual)} not to equal ${JSON.stringify(expected)}`
                    : `Expected ${JSON.stringify(this.actual)} to equal ${JSON.stringify(expected)}`
            );
        }
    }

    toStrictEqual(expected) {
        return this.toEqual(expected);
    }

    toBeTruthy() {
        const passed = this.isNot ? !this.actual : !!this.actual;
        if (!passed) {
            throw new Error(
                this.isNot
                    ? `Expected ${this.actual} not to be truthy`
                    : `Expected ${this.actual} to be truthy`
            );
        }
    }

    toBeFalsy() {
        const passed = this.isNot ? !!this.actual : !this.actual;
        if (!passed) {
            throw new Error(
                this.isNot
                    ? `Expected ${this.actual} not to be falsy`
                    : `Expected ${this.actual} to be falsy`
            );
        }
    }

    toBeNull() {
        const passed = this.isNot ? this.actual !== null : this.actual === null;
        if (!passed) {
            throw new Error(
                this.isNot
                    ? `Expected ${this.actual} not to be null`
                    : `Expected ${this.actual} to be null`
            );
        }
    }

    toBeUndefined() {
        const passed = this.isNot ? this.actual !== undefined : this.actual === undefined;
        if (!passed) {
            throw new Error(
                this.isNot
                    ? `Expected ${this.actual} not to be undefined`
                    : `Expected ${this.actual} to be undefined`
            );
        }
    }

    toBeDefined() {
        const passed = this.isNot ? this.actual === undefined : this.actual !== undefined;
        if (!passed) {
            throw new Error(
                this.isNot
                    ? `Expected ${this.actual} not to be defined`
                    : `Expected ${this.actual} to be defined`
            );
        }
    }

    toBeGreaterThan(expected) {
        const passed = this.isNot ? this.actual <= expected : this.actual > expected;
        if (!passed) {
            throw new Error(
                this.isNot
                    ? `Expected ${this.actual} not to be greater than ${expected}`
                    : `Expected ${this.actual} to be greater than ${expected}`
            );
        }
    }

    toBeLessThan(expected) {
        const passed = this.isNot ? this.actual >= expected : this.actual < expected;
        if (!passed) {
            throw new Error(
                this.isNot
                    ? `Expected ${this.actual} not to be less than ${expected}`
                    : `Expected ${this.actual} to be less than ${expected}`
            );
        }
    }

    toContain(item) {
        const contains = Array.isArray(this.actual) 
            ? this.actual.includes(item)
            : typeof this.actual === 'string' && this.actual.includes(item);
        
        const passed = this.isNot ? !contains : contains;
        if (!passed) {
            throw new Error(
                this.isNot
                    ? `Expected ${JSON.stringify(this.actual)} not to contain ${item}`
                    : `Expected ${JSON.stringify(this.actual)} to contain ${item}`
            );
        }
    }

    toHaveLength(length) {
        const passed = this.isNot 
            ? this.actual.length !== length 
            : this.actual.length === length;
        
        if (!passed) {
            throw new Error(
                this.isNot
                    ? `Expected length ${this.actual.length} not to be ${length}`
                    : `Expected length ${this.actual.length} to be ${length}`
            );
        }
    }

    toHaveProperty(property, value) {
        const hasProperty = property in this.actual;
        
        if (value !== undefined) {
            const passed = this.isNot
                ? !(hasProperty && this.actual[property] === value)
                : hasProperty && this.actual[property] === value;
            
            if (!passed) {
                throw new Error(
                    this.isNot
                        ? `Expected object not to have property ${property} with value ${value}`
                        : `Expected object to have property ${property} with value ${value}`
                );
            }
        } else {
            const passed = this.isNot ? !hasProperty : hasProperty;
            if (!passed) {
                throw new Error(
                    this.isNot
                        ? `Expected object not to have property ${property}`
                        : `Expected object to have property ${property}`
                );
            }
        }
    }

    toThrow(expectedError) {
        let didThrow = false;
        let thrownError = null;
        
        try {
            this.actual();
        } catch (error) {
            didThrow = true;
            thrownError = error;
        }
        
        if (expectedError) {
            const errorMatches = typeof expectedError === 'string'
                ? thrownError && thrownError.message.includes(expectedError)
                : thrownError instanceof expectedError;
            
            const passed = this.isNot ? !errorMatches : errorMatches;
            if (!passed) {
                throw new Error(
                    this.isNot
                        ? `Expected function not to throw ${expectedError}`
                        : `Expected function to throw ${expectedError}`
                );
            }
        } else {
            const passed = this.isNot ? !didThrow : didThrow;
            if (!passed) {
                throw new Error(
                    this.isNot
                        ? 'Expected function not to throw'
                        : 'Expected function to throw'
                );
            }
        }
    }

    toMatch(pattern) {
        const matches = typeof pattern === 'string'
            ? this.actual.includes(pattern)
            : pattern.test(this.actual);
        
        const passed = this.isNot ? !matches : matches;
        if (!passed) {
            throw new Error(
                this.isNot
                    ? `Expected ${this.actual} not to match ${pattern}`
                    : `Expected ${this.actual} to match ${pattern}`
            );
        }
    }

    _deepEqual(obj1, obj2) {
        if (obj1 === obj2) return true;
        
        if (obj1 === null || obj2 === null) return false;
        if (typeof obj1 !== 'object' || typeof obj2 !== 'object') return false;
        
        const keys1 = Object.keys(obj1);
        const keys2 = Object.keys(obj2);
        
        if (keys1.length !== keys2.length) return false;
        
        for (const key of keys1) {
            if (!keys2.includes(key)) return false;
            if (!this._deepEqual(obj1[key], obj2[key])) return false;
        }
        
        return true;
    }
}

/**
 * Create an expectation
 */
function expect(actual) {
    return new Expectation(actual);
}

/**
 * Mock function
 */
class MockFunction {
    constructor(implementation = null) {
        this.implementation = implementation;
        this.calls = [];
        this.results = [];
    }

    mockImplementation(fn) {
        this.implementation = fn;
        return this;
    }

    mockReturnValue(value) {
        this.implementation = () => value;
        return this;
    }

    mockReturnValueOnce(value) {
        const originalImpl = this.implementation;
        const callCount = this.calls.length;
        
        this.implementation = function(...args) {
            if (this.calls.length === callCount) {
                return value;
            }
            return originalImpl ? originalImpl.apply(this, args) : undefined;
        }.bind(this);
        
        return this;
    }

    mockResolvedValue(value) {
        this.implementation = () => Promise.resolve(value);
        return this;
    }

    mockRejectedValue(value) {
        this.implementation = () => Promise.reject(value);
        return this;
    }

    __call(...args) {
        this.calls.push(args);
        
        try {
            const result = this.implementation ? this.implementation(...args) : undefined;
            this.results.push({ type: 'return', value: result });
            return result;
        } catch (error) {
            this.results.push({ type: 'throw', value: error });
            throw error;
        }
    }

    toHaveBeenCalled() {
        return this.calls.length > 0;
    }

    toHaveBeenCalledTimes(times) {
        return this.calls.length === times;
    }

    toHaveBeenCalledWith(...args) {
        return this.calls.some(call => 
            call.length === args.length &&
            call.every((arg, i) => arg === args[i])
        );
    }

    mockClear() {
        this.calls = [];
        this.results = [];
        return this;
    }

    mockReset() {
        this.mockClear();
        this.implementation = null;
        return this;
    }
}

/**
 * Create a mock function
 */
function fn(implementation = null) {
    const mockFn = new MockFunction(implementation);
    
    const callableFunction = function(...args) {
        return mockFn.__call(...args);
    };
    
    // Wrap methods to return callableFunction instead of mockFn
    callableFunction.mockImplementation = function(fn) {
        mockFn.mockImplementation(fn);
        return callableFunction;
    };
    callableFunction.mockReturnValue = function(value) {
        mockFn.mockReturnValue(value);
        return callableFunction;
    };
    callableFunction.mockReturnValueOnce = function(value) {
        mockFn.mockReturnValueOnce(value);
        return callableFunction;
    };
    callableFunction.mockResolvedValue = function(value) {
        mockFn.mockResolvedValue(value);
        return callableFunction;
    };
    callableFunction.mockRejectedValue = function(value) {
        mockFn.mockRejectedValue(value);
        return callableFunction;
    };
    callableFunction.mockClear = function() {
        mockFn.mockClear();
        return callableFunction;
    };
    callableFunction.mockReset = function() {
        mockFn.mockReset();
        return callableFunction;
    };
    
    // Expose the mock object
    callableFunction.mock = {
        get calls() { return mockFn.calls; },
        get results() { return mockFn.results; }
    };
    
    return callableFunction;
}

/**
 * Create a module mock
 */
function mock(moduleName, factory) {
    // Simplified mock - in real Jest this would integrate with module system
    return {
        moduleName,
        factory
    };
}

/**
 * Spy on object method
 */
function spyOn(object, methodName) {
    const original = object[methodName];
    const mockFn = fn(original.bind(object));
    
    object[methodName] = mockFn;
    
    mockFn.mockRestore = function() {
        object[methodName] = original;
    };
    
    return mockFn;
}

/**
 * Run all tests
 */
async function runTests() {
    console.log('\n=== Jest Test Runner ===\n');
    
    let totalTests = 0;
    let passedTests = 0;
    let failedTests = 0;
    
    // Run beforeAll hooks
    for (const hook of testState.beforeAllHooks) {
        await hook();
    }
    
    async function runSuite(suite, indent = 0) {
        const indentStr = '  '.repeat(indent);
        console.log(`${indentStr}${suite.description}`);
        
        // Run suite's beforeAll hooks
        for (const hook of suite.beforeAllHooks) {
            await hook();
        }
        
        for (const item of suite.tests) {
            if (item.isTest) {
                totalTests++;
                
                // Run beforeEach hooks
                for (const hook of [...testState.beforeEachHooks, ...suite.beforeEachHooks]) {
                    await hook();
                }
                
                try {
                    await item.testFunction();
                    passedTests++;
                    console.log(`${indentStr}  ✓ ${item.description}`);
                } catch (error) {
                    failedTests++;
                    console.log(`${indentStr}  ✗ ${item.description}`);
                    console.log(`${indentStr}    ${error.message}`);
                }
                
                // Run afterEach hooks
                for (const hook of [...suite.afterEachHooks, ...testState.afterEachHooks]) {
                    await hook();
                }
            } else {
                // Nested suite
                await runSuite(item, indent + 1);
            }
        }
        
        // Run suite's afterAll hooks
        for (const hook of suite.afterAllHooks) {
            await hook();
        }
    }
    
    for (const suite of testState.suites) {
        await runSuite(suite);
    }
    
    // Run afterAll hooks
    for (const hook of testState.afterAllHooks) {
        await hook();
    }
    
    console.log(`\n=== Test Results ===`);
    console.log(`Total: ${totalTests}`);
    console.log(`Passed: ${passedTests}`);
    console.log(`Failed: ${failedTests}`);
    console.log(`Success Rate: ${totalTests > 0 ? ((passedTests / totalTests) * 100).toFixed(2) : 0}%\n`);
    
    return {
        total: totalTests,
        passed: passedTests,
        failed: failedTests
    };
}

/**
 * Clear all test state (useful for re-running tests)
 */
function clearTestState() {
    testState.suites = [];
    testState.currentSuite = null;
    testState.testResults = [];
    testState.beforeEachHooks = [];
    testState.afterEachHooks = [];
    testState.beforeAllHooks = [];
    testState.afterAllHooks = [];
}

// Export Jest API
module.exports = {
    describe,
    test,
    it,
    expect,
    beforeEach,
    afterEach,
    beforeAll,
    afterAll,
    jest: {
        fn,
        mock,
        spyOn
    },
    runTests,
    clearTestState
};
