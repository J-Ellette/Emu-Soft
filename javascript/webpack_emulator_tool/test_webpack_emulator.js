/**
 * Test Suite for Webpack Emulator
 */

const webpack = require('./webpack_emulator');

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

console.log('Running Webpack Emulator Tests...\n');

// Test 1: Basic webpack function
console.log('Test Group: Basic Functionality');
const compiler1 = webpack({
    entry: './src/index.js',
    output: {
        filename: 'bundle.js',
        path: './dist'
    }
});
assert(compiler1 instanceof webpack.Compiler, 'webpack() returns Compiler instance');

// Test 2: Compiler run with callback
console.log('\nTest Group: Compiler Execution');
webpack({
    entry: './src/app.js',
    output: {
        filename: 'app.bundle.js'
    }
}, (err, stats) => {
    assert(!err, 'Compilation completes without errors');
    assert(stats !== null, 'Stats object is returned');
    assert(stats.compilation !== null, 'Stats contains compilation object');
});

// Test 3: Multiple entry points
console.log('\nTest Group: Entry Points');
const compiler3 = webpack({
    entry: {
        main: './src/main.js',
        vendor: './src/vendor.js'
    }
});
compiler3.run((err, stats) => {
    assert(!err, 'Multiple entry points are processed');
    const json = stats.toJson();
    assert(json.modules.length > 0, 'Modules are built from entries');
});

// Test 4: Module system
console.log('\nTest Group: Module System');
const { Module } = webpack;
const testModule = new Module(1, './test.js', 'console.log("test");', ['./dep.js']);
assert(testModule.id === 1, 'Module has correct id');
assert(testModule.filepath === './test.js', 'Module has correct filepath');
assert(testModule.dependencies.length === 1, 'Module tracks dependencies');

// Test 5: Compilation
console.log('\nTest Group: Compilation');
const { Compilation } = webpack;
const compilation = new Compilation();
compilation.addModule(testModule);
assert(compilation.modules.length === 1, 'Modules can be added to compilation');
compilation.addAsset('bundle.js', 'var x = 1;');
assert(compilation.assets['bundle.js'] !== undefined, 'Assets can be added to compilation');

// Test 6: Loaders configuration
console.log('\nTest Group: Loaders');
const compiler6 = webpack({
    entry: './src/index.js',
    module: {
        rules: [
            {
                test: /\.js$/,
                use: 'babel-loader'
            },
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader']
            }
        ]
    }
});
compiler6.run((err, stats) => {
    assert(!err, 'Loaders are configured');
    const json = stats.toJson();
    assert(json.modules.length > 0, 'Modules are processed with loaders');
});

// Test 7: Plugins system
console.log('\nTest Group: Plugins');
const { BannerPlugin, DefinePlugin, HtmlWebpackPlugin } = webpack;

const bannerPlugin = new BannerPlugin('My Banner');
assert(bannerPlugin instanceof webpack.WebpackPlugin, 'BannerPlugin is a WebpackPlugin');

const definePlugin = new DefinePlugin({ 'process.env.NODE_ENV': '"production"' });
assert(definePlugin.definitions !== undefined, 'DefinePlugin stores definitions');

const htmlPlugin = new HtmlWebpackPlugin({ title: 'Test App' });
assert(htmlPlugin.options.title === 'Test App', 'HtmlWebpackPlugin stores options');

// Test 8: Plugin application
console.log('\nTest Group: Plugin Application');
const compiler8 = webpack({
    entry: './src/index.js',
    plugins: [
        new BannerPlugin('Copyright 2024'),
        new DefinePlugin({ VERSION: '"1.0.0"' })
    ]
});
compiler8.run((err, stats) => {
    assert(!err, 'Plugins are applied successfully');
    const assets = stats.compilation.assets;
    const bundleContent = assets['bundle.js'];
    assert(bundleContent.includes('Copyright 2024'), 'BannerPlugin adds banner to assets');
});

// Test 9: HtmlWebpackPlugin generates HTML
console.log('\nTest Group: HtmlWebpackPlugin');
const compiler9 = webpack({
    entry: './src/index.js',
    plugins: [
        new HtmlWebpackPlugin({ title: 'My App', filename: 'index.html' })
    ]
});
compiler9.run((err, stats) => {
    assert(!err, 'HtmlWebpackPlugin runs without error');
    const html = stats.compilation.assets['index.html'];
    assert(html !== undefined, 'HTML file is generated');
    assert(html.includes('My App'), 'HTML contains correct title');
    assert(html.includes('<script'), 'HTML includes script tags');
});

// Test 10: Compiler hooks
console.log('\nTest Group: Compiler Hooks');
let hooksCalled = [];
const compiler10 = webpack({
    entry: './src/index.js'
});
compiler10.plugin('beforeRun', () => hooksCalled.push('beforeRun'));
compiler10.plugin('run', () => hooksCalled.push('run'));
compiler10.plugin('emit', () => hooksCalled.push('emit'));
compiler10.plugin('done', () => hooksCalled.push('done'));

compiler10.run((err, stats) => {
    assert(hooksCalled.includes('beforeRun'), 'beforeRun hook is called');
    assert(hooksCalled.includes('run'), 'run hook is called');
    assert(hooksCalled.includes('emit'), 'emit hook is called');
    assert(hooksCalled.includes('done'), 'done hook is called');
    assert(hooksCalled.indexOf('beforeRun') < hooksCalled.indexOf('run'), 'Hooks are called in correct order');
});

// Test 11: Output configuration
console.log('\nTest Group: Output Configuration');
const compiler11 = webpack({
    entry: './src/index.js',
    output: {
        filename: 'custom.bundle.js',
        path: './public'
    }
});
compiler11.run((err, stats) => {
    assert(!err, 'Custom output configuration works');
    assert(stats.compilation.assets['custom.bundle.js'] !== undefined, 'Custom filename is used');
});

// Test 12: Stats JSON output
console.log('\nTest Group: Stats JSON');
const compiler12 = webpack({
    entry: './src/index.js'
});
compiler12.run((err, stats) => {
    const json = stats.toJson();
    assert(json.modules !== undefined, 'Stats JSON contains modules');
    assert(json.assets !== undefined, 'Stats JSON contains assets');
    assert(json.errors !== undefined, 'Stats JSON contains errors array');
    assert(json.warnings !== undefined, 'Stats JSON contains warnings array');
});

// Test 13: Dependency extraction
console.log('\nTest Group: Dependency Extraction');
const compiler13 = webpack({
    entry: './src/index.js'
});
const testContent = `
import React from 'react';
import './styles.css';
const lodash = require('lodash');
const utils = require('./utils');
`;
const deps = compiler13.extractDependencies(testContent);
assert(deps.length === 4, 'All dependencies are extracted');
assert(deps.includes('react'), 'ES6 import is extracted');
assert(deps.includes('lodash'), 'CommonJS require is extracted');

// Test 14: Watch mode
console.log('\nTest Group: Watch Mode');
const compiler14 = webpack({
    entry: './src/index.js'
});
const watcher = compiler14.watch({}, (err, stats) => {
    assert(!err, 'Watch mode compilation succeeds');
});
assert(watcher !== null, 'Watch mode returns watcher object');
assert(typeof watcher.close === 'function', 'Watcher has close method');
watcher.close();

// Test 15: Bundle generation
console.log('\nTest Group: Bundle Generation');
const compiler15 = webpack({
    entry: './src/index.js'
});
compiler15.run((err, stats) => {
    const bundle = stats.compilation.assets['bundle.js'];
    assert(bundle.includes('__webpack_require__'), 'Bundle contains webpack runtime');
    assert(bundle.includes('installedModules'), 'Bundle contains module cache');
    assert(bundle.includes('function(module, exports, __webpack_require__)'), 'Bundle has module wrapper');
});

// Test 16: Loader execution order
console.log('\nTest Group: Loader Execution');
const compiler16 = webpack({
    entry: './src/index.js',
    module: {
        rules: [
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader']
            }
        ]
    }
});
compiler16.run((err, stats) => {
    assert(!err, 'Multiple loaders in array are processed');
});

// Test 17: Compilation errors
console.log('\nTest Group: Error Handling');
const compilation17 = new Compilation();
assert(compilation17.hasErrors() === false, 'New compilation has no errors');
compilation17.errors.push('Test error');
assert(compilation17.hasErrors() === true, 'Compilation detects errors');

// Test 18: Module transformation
console.log('\nTest Group: Module Transformation');
const compiler18 = webpack({
    entry: './src/app.js',
    module: {
        rules: [
            {
                test: /\.js$/,
                use: 'babel-loader'
            }
        ]
    }
});
compiler18.run((err, stats) => {
    const module = stats.compilation.modules[0];
    assert(module.transformedContent !== module.content, 'Module content is transformed');
    assert(module.transformedContent.includes('Transpiled by Babel'), 'Babel loader transformation applied');
});

// Test 19: Stats with assets info
console.log('\nTest Group: Asset Information');
const compiler19 = webpack({
    entry: './src/index.js',
    plugins: [
        new HtmlWebpackPlugin()
    ]
});
compiler19.run((err, stats) => {
    const json = stats.toJson();
    assert(json.assets.length >= 2, 'Multiple assets are tracked'); // bundle.js + index.html
    json.assets.forEach(asset => {
        assert(asset.name !== undefined, 'Asset has name');
        assert(asset.size !== undefined, 'Asset has size');
    });
});

// Test 20: Custom plugin integration
console.log('\nTest Group: Custom Plugin');
class CustomPlugin extends webpack.WebpackPlugin {
    constructor() {
        super();
        this.called = false;
    }
    apply(compiler) {
        this.called = true;
        compiler.plugin('emit', (compilation) => {
            compilation.addAsset('custom.txt', 'Custom plugin output');
        });
    }
}
const customPlugin = new CustomPlugin();
const compiler20 = webpack({
    entry: './src/index.js',
    plugins: [customPlugin]
});
assert(customPlugin.called === true, 'Custom plugin apply method is called');
compiler20.run((err, stats) => {
    assert(stats.compilation.assets['custom.txt'] !== undefined, 'Custom plugin adds asset');
    assert(stats.compilation.assets['custom.txt'] === 'Custom plugin output', 'Custom plugin asset has correct content');
});

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
