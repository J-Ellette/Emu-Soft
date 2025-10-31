# Lodash Emulator - Utility Library for JavaScript

This module emulates the **lodash** library, which is a modern JavaScript utility library delivering modularity, performance, and extras. It provides utility functions for common programming tasks using the functional programming paradigm.

## What is lodash?

Lodash is one of the most popular JavaScript utility libraries. It is designed to:
- Make JavaScript easier by taking the hassle out of working with arrays, numbers, objects, strings, etc.
- Provide consistent cross-environment iteration support
- Offer performant functional programming patterns
- Include utility functions for common tasks

## Features

This emulator implements core lodash functionality:

### Array Functions
- **chunk**: Split array into groups
- **compact**: Remove falsy values
- **intersection**: Find common values across arrays
- **union**: Combine unique values from arrays
- **uniq**: Remove duplicates
- **without**: Exclude specific values
- **first/last**: Get first or last element
- **flatten/flattenDeep**: Flatten nested arrays
- **nth**: Get element at index (supports negative indices)

### Collection Functions
- **map**: Transform collection elements
- **filter**: Filter collection by predicate
- **some**: Check if any element matches
- **every**: Check if all elements match
- **reduce**: Reduce collection to single value
- **size**: Get collection size
- **sortBy**: Sort by property or function
- **groupBy**: Group elements by key

### Object Functions
- **assign**: Merge objects
- **mapValues**: Transform object values
- **keys/values**: Get object keys or values
- **pick/omit**: Select or exclude properties
- **get/set**: Access nested properties safely
- **has**: Check if property exists

### String Functions
- **camelCase**: Convert to camelCase
- **kebabCase**: Convert to kebab-case
- **snakeCase**: Convert to snake_case
- **capitalize**: Capitalize string
- **upperFirst**: Uppercase first character
- **pad**: Pad string to length
- **repeat**: Repeat string n times
- **lowerCase**: Convert to lower case with spaces

### Function Utilities
- **debounce**: Delay function execution
- **throttle**: Limit function execution rate
- **once**: Execute function only once
- **partial**: Partial function application

### Utility Functions
- **cloneDeep**: Deep clone objects
- **isEqual**: Deep equality comparison
- **uniqueId**: Generate unique IDs
- **random**: Generate random numbers

### Type Checking
- **isArray/isObject/isString/isNumber/isFunction/isBoolean**
- **isNull/isUndefined/isNil**
- **isEmpty**: Check if value is empty

## Usage Examples

### Array Operations

```javascript
const _ = require('./lodash_emulator');

// Split array into chunks
_.chunk([1, 2, 3, 4, 5], 2);
// => [[1, 2], [3, 4], [5]]

// Remove falsy values
_.compact([0, 1, false, 2, '', 3]);
// => [1, 2, 3]

// Get unique values
_.uniq([1, 2, 1, 3, 2, 4]);
// => [1, 2, 3, 4]

// Find intersection
_.intersection([1, 2, 3], [2, 3, 4], [3, 4, 5]);
// => [3]

// Flatten arrays
_.flattenDeep([1, [2, 3], [4, [5]]]);
// => [1, 2, 3, 4, 5]

// Get element at index (supports negative)
_.nth([1, 2, 3, 4], -1);
// => 4
```

### Collection Operations

```javascript
const _ = require('./lodash_emulator');

const users = [
    { name: 'Alice', age: 30 },
    { name: 'Bob', age: 25 },
    { name: 'Charlie', age: 35 }
];

// Map to specific property
_.map(users, 'name');
// => ['Alice', 'Bob', 'Charlie']

// Filter collection
_.filter(users, user => user.age > 28);
// => [{ name: 'Alice', age: 30 }, { name: 'Charlie', age: 35 }]

// Sort by property
_.sortBy(users, 'age');
// => [{ name: 'Bob', age: 25 }, { name: 'Alice', age: 30 }, { name: 'Charlie', age: 35 }]

// Group by property
const items = [
    { type: 'fruit', name: 'apple' },
    { type: 'vegetable', name: 'carrot' },
    { type: 'fruit', name: 'banana' }
];
_.groupBy(items, 'type');
// => { fruit: [...], vegetable: [...] }

// Reduce to single value
_.reduce([1, 2, 3, 4], (sum, n) => sum + n, 0);
// => 10

// Check conditions
_.some(users, user => user.age > 30);
// => true

_.every(users, user => user.age > 20);
// => true
```

### Object Operations

```javascript
const _ = require('./lodash_emulator');

const user = {
    name: 'Alice',
    email: 'alice@example.com',
    age: 30,
    password: 'secret'
};

// Pick specific properties
_.pick(user, 'name', 'email');
// => { name: 'Alice', email: 'alice@example.com' }

// Omit properties
_.omit(user, 'password');
// => { name: 'Alice', email: 'alice@example.com', age: 30 }

// Get nested property safely
const data = { user: { profile: { name: 'Alice' } } };
_.get(data, 'user.profile.name');
// => 'Alice'

_.get(data, 'user.profile.age', 'Unknown');
// => 'Unknown'

// Set nested property
const obj = {};
_.set(obj, 'user.profile.name', 'Alice');
// obj => { user: { profile: { name: 'Alice' } } }

// Check if property exists
_.has(data, 'user.profile.name');
// => true

// Transform values
_.mapValues({ a: 1, b: 2 }, x => x * 2);
// => { a: 2, b: 4 }

// Merge objects
_.assign({ a: 1 }, { b: 2 }, { c: 3 });
// => { a: 1, b: 2, c: 3 }
```

### String Operations

```javascript
const _ = require('./lodash_emulator');

// Convert to different cases
_.camelCase('hello world');
// => 'helloWorld'

_.kebabCase('helloWorld');
// => 'hello-world'

_.snakeCase('helloWorld');
// => 'hello_world'

// Capitalize
_.capitalize('hello');
// => 'Hello'

_.upperFirst('hello world');
// => 'Hello world'

// Pad string
_.pad('hi', 5);
// => ' hi  '

// Repeat string
_.repeat('ab', 3);
// => 'ababab'
```

### Function Utilities

```javascript
const _ = require('./lodash_emulator');

// Debounce - delay execution until after wait time
const saveInput = _.debounce((text) => {
    console.log('Saving:', text);
}, 300);

// Will only save once after user stops typing for 300ms
saveInput('h');
saveInput('he');
saveInput('hel');
saveInput('hello');

// Throttle - limit execution rate
const trackScroll = _.throttle(() => {
    console.log('Scroll position:', window.scrollY);
}, 100);

window.addEventListener('scroll', trackScroll);

// Once - execute only one time
const initialize = _.once(() => {
    console.log('Initializing...');
});

initialize(); // logs 'Initializing...'
initialize(); // does nothing
initialize(); // does nothing

// Partial application
const greet = (greeting, name) => `${greeting}, ${name}!`;
const sayHello = _.partial(greet, 'Hello');

sayHello('Alice'); // => 'Hello, Alice!'
sayHello('Bob');   // => 'Hello, Bob!'
```

### Utility Functions

```javascript
const _ = require('./lodash_emulator');

// Deep clone
const original = { a: 1, b: { c: 2 } };
const clone = _.cloneDeep(original);
clone.b.c = 3;
// original.b.c is still 2

// Deep equality
_.isEqual({ a: 1, b: 2 }, { a: 1, b: 2 });
// => true

_.isEqual([1, 2, 3], [1, 2, 3]);
// => true

// Generate unique IDs
_.uniqueId('user_');  // => 'user_1'
_.uniqueId('user_');  // => 'user_2'
_.uniqueId('item_');  // => 'item_3'

// Random numbers
_.random(1, 10);      // => random number between 1 and 10
_.random(100);        // => random number between 0 and 100
```

### Type Checking

```javascript
const _ = require('./lodash_emulator');

_.isArray([1, 2, 3]);           // => true
_.isObject({ a: 1 });           // => true
_.isString('hello');            // => true
_.isNumber(42);                 // => true
_.isFunction(() => {});         // => true
_.isBoolean(true);              // => true
_.isNull(null);                 // => true
_.isUndefined(undefined);       // => true
_.isNil(null);                  // => true
_.isNil(undefined);             // => true
_.isEmpty([]);                  // => true
_.isEmpty({});                  // => true
_.isEmpty('');                  // => true
```

### Integration Example: Data Processing Pipeline

```javascript
const _ = require('./lodash_emulator');

const orders = [
    { id: 1, customer: 'Alice', amount: 100, status: 'completed' },
    { id: 2, customer: 'Bob', amount: 200, status: 'pending' },
    { id: 3, customer: 'Alice', amount: 150, status: 'completed' },
    { id: 4, customer: 'Charlie', amount: 75, status: 'completed' },
    { id: 5, customer: 'Bob', amount: 300, status: 'completed' }
];

// Get total sales by customer for completed orders
const result = _.mapValues(
    _.groupBy(
        _.filter(orders, order => order.status === 'completed'),
        'customer'
    ),
    customerOrders => _.reduce(customerOrders, (sum, order) => sum + order.amount, 0)
);

console.log(result);
// => { Alice: 250, Charlie: 75, Bob: 300 }

// Get top customers
const topCustomers = _.map(
    _.sortBy(
        _.map(_.keys(result), customer => ({
            customer,
            total: result[customer]
        })),
        'total'
    ).reverse(),
    'customer'
);

console.log(topCustomers);
// => ['Bob', 'Alice', 'Charlie']
```

## Testing

Run the comprehensive test suite:

```bash
node test_lodash_emulator.js
```

Tests cover:
- Array manipulation (11 tests)
- Collection operations (10 tests)
- Object manipulation (9 tests)
- String transformation (8 tests)
- Function utilities (4 tests)
- Utility functions (4 tests)
- Type checking (10 tests)
- Integration scenarios (3 tests)

Total: 59 tests, all passing

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for lodash in development and testing:

```javascript
// Instead of:
// const _ = require('lodash');

// Use:
const _ = require('./lodash_emulator');

// The rest of your code remains unchanged
const result = _.map([1, 2, 3], n => n * 2);
```

## Use Cases

Perfect for:
- **Local Development**: Develop without npm dependencies
- **Testing**: Test utility functions without external dependencies
- **Learning**: Understand functional programming patterns
- **Prototyping**: Quickly prototype data transformations
- **Education**: Teach JavaScript utility patterns
- **Environments**: Run in restricted environments

## Limitations

This is an emulator for development and testing purposes:
- Subset of lodash functions (most common ones)
- May have minor performance differences
- No chain() method for method chaining
- Simplified implementations for some functions
- Not optimized for large-scale production use

## Supported Features

### Array Functions (11)
- ✅ chunk, compact, intersection, union, uniq
- ✅ without, first, last, flatten, flattenDeep, nth

### Collection Functions (10)
- ✅ map, filter, some, every, reduce
- ✅ size, sortBy, groupBy

### Object Functions (9)
- ✅ assign, mapValues, keys, values
- ✅ pick, omit, get, set, has

### String Functions (8)
- ✅ camelCase, kebabCase, snakeCase
- ✅ capitalize, upperFirst, pad, repeat, lowerCase

### Function Utilities (4)
- ✅ debounce, throttle, once, partial

### Utility Functions (4)
- ✅ cloneDeep, isEqual, uniqueId, random

### Type Checking (10)
- ✅ isArray, isObject, isString, isNumber, isFunction
- ✅ isBoolean, isNull, isUndefined, isNil, isEmpty

## Real-World Programming Concepts

This emulator teaches the following concepts:

1. **Functional Programming**: Pure functions, immutability
2. **Array Manipulation**: Filtering, mapping, reducing
3. **Object Manipulation**: Property access, transformation
4. **Higher-Order Functions**: Functions that accept/return functions
5. **Currying**: Partial application of arguments
6. **Debouncing/Throttling**: Rate limiting function execution
7. **Type Checking**: Runtime type validation
8. **Deep Operations**: Deep cloning, deep equality

## Compatibility

Emulates core features of:
- Lodash 4.x API patterns
- Common utility function patterns
- Functional programming conventions

## License

Part of the Emu-Soft project. See main repository LICENSE.
