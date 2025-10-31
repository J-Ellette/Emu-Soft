/**
 * Tests for lodash emulator
 * 
 * Comprehensive test suite for utility library emulator functionality.
 */

const _ = require('./lodash_emulator');

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
        console.log('Running Lodash Emulator Tests\n');
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
// ARRAY FUNCTION TESTS
// ============================================================================

runner.test('chunk - should split array into chunks', () => {
    const result = _.chunk([1, 2, 3, 4, 5], 2);
    assertDeepEqual(result, [[1, 2], [3, 4], [5]]);
});

runner.test('compact - should remove falsy values', () => {
    const result = _.compact([0, 1, false, 2, '', 3, null, undefined]);
    assertDeepEqual(result, [1, 2, 3]);
});

runner.test('intersection - should return common values', () => {
    const result = _.intersection([1, 2, 3], [2, 3, 4], [3, 4, 5]);
    assertDeepEqual(result, [3]);
});

runner.test('union - should return unique values from all arrays', () => {
    const result = _.union([1, 2], [2, 3], [3, 4]);
    assertDeepEqual(result, [1, 2, 3, 4]);
});

runner.test('uniq - should return unique values', () => {
    const result = _.uniq([1, 2, 1, 3, 2, 4]);
    assertDeepEqual(result, [1, 2, 3, 4]);
});

runner.test('without - should exclude values', () => {
    const result = _.without([1, 2, 3, 4, 5], 2, 4);
    assertDeepEqual(result, [1, 3, 5]);
});

runner.test('first - should get first element', () => {
    const result = _.first([1, 2, 3]);
    assertEqual(result, 1);
});

runner.test('last - should get last element', () => {
    const result = _.last([1, 2, 3]);
    assertEqual(result, 3);
});

runner.test('flatten - should flatten array one level', () => {
    const result = _.flatten([1, [2, 3], [4, [5]]]);
    assertDeepEqual(result, [1, 2, 3, 4, [5]]);
});

runner.test('flattenDeep - should flatten array recursively', () => {
    const result = _.flattenDeep([1, [2, 3], [4, [5, [6]]]]);
    assertDeepEqual(result, [1, 2, 3, 4, 5, 6]);
});

runner.test('nth - should get element at index', () => {
    const arr = [1, 2, 3, 4];
    assertEqual(_.nth(arr, 1), 2);
    assertEqual(_.nth(arr, -1), 4);
});

// ============================================================================
// COLLECTION FUNCTION TESTS
// ============================================================================

runner.test('map - should map array values', () => {
    const result = _.map([1, 2, 3], x => x * 2);
    assertDeepEqual(result, [2, 4, 6]);
});

runner.test('map - should map object values', () => {
    const result = _.map({ a: 1, b: 2 }, x => x * 2);
    assertDeepEqual(result, [2, 4]);
});

runner.test('map - should map by property name', () => {
    const users = [{ name: 'Alice' }, { name: 'Bob' }];
    const result = _.map(users, 'name');
    assertDeepEqual(result, ['Alice', 'Bob']);
});

runner.test('filter - should filter array', () => {
    const result = _.filter([1, 2, 3, 4], x => x % 2 === 0);
    assertDeepEqual(result, [2, 4]);
});

runner.test('some - should check if any element matches', () => {
    const result = _.some([1, 2, 3], x => x > 2);
    assert(result === true);
});

runner.test('every - should check if all elements match', () => {
    const result = _.every([2, 4, 6], x => x % 2 === 0);
    assert(result === true);
});

runner.test('reduce - should reduce array to single value', () => {
    const result = _.reduce([1, 2, 3, 4], (sum, n) => sum + n, 0);
    assertEqual(result, 10);
});

runner.test('size - should get collection size', () => {
    assertEqual(_.size([1, 2, 3]), 3);
    assertEqual(_.size({ a: 1, b: 2 }), 2);
    assertEqual(_.size('hello'), 5);
});

runner.test('sortBy - should sort by iteratee', () => {
    const users = [{ age: 30 }, { age: 20 }, { age: 40 }];
    const result = _.sortBy(users, 'age');
    assertDeepEqual(result, [{ age: 20 }, { age: 30 }, { age: 40 }]);
});

runner.test('groupBy - should group by key', () => {
    const items = [
        { type: 'fruit', name: 'apple' },
        { type: 'vegetable', name: 'carrot' },
        { type: 'fruit', name: 'banana' }
    ];
    const result = _.groupBy(items, 'type');
    assert(result.fruit.length === 2);
    assert(result.vegetable.length === 1);
});

// ============================================================================
// OBJECT FUNCTION TESTS
// ============================================================================

runner.test('assign - should assign properties', () => {
    const result = _.assign({ a: 1 }, { b: 2 }, { c: 3 });
    assertDeepEqual(result, { a: 1, b: 2, c: 3 });
});

runner.test('mapValues - should map object values', () => {
    const result = _.mapValues({ a: 1, b: 2 }, x => x * 2);
    assertDeepEqual(result, { a: 2, b: 4 });
});

runner.test('keys - should get object keys', () => {
    const result = _.keys({ a: 1, b: 2, c: 3 });
    assertDeepEqual(result, ['a', 'b', 'c']);
});

runner.test('values - should get object values', () => {
    const result = _.values({ a: 1, b: 2, c: 3 });
    assertDeepEqual(result, [1, 2, 3]);
});

runner.test('pick - should pick properties', () => {
    const obj = { a: 1, b: 2, c: 3, d: 4 };
    const result = _.pick(obj, 'a', 'c');
    assertDeepEqual(result, { a: 1, c: 3 });
});

runner.test('omit - should omit properties', () => {
    const obj = { a: 1, b: 2, c: 3, d: 4 };
    const result = _.omit(obj, 'b', 'd');
    assertDeepEqual(result, { a: 1, c: 3 });
});

runner.test('get - should get nested value', () => {
    const obj = { a: { b: { c: 42 } } };
    assertEqual(_.get(obj, 'a.b.c'), 42);
    assertEqual(_.get(obj, 'a.b.d', 'default'), 'default');
});

runner.test('set - should set nested value', () => {
    const obj = { a: {} };
    _.set(obj, 'a.b.c', 42);
    assertEqual(obj.a.b.c, 42);
});

runner.test('has - should check if property exists', () => {
    const obj = { a: { b: 2 } };
    assert(_.has(obj, 'a.b') === true);
    assert(_.has(obj, 'a.c') === false);
});

// ============================================================================
// STRING FUNCTION TESTS
// ============================================================================

runner.test('camelCase - should convert to camelCase', () => {
    assertEqual(_.camelCase('hello world'), 'helloWorld');
    assertEqual(_.camelCase('hello-world'), 'helloWorld');
    assertEqual(_.camelCase('hello_world'), 'helloWorld');
});

runner.test('kebabCase - should convert to kebab-case', () => {
    assertEqual(_.kebabCase('helloWorld'), 'hello-world');
    assertEqual(_.kebabCase('hello world'), 'hello-world');
});

runner.test('snakeCase - should convert to snake_case', () => {
    assertEqual(_.snakeCase('helloWorld'), 'hello_world');
    assertEqual(_.snakeCase('hello world'), 'hello_world');
});

runner.test('capitalize - should capitalize string', () => {
    assertEqual(_.capitalize('hello'), 'Hello');
    assertEqual(_.capitalize('HELLO'), 'Hello');
});

runner.test('upperFirst - should uppercase first character', () => {
    assertEqual(_.upperFirst('hello'), 'Hello');
    assertEqual(_.upperFirst('HELLO'), 'HELLO');
});

runner.test('pad - should pad string', () => {
    const result = _.pad('hi', 5);
    assertEqual(result, ' hi  ');
});

runner.test('repeat - should repeat string', () => {
    assertEqual(_.repeat('ab', 3), 'ababab');
});

runner.test('lowerCase - should convert to lower case', () => {
    assertEqual(_.lowerCase('helloWorld'), 'hello world');
    assertEqual(_.lowerCase('hello-world'), 'hello world');
});

// ============================================================================
// FUNCTION UTILITY TESTS
// ============================================================================

runner.test('debounce - should debounce function calls', (done) => {
    let count = 0;
    const increment = _.debounce(() => count++, 50);
    
    increment();
    increment();
    increment();
    
    setTimeout(() => {
        assertEqual(count, 1, 'Should only call once');
    }, 100);
});

runner.test('throttle - should throttle function calls', (done) => {
    let count = 0;
    const increment = _.throttle(() => count++, 50);
    
    increment();
    increment();
    increment();
    
    setTimeout(() => {
        assert(count >= 1, 'Should call at least once');
    }, 100);
});

runner.test('once - should call function only once', () => {
    let count = 0;
    const increment = _.once(() => count++);
    
    increment();
    increment();
    increment();
    
    assertEqual(count, 1);
});

runner.test('partial - should partially apply arguments', () => {
    const greet = (greeting, name) => `${greeting}, ${name}!`;
    const sayHello = _.partial(greet, 'Hello');
    
    assertEqual(sayHello('Alice'), 'Hello, Alice!');
});

// ============================================================================
// UTILITY FUNCTION TESTS
// ============================================================================

runner.test('cloneDeep - should deep clone object', () => {
    const obj = { a: 1, b: { c: 2 } };
    const clone = _.cloneDeep(obj);
    
    clone.b.c = 3;
    assertEqual(obj.b.c, 2, 'Original should not be modified');
    assertEqual(clone.b.c, 3);
});

runner.test('isEqual - should compare values deeply', () => {
    assert(_.isEqual({ a: 1, b: 2 }, { a: 1, b: 2 }) === true);
    assert(_.isEqual({ a: 1, b: 2 }, { a: 1, b: 3 }) === false);
    assert(_.isEqual([1, 2, 3], [1, 2, 3]) === true);
});

runner.test('uniqueId - should generate unique IDs', () => {
    const id1 = _.uniqueId('user_');
    const id2 = _.uniqueId('user_');
    
    assert(id1 !== id2);
    assert(id1.startsWith('user_'));
});

runner.test('random - should generate random number', () => {
    const num = _.random(1, 10);
    assert(num >= 1 && num <= 10);
});

// ============================================================================
// TYPE CHECKING TESTS
// ============================================================================

runner.test('isArray - should check if value is array', () => {
    assert(_.isArray([]) === true);
    assert(_.isArray({}) === false);
});

runner.test('isObject - should check if value is object', () => {
    assert(_.isObject({}) === true);
    assert(_.isObject([]) === false);
    assert(_.isObject(null) === false);
});

runner.test('isString - should check if value is string', () => {
    assert(_.isString('hello') === true);
    assert(_.isString(123) === false);
});

runner.test('isNumber - should check if value is number', () => {
    assert(_.isNumber(123) === true);
    assert(_.isNumber('123') === false);
    assert(_.isNumber(NaN) === false);
});

runner.test('isFunction - should check if value is function', () => {
    assert(_.isFunction(() => {}) === true);
    assert(_.isFunction({}) === false);
});

runner.test('isBoolean - should check if value is boolean', () => {
    assert(_.isBoolean(true) === true);
    assert(_.isBoolean(1) === false);
});

runner.test('isNull - should check if value is null', () => {
    assert(_.isNull(null) === true);
    assert(_.isNull(undefined) === false);
});

runner.test('isUndefined - should check if value is undefined', () => {
    assert(_.isUndefined(undefined) === true);
    assert(_.isUndefined(null) === false);
});

runner.test('isNil - should check if value is null or undefined', () => {
    assert(_.isNil(null) === true);
    assert(_.isNil(undefined) === true);
    assert(_.isNil(0) === false);
});

runner.test('isEmpty - should check if value is empty', () => {
    assert(_.isEmpty([]) === true);
    assert(_.isEmpty({}) === true);
    assert(_.isEmpty('') === true);
    assert(_.isEmpty([1]) === false);
});

// ============================================================================
// INTEGRATION TESTS
// ============================================================================

runner.test('Integration - data transformation pipeline', () => {
    const users = [
        { name: 'Alice', age: 30, active: true },
        { name: 'Bob', age: 25, active: false },
        { name: 'Charlie', age: 35, active: true },
        { name: 'David', age: 28, active: true }
    ];
    
    // Filter active users, sort by age, get names
    const result = _.map(
        _.sortBy(
            _.filter(users, user => user.active),
            'age'
        ),
        'name'
    );
    
    assertDeepEqual(result, ['David', 'Alice', 'Charlie']);
});

runner.test('Integration - complex object manipulation', () => {
    const data = {
        users: {
            admin: { name: 'Alice', level: 5 },
            user1: { name: 'Bob', level: 2 },
            user2: { name: 'Charlie', level: 3 }
        }
    };
    
    const adminName = _.get(data, 'users.admin.name');
    assertEqual(adminName, 'Alice');
    
    const userLevels = _.mapValues(data.users, 'level');
    assertDeepEqual(userLevels, { admin: 5, user1: 2, user2: 3 });
});

runner.test('Integration - array operations', () => {
    const arr1 = [1, 2, 3, 4, 5];
    const arr2 = [3, 4, 5, 6, 7];
    
    const common = _.intersection(arr1, arr2);
    const all = _.union(arr1, arr2);
    const unique = _.uniq([...arr1, ...arr2]);
    
    assertDeepEqual(common, [3, 4, 5]);
    assertDeepEqual(all, [1, 2, 3, 4, 5, 6, 7]);
    assertDeepEqual(unique, [1, 2, 3, 4, 5, 6, 7]);
});

// Run all tests
runner.run().catch(console.error);
