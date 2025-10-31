/**
 * Lodash Emulator - Utility Library for JavaScript
 * 
 * This module emulates the lodash library, which is a modern JavaScript utility
 * library delivering modularity, performance, and extras. It provides utility
 * functions for common programming tasks using functional programming paradigm.
 * 
 * Key Features:
 * - Array manipulation
 * - Object manipulation
 * - String manipulation
 * - Function utilities
 * - Collection utilities
 * - Type checking
 */

const _ = {};

// ============================================================================
// ARRAY FUNCTIONS
// ============================================================================

/**
 * Creates an array of elements split into groups the length of size.
 */
_.chunk = function(array, size = 1) {
    if (!Array.isArray(array) || size < 1) {
        return [];
    }
    
    const result = [];
    for (let i = 0; i < array.length; i += size) {
        result.push(array.slice(i, i + size));
    }
    return result;
};

/**
 * Creates an array with all falsey values removed.
 */
_.compact = function(array) {
    if (!Array.isArray(array)) {
        return [];
    }
    return array.filter(Boolean);
};

/**
 * Creates an array of unique values that are included in all given arrays.
 */
_.intersection = function(...arrays) {
    if (arrays.length === 0) return [];
    
    const first = arrays[0];
    return first.filter(item => 
        arrays.every(arr => arr.includes(item))
    );
};

/**
 * Creates an array of unique values from all given arrays.
 */
_.union = function(...arrays) {
    return [...new Set(arrays.flat())];
};

/**
 * Creates a duplicate-free version of an array.
 */
_.uniq = function(array) {
    if (!Array.isArray(array)) {
        return [];
    }
    return [...new Set(array)];
};

/**
 * Creates an array excluding all given values.
 */
_.without = function(array, ...values) {
    if (!Array.isArray(array)) {
        return [];
    }
    return array.filter(item => !values.includes(item));
};

/**
 * Gets the first element of array.
 */
_.first = function(array) {
    return array ? array[0] : undefined;
};

/**
 * Gets the last element of array.
 */
_.last = function(array) {
    return array ? array[array.length - 1] : undefined;
};

/**
 * Flattens array a single level deep.
 */
_.flatten = function(array) {
    if (!Array.isArray(array)) {
        return [];
    }
    return array.flat();
};

/**
 * Recursively flattens array.
 */
_.flattenDeep = function(array) {
    if (!Array.isArray(array)) {
        return [];
    }
    return array.flat(Infinity);
};

/**
 * Gets the element at index n of array.
 */
_.nth = function(array, n = 0) {
    if (!array) return undefined;
    return n < 0 ? array[array.length + n] : array[n];
};

// ============================================================================
// COLLECTION FUNCTIONS
// ============================================================================

/**
 * Creates an array of values by running each element in collection through iteratee.
 */
_.map = function(collection, iteratee) {
    if (Array.isArray(collection)) {
        return collection.map(typeof iteratee === 'string' ? 
            item => item[iteratee] : iteratee);
    }
    if (typeof collection === 'object' && collection !== null) {
        return Object.values(collection).map(typeof iteratee === 'string' ? 
            item => item[iteratee] : iteratee);
    }
    return [];
};

/**
 * Iterates over elements of collection, returning an array of all elements predicate returns truthy for.
 */
_.filter = function(collection, predicate) {
    if (Array.isArray(collection)) {
        return collection.filter(predicate);
    }
    if (typeof collection === 'object' && collection !== null) {
        return Object.values(collection).filter(predicate);
    }
    return [];
};

/**
 * Checks if predicate returns truthy for any element of collection.
 */
_.some = function(collection, predicate) {
    if (Array.isArray(collection)) {
        return collection.some(predicate);
    }
    if (typeof collection === 'object' && collection !== null) {
        return Object.values(collection).some(predicate);
    }
    return false;
};

/**
 * Checks if predicate returns truthy for all elements of collection.
 */
_.every = function(collection, predicate) {
    if (Array.isArray(collection)) {
        return collection.every(predicate);
    }
    if (typeof collection === 'object' && collection !== null) {
        return Object.values(collection).every(predicate);
    }
    return true;
};

/**
 * Reduces collection to a value which is the accumulated result of running each element through iteratee.
 */
_.reduce = function(collection, iteratee, accumulator) {
    if (Array.isArray(collection)) {
        return arguments.length > 2 ? 
            collection.reduce(iteratee, accumulator) : 
            collection.reduce(iteratee);
    }
    if (typeof collection === 'object' && collection !== null) {
        const values = Object.values(collection);
        return arguments.length > 2 ? 
            values.reduce(iteratee, accumulator) : 
            values.reduce(iteratee);
    }
    return accumulator;
};

/**
 * Gets the size of collection.
 */
_.size = function(collection) {
    if (Array.isArray(collection) || typeof collection === 'string') {
        return collection.length;
    }
    if (typeof collection === 'object' && collection !== null) {
        return Object.keys(collection).length;
    }
    return 0;
};

/**
 * Creates an array of elements, sorted in ascending order by the results of running each element through iteratee.
 */
_.sortBy = function(collection, iteratee) {
    if (!Array.isArray(collection)) {
        return [];
    }
    
    const getKey = typeof iteratee === 'string' ? 
        item => item[iteratee] : 
        iteratee;
    
    return [...collection].sort((a, b) => {
        const aVal = getKey(a);
        const bVal = getKey(b);
        if (aVal < bVal) return -1;
        if (aVal > bVal) return 1;
        return 0;
    });
};

/**
 * Creates an object composed of keys generated from the results of running each element through iteratee.
 */
_.groupBy = function(collection, iteratee) {
    if (!Array.isArray(collection)) {
        return {};
    }
    
    const getKey = typeof iteratee === 'string' ? 
        item => item[iteratee] : 
        iteratee;
    
    return collection.reduce((result, item) => {
        const key = getKey(item);
        if (!result[key]) {
            result[key] = [];
        }
        result[key].push(item);
        return result;
    }, {});
};

// ============================================================================
// OBJECT FUNCTIONS
// ============================================================================

/**
 * Assigns own enumerable string keyed properties of source objects to the destination object.
 */
_.assign = function(target, ...sources) {
    return Object.assign(target || {}, ...sources);
};

/**
 * Creates an object with the same keys as object and values generated by running each property through iteratee.
 */
_.mapValues = function(obj, iteratee) {
    if (typeof obj !== 'object' || obj === null) {
        return {};
    }
    
    const result = {};
    for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
            result[key] = typeof iteratee === 'function' ? 
                iteratee(obj[key], key, obj) : 
                obj[key][iteratee];
        }
    }
    return result;
};

/**
 * Creates an array of the own enumerable property names of object.
 */
_.keys = function(obj) {
    return obj ? Object.keys(obj) : [];
};

/**
 * Creates an array of the own enumerable property values of object.
 */
_.values = function(obj) {
    return obj ? Object.values(obj) : [];
};

/**
 * Creates an object composed of the picked object properties.
 */
_.pick = function(obj, ...keys) {
    if (typeof obj !== 'object' || obj === null) {
        return {};
    }
    
    const flatKeys = keys.flat();
    const result = {};
    flatKeys.forEach(key => {
        if (key in obj) {
            result[key] = obj[key];
        }
    });
    return result;
};

/**
 * The opposite of _.pick; this method creates an object composed of the own and inherited enumerable property paths of object that are not omitted.
 */
_.omit = function(obj, ...keys) {
    if (typeof obj !== 'object' || obj === null) {
        return {};
    }
    
    const flatKeys = keys.flat();
    const result = {};
    for (const key in obj) {
        if (obj.hasOwnProperty(key) && !flatKeys.includes(key)) {
            result[key] = obj[key];
        }
    }
    return result;
};

/**
 * Gets the value at path of object.
 */
_.get = function(obj, path, defaultValue) {
    if (typeof obj !== 'object' || obj === null) {
        return defaultValue;
    }
    
    const keys = Array.isArray(path) ? path : path.split('.');
    let result = obj;
    
    for (const key of keys) {
        if (result == null) {
            return defaultValue;
        }
        result = result[key];
    }
    
    return result !== undefined ? result : defaultValue;
};

/**
 * Sets the value at path of object.
 */
_.set = function(obj, path, value) {
    if (typeof obj !== 'object' || obj === null) {
        return obj;
    }
    
    const keys = Array.isArray(path) ? path : path.split('.');
    let current = obj;
    
    for (let i = 0; i < keys.length - 1; i++) {
        const key = keys[i];
        if (!(key in current) || typeof current[key] !== 'object') {
            current[key] = {};
        }
        current = current[key];
    }
    
    current[keys[keys.length - 1]] = value;
    return obj;
};

/**
 * Checks if path is a direct property of object.
 */
_.has = function(obj, path) {
    if (typeof obj !== 'object' || obj === null) {
        return false;
    }
    
    const keys = Array.isArray(path) ? path : path.split('.');
    let current = obj;
    
    for (const key of keys) {
        if (!current.hasOwnProperty(key)) {
            return false;
        }
        current = current[key];
    }
    
    return true;
};

// ============================================================================
// STRING FUNCTIONS
// ============================================================================

/**
 * Converts string to camelCase.
 */
_.camelCase = function(str) {
    if (typeof str !== 'string') return '';
    
    return str
        .replace(/[^a-zA-Z0-9]+(.)/g, (_, chr) => chr.toUpperCase())
        .replace(/^[A-Z]/, chr => chr.toLowerCase());
};

/**
 * Converts string to kebab-case.
 */
_.kebabCase = function(str) {
    if (typeof str !== 'string') return '';
    
    return str
        .replace(/([a-z])([A-Z])/g, '$1-$2')
        .replace(/[\s_]+/g, '-')
        .toLowerCase();
};

/**
 * Converts string to snake_case.
 */
_.snakeCase = function(str) {
    if (typeof str !== 'string') return '';
    
    return str
        .replace(/([a-z])([A-Z])/g, '$1_$2')
        .replace(/[\s-]+/g, '_')
        .toLowerCase();
};

/**
 * Converts the first character of string to upper case and the remaining to lower case.
 */
_.capitalize = function(str) {
    if (typeof str !== 'string') return '';
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

/**
 * Converts the first character of string to upper case.
 */
_.upperFirst = function(str) {
    if (typeof str !== 'string') return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
};

/**
 * Pads string on the left and right sides if it's shorter than length.
 */
_.pad = function(str, length, chars = ' ') {
    if (typeof str !== 'string') str = String(str);
    if (str.length >= length) return str;
    
    const padLength = length - str.length;
    const leftPad = Math.floor(padLength / 2);
    const rightPad = padLength - leftPad;
    
    return chars.repeat(leftPad) + str + chars.repeat(rightPad);
};

/**
 * Repeats the given string n times.
 */
_.repeat = function(str, n = 1) {
    if (typeof str !== 'string') return '';
    return str.repeat(n);
};

/**
 * Converts string, as space separated words, to lower case.
 */
_.lowerCase = function(str) {
    if (typeof str !== 'string') return '';
    return str
        .replace(/([a-z])([A-Z])/g, '$1 $2')
        .replace(/[_-]/g, ' ')
        .toLowerCase();
};

// ============================================================================
// FUNCTION UTILITIES
// ============================================================================

/**
 * Creates a debounced function that delays invoking func until after wait milliseconds.
 */
_.debounce = function(func, wait = 0) {
    let timeoutId;
    
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), wait);
    };
};

/**
 * Creates a throttled function that only invokes func at most once per every wait milliseconds.
 */
_.throttle = function(func, wait = 0) {
    let lastRun = 0;
    let timeoutId;
    
    return function(...args) {
        const now = Date.now();
        const remaining = wait - (now - lastRun);
        
        if (remaining <= 0) {
            clearTimeout(timeoutId);
            lastRun = now;
            func.apply(this, args);
        } else if (!timeoutId) {
            timeoutId = setTimeout(() => {
                lastRun = Date.now();
                timeoutId = null;
                func.apply(this, args);
            }, remaining);
        }
    };
};

/**
 * Creates a function that is restricted to invoking func once.
 */
_.once = function(func) {
    let called = false;
    let result;
    
    return function(...args) {
        if (!called) {
            called = true;
            result = func.apply(this, args);
        }
        return result;
    };
};

/**
 * Creates a function that invokes func with arguments arranged according to the specified indexes.
 */
_.partial = function(func, ...partialArgs) {
    return function(...args) {
        return func.apply(this, [...partialArgs, ...args]);
    };
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Creates a deep clone of value.
 */
_.cloneDeep = function(value) {
    if (value === null || typeof value !== 'object') {
        return value;
    }
    
    if (Array.isArray(value)) {
        return value.map(item => _.cloneDeep(item));
    }
    
    const cloned = {};
    for (const key in value) {
        if (value.hasOwnProperty(key)) {
            cloned[key] = _.cloneDeep(value[key]);
        }
    }
    return cloned;
};

/**
 * Performs a deep comparison between two values.
 */
_.isEqual = function(a, b) {
    if (a === b) return true;
    
    if (a == null || b == null) return false;
    
    if (typeof a !== typeof b) return false;
    
    if (typeof a !== 'object') return a === b;
    
    if (Array.isArray(a) !== Array.isArray(b)) return false;
    
    if (Array.isArray(a)) {
        if (a.length !== b.length) return false;
        return a.every((item, index) => _.isEqual(item, b[index]));
    }
    
    const keysA = Object.keys(a);
    const keysB = Object.keys(b);
    
    if (keysA.length !== keysB.length) return false;
    
    return keysA.every(key => _.isEqual(a[key], b[key]));
};

/**
 * Generates a unique ID.
 */
_.uniqueId = (function() {
    let idCounter = 0;
    return function(prefix = '') {
        return prefix + (++idCounter);
    };
})();

/**
 * Returns a random integer between min and max.
 */
_.random = function(min = 0, max = 1) {
    if (arguments.length === 1) {
        max = min;
        min = 0;
    }
    return Math.floor(Math.random() * (max - min + 1)) + min;
};

// ============================================================================
// TYPE CHECKING
// ============================================================================

_.isArray = Array.isArray;

_.isObject = function(value) {
    return value !== null && typeof value === 'object' && !Array.isArray(value);
};

_.isString = function(value) {
    return typeof value === 'string';
};

_.isNumber = function(value) {
    return typeof value === 'number' && !isNaN(value);
};

_.isFunction = function(value) {
    return typeof value === 'function';
};

_.isBoolean = function(value) {
    return typeof value === 'boolean';
};

_.isNull = function(value) {
    return value === null;
};

_.isUndefined = function(value) {
    return value === undefined;
};

_.isNil = function(value) {
    return value == null;
};

_.isEmpty = function(value) {
    if (value == null) return true;
    if (Array.isArray(value) || typeof value === 'string') return value.length === 0;
    if (typeof value === 'object') return Object.keys(value).length === 0;
    return false;
};

module.exports = _;
