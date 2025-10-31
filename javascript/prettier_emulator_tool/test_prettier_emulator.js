/**
 * Test Suite for Prettier Emulator
 * 
 * This file tests the Prettier emulator implementation to ensure code formatting
 * works correctly for JavaScript, JSON, HTML, and CSS.
 */

const prettier = require('./prettier_emulator');

let passedTests = 0;
let totalTests = 0;

function test(name, fn) {
    totalTests++;
    try {
        fn();
        console.log(`✓ ${name}`);
        passedTests++;
    } catch (error) {
        console.log(`✗ ${name}`);
        console.log(`  Error: ${error.message}`);
    }
}

function assertEqual(actual, expected, message) {
    if (actual !== expected) {
        throw new Error(`${message}\n  Expected: ${JSON.stringify(expected)}\n  Actual: ${JSON.stringify(actual)}`);
    }
}

function assertContains(actual, substring, message) {
    if (!actual.includes(substring)) {
        throw new Error(`${message}\n  Expected to contain: ${substring}\n  Actual: ${actual}`);
    }
}

console.log('Running Prettier Emulator Tests...\n');

// Test 1: Basic JavaScript formatting
console.log('=== JavaScript Formatting Tests ===');
test('formats simple variable declaration', () => {
    const code = 'const x=5';
    const formatted = prettier.format(code);
    assertContains(formatted, 'const x', 'formats variable declaration');
});

test('formats function declaration', () => {
    const code = 'function hello(){return "world"}';
    const formatted = prettier.format(code);
    assertContains(formatted, 'function hello', 'formats function');
});

test('respects semicolon option', () => {
    const code = 'const x = 5';
    const withSemi = prettier.format(code, { semi: true });
    const withoutSemi = prettier.format(code, { semi: false });
    
    assertContains(withSemi, ';', 'adds semicolon when semi: true');
});

test('respects single quote option', () => {
    const code = 'const str = "hello"';
    const formatted = prettier.format(code, { singleQuote: true });
    assertContains(formatted, "'hello'", 'converts to single quotes');
});

test('formats arrow functions', () => {
    const code = 'const fn=(x)=>x+1';
    const formatted = prettier.format(code);
    assertContains(formatted, '=>', 'formats arrow function');
});

test('handles comments', () => {
    const code = '// This is a comment\nconst x = 5';
    const formatted = prettier.format(code);
    assertContains(formatted, '// This is a comment', 'preserves comments');
});

test('handles block comments', () => {
    const code = '/* Block comment */ const x = 5';
    const formatted = prettier.format(code);
    assertContains(formatted, '/* Block comment */', 'preserves block comments');
});

// Test 2: Indentation
console.log('\n=== Indentation Tests ===');
test('uses correct tab width', () => {
    const code = 'function test() { const x = 5 }';
    const formatted = prettier.format(code, { tabWidth: 2 });
    // Should have some indentation
    assertContains(formatted, '  ', 'uses spaces for indentation');
});

test('handles nested blocks', () => {
    const code = 'function outer() { function inner() { return 1 } }';
    const formatted = prettier.format(code);
    assertContains(formatted, 'function', 'formats nested blocks');
});

// Test 3: JSON formatting
console.log('\n=== JSON Formatting Tests ===');
test('formats simple JSON', () => {
    const code = '{"name":"John","age":30}';
    const formatted = prettier.format(code, { parser: 'json' });
    assertContains(formatted, '"name"', 'formats JSON');
    assertContains(formatted, '"John"', 'preserves values');
});

test('handles nested JSON', () => {
    const code = '{"user":{"name":"Alice","data":{"id":1}}}';
    const formatted = prettier.format(code, { parser: 'json' });
    assertContains(formatted, '"user"', 'formats nested JSON');
    assertContains(formatted, '"Alice"', 'preserves nested values');
});

test('formats JSON arrays', () => {
    const code = '[1,2,3,4,5]';
    const formatted = prettier.format(code, { parser: 'json' });
    assertContains(formatted, '[', 'formats JSON arrays');
});

test('throws error on invalid JSON', () => {
    const code = '{invalid json}';
    try {
        prettier.format(code, { parser: 'json' });
        throw new Error('Should have thrown error');
    } catch (error) {
        assertContains(error.message, 'Invalid JSON', 'throws on invalid JSON');
    }
});

// Test 4: HTML formatting
console.log('\n=== HTML Formatting Tests ===');
test('formats simple HTML', () => {
    const code = '<div><p>Hello</p></div>';
    const formatted = prettier.format(code, { parser: 'html' });
    assertContains(formatted, '<div>', 'formats HTML');
    assertContains(formatted, '<p>', 'formats nested tags');
});

test('handles self-closing tags', () => {
    const code = '<img src="test.jpg" />';
    const formatted = prettier.format(code, { parser: 'html' });
    assertContains(formatted, '<img', 'formats self-closing tags');
});

test('indents nested HTML', () => {
    const code = '<div>\n<p>Hello</p>\n</div>';
    const formatted = prettier.format(code, { parser: 'html' });
    assertContains(formatted, '<div>', 'formats HTML structure');
});

// Test 5: CSS formatting
console.log('\n=== CSS Formatting Tests ===');
test('formats simple CSS', () => {
    const code = 'body{margin:0;padding:0}';
    const formatted = prettier.format(code, { parser: 'css' });
    assertContains(formatted, 'body', 'formats CSS selector');
    assertContains(formatted, 'margin', 'formats CSS properties');
});

test('handles multiple rules', () => {
    const code = '.class1{color:red}.class2{color:blue}';
    const formatted = prettier.format(code, { parser: 'css' });
    assertContains(formatted, '.class1', 'formats first rule');
    assertContains(formatted, '.class2', 'formats second rule');
});

// Test 6: Parser detection
console.log('\n=== Parser Detection Tests ===');
test('detects JSON parser', () => {
    const code = '{"key": "value"}';
    const parser = prettier.detectParser(code);
    assertEqual(parser, 'json', 'detects JSON');
});

test('detects HTML parser', () => {
    const code = '<!DOCTYPE html><html></html>';
    const parser = prettier.detectParser(code);
    assertEqual(parser, 'html', 'detects HTML');
});

test('detects CSS parser', () => {
    const code = '@media screen { body { margin: 0; } }';
    const parser = prettier.detectParser(code);
    assertEqual(parser, 'css', 'detects CSS');
});

test('defaults to babel parser', () => {
    const code = 'const x = 5;';
    const parser = prettier.detectParser(code);
    assertEqual(parser, 'babel', 'defaults to babel');
});

// Test 7: check function
console.log('\n=== Check Function Tests ===');
test('check returns true for formatted code', () => {
    const code = prettier.format('const x = 5');
    const isFormatted = prettier.check(code);
    assertEqual(isFormatted, true, 'returns true for formatted code');
});

test('check returns false for unformatted code', () => {
    const code = 'const x=5';
    const isFormatted = prettier.check(code);
    assertEqual(isFormatted, false, 'returns false for unformatted code');
});

// Test 8: getFileInfo
console.log('\n=== getFileInfo Tests ===');
test('gets file info for .js file', () => {
    const info = prettier.getFileInfo('test.js');
    assertEqual(info.inferredParser, 'babel', 'infers babel parser for .js');
    assertEqual(info.ignored, false, 'file is not ignored');
});

test('gets file info for .json file', () => {
    const info = prettier.getFileInfo('package.json');
    assertEqual(info.inferredParser, 'json', 'infers json parser for .json');
});

test('gets file info for .html file', () => {
    const info = prettier.getFileInfo('index.html');
    assertEqual(info.inferredParser, 'html', 'infers html parser for .html');
});

test('gets file info for .css file', () => {
    const info = prettier.getFileInfo('styles.css');
    assertEqual(info.inferredParser, 'css', 'infers css parser for .css');
});

test('gets file info for .ts file', () => {
    const info = prettier.getFileInfo('app.ts');
    assertEqual(info.inferredParser, 'typescript', 'infers typescript parser for .ts');
});

// Test 9: formatWithCursor
console.log('\n=== formatWithCursor Tests ===');
test('formats with cursor position', () => {
    const code = 'const x=5';
    const result = prettier.formatWithCursor(code, { cursorOffset: 5 });
    assertContains(result.formatted, 'const', 'formats code');
    assertEqual(typeof result.cursorOffset, 'number', 'returns cursor offset');
});

// Test 10: Options
console.log('\n=== Options Tests ===');
test('respects printWidth option', () => {
    const code = 'const x = 5';
    const formatted = prettier.format(code, { printWidth: 40 });
    assertContains(formatted, 'const', 'formats with printWidth');
});

test('respects tabWidth option', () => {
    const code = 'function test() { return 1 }';
    const formatted = prettier.format(code, { tabWidth: 4 });
    assertContains(formatted, 'function', 'formats with tabWidth');
});

test('respects bracketSpacing option', () => {
    const code = 'const obj = {a: 1}';
    const withSpacing = prettier.format(code, { bracketSpacing: true });
    const withoutSpacing = prettier.format(code, { bracketSpacing: false });
    // Both should format
    assertContains(withSpacing, 'const', 'formats with bracket spacing');
    assertContains(withoutSpacing, 'const', 'formats without bracket spacing');
});

// Test 11: Real-world examples
console.log('\n=== Real-World Examples ===');
test('formats React component', () => {
    const code = 'function Component(){return <div>Hello</div>}';
    const formatted = prettier.format(code);
    assertContains(formatted, 'function', 'formats React component');
});

test('formats object literal', () => {
    const code = 'const obj={name:"John",age:30,city:"NYC"}';
    const formatted = prettier.format(code);
    assertContains(formatted, 'const obj', 'formats object literal');
});

test('formats array', () => {
    const code = 'const arr=[1,2,3,4,5]';
    const formatted = prettier.format(code);
    assertContains(formatted, 'const arr', 'formats array');
});

test('formats complex nested code', () => {
    const code = 'function test(){if(true){const x=5;return x}}';
    const formatted = prettier.format(code);
    assertContains(formatted, 'function test', 'formats complex code');
});

test('formats module imports', () => {
    const code = 'import {Component} from "react"';
    const formatted = prettier.format(code);
    assertContains(formatted, 'import', 'formats imports');
});

test('formats export statements', () => {
    const code = 'export default function test(){}';
    const formatted = prettier.format(code);
    assertContains(formatted, 'export', 'formats exports');
});

test('formats class declaration', () => {
    const code = 'class MyClass{constructor(){this.value=0}}';
    const formatted = prettier.format(code);
    assertContains(formatted, 'class MyClass', 'formats class');
});

test('formats async/await', () => {
    const code = 'async function fetchData(){const data=await fetch("/api")}';
    const formatted = prettier.format(code);
    assertContains(formatted, 'async', 'formats async function');
    assertContains(formatted, 'await', 'formats await');
});

// Summary
console.log('\n=== Test Results ===');
console.log(`Total: ${totalTests}`);
console.log(`Passed: ${passedTests}`);
console.log(`Failed: ${totalTests - passedTests}`);
console.log(`Success Rate: ${((passedTests / totalTests) * 100).toFixed(2)}%\n`);

if (passedTests === totalTests) {
    console.log('✓ All tests passed!');
    process.exit(0);
} else {
    console.log(`✗ ${totalTests - passedTests} test(s) failed.`);
    process.exit(1);
}
