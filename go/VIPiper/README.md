# Viper Emulator - Configuration Management for Go

**Developed by PowerShield, as an alternative to Viper**


This module emulates the **Viper** library, which is a complete configuration solution for Go applications. Viper is designed to work seamlessly with 12-Factor apps and handles multiple configuration sources.

## What is Viper?

Viper is a configuration management library for Go applications. It is designed to:
- Support multiple configuration formats (JSON, YAML, TOML, HCL, etc.)
- Read from various sources (files, environment variables, command-line flags, remote systems)
- Provide default values for configuration
- Watch and re-read config files automatically
- Support nested configuration structures
- Marshal/unmarshal configuration into structs

## Features

This emulator implements core Viper functionality:

### Configuration Sources
- **Explicit Settings**: Set values directly in code
- **Default Values**: Define fallback values
- **Environment Variables**: Bind config keys to environment variables
- **Configuration Files**: Read/write JSON configuration files
- **Priority Order**: Environment > Config > Defaults

### Data Access
- **Type-Safe Getters**: Get values as string, int, bool, float64, slice, or map
- **Nested Configuration**: Access nested config with Sub()
- **All Keys/Settings**: Retrieve all configuration keys and values
- **IsSet Check**: Check if a key has been set

### File Operations
- **ReadInConfig**: Read configuration from file
- **WriteConfig**: Write configuration to file
- **WriteConfigAs**: Write to a specific file
- **SafeWriteConfig**: Write only if file doesn't exist

### Advanced Features
- **Unmarshal**: Load configuration into structs
- **UnmarshalKey**: Load specific key into struct
- **Sub-configurations**: Work with config subsections
- **Reset**: Clear all configuration

## Usage Examples

### Basic Usage

```go
package main

import (
    "fmt"
    "viper_emulator"
)

func main() {
    // Set values
    viper.Set("app.name", "MyApp")
    viper.Set("app.version", "1.0.0")
    viper.Set("server.port", 8080)

    // Get values
    appName := viper.GetString("app.name")
    port := viper.GetInt("server.port")

    fmt.Printf("%s running on port %d\n", appName, port)
}
```

### Default Values

```go
package main

import (
    "fmt"
    "viper_emulator"
)

func main() {
    // Set defaults
    viper.SetDefault("server.host", "localhost")
    viper.SetDefault("server.port", 8080)
    viper.SetDefault("server.timeout", 30)

    // Values will use defaults if not explicitly set
    host := viper.GetString("server.host")
    port := viper.GetInt("server.port")
    
    fmt.Printf("Server: %s:%d\n", host, port)
}
```

### Environment Variables

```go
package main

import (
    "fmt"
    "os"
    "viper_emulator"
)

func main() {
    // Bind config keys to environment variables
    viper.BindEnv("database.host", "DB_HOST")
    viper.BindEnv("database.port", "DB_PORT")
    viper.BindEnv("database.name", "DB_NAME")

    // Set environment variables
    os.Setenv("DB_HOST", "prod-server")
    os.Setenv("DB_PORT", "5432")
    os.Setenv("DB_NAME", "myapp_prod")

    // Values will be read from environment
    host := viper.GetString("database.host")
    port := viper.GetInt("database.port")
    dbname := viper.GetString("database.name")

    fmt.Printf("Database: %s:%d/%s\n", host, port, dbname)
}
```

### Configuration Files

```go
package main

import (
    "fmt"
    "viper_emulator"
)

func main() {
    // Write configuration to file
    viper.Set("app.name", "MyApp")
    viper.Set("app.version", "1.0.0")
    viper.Set("server.port", 8080)
    
    viper.SetConfigFile("/etc/myapp/config.json")
    viper.SetConfigType("json")
    viper.WriteConfig()

    // Read configuration from file
    v := viper.New()
    v.SetConfigFile("/etc/myapp/config.json")
    v.SetConfigType("json")
    
    err := v.ReadInConfig()
    if err != nil {
        panic(err)
    }

    appName := v.GetString("app.name")
    fmt.Printf("Loaded config for: %s\n", appName)
}
```

### Type-Safe Getters

```go
package main

import (
    "fmt"
    "viper_emulator"
)

func main() {
    viper.Set("app.name", "MyApp")
    viper.Set("server.port", 8080)
    viper.Set("debug.enabled", true)
    viper.Set("metrics.interval", 60.5)
    viper.Set("tags", []string{"api", "web", "production"})

    // Get different types
    name := viper.GetString("app.name")
    port := viper.GetInt("server.port")
    debug := viper.GetBool("debug.enabled")
    interval := viper.GetFloat64("metrics.interval")
    tags := viper.GetStringSlice("tags")

    fmt.Printf("App: %s\n", name)
    fmt.Printf("Port: %d\n", port)
    fmt.Printf("Debug: %t\n", debug)
    fmt.Printf("Interval: %.1f\n", interval)
    fmt.Printf("Tags: %v\n", tags)
}
```

### Nested Configuration

```go
package main

import (
    "fmt"
    "viper_emulator"
)

func main() {
    // Set nested configuration
    viper.Set("database", map[string]interface{}{
        "host": "localhost",
        "port": 5432,
        "credentials": map[string]interface{}{
            "username": "admin",
            "password": "secret",
        },
    })

    // Access nested values
    dbMap := viper.GetStringMap("database")
    host := dbMap["host"]
    
    // Or use Sub for subsections
    dbConfig := viper.Sub("database")
    dbHost := dbConfig.GetString("host")
    dbPort := dbConfig.GetInt("port")

    fmt.Printf("Database: %s:%d\n", dbHost, dbPort)
}
```

### Unmarshal into Structs

```go
package main

import (
    "fmt"
    "viper_emulator"
)

type ServerConfig struct {
    Host    string `json:"host"`
    Port    int    `json:"port"`
    Timeout int    `json:"timeout"`
}

type AppConfig struct {
    Name    string       `json:"name"`
    Version string       `json:"version"`
    Server  ServerConfig `json:"server"`
}

func main() {
    // Set configuration
    viper.Set("name", "MyApp")
    viper.Set("version", "1.0.0")
    viper.Set("server", map[string]interface{}{
        "host":    "0.0.0.0",
        "port":    float64(8080),
        "timeout": float64(30),
    })

    // Unmarshal into struct
    var config AppConfig
    err := viper.Unmarshal(&config)
    if err != nil {
        panic(err)
    }

    fmt.Printf("App: %s v%s\n", config.Name, config.Version)
    fmt.Printf("Server: %s:%d\n", config.Server.Host, int(config.Server.Port))
}
```

### UnmarshalKey for Subsections

```go
package main

import (
    "fmt"
    "viper_emulator"
)

type DatabaseConfig struct {
    Host     string  `json:"host"`
    Port     float64 `json:"port"`
    Database string  `json:"database"`
}

func main() {
    viper.Set("database", map[string]interface{}{
        "host":     "localhost",
        "port":     float64(5432),
        "database": "myapp",
    })

    // Unmarshal only the database section
    var dbConfig DatabaseConfig
    err := viper.UnmarshalKey("database", &dbConfig)
    if err != nil {
        panic(err)
    }

    fmt.Printf("DB: %s:%d/%s\n", dbConfig.Host, int(dbConfig.Port), dbConfig.Database)
}
```

### Configuration Priority

```go
package main

import (
    "fmt"
    "os"
    "viper_emulator"
)

func main() {
    // Priority: Environment > Config > Defaults

    // Set default
    viper.SetDefault("port", 8080)
    fmt.Printf("Default port: %d\n", viper.GetInt("port"))

    // Set explicit value
    viper.Set("port", 3000)
    fmt.Printf("Config port: %d\n", viper.GetInt("port"))

    // Bind to environment (highest priority)
    os.Setenv("APP_PORT", "9000")
    viper.BindEnv("port", "APP_PORT")
    fmt.Printf("Env port: %d\n", viper.GetInt("port"))
}
```

### Check if Key is Set

```go
package main

import (
    "fmt"
    "viper_emulator"
)

func main() {
    viper.Set("configured", "value")

    if viper.IsSet("configured") {
        fmt.Println("Key is set")
    }

    if !viper.IsSet("notset") {
        fmt.Println("Key is not set")
    }
}
```

### All Keys and Settings

```go
package main

import (
    "fmt"
    "viper_emulator"
)

func main() {
    viper.Set("app.name", "MyApp")
    viper.Set("app.version", "1.0.0")
    viper.Set("server.port", 8080)

    // Get all keys
    keys := viper.AllKeys()
    fmt.Printf("Keys: %v\n", keys)

    // Get all settings
    settings := viper.AllSettings()
    fmt.Printf("Settings: %v\n", settings)
}
```

### Using Multiple Viper Instances

```go
package main

import (
    "fmt"
    "viper_emulator"
)

func main() {
    // Create separate instances for different configs
    appConfig := viper.New()
    appConfig.Set("name", "MainApp")
    appConfig.Set("port", 8080)

    dbConfig := viper.New()
    dbConfig.Set("host", "localhost")
    dbConfig.Set("port", 5432)

    fmt.Printf("App: %s on port %d\n", 
        appConfig.GetString("name"), 
        appConfig.GetInt("port"))
    
    fmt.Printf("DB: %s:%d\n", 
        dbConfig.GetString("host"), 
        dbConfig.GetInt("port"))
}
```

### Safe Write (Don't Overwrite)

```go
package main

import (
    "fmt"
    "viper_emulator"
)

func main() {
    viper.Set("app", "MyApp")
    viper.SetConfigFile("/tmp/config.json")
    viper.SetConfigType("json")

    // First write succeeds
    err := viper.SafeWriteConfig()
    if err == nil {
        fmt.Println("Config file created")
    }

    // Second write fails (file exists)
    err = viper.SafeWriteConfig()
    if err != nil {
        fmt.Println("Config file already exists")
    }
}
```

## Testing

Run the comprehensive test suite:

```bash
go run test_viper_emulator.go
```

Tests cover:
- Basic Set/Get operations
- Type-safe getters (String, Int, Bool, Float64, Slice, Map)
- Default values and precedence
- Environment variable binding
- Configuration file read/write
- Safe write operations
- Unmarshal into structs
- UnmarshalKey for subsections
- Nested configurations
- Sub-configurations
- Type conversions
- Configuration priority
- Global functions
- Reset functionality

Total: 26 tests

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for Viper in development and testing:

```go
// Instead of:
// import "github.com/spf13/viper"

// Use:
// import "viper_emulator"

// The rest of your code remains unchanged
func main() {
    viper.SetDefault("port", 8080)
    port := viper.GetInt("port")
}
```

## Use Cases

Perfect for:
- **Local Development**: Develop applications without external dependencies
- **Testing**: Test configuration loading and precedence
- **Learning**: Understand configuration management patterns
- **Prototyping**: Quickly prototype applications with config
- **Education**: Teach configuration best practices
- **CI/CD**: Run tests without file system dependencies

## Limitations

This is an emulator for development and testing purposes:
- JSON configuration files only (no YAML, TOML, HCL, etc.)
- No remote configuration support (etcd, Consul, etc.)
- No automatic config file watching/reloading
- No config file search paths (simplified)
- No automatic environment variable binding
- No flag binding (pflag integration)
- Simplified file path handling
- No config validation

## Supported Features

### Core Features
- ✅ Set/Get configuration values
- ✅ Default values
- ✅ Environment variable binding
- ✅ Configuration priority (Env > Config > Defaults)
- ✅ Nested configuration

### Type-Safe Getters
- ✅ GetString
- ✅ GetInt
- ✅ GetBool
- ✅ GetFloat64
- ✅ GetStringSlice
- ✅ GetStringMap

### File Operations
- ✅ SetConfigFile
- ✅ SetConfigName
- ✅ SetConfigType (JSON)
- ✅ ReadInConfig
- ✅ WriteConfig
- ✅ WriteConfigAs
- ✅ SafeWriteConfig

### Advanced Features
- ✅ IsSet
- ✅ AllKeys
- ✅ AllSettings
- ✅ Sub (sub-configurations)
- ✅ Unmarshal
- ✅ UnmarshalKey
- ✅ Reset
- ✅ Multiple instances (New)

### Global Functions
- ✅ All instance methods available as global functions

## Real-World Configuration Concepts

This emulator teaches the following concepts:

1. **Configuration Hierarchy**: Understanding config sources and precedence
2. **Environment Variables**: Using env vars for deployment config
3. **Default Values**: Providing sensible defaults
4. **Type Safety**: Using type-safe getters for config values
5. **Nested Configuration**: Organizing config in sections
6. **Struct Marshaling**: Loading config into typed structs
7. **File Persistence**: Saving and loading configuration
8. **12-Factor Apps**: Following 12-factor configuration principles
9. **Configuration Testing**: Testing config loading and precedence
10. **Multiple Configs**: Managing separate config instances

## Compatibility

Emulates core features of:
- Viper v1.x API patterns
- Standard configuration management practices
- 12-Factor app configuration principles

## License

Part of the Emu-Soft project. See main repository LICENSE.
