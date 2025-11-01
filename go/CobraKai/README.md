# Cobra Emulator - CLI Framework for Go

**Developed by PowerShield, as an alternative to Cobra**


This module emulates the **Cobra** library, which is a powerful library for creating modern CLI applications in Go. Cobra is used in many popular projects including Kubernetes, Hugo, and GitHub CLI.

## What is Cobra?

Cobra is a library providing a simple interface to create powerful modern CLI applications similar to git & go tools. It is designed to provide:
- Easy subcommand-based CLIs (like `app server`, `app config create`)
- Fully POSIX-compliant flags (including short & long versions)
- Nested subcommands for complex command structures
- Intelligent suggestions (`app srver` suggests `server`)
- Automatic help generation for commands and flags
- Shell autocompletion support

## Features

This emulator implements core Cobra functionality:

### Commands
- **Root Command**: The main application command
- **Subcommands**: Nested command structures (e.g., `app api user list`)
- **Command Execution**: Execute commands with arguments
- **Command Help**: Display help information for commands

### Flags
- **String Flags**: Text-based flags
- **Integer Flags**: Numeric flags
- **Boolean Flags**: True/false flags
- **Shorthand Flags**: Single-character flag aliases (e.g., `-n` for `--name`)
- **Default Values**: Automatic default value support
- **Flag Parsing**: Parse flags with `=` or space separation

### Command Structure
- **Use Field**: Command name and syntax
- **Short Field**: Brief command description
- **Long Field**: Detailed command description
- **Run Function**: Command execution handler
- **Arguments**: Non-flag command arguments

## Usage Examples

### Basic Command

```go
package main

import (
    "fmt"
    "cobra_emulator"
)

func main() {
    var rootCmd = &cobra.Command{
        Use:   "app",
        Short: "My application",
        Long:  "A simple application built with Cobra emulator",
        Run: func(cmd *cobra.Command, args []string) {
            fmt.Println("Hello from my app!")
        },
    }

    rootCmd.Execute()
}
```

### Command with String Flag

```go
package main

import (
    "fmt"
    "cobra_emulator"
)

func main() {
    var name string

    var rootCmd = &cobra.Command{
        Use:   "greet",
        Short: "Greet someone",
        Run: func(cmd *cobra.Command, args []string) {
            fmt.Printf("Hello, %s!\n", name)
        },
    }

    rootCmd.Flags().StringP("name", "n", "World", "Name to greet")
    
    // Simulate: greet --name=Alice
    rootCmd.ExecuteWithArgs([]string{"--name=Alice"})
}
```

### Command with Multiple Flags

```go
package main

import (
    "fmt"
    "cobra_emulator"
)

func main() {
    var host string
    var port int
    var verbose bool

    var serverCmd = &cobra.Command{
        Use:   "server",
        Short: "Start the server",
        Run: func(cmd *cobra.Command, args []string) {
            fmt.Printf("Starting server on %s:%d\n", host, port)
            if verbose {
                fmt.Println("Verbose mode enabled")
            }
        },
    }

    serverCmd.Flags().StringP("host", "h", "localhost", "Server host")
    serverCmd.Flags().IntP("port", "p", 8080, "Server port")
    serverCmd.Flags().BoolP("verbose", "v", false, "Verbose output")

    // Simulate: server --host=0.0.0.0 --port=3000 --verbose
    serverCmd.ExecuteWithArgs([]string{"--host=0.0.0.0", "--port=3000", "--verbose"})
}
```

### Subcommands

```go
package main

import (
    "fmt"
    "cobra_emulator"
)

func main() {
    var rootCmd = &cobra.Command{
        Use:   "app",
        Short: "Application root",
    }

    var versionCmd = &cobra.Command{
        Use:   "version",
        Short: "Print version",
        Run: func(cmd *cobra.Command, args []string) {
            fmt.Println("App version 1.0.0")
        },
    }

    var configCmd = &cobra.Command{
        Use:   "config",
        Short: "Manage configuration",
        Run: func(cmd *cobra.Command, args []string) {
            fmt.Println("Config management")
        },
    }

    rootCmd.AddCommand(versionCmd)
    rootCmd.AddCommand(configCmd)

    // Simulate: app version
    rootCmd.ExecuteWithArgs([]string{"version"})
}
```

### Nested Subcommands

```go
package main

import (
    "fmt"
    "cobra_emulator"
)

func main() {
    var rootCmd = &cobra.Command{
        Use:   "app",
        Short: "Application",
    }

    var apiCmd = &cobra.Command{
        Use:   "api",
        Short: "API commands",
    }

    var userCmd = &cobra.Command{
        Use:   "user",
        Short: "User management",
    }

    var listCmd = &cobra.Command{
        Use:   "list",
        Short: "List all users",
        Run: func(cmd *cobra.Command, args []string) {
            fmt.Println("Listing all users...")
        },
    }

    var createCmd = &cobra.Command{
        Use:   "create [name]",
        Short: "Create a new user",
        Run: func(cmd *cobra.Command, args []string) {
            if len(args) > 0 {
                fmt.Printf("Creating user: %s\n", args[0])
            }
        },
    }

    rootCmd.AddCommand(apiCmd)
    apiCmd.AddCommand(userCmd)
    userCmd.AddCommand(listCmd, createCmd)

    // Simulate: app api user list
    rootCmd.ExecuteWithArgs([]string{"api", "user", "list"})
    
    // Simulate: app api user create Alice
    rootCmd.ExecuteWithArgs([]string{"api", "user", "create", "Alice"})
}
```

### Command with Arguments

```go
package main

import (
    "fmt"
    "cobra_emulator"
)

func main() {
    var getCmd = &cobra.Command{
        Use:   "get [id]",
        Short: "Get resource by ID",
        Run: func(cmd *cobra.Command, args []string) {
            if len(args) == 0 {
                fmt.Println("Error: ID required")
                return
            }
            fmt.Printf("Getting resource with ID: %s\n", args[0])
        },
    }

    // Simulate: get 123
    getCmd.ExecuteWithArgs([]string{"123"})
}
```

### Flags and Arguments Together

```go
package main

import (
    "fmt"
    "cobra_emulator"
)

func main() {
    var format string

    var exportCmd = &cobra.Command{
        Use:   "export [file]",
        Short: "Export data to file",
        Run: func(cmd *cobra.Command, args []string) {
            filename := "output.txt"
            if len(args) > 0 {
                filename = args[0]
            }
            fmt.Printf("Exporting to %s in %s format\n", filename, format)
        },
    }

    exportCmd.Flags().StringP("format", "f", "json", "Output format")

    // Simulate: export data.txt --format=csv
    exportCmd.ExecuteWithArgs([]string{"data.txt", "--format=csv"})
}
```

### Real-World CLI Example: Git-like Interface

```go
package main

import (
    "fmt"
    "cobra_emulator"
)

func main() {
    var rootCmd = &cobra.Command{
        Use:   "git",
        Short: "Git version control",
    }

    // git init
    var initCmd = &cobra.Command{
        Use:   "init",
        Short: "Initialize a repository",
        Run: func(cmd *cobra.Command, args []string) {
            fmt.Println("Initialized empty Git repository")
        },
    }

    // git clone
    var cloneCmd = &cobra.Command{
        Use:   "clone [repository]",
        Short: "Clone a repository",
        Run: func(cmd *cobra.Command, args []string) {
            if len(args) > 0 {
                fmt.Printf("Cloning repository: %s\n", args[0])
            }
        },
    }

    // git commit
    var message string
    var commitCmd = &cobra.Command{
        Use:   "commit",
        Short: "Record changes",
        Run: func(cmd *cobra.Command, args []string) {
            fmt.Printf("Committing with message: %s\n", message)
        },
    }
    commitCmd.Flags().StringP("message", "m", "", "Commit message")

    // git status
    var statusCmd = &cobra.Command{
        Use:   "status",
        Short: "Show working tree status",
        Run: func(cmd *cobra.Command, args []string) {
            fmt.Println("On branch main")
            fmt.Println("nothing to commit, working tree clean")
        },
    }

    rootCmd.AddCommand(initCmd, cloneCmd, commitCmd, statusCmd)

    // Simulate various commands
    rootCmd.ExecuteWithArgs([]string{"init"})
    rootCmd.ExecuteWithArgs([]string{"commit", "-m", "Initial commit"})
    rootCmd.ExecuteWithArgs([]string{"status"})
}
```

### Real-World CLI Example: Docker-like Interface

```go
package main

import (
    "fmt"
    "cobra_emulator"
)

func main() {
    var rootCmd = &cobra.Command{
        Use:   "docker",
        Short: "Docker container management",
    }

    // docker run
    var detach bool
    var port string
    var runCmd = &cobra.Command{
        Use:   "run [image]",
        Short: "Run a container",
        Run: func(cmd *cobra.Command, args []string) {
            if len(args) == 0 {
                fmt.Println("Error: image required")
                return
            }
            fmt.Printf("Running container from image: %s\n", args[0])
            if detach {
                fmt.Println("Running in detached mode")
            }
            if port != "" {
                fmt.Printf("Port mapping: %s\n", port)
            }
        },
    }
    runCmd.Flags().BoolP("detach", "d", false, "Run in background")
    runCmd.Flags().StringP("port", "p", "", "Port mapping")

    // docker ps
    var all bool
    var psCmd = &cobra.Command{
        Use:   "ps",
        Short: "List containers",
        Run: func(cmd *cobra.Command, args []string) {
            if all {
                fmt.Println("Listing all containers...")
            } else {
                fmt.Println("Listing running containers...")
            }
        },
    }
    psCmd.Flags().BoolP("all", "a", false, "Show all containers")

    // docker stop
    var stopCmd = &cobra.Command{
        Use:   "stop [container]",
        Short: "Stop a container",
        Run: func(cmd *cobra.Command, args []string) {
            if len(args) > 0 {
                fmt.Printf("Stopping container: %s\n", args[0])
            }
        },
    }

    rootCmd.AddCommand(runCmd, psCmd, stopCmd)

    // Simulate commands
    rootCmd.ExecuteWithArgs([]string{"run", "nginx", "-d", "-p", "8080:80"})
    rootCmd.ExecuteWithArgs([]string{"ps", "-a"})
}
```

### Getting Flag Values

```go
package main

import (
    "fmt"
    "cobra_emulator"
)

func main() {
    var cmd = &cobra.Command{
        Use: "test",
        Run: func(cmd *cobra.Command, args []string) {
            // Get string flag
            name := cmd.GetString("name")
            fmt.Printf("Name: %s\n", name)

            // Get int flag
            count := cmd.GetInt("count")
            fmt.Printf("Count: %d\n", count)

            // Get bool flag
            verbose := cmd.GetBool("verbose")
            fmt.Printf("Verbose: %t\n", verbose)
        },
    }

    cmd.Flags().String("name", "default", "Name")
    cmd.Flags().Int("count", 10, "Count")
    cmd.Flags().Bool("verbose", false, "Verbose")

    cmd.ExecuteWithArgs([]string{"--name=Test", "--count=5", "--verbose"})
}
```

## Testing

Run the comprehensive test suite:

```bash
go run test_cobra_emulator.go
```

Tests cover:
- Basic command execution
- Commands with arguments
- String, int, and boolean flags
- Shorthand flags
- Default flag values
- Subcommands (single and nested)
- Subcommands with flags and arguments
- Mixed flags and arguments
- Multiple flags
- Command parsing
- Helper methods

Total: 20 tests

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for Cobra in development and testing:

```go
// Instead of:
// import "github.com/spf13/cobra"

// Use:
// import "cobra_emulator"

// The rest of your code remains largely unchanged
func main() {
    var rootCmd = &cobra.Command{
        Use:   "app",
        Short: "My application",
    }
    
    rootCmd.Execute()
}
```

## Use Cases

Perfect for:
- **Local Development**: Develop CLI applications without external dependencies
- **Testing**: Test CLI commands and flag parsing
- **Learning**: Understand CLI framework patterns in Go
- **Prototyping**: Quickly prototype command-line tools
- **Education**: Teach CLI development concepts
- **CI/CD**: Run CLI tests without network dependencies

## Limitations

This is an emulator for development and testing purposes:
- No automatic help generation (simplified Help() method)
- No shell autocompletion
- No intelligent suggestions for typos
- No persistent flags inheritance (simplified)
- No flag validation beyond parsing
- No required flags enforcement
- No custom flag types
- Simplified flag parsing (no complex scenarios)

## Supported Features

### Core Features
- ✅ Command creation and execution
- ✅ Subcommands (nested structure)
- ✅ Command arguments
- ✅ Command descriptions (Use, Short, Long)

### Flags
- ✅ String flags
- ✅ Int flags
- ✅ Bool flags
- ✅ Shorthand flags (-n)
- ✅ Long flags (--name)
- ✅ Flag with = (--name=value)
- ✅ Flag with space (--name value)
- ✅ Default flag values
- ✅ Flag getters (GetString, GetInt, GetBool)

### Commands
- ✅ Root commands
- ✅ Subcommands
- ✅ Nested subcommands
- ✅ AddCommand()
- ✅ Execute()
- ✅ ExecuteWithArgs() (for testing)
- ✅ Run function
- ✅ Args() method
- ✅ Printf/Println/Print methods

## Real-World CLI Concepts

This emulator teaches the following concepts:

1. **Command Hierarchies**: Organizing commands in tree structures
2. **Flag Parsing**: Processing command-line flags and arguments
3. **Subcommands**: Creating complex CLI interfaces
4. **POSIX Conventions**: Following standard CLI patterns
5. **Help Systems**: Providing user assistance
6. **Argument Handling**: Processing positional arguments
7. **Configuration**: Using flags for command configuration
8. **CLI Design**: Building intuitive command-line interfaces

## Compatibility

Emulates core features of:
- Cobra v1.x API patterns
- Standard POSIX flag conventions
- Common CLI tool patterns (git, docker, kubectl)

## License

Part of the Emu-Soft project. See main repository LICENSE.
