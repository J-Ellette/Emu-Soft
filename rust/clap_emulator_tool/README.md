# Clap Emulator - CLI Argument Parser for Rust

This module emulates **Clap** (Command Line Argument Parser), which is Rust's most widely-used library for parsing command-line arguments. Clap provides a powerful, efficient way to build CLI applications with minimal boilerplate.

## What is Clap?

Clap is a command-line argument parser for Rust that provides:
- **Declarative API**: Define CLI structure with builder pattern
- **Type Safety**: Leverage Rust's type system for argument parsing
- **Subcommands**: Support for nested command structures
- **Help Generation**: Automatic help text generation
- **Flexible Parsing**: Long/short flags, options with values
- **Default Values**: Specify default values for arguments
- **Validation**: Built-in argument validation

## Features

This emulator implements core Clap functionality:

### Command Structure
- **Command Builder**: Fluent API for building CLI applications
- **Metadata**: Set version, author, about text
- **Arguments**: Add flags and options
- **Subcommands**: Nested command hierarchies

### Arguments
- **Flags**: Boolean flags (--verbose, -v)
- **Options**: Arguments with values (--config file.toml)
- **Short/Long**: Support for both -v and --verbose
- **Required**: Mark arguments as required
- **Default Values**: Provide default values
- **Help Text**: Document arguments

### Parsing
- **Automatic Parsing**: Parse from command line
- **Custom Parsing**: Parse from array of strings
- **Type Conversion**: Parse values to typed data
- **Validation**: Basic argument validation

## Usage Examples

### Basic CLI Application

```rust
use clap_emulator::*;

fn main() {
    let matches = Command::new("myapp")
        .version("1.0.0")
        .author("Your Name")
        .about("My CLI application")
        .arg(Arg::new("verbose")
            .long("verbose")
            .short('v')
            .help("Enable verbose output"))
        .get_matches();
    
    if matches.get_flag("verbose") {
        println!("Verbose mode enabled");
    }
}
```

### Arguments with Values

```rust
use clap_emulator::*;

fn main() {
    let matches = Command::new("converter")
        .arg(Arg::new("input")
            .long("input")
            .short('i')
            .takes_value(true)
            .required(true)
            .help("Input file"))
        .arg(Arg::new("output")
            .long("output")
            .short('o')
            .takes_value(true)
            .required(true)
            .help("Output file"))
        .get_matches();
    
    let input = matches.value_of("input").unwrap();
    let output = matches.value_of("output").unwrap();
    println!("Converting {} to {}", input, output);
}
```

### Default Values

```rust
use clap_emulator::*;

fn main() {
    let matches = Command::new("server")
        .arg(Arg::new("port")
            .long("port")
            .short('p')
            .takes_value(true)
            .default_value("8080"))
        .arg(Arg::new("host")
            .long("host")
            .takes_value(true)
            .default_value("localhost"))
        .get_matches();
    
    let port = matches.value_of("port").unwrap();
    let host = matches.value_of("host").unwrap();
    println!("Starting server on {}:{}", host, port);
}
```

### Subcommands

```rust
use clap_emulator::*;

fn main() {
    let matches = Command::new("git")
        .about("A version control system")
        .subcommand(
            Command::new("add")
                .about("Add files to staging")
                .arg(Arg::new("all")
                    .long("all")
                    .short('A'))
        )
        .subcommand(
            Command::new("commit")
                .about("Commit changes")
                .arg(Arg::new("message")
                    .long("message")
                    .short('m')
                    .takes_value(true)
                    .required(true))
        )
        .get_matches();
    
    match matches.subcommand() {
        Some(("add", _)) => println!("Adding files..."),
        Some(("commit", sub_m)) => {
            let msg = sub_m.value_of("message").unwrap();
            println!("Committing: {}", msg);
        }
        _ => println!("No subcommand provided"),
    }
}
```

### Typed Value Parsing

```rust
use clap_emulator::*;

fn main() {
    let matches = Command::new("calculator")
        .arg(Arg::new("number")
            .long("number")
            .short('n')
            .takes_value(true))
        .get_matches();
    
    if let Some(num) = matches.get_one::<i32>("number") {
        println!("Number: {}", num);
        println!("Doubled: {}", num * 2);
    }
}
```

### Testing CLI Applications

```rust
use clap_emulator::*;

fn main() {
    let app = Command::new("test")
        .arg(Arg::new("verbose")
            .long("verbose")
            .short('v'));
    
    // Parse from custom arguments
    let matches = app.try_get_matches_from(&["test", "--verbose"])
        .expect("Failed to parse arguments");
    
    assert!(matches.get_flag("verbose"));
}
```

## Testing

Run the comprehensive test suite:

```bash
rustc test_clap_emulator.rs && ./test_clap_emulator
```

Tests cover:
- Command creation and metadata
- Long and short flags
- Options with values
- Default values
- Multiple flags and options
- Subcommands
- Subcommands with arguments
- Typed value parsing (i32, String)
- is_present checks
- value_of method
- get_flag method
- Missing arguments

Total: 20 tests

## Use Cases

Perfect for:
- **CLI Applications**: Build command-line tools
- **Testing**: Test CLI parsing logic
- **Learning**: Understand CLI argument parsing
- **Prototyping**: Quickly prototype CLI interfaces
- **Education**: Teach CLI design patterns

## Limitations

This is an emulator for development and testing purposes:
- No automatic help generation
- No argument validation beyond parsing
- No derive macros (manual builder only)
- No environment variable support
- No shell completion generation
- Simplified error handling
- No multiple values per argument
- No argument groups
- No custom validators

## Supported Features

### Core Features
- ✅ Command builder API
- ✅ Long flags (--flag)
- ✅ Short flags (-f)
- ✅ Options with values
- ✅ Default values
- ✅ Required arguments
- ✅ Subcommands
- ✅ Typed value parsing

### Methods
- ✅ get_flag()
- ✅ value_of()
- ✅ get_one<T>()
- ✅ is_present()
- ✅ subcommand()
- ✅ subcommand_name()
- ✅ try_get_matches_from()

## Real-World CLI Concepts

This emulator teaches the following concepts:

1. **Argument Parsing**: Converting string arguments to structured data
2. **Flag vs Option**: Boolean flags vs options with values
3. **Short vs Long**: -v vs --verbose conventions
4. **Subcommands**: Nested command structures
5. **Default Values**: Providing sensible defaults
6. **Type Safety**: Parsing to typed values
7. **Builder Pattern**: Fluent API design
8. **Command Hierarchy**: Organizing related commands

## Compatibility

Emulates core concepts of:
- Clap 4.x builder API
- Standard CLI conventions
- Unix-style argument parsing

## License

Part of the Emu-Soft project. See main repository LICENSE.
