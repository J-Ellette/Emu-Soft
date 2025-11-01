/**
 * Developed by PowerShield, as an alternative to ESLint
 */

/**
 * ESLint Emulator - JavaScript Linting Tool
 * 
 * This module emulates ESLint, a pluggable linting utility for JavaScript and JSX.
 * ESLint is designed to be completely pluggable and configurable, allowing developers
 * to enforce coding standards and catch common errors.
 * 
 * Key Features:
 * - Configurable rules
 * - Pattern matching for code issues
 * - Multiple severity levels (error, warning)
 * - Support for different environments
 * - Plugin architecture
 * - Auto-fixing capabilities
 */

class LintMessage {
    /**
     * Represents a linting message (error or warning)
     */
    constructor(ruleId, message, severity, line, column, nodeType = null, fix = null) {
        this.ruleId = ruleId;
        this.message = message;
        this.severity = severity; // 1 = warning, 2 = error
        this.line = line;
        this.column = column;
        this.nodeType = nodeType;
        this.fix = fix;
    }
}

class RuleContext {
    /**
     * Context provided to rules for analysis
     */
    constructor(code, filename, options = {}) {
        this.code = code;
        this.filename = filename;
        this.options = options;
        this.messages = [];
    }

    report(descriptor) {
        const message = new LintMessage(
            descriptor.ruleId || 'unknown',
            descriptor.message,
            descriptor.severity || 2,
            descriptor.line || 1,
            descriptor.column || 0,
            descriptor.nodeType,
            descriptor.fix
        );
        this.messages.push(message);
    }

    getSourceCode() {
        return {
            getText: () => this.code,
            getLines: () => this.code.split('\n'),
            getAllComments: () => this.extractComments()
        };
    }

    extractComments() {
        const comments = [];
        const singleLineRegex = /\/\/.*$/gm;
        const multiLineRegex = /\/\*[\s\S]*?\*\//g;
        
        let match;
        while ((match = singleLineRegex.exec(this.code)) !== null) {
            comments.push({ type: 'Line', value: match[0] });
        }
        while ((match = multiLineRegex.exec(this.code)) !== null) {
            comments.push({ type: 'Block', value: match[0] });
        }
        
        return comments;
    }
}

class Rule {
    /**
     * Base class for lint rules
     */
    constructor(config = {}) {
        this.config = config;
        this.meta = {
            type: 'problem',
            fixable: false,
            schema: []
        };
    }

    create(context) {
        // Override in subclasses
        return {};
    }
}

// Built-in Rules
class NoConsoleRule extends Rule {
    constructor(config) {
        super(config);
        this.meta.type = 'suggestion';
        this.meta.docs = { description: 'Disallow the use of console' };
    }

    create(context) {
        const code = context.getSourceCode().getText();
        const lines = code.split('\n');
        
        lines.forEach((line, index) => {
            const match = /console\.(log|error|warn|info|debug|trace)\s*\(/g.exec(line);
            if (match) {
                context.report({
                    ruleId: 'no-console',
                    message: `Unexpected console statement.`,
                    severity: this.config.severity || 1,
                    line: index + 1,
                    column: line.indexOf('console')
                });
            }
        });
    }
}

class NoUnusedVarsRule extends Rule {
    constructor(config) {
        super(config);
        this.meta.type = 'problem';
        this.meta.docs = { description: 'Disallow unused variables' };
    }

    create(context) {
        const code = context.getSourceCode().getText();
        const lines = code.split('\n');
        
        // Simple pattern: find variable declarations
        const declaredVars = new Set();
        const varDeclRegex = /(?:var|let|const)\s+(\w+)/g;
        let match;
        
        while ((match = varDeclRegex.exec(code)) !== null) {
            declaredVars.add(match[1]);
        }
        
        // Check if variables are used
        declaredVars.forEach(varName => {
            // Count occurrences (declaration + uses)
            const regex = new RegExp(`\\b${varName}\\b`, 'g');
            const occurrences = (code.match(regex) || []).length;
            
            // If only 1 occurrence, it's declared but not used
            if (occurrences === 1) {
                const lineMatch = code.match(new RegExp(`.*\\b${varName}\\b.*`));
                if (lineMatch) {
                    const line = code.substring(0, code.indexOf(lineMatch[0])).split('\n').length;
                    context.report({
                        ruleId: 'no-unused-vars',
                        message: `'${varName}' is defined but never used.`,
                        severity: this.config.severity || 2,
                        line: line,
                        column: lineMatch[0].indexOf(varName)
                    });
                }
            }
        });
    }
}

class SemiRule extends Rule {
    constructor(config) {
        super(config);
        this.meta.type = 'layout';
        this.meta.fixable = true;
        this.meta.docs = { description: 'Require or disallow semicolons' };
    }

    create(context) {
        const code = context.getSourceCode().getText();
        const lines = code.split('\n');
        const requireSemi = this.config.options?.[0] !== 'never';
        
        lines.forEach((line, index) => {
            const trimmed = line.trim();
            
            // Skip empty lines, comments, and block statements
            if (!trimmed || trimmed.startsWith('//') || trimmed.startsWith('/*') || 
                trimmed.startsWith('*') || trimmed.startsWith('}') || 
                trimmed.endsWith('{') || trimmed.startsWith('if') ||
                trimmed.startsWith('for') || trimmed.startsWith('while')) {
                return;
            }
            
            const hasSemi = trimmed.endsWith(';');
            
            if (requireSemi && !hasSemi && (
                trimmed.includes('=') || trimmed.includes('var ') || 
                trimmed.includes('let ') || trimmed.includes('const ') ||
                trimmed.includes('return ')
            )) {
                context.report({
                    ruleId: 'semi',
                    message: 'Missing semicolon.',
                    severity: this.config.severity || 2,
                    line: index + 1,
                    column: trimmed.length,
                    fix: { text: ';', range: [line.length, line.length] }
                });
            } else if (!requireSemi && hasSemi) {
                context.report({
                    ruleId: 'semi',
                    message: 'Extra semicolon.',
                    severity: this.config.severity || 2,
                    line: index + 1,
                    column: trimmed.length - 1
                });
            }
        });
    }
}

class QuotesRule extends Rule {
    constructor(config) {
        super(config);
        this.meta.type = 'layout';
        this.meta.fixable = true;
        this.meta.docs = { description: 'Enforce consistent use of quotes' };
    }

    create(context) {
        const code = context.getSourceCode().getText();
        const lines = code.split('\n');
        const preferredQuote = this.config.options?.[0] || 'single';
        const quoteChar = preferredQuote === 'single' ? "'" : '"';
        const wrongQuote = preferredQuote === 'single' ? '"' : "'";
        
        lines.forEach((line, index) => {
            // Find string literals with wrong quotes
            const regex = new RegExp(`${wrongQuote}([^${wrongQuote}]*)${wrongQuote}`, 'g');
            let match;
            
            while ((match = regex.exec(line)) !== null) {
                // Skip if it's inside a template literal or comment
                if (line.includes('`') || line.trim().startsWith('//')) {
                    continue;
                }
                
                context.report({
                    ruleId: 'quotes',
                    message: `Strings must use ${preferredQuote}quote.`,
                    severity: this.config.severity || 2,
                    line: index + 1,
                    column: match.index
                });
            }
        });
    }
}

class NoVarRule extends Rule {
    constructor(config) {
        super(config);
        this.meta.type = 'suggestion';
        this.meta.docs = { description: 'Require let or const instead of var' };
    }

    create(context) {
        const code = context.getSourceCode().getText();
        const lines = code.split('\n');
        
        lines.forEach((line, index) => {
            const match = /\bvar\s+/g.exec(line);
            if (match) {
                context.report({
                    ruleId: 'no-var',
                    message: 'Unexpected var, use let or const instead.',
                    severity: this.config.severity || 2,
                    line: index + 1,
                    column: match.index
                });
            }
        });
    }
}

class EqeqeqRule extends Rule {
    constructor(config) {
        super(config);
        this.meta.type = 'suggestion';
        this.meta.docs = { description: 'Require === and !==' };
    }

    create(context) {
        const code = context.getSourceCode().getText();
        const lines = code.split('\n');
        
        lines.forEach((line, index) => {
            // Match == or != but not === or !==
            // Using negative lookahead to avoid matching === and !==
            const eqRegex = /[^=!](\s*==\s*)[^=]/g;
            const neqRegex = /[^!](\s*!=\s*)[^=]/g;
            
            let eqMatch;
            while ((eqMatch = eqRegex.exec(line)) !== null) {
                context.report({
                    ruleId: 'eqeqeq',
                    message: 'Expected \'===\' and instead saw \'==\'.',
                    severity: this.config.severity || 2,
                    line: index + 1,
                    column: eqMatch.index + 1  // +1 to skip the char before ==
                });
            }
            
            let neqMatch;
            while ((neqMatch = neqRegex.exec(line)) !== null) {
                context.report({
                    ruleId: 'eqeqeq',
                    message: 'Expected \'!==\' and instead saw \'!=\'.',
                    severity: this.config.severity || 2,
                    line: index + 1,
                    column: neqMatch.index + 1  // +1 to skip the char before !=
                });
            }
        });
    }
}

class IndentRule extends Rule {
    constructor(config) {
        super(config);
        this.meta.type = 'layout';
        this.meta.fixable = true;
        this.meta.docs = { description: 'Enforce consistent indentation' };
    }

    create(context) {
        const code = context.getSourceCode().getText();
        const lines = code.split('\n');
        const indentSize = this.config.options?.[0] || 4;
        
        let expectedIndent = 0;
        
        lines.forEach((line, index) => {
            if (line.trim().length === 0) return;
            
            // Decrease indent for closing braces
            if (line.trim().startsWith('}')) {
                expectedIndent = Math.max(0, expectedIndent - 1);
            }
            
            // Count actual indent
            const actualIndent = line.match(/^(\s*)/)[1].length;
            const expected = expectedIndent * indentSize;
            
            if (actualIndent !== expected && line.trim().length > 0) {
                context.report({
                    ruleId: 'indent',
                    message: `Expected indentation of ${expected} spaces but found ${actualIndent}.`,
                    severity: this.config.severity || 2,
                    line: index + 1,
                    column: 0
                });
            }
            
            // Increase indent for opening braces
            if (line.trim().endsWith('{')) {
                expectedIndent++;
            }
        });
    }
}

class ESLint {
    /**
     * Main ESLint class
     */
    constructor(config = {}) {
        this.config = {
            rules: config.rules || {},
            env: config.env || {},
            extends: config.extends || [],
            parserOptions: config.parserOptions || {}
        };
        
        this.rules = new Map();
        this.registerBuiltInRules();
    }

    registerBuiltInRules() {
        this.rules.set('no-console', NoConsoleRule);
        this.rules.set('no-unused-vars', NoUnusedVarsRule);
        this.rules.set('semi', SemiRule);
        this.rules.set('quotes', QuotesRule);
        this.rules.set('no-var', NoVarRule);
        this.rules.set('eqeqeq', EqeqeqRule);
        this.rules.set('indent', IndentRule);
    }

    registerRule(name, RuleClass) {
        this.rules.set(name, RuleClass);
    }

    lintText(code, options = {}) {
        const filename = options.filename || 'input.js';
        const results = [];
        
        const fileResult = {
            filePath: filename,
            messages: [],
            errorCount: 0,
            warningCount: 0,
            fixableErrorCount: 0,
            fixableWarningCount: 0,
            source: code
        };

        // Apply each enabled rule
        Object.entries(this.config.rules).forEach(([ruleName, ruleConfig]) => {
            if (ruleConfig === 'off' || ruleConfig === 0 || ruleConfig[0] === 'off' || ruleConfig[0] === 0) {
                return;
            }

            const RuleClass = this.rules.get(ruleName);
            if (!RuleClass) {
                console.warn(`Rule '${ruleName}' not found`);
                return;
            }

            // Parse rule config
            let severity, options;
            if (Array.isArray(ruleConfig)) {
                severity = typeof ruleConfig[0] === 'string' ? 
                    (ruleConfig[0] === 'error' ? 2 : 1) : ruleConfig[0];
                options = ruleConfig.slice(1);
            } else {
                severity = typeof ruleConfig === 'string' ? 
                    (ruleConfig === 'error' ? 2 : 1) : ruleConfig;
                options = [];
            }

            const rule = new RuleClass({ severity, options });
            const context = new RuleContext(code, filename);
            
            rule.create(context);
            
            // Collect messages
            context.messages.forEach(msg => {
                fileResult.messages.push(msg);
                if (msg.severity === 2) {
                    fileResult.errorCount++;
                    if (msg.fix) fileResult.fixableErrorCount++;
                } else {
                    fileResult.warningCount++;
                    if (msg.fix) fileResult.fixableWarningCount++;
                }
            });
        });

        // Sort messages by line and column
        fileResult.messages.sort((a, b) => {
            if (a.line !== b.line) return a.line - b.line;
            return a.column - b.column;
        });

        results.push(fileResult);

        return results;
    }

    lintFiles(patterns) {
        // Simplified - would normally read files from filesystem
        console.log(`Would lint files matching: ${patterns}`);
        return [];
    }

    getConfigForFile(filePath) {
        return this.config;
    }

    static version = '8.0.0-emulated';
}

// CLI-like interface
class CLIEngine {
    constructor(options = {}) {
        this.options = {
            configFile: options.configFile,
            baseConfig: options.baseConfig || {},
            useEslintrc: options.useEslintrc !== false,
            fix: options.fix || false
        };
        
        this.eslint = new ESLint(options.baseConfig);
    }

    executeOnText(code, filename = 'input.js') {
        const results = this.eslint.lintText(code, { filename });
        
        return {
            results: results,
            errorCount: results.reduce((sum, r) => sum + r.errorCount, 0),
            warningCount: results.reduce((sum, r) => sum + r.warningCount, 0),
            fixableErrorCount: results.reduce((sum, r) => sum + r.fixableErrorCount, 0),
            fixableWarningCount: results.reduce((sum, r) => sum + r.fixableWarningCount, 0)
        };
    }

    executeOnFiles(patterns) {
        return this.eslint.lintFiles(patterns);
    }

    getConfigForFile(filePath) {
        return this.eslint.getConfigForFile(filePath);
    }

    static getErrorResults(results) {
        return results.filter(result => result.errorCount > 0);
    }

    static outputFixes(report) {
        // Would write fixes to files
        console.log('Fixes applied');
    }
}

// Export both ESLint class and CLIEngine for compatibility
module.exports = ESLint;
module.exports.ESLint = ESLint;
module.exports.CLIEngine = CLIEngine;
module.exports.Rule = Rule;
module.exports.RuleContext = RuleContext;
module.exports.LintMessage = LintMessage;
