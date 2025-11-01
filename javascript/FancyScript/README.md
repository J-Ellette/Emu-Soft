# Prettier Emulator - Code Formatter for JavaScript

**Developed by PowerShield, as an alternative to Prettier**


This module emulates the **Prettier** code formatter, which is an opinionated code formatter that supports many languages and integrates with most editors. Prettier removes all original styling and ensures that all outputted code conforms to a consistent style.

## What is Prettier?

Prettier is an opinionated code formatter created by James Long. It is designed to:
- Enforce a consistent code style across your entire codebase
- Save time and energy by eliminating debates about code formatting
- Support multiple languages (JavaScript, TypeScript, CSS, HTML, JSON, and more)
- Integrate seamlessly with editors and version control systems
- Format code automatically on save or commit

## Features

This emulator implements core Prettier functionality:

### Supported Languages
- **JavaScript/TypeScript**: Full ES6+ syntax support
- **JSON**: Format and validate JSON files
- **HTML**: Format HTML documents
- **CSS/SCSS/Less**: Format stylesheets

### Formatting Options
- **printWidth**: Line length before wrapping
- **tabWidth**: Spaces per indentation level
- **useTabs**: Use tabs instead of spaces
- **semi**: Add semicolons at end of statements
- **singleQuote**: Use single quotes instead of double
- **quoteProps**: Quote object properties as needed
- **trailingComma**: Add trailing commas where valid
- **bracketSpacing**: Add spaces inside object literals
- **arrowParens**: Include parentheses around arrow function parameters
- **endOfLine**: Line ending style (LF, CRLF, CR)

### API Methods
- **format()**: Format code with options
- **check()**: Check if code is already formatted
- **formatWithCursor()**: Format while preserving cursor position
- **getFileInfo()**: Get file parser information
- **resolveConfig()**: Resolve Prettier configuration
- **detectParser()**: Automatically detect parser from code

## Usage Examples

### Basic Formatting

```javascript
const prettier = require('./prettier_emulator');

const code = 'const x=5';
const formatted = prettier.format(code);
console.log(formatted);
// Output:
// const x = 5;
```

### Format with Options

```javascript
const prettier = require('./prettier_emulator');

const code = 'const name="John"';

// Use single quotes
const formatted = prettier.format(code, {
    singleQuote: true
});
console.log(formatted);
// Output:
// const name = 'John';
```

### Semicolon Options

```javascript
const prettier = require('./prettier_emulator');

const code = 'const x = 5';

// With semicolons (default)
const withSemi = prettier.format(code, { semi: true });
console.log(withSemi);
// Output: const x = 5;

// Without semicolons
const withoutSemi = prettier.format(code, { semi: false });
console.log(withoutSemi);
// Output: const x = 5
```

### Indentation Options

```javascript
const prettier = require('./prettier_emulator');

const code = 'function test() { return 1 }';

// 2 spaces (default)
const twoSpaces = prettier.format(code, { tabWidth: 2 });

// 4 spaces
const fourSpaces = prettier.format(code, { tabWidth: 4 });

// Tabs instead of spaces
const withTabs = prettier.format(code, { useTabs: true });
```

### Format JSON

```javascript
const prettier = require('./prettier_emulator');

const code = '{"name":"John","age":30,"city":"New York"}';

const formatted = prettier.format(code, { parser: 'json' });
console.log(formatted);
// Output:
// {
//   "name": "John",
//   "age": 30,
//   "city": "New York"
// }
```

### Format HTML

```javascript
const prettier = require('./prettier_emulator');

const code = '<div><h1>Title</h1><p>Paragraph</p></div>';

const formatted = prettier.format(code, { parser: 'html' });
console.log(formatted);
// Output:
// <div>
//   <h1>Title</h1>
//   <p>Paragraph</p>
// </div>
```

### Format CSS

```javascript
const prettier = require('./prettier_emulator');

const code = 'body{margin:0;padding:0}h1{color:blue}';

const formatted = prettier.format(code, { parser: 'css' });
console.log(formatted);
// Output:
// body {
//   margin: 0;
//   padding: 0;
// }
// h1 {
//   color: blue;
// }
```

### Check if Code is Formatted

```javascript
const prettier = require('./prettier_emulator');

const formattedCode = 'const x = 5;\n';
const unformattedCode = 'const x=5';

console.log(prettier.check(formattedCode));   // true
console.log(prettier.check(unformattedCode)); // false
```

### Auto-detect Parser

```javascript
const prettier = require('./prettier_emulator');

// JavaScript code
const jsCode = 'const x = 5';
const jsFormatted = prettier.format(jsCode);

// JSON code (auto-detected)
const jsonCode = '{"key": "value"}';
const jsonFormatted = prettier.format(jsonCode);

// HTML code (auto-detected)
const htmlCode = '<!DOCTYPE html><html></html>';
const htmlFormatted = prettier.format(htmlCode);
```

### Get File Info

```javascript
const prettier = require('./prettier_emulator');

const jsInfo = prettier.getFileInfo('app.js');
console.log(jsInfo);
// { ignored: false, inferredParser: 'babel' }

const jsonInfo = prettier.getFileInfo('package.json');
console.log(jsonInfo);
// { ignored: false, inferredParser: 'json' }

const htmlInfo = prettier.getFileInfo('index.html');
console.log(htmlInfo);
// { ignored: false, inferredParser: 'html' }
```

### Format with Cursor Position

```javascript
const prettier = require('./prettier_emulator');

const code = 'const x=5';
const result = prettier.formatWithCursor(code, {
    cursorOffset: 5
});

console.log(result.formatted);   // const x = 5;
console.log(result.cursorOffset); // Updated cursor position
```

### Real-World Example: Format Function

```javascript
const prettier = require('./prettier_emulator');

const code = `
function calculateTotal(items){
const subtotal=items.reduce((sum,item)=>sum+item.price,0)
const tax=subtotal*0.08
return subtotal+tax
}
`;

const formatted = prettier.format(code, {
    semi: true,
    singleQuote: true,
    tabWidth: 2
});

console.log(formatted);
// Output:
// function calculateTotal(items) {
//   const subtotal = items.reduce((sum, item) => sum + item.price, 0);
//   const tax = subtotal * 0.08;
//   return subtotal + tax;
// }
```

### Real-World Example: Format React Component

```javascript
const prettier = require('./prettier_emulator');

const code = `
function UserProfile({user}){
return <div><h1>{user.name}</h1><p>{user.email}</p></div>
}
`;

const formatted = prettier.format(code, {
    semi: true,
    jsxSingleQuote: false
});

console.log(formatted);
```

### Real-World Example: Format Object Literal

```javascript
const prettier = require('./prettier_emulator');

const code = `const config={api:{url:"https://api.example.com",timeout:5000},features:{darkMode:true,notifications:false}}`;

const formatted = prettier.format(code, {
    semi: true,
    singleQuote: true,
    bracketSpacing: true
});

console.log(formatted);
// Output:
// const config = {
//   api: { url: 'https://api.example.com', timeout: 5000 },
//   features: { darkMode: true, notifications: false }
// };
```

### Real-World Example: Format Array

```javascript
const prettier = require('./prettier_emulator');

const code = `const colors=['red','green','blue','yellow','purple','orange']`;

const formatted = prettier.format(code, {
    singleQuote: true,
    trailingComma: 'es5'
});

console.log(formatted);
```

### Real-World Example: Format Import Statements

```javascript
const prettier = require('./prettier_emulator');

const code = `import {Component,useState,useEffect} from "react"`;

const formatted = prettier.format(code, {
    singleQuote: true
});

console.log(formatted);
// Output:
// import { Component, useState, useEffect } from 'react';
```

### Real-World Example: Format Class

```javascript
const prettier = require('./prettier_emulator');

const code = `
class Calculator{
constructor(){this.result=0}
add(a,b){return a+b}
multiply(a,b){return a*b}
}
`;

const formatted = prettier.format(code);
console.log(formatted);
```

### Configuration Example

```javascript
const prettier = require('./prettier_emulator');

// Create a config object
const prettierConfig = {
    printWidth: 80,
    tabWidth: 2,
    useTabs: false,
    semi: true,
    singleQuote: true,
    quoteProps: 'as-needed',
    trailingComma: 'es5',
    bracketSpacing: true,
    arrowParens: 'always'
};

// Use config for all formatting
const code1 = 'const x=5';
const code2 = 'function test(){return 1}';

const formatted1 = prettier.format(code1, prettierConfig);
const formatted2 = prettier.format(code2, prettierConfig);
```

## Testing

Run the comprehensive test suite:

```bash
node test_prettier_emulator.js
```

Tests cover:
- JavaScript formatting (7 tests)
- Indentation (2 tests)
- JSON formatting (4 tests)
- HTML formatting (3 tests)
- CSS formatting (2 tests)
- Parser detection (4 tests)
- Check function (2 tests)
- getFileInfo (5 tests)
- formatWithCursor (1 test)
- Options (3 tests)
- Real-world examples (8 tests)

Total: 41 tests

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for Prettier in development and testing:

```javascript
// Instead of:
// const prettier = require('prettier');

// Use:
const prettier = require('./prettier_emulator');

// The rest of your code remains unchanged
const formatted = prettier.format(code, { semi: true });
```

## Use Cases

Perfect for:
- **Local Development**: Format code without npm dependencies
- **CI/CD**: Enforce code style in pipelines
- **Learning**: Understand code formatting principles
- **Education**: Teach consistent code style
- **Prototyping**: Quickly format code examples
- **Testing**: Test formatting rules

## Limitations

This is an emulator for development and testing purposes:
- Simplified tokenizer (not a full parser)
- Limited language support compared to real Prettier
- No plugin system
- No configuration file reading (.prettierrc)
- Simplified formatting rules
- No ignore file support (.prettierignore)
- No editor integrations
- Basic cursor tracking

## Supported Features

### Core Functions
- ✅ format(code, options)
- ✅ check(code, options)
- ✅ formatWithCursor(code, options)
- ✅ getFileInfo(filePath)
- ✅ resolveConfig(filePath) (simplified)
- ✅ detectParser(code)

### Languages
- ✅ JavaScript/ES6+
- ✅ TypeScript (basic)
- ✅ JSON
- ✅ HTML
- ✅ CSS/SCSS/Less

### Options
- ✅ printWidth
- ✅ tabWidth
- ✅ useTabs
- ✅ semi
- ✅ singleQuote
- ✅ quoteProps
- ✅ jsxSingleQuote
- ✅ trailingComma
- ✅ bracketSpacing
- ✅ bracketSameLine
- ✅ arrowParens
- ✅ endOfLine

### Features
- ✅ Automatic semicolon insertion
- ✅ Quote style conversion
- ✅ Indentation normalization
- ✅ Bracket spacing
- ✅ Operator spacing
- ✅ Comment preservation
- ✅ Parser auto-detection

## Real-World Code Formatting Concepts

This emulator teaches the following concepts:

1. **Consistent Style**: Enforcing uniform code appearance
2. **AST Transformation**: How formatters parse and rebuild code
3. **Tokenization**: Breaking code into meaningful pieces
4. **Whitespace Normalization**: Standardizing spaces and newlines
5. **Quote Consistency**: Managing string delimiters
6. **Indentation Rules**: Applying consistent indentation
7. **Line Length Management**: Wrapping long lines
8. **Syntax Preservation**: Maintaining code semantics while changing style

## Compatibility

Emulates core features of:
- Prettier 2.x+ API patterns
- Common formatting options
- Standard formatting behaviors

## License

Part of the Emu-Soft project. See main repository LICENSE.
