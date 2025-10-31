#[path = "clap_emulator.rs"]
mod clap_emulator;

use clap_emulator::*;

struct TestResult {
    name: String,
    passed: bool,
    error: Option<String>,
}

fn test_runner<F>(name: &str, test_fn: F) -> TestResult
where
    F: FnOnce() -> Result<(), String>,
{
    match test_fn() {
        Ok(_) => TestResult {
            name: name.to_string(),
            passed: true,
            error: None,
        },
        Err(e) => TestResult {
            name: name.to_string(),
            passed: false,
            error: Some(e),
        },
    }
}

fn main() {
    println!("Running Clap Emulator Tests");
    println!("===========================\n");
    
    let mut results = Vec::new();
    
    // Test 1: Command creation
    results.push(test_runner("Command creation", || {
        let _cmd = Command::new("test");
        Ok(())
    }));
    
    // Test 2: Command with metadata
    results.push(test_runner("Command with metadata", || {
        let _cmd = Command::new("test")
            .about("Test app")
            .version("1.0.0")
            .author("Test Author");
        Ok(())
    }));
    
    // Test 3: Long flag
    results.push(test_runner("Long flag", || {
        let app = Command::new("test")
            .arg(Arg::new("verbose").long("verbose"));
        
        let matches = app.try_get_matches_from(&["test", "--verbose"])
            .map_err(|e| e.to_string())?;
        
        if matches.is_present("verbose") {
            Ok(())
        } else {
            Err("Flag not present".to_string())
        }
    }));
    
    // Test 4: Short flag
    results.push(test_runner("Short flag", || {
        let app = Command::new("test")
            .arg(Arg::new("verbose").short('v'));
        
        let matches = app.try_get_matches_from(&["test", "-v"])
            .map_err(|e| e.to_string())?;
        
        if matches.is_present("verbose") {
            Ok(())
        } else {
            Err("Flag not present".to_string())
        }
    }));
    
    // Test 5: Long option with value
    results.push(test_runner("Long option with value", || {
        let app = Command::new("test")
            .arg(Arg::new("config")
                .long("config")
                .takes_value(true));
        
        let matches = app.try_get_matches_from(&["test", "--config", "file.toml"])
            .map_err(|e| e.to_string())?;
        
        if matches.value_of("config") == Some("file.toml") {
            Ok(())
        } else {
            Err(format!("Expected 'file.toml', got {:?}", matches.value_of("config")))
        }
    }));
    
    // Test 6: Short option with value
    results.push(test_runner("Short option with value", || {
        let app = Command::new("test")
            .arg(Arg::new("output")
                .short('o')
                .takes_value(true));
        
        let matches = app.try_get_matches_from(&["test", "-o", "output.txt"])
            .map_err(|e| e.to_string())?;
        
        if matches.value_of("output") == Some("output.txt") {
            Ok(())
        } else {
            Err(format!("Expected 'output.txt', got {:?}", matches.value_of("output")))
        }
    }));
    
    // Test 7: Default values
    results.push(test_runner("Default values", || {
        let app = Command::new("test")
            .arg(Arg::new("port")
                .long("port")
                .takes_value(true)
                .default_value("8080"));
        
        let matches = app.try_get_matches_from(&["test"])
            .map_err(|e| e.to_string())?;
        
        if matches.value_of("port") == Some("8080") {
            Ok(())
        } else {
            Err(format!("Expected '8080', got {:?}", matches.value_of("port")))
        }
    }));
    
    // Test 8: Override default value
    results.push(test_runner("Override default value", || {
        let app = Command::new("test")
            .arg(Arg::new("port")
                .long("port")
                .takes_value(true)
                .default_value("8080"));
        
        let matches = app.try_get_matches_from(&["test", "--port", "3000"])
            .map_err(|e| e.to_string())?;
        
        if matches.value_of("port") == Some("3000") {
            Ok(())
        } else {
            Err(format!("Expected '3000', got {:?}", matches.value_of("port")))
        }
    }));
    
    // Test 9: Multiple flags
    results.push(test_runner("Multiple flags", || {
        let app = Command::new("test")
            .arg(Arg::new("verbose").long("verbose"))
            .arg(Arg::new("debug").long("debug"));
        
        let matches = app.try_get_matches_from(&["test", "--verbose", "--debug"])
            .map_err(|e| e.to_string())?;
        
        if matches.is_present("verbose") && matches.is_present("debug") {
            Ok(())
        } else {
            Err("Flags not present".to_string())
        }
    }));
    
    // Test 10: get_flag method
    results.push(test_runner("get_flag method", || {
        let app = Command::new("test")
            .arg(Arg::new("verbose").long("verbose"));
        
        let matches = app.try_get_matches_from(&["test", "--verbose"])
            .map_err(|e| e.to_string())?;
        
        if matches.get_flag("verbose") {
            Ok(())
        } else {
            Err("Flag not set".to_string())
        }
    }));
    
    // Test 11: Subcommand
    results.push(test_runner("Subcommand", || {
        let app = Command::new("git")
            .subcommand(Command::new("add"));
        
        let matches = app.try_get_matches_from(&["git", "add"])
            .map_err(|e| e.to_string())?;
        
        if matches.subcommand_name() == Some("add") {
            Ok(())
        } else {
            Err(format!("Expected 'add', got {:?}", matches.subcommand_name()))
        }
    }));
    
    // Test 12: Subcommand with arguments
    results.push(test_runner("Subcommand with arguments", || {
        let app = Command::new("git")
            .subcommand(
                Command::new("commit")
                    .arg(Arg::new("message")
                        .long("message")
                        .takes_value(true))
            );
        
        let matches = app.try_get_matches_from(&["git", "commit", "--message", "Test"])
            .map_err(|e| e.to_string())?;
        
        if let Some((name, sub_m)) = matches.subcommand() {
            if name == "commit" && sub_m.value_of("message") == Some("Test") {
                return Ok(());
            }
        }
        Err("Subcommand or argument not found".to_string())
    }));
    
    // Test 13: Typed value parsing - i32
    results.push(test_runner("Typed value parsing - i32", || {
        let app = Command::new("test")
            .arg(Arg::new("count")
                .long("count")
                .takes_value(true));
        
        let matches = app.try_get_matches_from(&["test", "--count", "42"])
            .map_err(|e| e.to_string())?;
        
        if let Some(value) = matches.get_one::<i32>("count") {
            if value == 42 {
                return Ok(());
            }
            return Err(format!("Expected 42, got {}", value));
        }
        Err("Value not found".to_string())
    }));
    
    // Test 14: Typed value parsing - String
    results.push(test_runner("Typed value parsing - String", || {
        let app = Command::new("test")
            .arg(Arg::new("name")
                .long("name")
                .takes_value(true));
        
        let matches = app.try_get_matches_from(&["test", "--name", "Alice"])
            .map_err(|e| e.to_string())?;
        
        if let Some(value) = matches.get_one::<String>("name") {
            if value == "Alice" {
                return Ok(());
            }
            return Err(format!("Expected 'Alice', got '{}'", value));
        }
        Err("Value not found".to_string())
    }));
    
    // Test 15: is_present for value arguments
    results.push(test_runner("is_present for value arguments", || {
        let app = Command::new("test")
            .arg(Arg::new("input")
                .long("input")
                .takes_value(true));
        
        let matches = app.try_get_matches_from(&["test", "--input", "file.txt"])
            .map_err(|e| e.to_string())?;
        
        if matches.is_present("input") {
            Ok(())
        } else {
            Err("Argument not present".to_string())
        }
    }));
    
    // Test 16: Long and short options together
    results.push(test_runner("Long and short options together", || {
        let app = Command::new("test")
            .arg(Arg::new("verbose")
                .long("verbose")
                .short('v'));
        
        let matches1 = app.clone().try_get_matches_from(&["test", "--verbose"])
            .map_err(|e| e.to_string())?;
        let matches2 = Command::new("test")
            .arg(Arg::new("verbose")
                .long("verbose")
                .short('v'))
            .try_get_matches_from(&["test", "-v"])
            .map_err(|e| e.to_string())?;
        
        if matches1.is_present("verbose") && matches2.is_present("verbose") {
            Ok(())
        } else {
            Err("Flags not recognized correctly".to_string())
        }
    }));
    
    // Test 17: No arguments provided
    results.push(test_runner("No arguments provided", || {
        let app = Command::new("test")
            .arg(Arg::new("verbose").long("verbose"));
        
        let matches = app.try_get_matches_from(&["test"])
            .map_err(|e| e.to_string())?;
        
        if !matches.is_present("verbose") {
            Ok(())
        } else {
            Err("Flag should not be present".to_string())
        }
    }));
    
    // Test 18: value_of returns None for missing argument
    results.push(test_runner("value_of returns None", || {
        let app = Command::new("test")
            .arg(Arg::new("config")
                .long("config")
                .takes_value(true));
        
        let matches = app.try_get_matches_from(&["test"])
            .map_err(|e| e.to_string())?;
        
        if matches.value_of("config").is_none() {
            Ok(())
        } else {
            Err("value_of should return None".to_string())
        }
    }));
    
    // Test 19: Multiple arguments with values
    results.push(test_runner("Multiple arguments with values", || {
        let app = Command::new("test")
            .arg(Arg::new("input")
                .long("input")
                .takes_value(true))
            .arg(Arg::new("output")
                .long("output")
                .takes_value(true));
        
        let matches = app.try_get_matches_from(&["test", "--input", "in.txt", "--output", "out.txt"])
            .map_err(|e| e.to_string())?;
        
        if matches.value_of("input") == Some("in.txt") && matches.value_of("output") == Some("out.txt") {
            Ok(())
        } else {
            Err("Arguments not parsed correctly".to_string())
        }
    }));
    
    // Test 20: Arg with help text
    results.push(test_runner("Arg with help text", || {
        let _app = Command::new("test")
            .arg(Arg::new("verbose")
                .long("verbose")
                .help("Enable verbose output"));
        Ok(())
    }));
    
    // Print results
    println!("\n=== Test Results ===");
    let mut passed = 0;
    for result in &results {
        if result.passed {
            println!("✓ {}", result.name);
            passed += 1;
        } else {
            println!("✗ {}: {}", result.name, result.error.as_ref().unwrap());
        }
    }
    
    println!("\nPassed: {}/{}", passed, results.len());
}
