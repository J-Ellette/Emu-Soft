/**
 * Developed by PowerShield, as an alternative to Webpack
 */

/**
 * Webpack Emulator - Module Bundler for JavaScript
 * 
 * This module emulates Webpack, a static module bundler for modern JavaScript
 * applications. When webpack processes your application, it internally builds
 * a dependency graph that maps every module your project needs and generates
 * one or more bundles.
 * 
 * Key Features:
 * - Module bundling (ES6, CommonJS)
 * - Entry point configuration
 * - Output configuration
 * - Loaders for transforming files
 * - Plugins for custom functionality
 * - Dependency resolution
 * - Code transformation
 */

const fs = require('fs');
const path = require('path');

class Module {
    /**
     * Represents a module in the dependency graph
     */
    constructor(id, filepath, content, dependencies = []) {
        this.id = id;
        this.filepath = filepath;
        this.content = content;
        this.dependencies = dependencies;
        this.transformedContent = content;
    }
}

class Compilation {
    /**
     * Represents a compilation of modules
     */
    constructor() {
        this.modules = [];
        this.assets = {};
        this.errors = [];
        this.warnings = [];
    }

    addModule(module) {
        this.modules.push(module);
    }

    addAsset(name, content) {
        this.assets[name] = content;
    }

    hasErrors() {
        return this.errors.length > 0;
    }
}

class Compiler {
    /**
     * The central orchestrator for webpack compilation
     */
    constructor(config) {
        this.config = config;
        this.hooks = {
            beforeRun: [],
            run: [],
            emit: [],
            afterEmit: [],
            done: []
        };
        this.compilation = null;
    }

    plugin(hookName, callback) {
        if (this.hooks[hookName]) {
            this.hooks[hookName].push(callback);
        }
    }

    runHook(hookName, ...args) {
        if (this.hooks[hookName]) {
            this.hooks[hookName].forEach(callback => callback(...args));
        }
    }

    run(callback) {
        this.runHook('beforeRun', this);
        this.runHook('run', this);

        try {
            this.compilation = new Compilation();
            this.compile();
            this.emit();

            this.runHook('done', {
                compilation: this.compilation,
                hasErrors: this.compilation.hasErrors()
            });

            callback(null, {
                compilation: this.compilation,
                toJson: () => ({
                    errors: this.compilation.errors,
                    warnings: this.compilation.warnings,
                    modules: this.compilation.modules.map(m => ({
                        id: m.id,
                        name: m.filepath
                    })),
                    assets: Object.keys(this.compilation.assets).map(name => ({
                        name,
                        size: this.compilation.assets[name].length
                    }))
                })
            });
        } catch (error) {
            callback(error);
        }
    }

    compile() {
        const entry = this.config.entry || './src/index.js';
        const entries = typeof entry === 'string' ? { main: entry } : entry;

        Object.keys(entries).forEach(name => {
            const entryPath = entries[name];
            this.buildModule(entryPath, 0);
        });
    }

    buildModule(filepath, depth = 0) {
        // Simulate reading a file
        let content = this.readFile(filepath);
        if (!content) return null;

        // Extract dependencies
        const dependencies = this.extractDependencies(content);

        // Create module
        const module = new Module(
            this.compilation.modules.length,
            filepath,
            content,
            dependencies
        );

        // Apply loaders
        module.transformedContent = this.applyLoaders(filepath, content);

        this.compilation.addModule(module);

        // Recursively build dependencies (limit depth to prevent infinite loops)
        if (depth < 10) {
            dependencies.forEach(dep => {
                const resolvedPath = this.resolveDependency(filepath, dep);
                if (resolvedPath && !this.compilation.modules.find(m => m.filepath === resolvedPath)) {
                    this.buildModule(resolvedPath, depth + 1);
                }
            });
        }

        return module;
    }

    readFile(filepath) {
        // Simulate reading file content
        // In a real implementation, this would use fs.readFileSync
        return `// Content of ${filepath}\n`;
    }

    extractDependencies(content) {
        const dependencies = [];
        
        // Extract ES6 imports with 'from' clause
        const importRegex = /import\s+.*?\s+from\s+['"](.+?)['"]/g;
        let match;
        while ((match = importRegex.exec(content)) !== null) {
            dependencies.push(match[1]);
        }

        // Extract ES6 side-effect imports (import './file')
        const sideEffectImportRegex = /import\s+['"](.+?)['"]/g;
        while ((match = sideEffectImportRegex.exec(content)) !== null) {
            if (!dependencies.includes(match[1])) {
                dependencies.push(match[1]);
            }
        }

        // Extract CommonJS requires
        const requireRegex = /require\s*\(\s*['"](.+?)['"]\s*\)/g;
        while ((match = requireRegex.exec(content)) !== null) {
            dependencies.push(match[1]);
        }

        return dependencies;
    }

    resolveDependency(fromFile, depPath) {
        // Simplified dependency resolution
        if (depPath.startsWith('./') || depPath.startsWith('../')) {
            const dir = path.dirname(fromFile);
            return path.join(dir, depPath);
        } else {
            // Assume node_modules
            return `node_modules/${depPath}`;
        }
    }

    applyLoaders(filepath, content) {
        let transformed = content;
        const rules = this.config.module?.rules || [];

        rules.forEach(rule => {
            if (rule.test && rule.test.test(filepath)) {
                const loaders = Array.isArray(rule.use) ? rule.use : [rule.use];
                loaders.forEach(loader => {
                    if (typeof loader === 'string') {
                        transformed = this.runLoader(loader, transformed, filepath);
                    } else if (loader.loader) {
                        transformed = this.runLoader(loader.loader, transformed, filepath, loader.options);
                    }
                });
            }
        });

        return transformed;
    }

    runLoader(loaderName, content, filepath, options = {}) {
        // Simulate loader execution
        switch (loaderName) {
            case 'babel-loader':
                return `// Transpiled by Babel\n${content}`;
            case 'css-loader':
                return `// CSS processed\nmodule.exports = "${content.replace(/\n/g, '\\n')}";`;
            case 'style-loader':
                return `// Style injected\n${content}`;
            case 'file-loader':
                return `module.exports = "__webpack_public_path__ + '${path.basename(filepath)}'";`;
            default:
                return content;
        }
    }

    emit() {
        const output = this.config.output || {};
        const filename = output.filename || 'bundle.js';
        const outputPath = output.path || './dist';

        // Generate bundle
        const bundle = this.generateBundle();

        this.compilation.addAsset(filename, bundle);

        this.runHook('emit', this.compilation);

        this.runHook('afterEmit', this.compilation);
    }

    generateBundle() {
        const modules = this.compilation.modules;
        
        // Simple webpack bundle template
        let bundle = `(function(modules) {
    var installedModules = {};
    
    function __webpack_require__(moduleId) {
        if(installedModules[moduleId]) {
            return installedModules[moduleId].exports;
        }
        var module = installedModules[moduleId] = {
            i: moduleId,
            l: false,
            exports: {}
        };
        
        modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
        module.l = true;
        return module.exports;
    }
    
    return __webpack_require__(0);
})({
`;

        modules.forEach((module, index) => {
            bundle += `    ${module.id}: function(module, exports, __webpack_require__) {\n`;
            bundle += `        ${module.transformedContent.split('\n').join('\n        ')}\n`;
            bundle += `    }${index < modules.length - 1 ? ',' : ''}\n`;
        });

        bundle += '});';

        return bundle;
    }

    watch(watchOptions, callback) {
        // Simulate watch mode
        console.log('Webpack is watching the files...');
        
        // Initial compilation
        this.run(callback);

        return {
            close: () => {
                console.log('Watch mode stopped');
            }
        };
    }
}

class WebpackPlugin {
    /**
     * Base class for webpack plugins
     */
    apply(compiler) {
        // Override in subclasses
    }
}

class BannerPlugin extends WebpackPlugin {
    constructor(options) {
        super();
        this.options = typeof options === 'string' ? { banner: options } : options;
    }

    apply(compiler) {
        compiler.plugin('emit', (compilation) => {
            const banner = this.options.banner;
            Object.keys(compilation.assets).forEach(filename => {
                compilation.assets[filename] = `/*! ${banner} */\n${compilation.assets[filename]}`;
            });
        });
    }
}

class DefinePlugin extends WebpackPlugin {
    constructor(definitions) {
        super();
        this.definitions = definitions;
    }

    apply(compiler) {
        compiler.plugin('run', () => {
            // In a real implementation, this would replace values in the code
            console.log('DefinePlugin: Defined constants', this.definitions);
        });
    }
}

class HtmlWebpackPlugin extends WebpackPlugin {
    constructor(options = {}) {
        super();
        this.options = options;
    }

    apply(compiler) {
        compiler.plugin('emit', (compilation) => {
            const template = this.options.template || 'index.html';
            const filename = this.options.filename || 'index.html';
            
            const htmlContent = this.generateHtml(compilation);
            compilation.addAsset(filename, htmlContent);
        });
    }

    generateHtml(compilation) {
        const scripts = Object.keys(compilation.assets)
            .filter(name => name.endsWith('.js'))
            .map(name => `    <script src="${name}"></script>`)
            .join('\n');

        return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>${this.options.title || 'Webpack App'}</title>
</head>
<body>
    <div id="root"></div>
${scripts}
</body>
</html>`;
    }
}

function webpack(config, callback) {
    /**
     * Main webpack function
     */
    const compiler = new Compiler(config);

    // Apply plugins
    if (config.plugins) {
        config.plugins.forEach(plugin => {
            plugin.apply(compiler);
        });
    }

    if (callback) {
        compiler.run(callback);
        return compiler;
    }

    return compiler;
}

// Export webpack and common plugins
webpack.Compiler = Compiler;
webpack.Compilation = Compilation;
webpack.WebpackPlugin = WebpackPlugin;
webpack.BannerPlugin = BannerPlugin;
webpack.DefinePlugin = DefinePlugin;
webpack.HtmlWebpackPlugin = HtmlWebpackPlugin;
webpack.Module = Module;

module.exports = webpack;
