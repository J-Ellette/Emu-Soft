/**
 * Prettier Emulator - Code Formatter for JavaScript
 * 
 * This module emulates the Prettier code formatter, which is an opinionated code
 * formatter that supports many languages and integrates with most editors. It removes
 * all original styling and ensures that all outputted code conforms to a consistent style.
 * 
 * Key Features:
 * - Automatic code formatting
 * - Configurable options
 * - Support for JavaScript, JSON, HTML, CSS
 * - Consistent output regardless of input style
 */

/**
 * Default Prettier options
 */
const DEFAULT_OPTIONS = {
    printWidth: 80,
    tabWidth: 2,
    useTabs: false,
    semi: true,
    singleQuote: false,
    quoteProps: 'as-needed',
    jsxSingleQuote: false,
    trailingComma: 'es5',
    bracketSpacing: true,
    bracketSameLine: false,
    arrowParens: 'always',
    endOfLine: 'lf'
};

/**
 * Token types for parsing
 */
const TokenType = {
    KEYWORD: 'keyword',
    IDENTIFIER: 'identifier',
    NUMBER: 'number',
    STRING: 'string',
    OPERATOR: 'operator',
    PUNCTUATION: 'punctuation',
    WHITESPACE: 'whitespace',
    COMMENT: 'comment'
};

/**
 * Simple tokenizer for JavaScript
 */
function tokenize(code) {
    const tokens = [];
    let i = 0;
    
    while (i < code.length) {
        const char = code[i];
        
        // Skip whitespace
        if (/\s/.test(char)) {
            i++;
            continue;
        }
        
        // Comments
        if (char === '/' && code[i + 1] === '/') {
            let comment = '';
            i += 2;
            while (i < code.length && code[i] !== '\n') {
                comment += code[i++];
            }
            tokens.push({ type: TokenType.COMMENT, value: '//' + comment });
            continue;
        }
        
        if (char === '/' && code[i + 1] === '*') {
            let comment = '';
            i += 2;
            while (i < code.length - 1 && !(code[i] === '*' && code[i + 1] === '/')) {
                comment += code[i++];
            }
            i += 2; // Skip */
            tokens.push({ type: TokenType.COMMENT, value: '/*' + comment + '*/' });
            continue;
        }
        
        // Strings
        if (char === '"' || char === '\'' || char === '`') {
            const quote = char;
            let str = quote;
            i++;
            while (i < code.length && code[i] !== quote) {
                if (code[i] === '\\') {
                    str += code[i++];
                    if (i < code.length) {
                        str += code[i++];
                    }
                } else {
                    str += code[i++];
                }
            }
            if (i < code.length) {
                str += quote;
                i++;
            }
            tokens.push({ type: TokenType.STRING, value: str, quote });
            continue;
        }
        
        // Numbers
        if (/\d/.test(char)) {
            let num = '';
            while (i < code.length && /[\d.]/.test(code[i])) {
                num += code[i++];
            }
            tokens.push({ type: TokenType.NUMBER, value: num });
            continue;
        }
        
        // Identifiers and keywords
        if (/[a-zA-Z_$]/.test(char)) {
            let ident = '';
            while (i < code.length && /[a-zA-Z0-9_$]/.test(code[i])) {
                ident += code[i++];
            }
            
            const keywords = [
                'const', 'let', 'var', 'function', 'return', 'if', 'else',
                'for', 'while', 'do', 'switch', 'case', 'break', 'continue',
                'class', 'extends', 'import', 'export', 'from', 'default',
                'async', 'await', 'try', 'catch', 'finally', 'throw', 'new'
            ];
            
            const type = keywords.includes(ident) ? TokenType.KEYWORD : TokenType.IDENTIFIER;
            tokens.push({ type, value: ident });
            continue;
        }
        
        // Operators and punctuation
        const twoCharOps = ['==', '!=', '<=', '>=', '&&', '||', '++', '--', '=>', '...'];
        const twoChar = code.slice(i, i + 2);
        
        if (twoCharOps.includes(twoChar)) {
            tokens.push({ type: TokenType.OPERATOR, value: twoChar });
            i += 2;
            continue;
        }
        
        if ('+-*/<>=!&|'.includes(char)) {
            tokens.push({ type: TokenType.OPERATOR, value: char });
            i++;
            continue;
        }
        
        if ('(){}[];:,'.includes(char)) {
            tokens.push({ type: TokenType.PUNCTUATION, value: char });
            i++;
            continue;
        }
        
        // Unknown character - skip it
        i++;
    }
    
    return tokens;
}

/**
 * Format JavaScript code
 */
function formatJavaScript(code, options) {
    const tokens = tokenize(code);
    let formatted = '';
    let indentLevel = 0;
    let needsSpace = false;
    let needsNewline = false;
    let lastWasStatement = false;
    
    const indent = () => {
        return options.useTabs
            ? '\t'.repeat(indentLevel)
            : ' '.repeat(indentLevel * options.tabWidth);
    };
    
    for (let i = 0; i < tokens.length; i++) {
        const token = tokens[i];
        const prevToken = tokens[i - 1];
        const nextToken = tokens[i + 1];
        
        // Handle newlines
        if (needsNewline) {
            formatted += '\n' + indent();
            needsNewline = false;
            needsSpace = false;
        }
        
        // Handle spaces
        if (needsSpace && token.type !== TokenType.PUNCTUATION) {
            formatted += ' ';
            needsSpace = false;
        }
        
        switch (token.type) {
            case TokenType.COMMENT:
                formatted += token.value;
                needsNewline = true;
                break;
                
            case TokenType.KEYWORD:
                formatted += token.value;
                needsSpace = true;
                lastWasStatement = false;
                break;
                
            case TokenType.IDENTIFIER:
            case TokenType.NUMBER:
                formatted += token.value;
                
                // Check if this could be end of a statement
                if (nextToken && nextToken.type === TokenType.KEYWORD) {
                    lastWasStatement = true;
                }
                
                // Space after if not followed by punctuation
                if (nextToken && nextToken.type !== TokenType.PUNCTUATION) {
                    needsSpace = true;
                }
                break;
                
            case TokenType.STRING:
                // Apply quote style
                let str = token.value;
                if (options.singleQuote && token.quote === '"') {
                    str = "'" + str.slice(1, -1) + "'";
                } else if (!options.singleQuote && token.quote === "'") {
                    str = '"' + str.slice(1, -1) + '"';
                }
                formatted += str;
                break;
                
            case TokenType.OPERATOR:
                // Spacing around operators
                if (token.value === '=>') {
                    formatted += ' => ';
                    needsSpace = false;
                } else if (['&&', '||', '==', '!=', '<=', '>='].includes(token.value)) {
                    formatted += ' ' + token.value + ' ';
                    needsSpace = false;
                } else if (token.value === '=') {
                    formatted += ' = ';
                    needsSpace = false;
                } else {
                    formatted += token.value;
                }
                break;
                
            case TokenType.PUNCTUATION:
                if (token.value === '{') {
                    // Bracket spacing
                    if (options.bracketSpacing && prevToken && prevToken.type === TokenType.PUNCTUATION && prevToken.value === '(') {
                        formatted += ' {';
                    } else if (options.bracketSpacing) {
                        formatted += ' {';
                    } else {
                        formatted += '{';
                    }
                    indentLevel++;
                    needsNewline = true;
                } else if (token.value === '}') {
                    indentLevel--;
                    formatted = formatted.trimEnd();
                    needsNewline = true;
                    formatted += '\n' + indent() + '}';
                    
                    // Check for semicolon after }
                    if (nextToken && (nextToken.type === TokenType.PUNCTUATION && nextToken.value === ';')) {
                        // Will be handled in next iteration
                    } else {
                        needsNewline = true;
                    }
                } else if (token.value === '(') {
                    formatted += '(';
                } else if (token.value === ')') {
                    formatted += ')';
                    needsSpace = true;
                } else if (token.value === '[') {
                    formatted += '[';
                } else if (token.value === ']') {
                    formatted += ']';
                } else if (token.value === ';') {
                    if (options.semi) {
                        formatted += ';';
                    }
                    needsNewline = true;
                    lastWasStatement = false;
                } else if (token.value === ',') {
                    formatted += ',';
                    needsSpace = true;
                } else if (token.value === ':') {
                    formatted += ':';
                    needsSpace = true;
                } else {
                    formatted += token.value;
                }
                break;
        }
        
        // Add semicolon at end of simple statement if missing
        if (options.semi && i === tokens.length - 1 && token.type !== TokenType.PUNCTUATION && token.value !== ';') {
            if (token.type === TokenType.NUMBER || token.type === TokenType.STRING || token.type === TokenType.IDENTIFIER) {
                formatted += ';';
            }
        }
    }
    
    // Clean up and return
    return formatted.trim() + '\n';
}

/**
 * Format JSON
 */
function formatJSON(code, options) {
    try {
        const obj = JSON.parse(code);
        const indent = options.useTabs ? '\t' : ' '.repeat(options.tabWidth);
        return JSON.stringify(obj, null, indent) + '\n';
    } catch (error) {
        throw new Error('Invalid JSON: ' + error.message);
    }
}

/**
 * Format HTML
 */
function formatHTML(code, options) {
    let formatted = '';
    let indentLevel = 0;
    const indent = options.useTabs ? '\t' : ' '.repeat(options.tabWidth);
    
    // Simple HTML formatter
    const lines = code.split('\n');
    
    for (let line of lines) {
        line = line.trim();
        if (!line) continue;
        
        // Closing tag - decrease indent before
        if (line.startsWith('</')) {
            indentLevel = Math.max(0, indentLevel - 1);
        }
        
        formatted += indent.repeat(indentLevel) + line + '\n';
        
        // Opening tag - increase indent after
        const isOpeningTag = line.startsWith('<') && !line.startsWith('</') && !line.endsWith('/>') && !line.includes('</');
        if (isOpeningTag) {
            indentLevel++;
        }
    }
    
    return formatted;
}

/**
 * Format CSS
 */
function formatCSS(code, options) {
    let formatted = '';
    let indentLevel = 0;
    const indent = options.useTabs ? '\t' : ' '.repeat(options.tabWidth);
    
    code = code.replace(/\s+/g, ' ').trim();
    
    let i = 0;
    while (i < code.length) {
        const char = code[i];
        
        if (char === '{') {
            formatted += ' {\n';
            indentLevel++;
            i++;
        } else if (char === '}') {
            indentLevel = Math.max(0, indentLevel - 1);
            formatted = formatted.trimEnd() + '\n' + indent.repeat(indentLevel) + '}\n';
            i++;
        } else if (char === ';') {
            formatted += ';\n';
            i++;
            // Skip spaces after semicolon
            while (i < code.length && code[i] === ' ') i++;
            formatted += indent.repeat(indentLevel);
        } else if (char === ':') {
            formatted += ': ';
            i++;
            // Skip spaces after colon
            while (i < code.length && code[i] === ' ') i++;
        } else {
            formatted += char;
            i++;
        }
    }
    
    return formatted.trim() + '\n';
}

/**
 * Main format function
 */
function format(code, options = {}) {
    // Merge with default options
    const opts = { ...DEFAULT_OPTIONS, ...options };
    
    // Detect parser based on file extension or content
    const parser = options.parser || detectParser(code);
    
    switch (parser) {
        case 'babel':
        case 'babel-flow':
        case 'flow':
        case 'typescript':
            return formatJavaScript(code, opts);
        case 'json':
            return formatJSON(code, opts);
        case 'html':
            return formatHTML(code, opts);
        case 'css':
        case 'scss':
        case 'less':
            return formatCSS(code, opts);
        default:
            return formatJavaScript(code, opts);
    }
}

/**
 * Detect parser from code
 */
function detectParser(code) {
    // Simple detection heuristics
    if (code.trim().startsWith('{') || code.trim().startsWith('[')) {
        try {
            JSON.parse(code);
            return 'json';
        } catch (e) {
            // Not JSON
        }
    }
    
    if (code.includes('<!DOCTYPE') || code.includes('<html')) {
        return 'html';
    }
    
    if (code.includes('@media') || code.includes('@keyframes')) {
        return 'css';
    }
    
    return 'babel';
}

/**
 * Check if code is formatted
 */
function check(code, options = {}) {
    const formatted = format(code, options);
    return code === formatted;
}

/**
 * Get file info for a file path
 */
function getFileInfo(filePath, options = {}) {
    const ext = filePath.split('.').pop();
    
    const parserMap = {
        'js': 'babel',
        'jsx': 'babel',
        'ts': 'typescript',
        'tsx': 'typescript',
        'json': 'json',
        'html': 'html',
        'htm': 'html',
        'css': 'css',
        'scss': 'scss',
        'less': 'less'
    };
    
    return {
        ignored: false,
        inferredParser: parserMap[ext] || 'babel'
    };
}

/**
 * Resolve config from file system (simplified)
 */
async function resolveConfig(filePath, options = {}) {
    // In a real implementation, this would read .prettierrc files
    return DEFAULT_OPTIONS;
}

/**
 * Clear config cache
 */
function clearConfigCache() {
    // No-op in this emulator
}

/**
 * Format with cursor position tracking
 */
function formatWithCursor(code, options = {}) {
    const cursorOffset = options.cursorOffset || 0;
    const formatted = format(code, options);
    
    // Simplified cursor tracking - just return approximate position
    return {
        formatted,
        cursorOffset: Math.min(cursorOffset, formatted.length)
    };
}

// Export Prettier API
module.exports = {
    format,
    check,
    formatWithCursor,
    getFileInfo,
    resolveConfig,
    clearConfigCache,
    
    // Parser detection
    detectParser,
    
    // Default options
    DEFAULT_OPTIONS
};
