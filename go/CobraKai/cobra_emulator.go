package main

// Developed by PowerShield, as an alternative to Cobra
import (
	"fmt"
	"os"
	"strings"
)

// Command represents a CLI command
type Command struct {
	Use   string
	Short string
	Long  string
	Run   func(cmd *Command, args []string)
	
	commands    []*Command
	parent      *Command
	flags       map[string]*Flag
	args        []string
	parsedArgs  []string
}

// Flag represents a command-line flag
type Flag struct {
	Name      string
	Shorthand string
	Usage     string
	Value     interface{}
	DefValue  interface{}
	Changed   bool
}

// Execute runs the root command
func (c *Command) Execute() error {
	return c.ExecuteWithArgs(os.Args[1:])
}

// ExecuteWithArgs runs the command with provided arguments (for testing)
func (c *Command) ExecuteWithArgs(args []string) error {
	// Parse the command tree
	cmd, cmdArgs, err := c.traverse(args)
	if err != nil {
		return err
	}
	
	// Parse flags
	err = cmd.parseFlags(cmdArgs)
	if err != nil {
		return err
	}
	
	// Store remaining args
	cmd.args = cmd.parsedArgs
	
	// Run the command
	if cmd.Run != nil {
		cmd.Run(cmd, cmd.args)
	}
	
	return nil
}

// traverse finds the appropriate command to execute
func (c *Command) traverse(args []string) (*Command, []string, error) {
	if len(args) == 0 {
		return c, args, nil
	}
	
	// Check if the first arg is a subcommand
	for _, subcmd := range c.commands {
		cmdName := strings.Split(subcmd.Use, " ")[0]
		if args[0] == cmdName {
			return subcmd.traverse(args[1:])
		}
	}
	
	// No subcommand found, this command should handle it
	return c, args, nil
}

// parseFlags parses command-line flags
func (c *Command) parseFlags(args []string) error {
	var parsedArgs []string
	
	for i := 0; i < len(args); i++ {
		arg := args[i]
		
		// Check if it's a flag
		if strings.HasPrefix(arg, "--") {
			// Long flag
			flagName := arg[2:]
			parts := strings.SplitN(flagName, "=", 2)
			flagName = parts[0]
			
			if flag, exists := c.flags[flagName]; exists {
				if len(parts) == 2 {
					// Value provided with =
					flag.Value = parts[1]
				} else if i+1 < len(args) && !strings.HasPrefix(args[i+1], "-") {
					// Value in next arg
					i++
					flag.Value = args[i]
				} else {
					// Boolean flag
					flag.Value = "true"
				}
				flag.Changed = true
			}
		} else if strings.HasPrefix(arg, "-") && len(arg) == 2 {
			// Short flag
			shorthand := arg[1:2]
			
			// Find flag by shorthand
			for _, flag := range c.flags {
				if flag.Shorthand == shorthand {
					if i+1 < len(args) && !strings.HasPrefix(args[i+1], "-") {
						i++
						flag.Value = args[i]
					} else {
						flag.Value = "true"
					}
					flag.Changed = true
					break
				}
			}
		} else {
			// Regular argument
			parsedArgs = append(parsedArgs, arg)
		}
	}
	
	c.parsedArgs = parsedArgs
	return nil
}

// AddCommand adds a subcommand
func (c *Command) AddCommand(commands ...*Command) {
	for _, cmd := range commands {
		cmd.parent = c
		c.commands = append(c.commands, cmd)
	}
}

// Flags returns a FlagSet for defining flags
func (c *Command) Flags() *FlagSet {
	if c.flags == nil {
		c.flags = make(map[string]*Flag)
	}
	return &FlagSet{cmd: c}
}

// PersistentFlags returns flags that persist to subcommands
func (c *Command) PersistentFlags() *FlagSet {
	// In this simplified version, we'll treat them the same
	return c.Flags()
}

// FlagSet represents a set of flags
type FlagSet struct {
	cmd *Command
}

// StringP adds a string flag with shorthand
func (fs *FlagSet) StringP(name, shorthand string, value string, usage string) *string {
	result := value
	flag := &Flag{
		Name:      name,
		Shorthand: shorthand,
		Usage:     usage,
		Value:     &result,
		DefValue:  value,
	}
	fs.cmd.flags[name] = flag
	return &result
}

// String adds a string flag
func (fs *FlagSet) String(name string, value string, usage string) *string {
	return fs.StringP(name, "", value, usage)
}

// IntP adds an int flag with shorthand
func (fs *FlagSet) IntP(name, shorthand string, value int, usage string) *int {
	result := value
	flag := &Flag{
		Name:      name,
		Shorthand: shorthand,
		Usage:     usage,
		Value:     &result,
		DefValue:  value,
	}
	fs.cmd.flags[name] = flag
	return &result
}

// Int adds an int flag
func (fs *FlagSet) Int(name string, value int, usage string) *int {
	return fs.IntP(name, "", value, usage)
}

// BoolP adds a boolean flag with shorthand
func (fs *FlagSet) BoolP(name, shorthand string, value bool, usage string) *bool {
	result := value
	flag := &Flag{
		Name:      name,
		Shorthand: shorthand,
		Usage:     usage,
		Value:     &result,
		DefValue:  value,
	}
	fs.cmd.flags[name] = flag
	return &result
}

// Bool adds a boolean flag
func (fs *FlagSet) Bool(name string, value bool, usage string) *bool {
	return fs.BoolP(name, "", value, usage)
}

// GetString gets a string flag value
func (c *Command) GetString(name string) string {
	if flag, exists := c.flags[name]; exists {
		if str, ok := flag.Value.(*string); ok {
			return *str
		}
		if str, ok := flag.Value.(string); ok {
			return str
		}
	}
	return ""
}

// GetInt gets an int flag value
// Note: String to int conversion errors are silently ignored, returning 0
func (c *Command) GetInt(name string) int {
	if flag, exists := c.flags[name]; exists {
		if i, ok := flag.Value.(*int); ok {
			return *i
		}
		if str, ok := flag.Value.(string); ok {
			// Try to parse string as int
			var result int
			fmt.Sscanf(str, "%d", &result) // Parse errors return 0
			return result
		}
	}
	return 0
}

// GetBool gets a boolean flag value
func (c *Command) GetBool(name string) bool {
	if flag, exists := c.flags[name]; exists {
		if b, ok := flag.Value.(*bool); ok {
			return *b
		}
		if str, ok := flag.Value.(string); ok {
			return str == "true"
		}
	}
	return false
}

// Printf prints formatted output
func (c *Command) Printf(format string, args ...interface{}) {
	fmt.Printf(format, args...)
}

// Println prints a line
func (c *Command) Println(args ...interface{}) {
	fmt.Println(args...)
}

// Print prints output
func (c *Command) Print(args ...interface{}) {
	fmt.Print(args...)
}

// SetArgs sets arguments for the command (for testing)
func (c *Command) SetArgs(args []string) {
	c.args = args
}

// Args returns the non-flag arguments
func (c *Command) Args() []string {
	return c.args
}

// Help displays help information
func (c *Command) Help() error {
	fmt.Printf("%s\n\n", c.Long)
	if c.Short != "" {
		fmt.Printf("%s\n\n", c.Short)
	}
	fmt.Printf("Usage:\n  %s\n\n", c.Use)
	
	if len(c.commands) > 0 {
		fmt.Println("Available Commands:")
		for _, cmd := range c.commands {
			cmdName := strings.Split(cmd.Use, " ")[0]
			fmt.Printf("  %-12s %s\n", cmdName, cmd.Short)
		}
		fmt.Println()
	}
	
	if len(c.flags) > 0 {
		fmt.Println("Flags:")
		for _, flag := range c.flags {
			shorthand := ""
			if flag.Shorthand != "" {
				shorthand = fmt.Sprintf("-%s, ", flag.Shorthand)
			}
			fmt.Printf("  %s--%s\t%s\n", shorthand, flag.Name, flag.Usage)
		}
		fmt.Println()
	}
	
	return nil
}

// Root command helper
func NewRootCommand() *Command {
	return &Command{
		Use:   "app",
		Short: "Application CLI",
		Long:  "A CLI application built with Cobra emulator",
	}
}
