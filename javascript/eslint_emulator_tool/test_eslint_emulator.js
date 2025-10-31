/**
 * Test Suite for ESLint Emulator
 */

const { ESLint, CLIEngine, Rule, RuleContext, LintMessage } = require('./eslint_emulator');

// Test results tracker
let passed = 0;
let failed = 0;

function assert(condition, testName) {
    if (condition) {
        console.log(`✓ ${testName}`);
        passed++;
    } else {
        console.log(`✗ ${testName}`);
        failed++;
    }
}

function assertEquals(actual, expected, testName) {
    const condition = JSON.stringify(actual) === JSON.stringify(expected);
    assert(condition, testName);
    if (!condition) {
        console.log(`  Expected: ${JSON.stringify(expected)}`);
        console.log(`  Actual: ${JSON.stringify(actual)}`);
    }
}

console.log('Running ESLint Emulator Tests...\n');

// Test 1: Basic ESLint instantiation
console.log('Test Group: Basic Functionality');
const eslint1 = new ESLint({
    rules: {
        'semi': 'error',
        'quotes': ['error', 'single']
    }
});
assert(eslint1 instanceof ESLint, 'ESLint instance is created');
assert(eslint1.rules.size > 0, 'Built-in rules are registered');

// Test 2: Lint text with no issues
console.log('\nTest Group: Clean Code');
const eslint2 = new ESLint({
    rules: {
        'semi': 'error'
    }
});
const cleanCode = `const x = 5;`;
const results2 = eslint2.lintText(cleanCode);
assert(results2.length === 1, 'Returns one result');
assert(results2[0].errorCount === 0, 'No errors in clean code');
assert(results2[0].warningCount === 0, 'No warnings in clean code');

// Test 3: no-console rule
console.log('\nTest Group: no-console Rule');
const eslint3 = new ESLint({
    rules: {
        'no-console': 'warn'
    }
});
const codeWithConsole = `console.log('hello');`;
const results3 = eslint3.lintText(codeWithConsole);
assert(results3[0].warningCount === 1, 'Detects console.log');
assert(results3[0].messages[0].ruleId === 'no-console', 'Correct rule ID');
assert(results3[0].messages[0].message.includes('console'), 'Message mentions console');

// Test 4: no-unused-vars rule
console.log('\nTest Group: no-unused-vars Rule');
const eslint4 = new ESLint({
    rules: {
        'no-unused-vars': 'error'
    }
});
const codeWithUnusedVar = `const unused = 5;\nconst used = 10;\nconsole.log(used);`;
const results4 = eslint4.lintText(codeWithUnusedVar);
assert(results4[0].errorCount === 1, 'Detects unused variable');
assert(results4[0].messages[0].message.includes('unused'), 'Message mentions unused variable');

// Test 5: semi rule - missing semicolons
console.log('\nTest Group: semi Rule');
const eslint5 = new ESLint({
    rules: {
        'semi': ['error', 'always']
    }
});
const codeWithoutSemi = `const x = 5\nconst y = 10`;
const results5 = eslint5.lintText(codeWithoutSemi);
assert(results5[0].errorCount === 2, 'Detects missing semicolons');
assert(results5[0].messages[0].ruleId === 'semi', 'Correct rule ID');

// Test 6: semi rule - extra semicolons
console.log('\nTest Group: semi Rule (never)');
const eslint6 = new ESLint({
    rules: {
        'semi': ['error', 'never']
    }
});
const codeWithSemi = `const x = 5;`;
const results6 = eslint6.lintText(codeWithSemi);
assert(results6[0].errorCount === 1, 'Detects extra semicolons');
assert(results6[0].messages[0].message.includes('Extra'), 'Message mentions extra semicolon');

// Test 7: quotes rule
console.log('\nTest Group: quotes Rule');
const eslint7 = new ESLint({
    rules: {
        'quotes': ['error', 'single']
    }
});
const codeWithDoubleQuotes = `const str = "hello";`;
const results7 = eslint7.lintText(codeWithDoubleQuotes);
assert(results7[0].errorCount === 1, 'Detects wrong quote style');
assert(results7[0].messages[0].ruleId === 'quotes', 'Correct rule ID');

// Test 8: no-var rule
console.log('\nTest Group: no-var Rule');
const eslint8 = new ESLint({
    rules: {
        'no-var': 'error'
    }
});
const codeWithVar = `var x = 5;`;
const results8 = eslint8.lintText(codeWithVar);
assert(results8[0].errorCount === 1, 'Detects var usage');
assert(results8[0].messages[0].message.includes('var'), 'Message mentions var');

// Test 9: eqeqeq rule
console.log('\nTest Group: eqeqeq Rule');
const eslint9 = new ESLint({
    rules: {
        'eqeqeq': 'error'
    }
});
const codeWithLooseEquality = `if (x == 5) { }\nif (y != 10) { }`;
const results9 = eslint9.lintText(codeWithLooseEquality);
assert(results9[0].errorCount === 2, 'Detects loose equality operators');
assert(results9[0].messages[0].message.includes('==='), 'Message suggests ===');

// Test 10: Multiple rules
console.log('\nTest Group: Multiple Rules');
const eslint10 = new ESLint({
    rules: {
        'semi': 'error',
        'quotes': ['error', 'single'],
        'no-var': 'error'
    }
});
const problematicCode = `var x = "hello"`;
const results10 = eslint10.lintText(problematicCode);
assert(results10[0].errorCount === 3, 'Detects multiple issues');

// Test 11: Rule configuration - off
console.log('\nTest Group: Rule Configuration');
const eslint11 = new ESLint({
    rules: {
        'no-console': 'off'
    }
});
const results11 = eslint11.lintText(`console.log('test');`);
assert(results11[0].errorCount === 0, 'Disabled rules are not applied');

// Test 12: Rule severity levels
console.log('\nTest Group: Severity Levels');
const eslint12 = new ESLint({
    rules: {
        'no-console': 'warn',
        'semi': 'error'
    }
});
const mixedCode = `const x = 5\nconsole.log('test');`;
const results12 = eslint12.lintText(mixedCode);
assert(results12[0].warningCount === 1, 'Warning severity is detected');
assert(results12[0].errorCount === 1, 'Error severity is detected');

// Test 13: Message properties
console.log('\nTest Group: Message Structure');
const eslint13 = new ESLint({
    rules: {
        'semi': 'error'
    }
});
const results13 = eslint13.lintText(`const x = 5`);
const msg = results13[0].messages[0];
assert(msg.ruleId !== undefined, 'Message has ruleId');
assert(msg.message !== undefined, 'Message has message text');
assert(msg.line !== undefined, 'Message has line number');
assert(msg.column !== undefined, 'Message has column number');
assert(msg.severity !== undefined, 'Message has severity');

// Test 14: LintMessage class
console.log('\nTest Group: LintMessage Class');
const lintMsg = new LintMessage('test-rule', 'Test message', 2, 1, 0);
assert(lintMsg.ruleId === 'test-rule', 'LintMessage stores ruleId');
assert(lintMsg.message === 'Test message', 'LintMessage stores message');
assert(lintMsg.severity === 2, 'LintMessage stores severity');
assert(lintMsg.line === 1, 'LintMessage stores line');
assert(lintMsg.column === 0, 'LintMessage stores column');

// Test 15: RuleContext
console.log('\nTest Group: RuleContext');
const context = new RuleContext('const x = 5;', 'test.js');
assert(context.code === 'const x = 5;', 'Context stores code');
assert(context.filename === 'test.js', 'Context stores filename');
const sourceCode = context.getSourceCode();
assert(sourceCode.getText() === 'const x = 5;', 'getSourceCode returns code');

// Test 16: CLIEngine
console.log('\nTest Group: CLIEngine');
const cli = new CLIEngine({
    baseConfig: {
        rules: {
            'semi': 'error'
        }
    }
});
assert(cli instanceof CLIEngine, 'CLIEngine instance is created');

// Test 17: CLIEngine executeOnText
console.log('\nTest Group: CLIEngine executeOnText');
const cliResults = cli.executeOnText(`const x = 5`);
assert(cliResults.results !== undefined, 'CLIEngine returns results');
assert(cliResults.errorCount === 1, 'CLIEngine counts errors');
assert(typeof cliResults.warningCount === 'number', 'CLIEngine counts warnings');

// Test 18: Multiple files result structure
console.log('\nTest Group: Result Structure');
const eslint18 = new ESLint({
    rules: {
        'semi': 'error'
    }
});
const results18 = eslint18.lintText(`const x = 5`, { filename: 'test.js' });
assert(results18[0].filePath === 'test.js', 'Result includes file path');
assert(Array.isArray(results18[0].messages), 'Result has messages array');
assert(typeof results18[0].errorCount === 'number', 'Result has error count');
assert(typeof results18[0].warningCount === 'number', 'Result has warning count');

// Test 19: indent rule
console.log('\nTest Group: indent Rule');
const eslint19 = new ESLint({
    rules: {
        'indent': ['error', 4]
    }
});
const badIndentCode = `function test() {\n  return 5;\n}`;
const results19 = eslint19.lintText(badIndentCode);
assert(results19[0].errorCount > 0, 'Detects indentation issues');

// Test 20: Custom rule registration
console.log('\nTest Group: Custom Rules');
class CustomRule extends Rule {
    create(context) {
        const code = context.getSourceCode().getText();
        if (code.includes('TODO')) {
            context.report({
                ruleId: 'no-todos',
                message: 'TODO comments are not allowed',
                severity: 1,
                line: 1,
                column: 0
            });
        }
    }
}

const eslint20 = new ESLint({
    rules: {
        'no-todos': 'warn'
    }
});
eslint20.registerRule('no-todos', CustomRule);
const results20 = eslint20.lintText('// TODO: fix this');
assert(results20[0].warningCount === 1, 'Custom rule is applied');
assert(results20[0].messages[0].message.includes('TODO'), 'Custom rule message is correct');

// Test 21: Message sorting
console.log('\nTest Group: Message Sorting');
const eslint21 = new ESLint({
    rules: {
        'semi': 'error',
        'no-var': 'error'
    }
});
const multiLineCode = `const x = 5\nvar y = 10;`;
const results21 = eslint21.lintText(multiLineCode);
assert(results21[0].messages[0].line <= results21[0].messages[1].line, 'Messages are sorted by line');

// Test 22: Fixable messages
console.log('\nTest Group: Fixable Messages');
const eslint22 = new ESLint({
    rules: {
        'semi': 'error'
    }
});
const results22 = eslint22.lintText(`const x = 5`);
assert(results22[0].fixableErrorCount === 1, 'Fixable errors are counted');
assert(results22[0].messages[0].fix !== null, 'Fix information is provided');

// Test 23: Array rule configuration
console.log('\nTest Group: Array Rule Config');
const eslint23 = new ESLint({
    rules: {
        'quotes': ['error', 'double']
    }
});
const results23 = eslint23.lintText(`const x = 'hello';`);
assert(results23[0].errorCount === 1, 'Array config is parsed correctly');

// Test 24: Numeric rule configuration
console.log('\nTest Group: Numeric Rule Config');
const eslint24 = new ESLint({
    rules: {
        'semi': 2
    }
});
const results24 = eslint24.lintText(`const x = 5`);
assert(results24[0].errorCount === 1, 'Numeric severity works');

// Test 25: Zero/off configuration
console.log('\nTest Group: Disabled Rules (0)');
const eslint25 = new ESLint({
    rules: {
        'semi': 0
    }
});
const results25 = eslint25.lintText(`const x = 5`);
assert(results25[0].errorCount === 0, 'Rule with 0 is disabled');

// Test 26: Source code extraction
console.log('\nTest Group: Source Code');
const eslint26 = new ESLint({
    rules: {
        'semi': 'error'
    }
});
const sourceText = `const x = 5;\nconst y = 10;`;
const results26 = eslint26.lintText(sourceText);
assert(results26[0].source === sourceText, 'Source code is preserved in results');

// Test 27: CLIEngine getConfigForFile
console.log('\nTest Group: CLIEngine Config');
const cli27 = new CLIEngine({
    baseConfig: {
        rules: {
            'semi': 'error'
        }
    }
});
const config27 = cli27.getConfigForFile('test.js');
assert(config27.rules !== undefined, 'Config is returned');

// Test 28: Version
console.log('\nTest Group: Version');
assert(ESLint.version !== undefined, 'ESLint has version');
assert(typeof ESLint.version === 'string', 'Version is a string');

// Test 29: Comments extraction
console.log('\nTest Group: Comment Extraction');
const context29 = new RuleContext('// comment\n/* block */', 'test.js');
const comments = context29.getSourceCode().getAllComments();
assert(comments.length === 2, 'Extracts comments');
assert(comments[0].type === 'Line', 'Identifies line comments');
assert(comments[1].type === 'Block', 'Identifies block comments');

// Test 30: Empty code
console.log('\nTest Group: Empty Code');
const eslint30 = new ESLint({
    rules: {
        'semi': 'error'
    }
});
const results30 = eslint30.lintText('');
assert(results30[0].errorCount === 0, 'Empty code produces no errors');
assert(results30[0].messages.length === 0, 'Empty code produces no messages');

// Final results
console.log('\n' + '='.repeat(50));
console.log(`Test Results: ${passed} passed, ${failed} failed`);
console.log('='.repeat(50));

if (failed === 0) {
    console.log('✓ All tests passed!');
} else {
    console.log(`✗ ${failed} test(s) failed`);
    process.exit(1);
}
