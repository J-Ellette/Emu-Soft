use std::collections::HashMap;

// Command represents a CLI command
pub struct Command {
    name: String,
    about: Option<String>,
    version: Option<String>,
    author: Option<String>,
    args: Vec<Arg>,
    subcommands: Vec<Command>,
}

impl Command {
    pub fn new(name: &str) -> Self {
        Command {
            name: name.to_string(),
            about: None,
            version: None,
            author: None,
            args: Vec::new(),
            subcommands: Vec::new(),
        }
    }
    
    pub fn about(mut self, about: &str) -> Self {
        self.about = Some(about.to_string());
        self
    }
    
    pub fn version(mut self, version: &str) -> Self {
        self.version = Some(version.to_string());
        self
    }
    
    pub fn author(mut self, author: &str) -> Self {
        self.author = Some(author.to_string());
        self
    }
    
    pub fn arg(mut self, arg: Arg) -> Self {
        self.args.push(arg);
        self
    }
    
    pub fn subcommand(mut self, cmd: Command) -> Self {
        self.subcommands.push(cmd);
        self
    }
    
    pub fn get_matches(self) -> ArgMatches {
        let args: Vec<String> = std::env::args().collect();
        self.parse_args(&args[1..])
    }
    
    pub fn try_get_matches_from(self, args: &[&str]) -> Result<ArgMatches, String> {
        let string_args: Vec<String> = args.iter().map(|s| s.to_string()).collect();
        Ok(self.parse_args(&string_args))
    }
    
    fn parse_args(self, args: &[String]) -> ArgMatches {
        let mut matches = ArgMatches::new();
        let mut i = 0;
        
        while i < args.len() {
            let arg = &args[i];
            
            // Check for subcommand
            if let Some(subcmd) = self.subcommands.iter().find(|c| c.name == *arg) {
                let subcmd_args = &args[i+1..];
                matches.subcommand = Some((
                    subcmd.name.clone(),
                    Box::new(subcmd.clone().parse_args(subcmd_args)),
                ));
                break;
            }
            
            // Check if it's a flag (starts with --)
            if arg.starts_with("--") {
                let flag_name = &arg[2..];
                
                // Find the argument definition
                if let Some(arg_def) = self.args.iter().find(|a| a.long == Some(flag_name.to_string())) {
                    if arg_def.takes_value {
                        i += 1;
                        if i < args.len() {
                            matches.values.insert(arg_def.id.clone(), args[i].clone());
                        }
                    } else {
                        matches.flags.insert(arg_def.id.clone());
                    }
                }
            } 
            // Check if it's a short flag (starts with -)
            else if arg.starts_with("-") && arg.len() == 2 {
                let flag_char = arg.chars().nth(1).unwrap();
                
                // Find the argument definition
                if let Some(arg_def) = self.args.iter().find(|a| a.short == Some(flag_char)) {
                    if arg_def.takes_value {
                        i += 1;
                        if i < args.len() {
                            matches.values.insert(arg_def.id.clone(), args[i].clone());
                        }
                    } else {
                        matches.flags.insert(arg_def.id.clone());
                    }
                }
            }
            // It's a positional argument
            else {
                matches.positional.push(arg.clone());
            }
            
            i += 1;
        }
        
        // Fill in default values
        for arg_def in &self.args {
            if !matches.values.contains_key(&arg_def.id) {
                if let Some(ref default) = arg_def.default_value {
                    matches.values.insert(arg_def.id.clone(), default.clone());
                }
            }
        }
        
        matches
    }
}

impl Clone for Command {
    fn clone(&self) -> Self {
        Command {
            name: self.name.clone(),
            about: self.about.clone(),
            version: self.version.clone(),
            author: self.author.clone(),
            args: self.args.clone(),
            subcommands: self.subcommands.clone(),
        }
    }
}

// Arg represents a command-line argument
#[derive(Clone)]
pub struct Arg {
    id: String,
    long: Option<String>,
    short: Option<char>,
    help: Option<String>,
    takes_value: bool,
    required: bool,
    default_value: Option<String>,
}

impl Arg {
    pub fn new(id: &str) -> Self {
        Arg {
            id: id.to_string(),
            long: None,
            short: None,
            help: None,
            takes_value: false,
            required: false,
            default_value: None,
        }
    }
    
    pub fn long(mut self, name: &str) -> Self {
        self.long = Some(name.to_string());
        self
    }
    
    pub fn short(mut self, c: char) -> Self {
        self.short = Some(c);
        self
    }
    
    pub fn help(mut self, help: &str) -> Self {
        self.help = Some(help.to_string());
        self
    }
    
    pub fn takes_value(mut self, takes: bool) -> Self {
        self.takes_value = takes;
        self
    }
    
    pub fn required(mut self, required: bool) -> Self {
        self.required = required;
        self
    }
    
    pub fn default_value(mut self, value: &str) -> Self {
        self.default_value = Some(value.to_string());
        self
    }
}

// ArgMatches holds parsed arguments
pub struct ArgMatches {
    values: HashMap<String, String>,
    flags: std::collections::HashSet<String>,
    positional: Vec<String>,
    subcommand: Option<(String, Box<ArgMatches>)>,
}

impl ArgMatches {
    fn new() -> Self {
        ArgMatches {
            values: HashMap::new(),
            flags: std::collections::HashSet::new(),
            positional: Vec::new(),
            subcommand: None,
        }
    }
    
    pub fn get_one<T: std::str::FromStr>(&self, id: &str) -> Option<T> {
        self.values.get(id).and_then(|v| v.parse().ok())
    }
    
    pub fn value_of(&self, id: &str) -> Option<&str> {
        self.values.get(id).map(|s| s.as_str())
    }
    
    pub fn is_present(&self, id: &str) -> bool {
        self.flags.contains(id) || self.values.contains_key(id)
    }
    
    pub fn get_flag(&self, id: &str) -> bool {
        self.flags.contains(id)
    }
    
    pub fn subcommand(&self) -> Option<(&str, &ArgMatches)> {
        self.subcommand.as_ref().map(|(name, matches)| (name.as_str(), matches.as_ref()))
    }
    
    pub fn subcommand_name(&self) -> Option<&str> {
        self.subcommand.as_ref().map(|(name, _)| name.as_str())
    }
    
    pub fn get_positional(&self, index: usize) -> Option<&str> {
        self.positional.get(index).map(|s| s.as_str())
    }
}

fn main() {
    println!("Clap Emulator - CLI Argument Parser");
    println!("====================================\n");
    
    // Example 1: Simple command with flags
    println!("=== Example 1: Simple Command ===");
    let app = Command::new("myapp")
        .about("A simple CLI application")
        .version("1.0.0")
        .author("John Doe")
        .arg(Arg::new("verbose")
            .long("verbose")
            .short('v')
            .help("Enable verbose output"))
        .arg(Arg::new("config")
            .long("config")
            .short('c')
            .takes_value(true)
            .help("Configuration file"));
    
    let matches = app.try_get_matches_from(&["myapp", "--verbose", "--config", "config.toml"]).unwrap();
    println!("Verbose: {}", matches.get_flag("verbose"));
    println!("Config: {}", matches.value_of("config").unwrap_or("none"));
    println!();
    
    // Example 2: Required arguments
    println!("=== Example 2: Required Arguments ===");
    let app = Command::new("copy")
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
            .help("Output file"));
    
    let matches = app.try_get_matches_from(&["copy", "-i", "input.txt", "-o", "output.txt"]).unwrap();
    println!("Input: {}", matches.value_of("input").unwrap());
    println!("Output: {}", matches.value_of("output").unwrap());
    println!();
    
    // Example 3: Default values
    println!("=== Example 3: Default Values ===");
    let app = Command::new("server")
        .arg(Arg::new("port")
            .long("port")
            .short('p')
            .takes_value(true)
            .default_value("8080")
            .help("Port to listen on"))
        .arg(Arg::new("host")
            .long("host")
            .short('h')
            .takes_value(true)
            .default_value("localhost")
            .help("Host to bind to"));
    
    let matches = app.try_get_matches_from(&["server"]).unwrap();
    println!("Port: {}", matches.value_of("port").unwrap());
    println!("Host: {}", matches.value_of("host").unwrap());
    println!();
    
    // Example 4: Subcommands
    println!("=== Example 4: Subcommands ===");
    let app = Command::new("git")
        .about("A version control system")
        .subcommand(
            Command::new("add")
                .about("Add files to staging")
                .arg(Arg::new("all")
                    .long("all")
                    .short('A')
                    .help("Add all files"))
        )
        .subcommand(
            Command::new("commit")
                .about("Commit changes")
                .arg(Arg::new("message")
                    .long("message")
                    .short('m')
                    .takes_value(true)
                    .help("Commit message"))
        );
    
    let matches = app.try_get_matches_from(&["git", "commit", "-m", "Initial commit"]).unwrap();
    if let Some((name, sub_m)) = matches.subcommand() {
        println!("Subcommand: {}", name);
        if let Some(msg) = sub_m.value_of("message") {
            println!("Message: {}", msg);
        }
    }
    println!();
    
    // Example 5: Typed value parsing
    println!("=== Example 5: Typed Values ===");
    let app = Command::new("calculator")
        .arg(Arg::new("number")
            .long("number")
            .short('n')
            .takes_value(true)
            .help("A number to process"));
    
    let matches = app.try_get_matches_from(&["calculator", "-n", "42"]).unwrap();
    if let Some(num) = matches.get_one::<i32>("number") {
        println!("Number: {}", num);
        println!("Doubled: {}", num * 2);
    }
    println!();
    
    println!("✓ Clap emulator demonstration complete");
}
