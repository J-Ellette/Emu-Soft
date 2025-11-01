# ESLint Emulator - JavaScript Linting Tool

**Developed by PowerShield, as an alternative to ESLint**


This module emulates **ESLint**, a pluggable linting utility for JavaScript and JSX. ESLint is designed to be completely pluggable and configurable, allowing developers to enforce coding standards and catch common errors.

## What is ESLint?

ESLint is a tool for identifying and reporting on patterns found in ECMAScript/JavaScript code, with the goal of making code more consistent and avoiding bugs. It is designed to be:
- Completely pluggable
- Highly configurable
- Rule-based analysis
- Support for custom rules
- Auto-fixing capabilities
- Wide ecosystem support

## Features

This emulator implements core ESLint functionality:

### Rule System
- **Built-in Rules**: Common JavaScript linting rules
- **Rule Configuration**: Enable, disable, and configure rules
- **Severity Levels**: Error (2) and warning (1) severities
- **Custom Rules**: Register and use custom rules
- **Rule Options**: Configure rules with options

### Built-in Rules
- **no-console**: Disallow console statements
- **no-unused-vars**: Disallow unused variables
- **semi**: Require or disallow semicolons
- **quotes**: Enforce consistent quote style
- **no-var**: Require let/const instead of var
- **eqeqeq**: Require === and !==
- **indent**: Enforce consistent indentation

### Configuration
- **Rule Enablement**: Enable/disable rules individually
- **Severity Control**: Set error or warning level
- **Rule Options**: Pass options to rules
- **Multiple Formats**: Support various config formats

### Linting
- **Text Linting**: Lint code strings directly
- **File Linting**: Lint files (simulated)
- **Error Reporting**: Detailed error messages with location
- **Fix Information**: Auto-fix suggestions
- **Statistics**: Error and warning counts

## Usage Examples

### Basic Usage

```javascript
const { ESLint } = require('./eslint_emulator');

const eslint = new ESLint({
    rules: {
        'semi': 'error',
        'quotes': ['error', 'single']
    }
});

const code = `const x = "hello"`;
const results = eslint.lintText(code);

console.log('Errors:', results[0].errorCount);
console.log('Warnings:', results[0].warningCount);
console.log('Messages:', results[0].messages);
```

### Rule Configuration

```javascript
const { ESLint } = require('./eslint_emulator');

// Simple configuration
const eslint = new ESLint({
    rules: {
        'semi': 'error',              // Enable as error
        'no-console': 'warn',          // Enable as warning
        'no-debugger': 'off'           // Disable
    }
});

// With options
const eslintWithOptions = new ESLint({
    rules: {
        'quotes': ['error', 'single'],     // Single quotes
        'indent': ['error', 4],            // 4 spaces
        'semi': ['error', 'always']        // Always require semicolons
    }
});
```

### Numeric Severity

```javascript
const { ESLint } = require('./eslint_emulator');

const eslint = new ESLint({
    rules: {
        'semi': 2,              // 2 = error
        'no-console': 1,        // 1 = warning
        'no-debugger': 0        // 0 = off
    }
});
```

### no-console Rule

```javascript
const { ESLint } = require('./eslint_emulator');

const eslint = new ESLint({
    rules: {
        'no-console': 'warn'
    }
});

const code = `
console.log('debugging');
console.error('error message');
`;

const results = eslint.lintText(code);
// Detects both console statements
```

### no-unused-vars Rule

```javascript
const { ESLint } = require('./eslint_emulator');

const eslint = new ESLint({
    rules: {
        'no-unused-vars': 'error'
    }
});

const code = `
const unused = 5;
const used = 10;
console.log(used);
`;

const results = eslint.lintText(code);
// Detects 'unused' variable
```

### semi Rule

```javascript
const { ESLint } = require('./eslint_emulator');

// Require semicolons
const eslintAlways = new ESLint({
    rules: {
        'semi': ['error', 'always']
    }
});

const code1 = `const x = 5`;  // Missing semicolon
const results1 = eslintAlways.lintText(code1);
// Error: Missing semicolon

// Disallow semicolons
const eslintNever = new ESLint({
    rules: {
        'semi': ['error', 'never']
    }
});

const code2 = `const x = 5;`;  // Has semicolon
const results2 = eslintNever.lintText(code2);
// Error: Extra semicolon
```

### quotes Rule

```javascript
const { ESLint } = require('./eslint_emulator');

// Enforce single quotes
const eslint = new ESLint({
    rules: {
        'quotes': ['error', 'single']
    }
});

const code = `const str = "hello";`;  // Double quotes
const results = eslint.lintText(code);
// Error: Should use single quotes

// Enforce double quotes
const eslintDouble = new ESLint({
    rules: {
        'quotes': ['error', 'double']
    }
});

const code2 = `const str = 'hello';`;  // Single quotes
const results2 = eslintDouble.lintText(code2);
// Error: Should use double quotes
```

### no-var Rule

```javascript
const { ESLint } = require('./eslint_emulator');

const eslint = new ESLint({
    rules: {
        'no-var': 'error'
    }
});

const code = `var x = 5;`;  // Using var
const results = eslint.lintText(code);
// Error: Use let or const instead
```

### eqeqeq Rule

```javascript
const { ESLint } = require('./eslint_emulator');

const eslint = new ESLint({
    rules: {
        'eqeqeq': 'error'
    }
});

const code = `
if (x == 5) { }   // Loose equality
if (y != 10) { }  // Loose inequality
`;

const results = eslint.lintText(code);
// Errors: Use === and !== instead
```

### indent Rule

```javascript
const { ESLint } = require('./eslint_emulator');

// Require 4 spaces
const eslint = new ESLint({
    rules: {
        'indent': ['error', 4]
    }
});

const code = `
function test() {
  return 5;  // Only 2 spaces
}
`;

const results = eslint.lintText(code);
// Error: Expected 4 spaces
```

### Multiple Rules

```javascript
const { ESLint } = require('./eslint_emulator');

const eslint = new ESLint({
    rules: {
        'semi': 'error',
        'quotes': ['error', 'single'],
        'no-var': 'error',
        'no-console': 'warn',
        'eqeqeq': 'error'
    }
});

const code = `
var x = "hello"
console.log(x == 5)
`;

const results = eslint.lintText(code);
// Multiple errors:
// - Missing semicolon
// - Wrong quote style
// - Using var
// - Using loose equality
// - Console statement (warning)
```

### Processing Results

```javascript
const { ESLint } = require('./eslint_emulator');

const eslint = new ESLint({
    rules: {
        'semi': 'error',
        'no-console': 'warn'
    }
});

const code = `
const x = 5
console.log(x);
`;

const results = eslint.lintText(code, { filename: 'app.js' });

results.forEach(result => {
    console.log('File:', result.filePath);
    console.log('Errors:', result.errorCount);
    console.log('Warnings:', result.warningCount);
    console.log('Fixable errors:', result.fixableErrorCount);
    console.log('Fixable warnings:', result.fixableWarningCount);
    
    result.messages.forEach(msg => {
        const severity = msg.severity === 2 ? 'Error' : 'Warning';
        console.log(`${severity} [${msg.ruleId}]: ${msg.message}`);
        console.log(`  at line ${msg.line}, column ${msg.column}`);
        
        if (msg.fix) {
            console.log('  Fix available:', msg.fix);
        }
    });
});
```

### CLIEngine API

```javascript
const { CLIEngine } = require('./eslint_emulator');

const cli = new CLIEngine({
    baseConfig: {
        rules: {
            'semi': 'error',
            'quotes': ['error', 'single']
        }
    }
});

const report = cli.executeOnText(`const x = "hello"`);

console.log('Total errors:', report.errorCount);
console.log('Total warnings:', report.warningCount);
console.log('Results:', report.results);
```

### Custom Rules

```javascript
const { ESLint, Rule } = require('./eslint_emulator');

// Define custom rule
class NoTodoRule extends Rule {
    constructor(config) {
        super(config);
        this.meta = {
            type: 'suggestion',
            docs: { description: 'Disallow TODO comments' }
        };
    }
    
    create(context) {
        const code = context.getSourceCode().getText();
        const lines = code.split('\n');
        
        lines.forEach((line, index) => {
            if (line.includes('TODO')) {
                context.report({
                    ruleId: 'no-todos',
                    message: 'TODO comments should be resolved',
                    severity: this.config.severity || 1,
                    line: index + 1,
                    column: line.indexOf('TODO')
                });
            }
        });
    }
}

// Register and use custom rule
const eslint = new ESLint({
    rules: {
        'no-todos': 'warn'
    }
});

eslint.registerRule('no-todos', NoTodoRule);

const code = `
// TODO: Fix this later
const x = 5;
`;

const results = eslint.lintText(code);
// Warning: TODO comments should be resolved
```

### RuleContext API

```javascript
const { RuleContext } = require('./eslint_emulator');

// Create context for rule development
const context = new RuleContext('const x = 5;', 'test.js');

// Get source code
const sourceCode = context.getSourceCode();
console.log(sourceCode.getText());        // 'const x = 5;'
console.log(sourceCode.getLines());       // ['const x = 5;']
console.log(sourceCode.getAllComments()); // []

// Report issues
context.report({
    ruleId: 'custom-rule',
    message: 'Custom issue found',
    severity: 2,
    line: 1,
    column: 0
});
```

### Disabling Rules

```javascript
const { ESLint } = require('./eslint_emulator');

const eslint = new ESLint({
    rules: {
        'no-console': 'off',        // String 'off'
        'semi': 0,                  // Numeric 0
        'quotes': ['off', 'single'] // Array with 'off'
    }
});

const code = `console.log("hello")`;
const results = eslint.lintText(code);
// No errors - all rules are disabled
```

### Checking Fix Availability

```javascript
const { ESLint } = require('./eslint_emulator');

const eslint = new ESLint({
    rules: {
        'semi': 'error',     // Fixable
        'no-var': 'error'    // Not fixable in this emulator
    }
});

const code = `var x = 5`;

const results = eslint.lintText(code);
const result = results[0];

console.log('Fixable errors:', result.fixableErrorCount);
console.log('Non-fixable errors:', result.errorCount - result.fixableErrorCount);

result.messages.forEach(msg => {
    if (msg.fix) {
        console.log(`${msg.ruleId} can be auto-fixed`);
    }
});
```

## Testing

Run the comprehensive test suite:

```bash
node test_eslint_emulator.js
```

Tests cover:
- Basic ESLint instantiation
- All built-in rules (no-console, no-unused-vars, semi, quotes, no-var, eqeqeq, indent)
- Rule configuration (string, numeric, array formats)
- Severity levels (error, warning, off)
- Message structure and properties
- RuleContext functionality
- CLIEngine API
- Custom rule registration
- Result structure and statistics
- Fixable message detection
- Comment extraction
- Empty code handling

Total: 63 tests

## Integration with Existing Code

This emulator is designed to be a learning tool and testing replacement for ESLint:

```javascript
// Instead of:
// const { ESLint } = require('eslint');

// Use:
const { ESLint } = require('./eslint_emulator');

// Most basic ESLint usage will work
const eslint = new ESLint({
    rules: {
        'semi': 'error',
        'quotes': ['error', 'single']
    }
});

const results = eslint.lintText(code);
```

## Use Cases

Perfect for:
- **Learning**: Understand how linters work
- **Testing**: Test code quality without real ESLint
- **Prototyping**: Quickly prototype linting rules
- **Education**: Teach code quality concepts
- **Rule Development**: Develop custom rules in isolation
- **CI/CD**: Test linting configurations

## Limitations

This is an emulator for learning and testing purposes:
- Simplified AST parsing (pattern matching instead)
- No real JavaScript parsing
- No plugin system integration
- No extends/overrides support
- Limited number of built-in rules
- Simplified fix generation
- No source map support
- No caching
- No parallel processing
- No file watching

## Supported Features

### Core Features
- ✅ ESLint class
- ✅ CLIEngine class
- ✅ Text linting
- ✅ Rule configuration
- ✅ Severity levels (error, warning, off)
- ✅ Custom rules

### Built-in Rules
- ✅ no-console
- ✅ no-unused-vars
- ✅ semi
- ✅ quotes
- ✅ no-var
- ✅ eqeqeq
- ✅ indent

### Configuration
- ✅ Rule enablement
- ✅ Severity configuration
- ✅ Rule options
- ✅ String format ('error', 'warn', 'off')
- ✅ Numeric format (0, 1, 2)
- ✅ Array format (['error', ...options])

### Results
- ✅ Error/warning counts
- ✅ Message details (line, column, severity)
- ✅ File path tracking
- ✅ Fix information
- ✅ Source code preservation

## Real-World Linting Concepts

This emulator teaches the following concepts:

1. **Static Analysis**: Analyzing code without execution
2. **Rule-Based Checking**: Defining and applying rules
3. **Pattern Matching**: Finding code patterns
4. **Severity Levels**: Differentiating errors and warnings
5. **Auto-Fixing**: Suggesting code corrections
6. **Configuration**: Customizing linter behavior
7. **Custom Rules**: Extending linter functionality
8. **Code Quality**: Maintaining consistent code standards
9. **Error Reporting**: Providing actionable feedback
10. **Plugin Architecture**: Extensible design patterns

## Compatibility

Emulates core features of:
- ESLint 7.x and 8.x API patterns
- CLIEngine API (pre-8.0)
- Common rule conventions
- Standard configuration formats

## License

Part of the Emu-Soft project. See main repository LICENSE.
