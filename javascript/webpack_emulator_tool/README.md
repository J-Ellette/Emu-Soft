# Webpack Emulator - Module Bundler for JavaScript

This module emulates **Webpack**, a static module bundler for modern JavaScript applications. When webpack processes your application, it internally builds a dependency graph that maps every module your project needs and generates one or more bundles.

## What is Webpack?

Webpack is a module bundler that takes modules with dependencies and generates static assets representing those modules. It is designed to be:
- Highly configurable and extensible
- Plugin-based architecture
- Code splitting and lazy loading support
- Asset management (JS, CSS, images, etc.)
- Development server with hot module replacement
- Tree shaking for dead code elimination

## Features

This emulator implements core Webpack functionality:

### Module Bundling
- **Entry Points**: Single or multiple entry points
- **Dependency Resolution**: Resolves ES6 imports and CommonJS requires
- **Module Graph**: Builds a dependency graph of all modules
- **Bundle Generation**: Creates webpack-style bundles with runtime

### Loaders System
- **File Transformation**: Transform files before bundling
- **Chained Loaders**: Apply multiple loaders in sequence
- **Loader Options**: Configure loaders with options
- **Built-in Loaders**: Support for common loaders (babel, css, file, etc.)

### Plugins System
- **Compilation Hooks**: Access compilation lifecycle
- **Asset Manipulation**: Modify or add assets
- **Custom Plugins**: Create custom plugins
- **Built-in Plugins**: BannerPlugin, DefinePlugin, HtmlWebpackPlugin

### Output Configuration
- **Filename**: Custom output filename patterns
- **Path**: Output directory configuration
- **Public Path**: CDN or path prefix support

### Compiler API
- **Run Mode**: One-time compilation
- **Watch Mode**: Continuous compilation on file changes
- **Stats**: Detailed compilation statistics
- **Error Handling**: Comprehensive error reporting

## Usage Examples

### Basic Configuration

```javascript
const webpack = require('./webpack_emulator');

const config = {
    entry: './src/index.js',
    output: {
        filename: 'bundle.js',
        path: './dist'
    }
};

webpack(config, (err, stats) => {
    if (err) {
        console.error(err);
        return;
    }
    
    const info = stats.toJson();
    console.log('Compilation successful!');
    console.log('Modules:', info.modules.length);
    console.log('Assets:', info.assets);
});
```

### Multiple Entry Points

```javascript
const webpack = require('./webpack_emulator');

const config = {
    entry: {
        app: './src/app.js',
        vendor: './src/vendor.js',
        admin: './src/admin.js'
    },
    output: {
        filename: '[name].bundle.js',
        path: './dist'
    }
};

webpack(config, (err, stats) => {
    console.log('Built multiple bundles:', Object.keys(stats.compilation.assets));
});
```

### Using Loaders

```javascript
const webpack = require('./webpack_emulator');

const config = {
    entry: './src/index.js',
    output: {
        filename: 'bundle.js',
        path: './dist'
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                use: 'babel-loader'
            },
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader']
            },
            {
                test: /\.(png|jpg|gif)$/,
                use: {
                    loader: 'file-loader',
                    options: {
                        name: '[name].[ext]',
                        outputPath: 'images/'
                    }
                }
            }
        ]
    }
};

webpack(config, (err, stats) => {
    console.log('Processed with loaders');
});
```

### Loader with Options

```javascript
const config = {
    entry: './src/index.js',
    module: {
        rules: [
            {
                test: /\.js$/,
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: ['@babel/preset-env']
                    }
                }
            }
        ]
    }
};
```

### Using Built-in Plugins

```javascript
const webpack = require('./webpack_emulator');
const { BannerPlugin, DefinePlugin, HtmlWebpackPlugin } = webpack;

const config = {
    entry: './src/index.js',
    output: {
        filename: 'bundle.js',
        path: './dist'
    },
    plugins: [
        new BannerPlugin('Copyright 2024 My Company'),
        new DefinePlugin({
            'process.env.NODE_ENV': '"production"',
            'VERSION': '"1.0.0"'
        }),
        new HtmlWebpackPlugin({
            title: 'My Application',
            filename: 'index.html'
        })
    ]
};

webpack(config, (err, stats) => {
    const assets = stats.compilation.assets;
    console.log('Generated files:', Object.keys(assets));
    // Output: ['bundle.js', 'index.html']
});
```

### BannerPlugin

```javascript
const { BannerPlugin } = require('./webpack_emulator');

// String banner
new BannerPlugin('Copyright 2024')

// Object options
new BannerPlugin({
    banner: 'Copyright 2024\nLicense: MIT'
})
```

### DefinePlugin

```javascript
const { DefinePlugin } = require('./webpack_emulator');

new DefinePlugin({
    'process.env.NODE_ENV': '"production"',
    'API_URL': '"https://api.example.com"',
    'FEATURE_FLAG': 'true',
    'VERSION': '"1.2.3"'
})
```

### HtmlWebpackPlugin

```javascript
const { HtmlWebpackPlugin } = require('./webpack_emulator');

new HtmlWebpackPlugin({
    title: 'My Application',
    filename: 'index.html',
    template: 'src/index.html' // Optional custom template
})
```

### Custom Plugin

```javascript
const webpack = require('./webpack_emulator');

class MyCustomPlugin extends webpack.WebpackPlugin {
    apply(compiler) {
        compiler.plugin('emit', (compilation) => {
            // Add a custom asset
            compilation.addAsset('custom-file.txt', 'Custom content');
        });
        
        compiler.plugin('done', (stats) => {
            console.log('Build completed!');
        });
    }
}

const config = {
    entry: './src/index.js',
    plugins: [
        new MyCustomPlugin()
    ]
};
```

### Accessing Compiler Directly

```javascript
const webpack = require('./webpack_emulator');

const compiler = webpack({
    entry: './src/index.js',
    output: {
        filename: 'bundle.js'
    }
});

// Add custom hooks
compiler.plugin('beforeRun', (compiler) => {
    console.log('Starting compilation...');
});

compiler.plugin('done', (stats) => {
    console.log('Compilation finished!');
});

// Run compilation
compiler.run((err, stats) => {
    if (err) {
        console.error('Compilation failed:', err);
        return;
    }
    
    const info = stats.toJson();
    console.log('Success!');
    console.log('Modules:', info.modules);
    console.log('Assets:', info.assets);
});
```

### Watch Mode

```javascript
const webpack = require('./webpack_emulator');

const compiler = webpack({
    entry: './src/index.js',
    output: {
        filename: 'bundle.js',
        path: './dist'
    }
});

const watcher = compiler.watch({
    aggregateTimeout: 300,
    poll: undefined
}, (err, stats) => {
    if (err) {
        console.error(err);
        return;
    }
    
    console.log('Rebuilt at', new Date().toLocaleTimeString());
});

// Stop watching
// watcher.close();
```

### Stats Object

```javascript
webpack(config, (err, stats) => {
    if (err) {
        console.error('Fatal error:', err);
        return;
    }
    
    // Get JSON representation
    const info = stats.toJson();
    
    // Check for errors
    if (info.errors.length > 0) {
        console.error('Compilation errors:');
        info.errors.forEach(error => console.error(error));
    }
    
    // Check for warnings
    if (info.warnings.length > 0) {
        console.warn('Compilation warnings:');
        info.warnings.forEach(warning => console.warn(warning));
    }
    
    // Display modules
    console.log('Modules built:', info.modules.length);
    info.modules.forEach(module => {
        console.log(`  - ${module.name} (id: ${module.id})`);
    });
    
    // Display assets
    console.log('Assets generated:');
    info.assets.forEach(asset => {
        console.log(`  - ${asset.name} (${asset.size} bytes)`);
    });
});
```

### Full Configuration Example

```javascript
const webpack = require('./webpack_emulator');
const { BannerPlugin, DefinePlugin, HtmlWebpackPlugin } = webpack;

const config = {
    // Entry points
    entry: {
        app: './src/app.js',
        vendor: './src/vendor.js'
    },
    
    // Output configuration
    output: {
        filename: '[name].bundle.js',
        path: './dist',
        publicPath: '/assets/'
    },
    
    // Module rules (loaders)
    module: {
        rules: [
            {
                test: /\.js$/,
                use: 'babel-loader'
            },
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader']
            },
            {
                test: /\.(png|jpg|gif|svg)$/,
                use: 'file-loader'
            }
        ]
    },
    
    // Plugins
    plugins: [
        new BannerPlugin('Copyright 2024'),
        new DefinePlugin({
            'process.env.NODE_ENV': '"production"'
        }),
        new HtmlWebpackPlugin({
            title: 'My App',
            filename: 'index.html'
        })
    ]
};

const compiler = webpack(config);

compiler.plugin('done', (stats) => {
    console.log('Build completed successfully!');
});

compiler.run((err, stats) => {
    if (err) {
        console.error('Build failed:', err);
        return;
    }
    
    const info = stats.toJson();
    console.log('Built', info.assets.length, 'assets');
});
```

## Testing

Run the comprehensive test suite:

```bash
node test_webpack_emulator.js
```

Tests cover:
- Basic webpack function and compiler creation
- Single and multiple entry points
- Module system and dependency tracking
- Compilation process
- Loader configuration and execution
- Plugin system and built-in plugins
- Output configuration
- Compiler hooks and lifecycle
- Watch mode
- Bundle generation
- Stats and error handling
- Custom plugin creation

## Integration with Existing Code

This emulator is designed to be a learning tool and testing replacement for Webpack:

```javascript
// Instead of:
// const webpack = require('webpack');

// Use:
const webpack = require('./webpack_emulator');

// Most basic webpack configurations will work
const config = {
    entry: './src/index.js',
    output: {
        filename: 'bundle.js',
        path: './dist'
    },
    module: {
        rules: [
            { test: /\.js$/, use: 'babel-loader' }
        ]
    }
};

webpack(config, (err, stats) => {
    // Handle compilation results
});
```

## Use Cases

Perfect for:
- **Learning**: Understand how module bundlers work
- **Testing**: Test webpack configurations without actual bundling
- **Prototyping**: Quickly prototype build configurations
- **Education**: Teach bundler concepts
- **Development**: Develop webpack plugins in isolation
- **CI/CD**: Test build configurations in CI pipelines

## Limitations

This is an emulator for learning and testing purposes:
- No actual file system operations (simulated)
- No real module resolution (simplified)
- No source maps generation
- No hot module replacement
- No code splitting
- No tree shaking
- No optimization/minification
- Simplified loader execution
- No dev server
- No complex plugin ecosystem integration

## Supported Features

### Core Features
- ✅ Single entry point
- ✅ Multiple entry points
- ✅ Output configuration
- ✅ Module bundling
- ✅ Dependency graph building
- ✅ Bundle generation

### Loaders
- ✅ Loader configuration
- ✅ Multiple loaders per rule
- ✅ Loader options
- ✅ Simulated transformations (babel, css, file loaders)

### Plugins
- ✅ Plugin system
- ✅ Compiler hooks
- ✅ BannerPlugin
- ✅ DefinePlugin
- ✅ HtmlWebpackPlugin
- ✅ Custom plugin support

### Compiler API
- ✅ compiler.run()
- ✅ compiler.watch()
- ✅ compiler.plugin()
- ✅ Compilation hooks
- ✅ Stats object

### Other
- ✅ Dependency extraction (ES6 imports, CommonJS requires)
- ✅ Module transformation
- ✅ Asset management
- ✅ Error handling

## Real-World Module Bundler Concepts

This emulator teaches the following concepts:

1. **Dependency Resolution**: How bundlers find and resolve dependencies
2. **Module Graph**: Building a graph of all application modules
3. **Loaders**: Transforming files before bundling
4. **Plugins**: Extending bundler functionality
5. **Compilation Process**: The stages of building a bundle
6. **Asset Management**: Handling different file types
7. **Entry Points**: Where bundling starts
8. **Output Configuration**: Where and how bundles are generated
9. **Code Transformation**: Converting modern code for browsers
10. **Build Optimization**: Understanding bundler internals

## Compatibility

Emulates core features of:
- Webpack 4.x and 5.x API patterns
- Common loader conventions
- Standard plugin interfaces
- Module resolution algorithms

## License

Part of the Emu-Soft project. See main repository LICENSE.
