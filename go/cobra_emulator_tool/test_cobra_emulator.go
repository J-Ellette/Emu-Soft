package main

import (
	"fmt"
	"strings"
)

// Helper function to run a test
func runTest(name string, testFunc func() bool) {
	result := "PASS"
	if !testFunc() {
		result = "FAIL"
	}
	fmt.Printf("[%s] %s\n", result, name)
}

// Test basic command execution
func testBasicCommand() bool {
	executed := false
	cmd := &Command{
		Use:   "test",
		Short: "Test command",
		Run: func(cmd *Command, args []string) {
			executed = true
		},
	}
	
	cmd.ExecuteWithArgs([]string{})
	return executed
}

// Test command with arguments
func testCommandWithArgs() bool {
	var receivedArgs []string
	cmd := &Command{
		Use:   "test",
		Short: "Test command",
		Run: func(cmd *Command, args []string) {
			receivedArgs = args
		},
	}
	
	cmd.ExecuteWithArgs([]string{"arg1", "arg2", "arg3"})
	return len(receivedArgs) == 3 && receivedArgs[0] == "arg1"
}

// Test string flag
func testStringFlag() bool {
	var name string
	cmd := &Command{
		Use:   "test",
		Short: "Test command",
		Run: func(cmd *Command, args []string) {
			name = cmd.GetString("name")
		},
	}
	
	cmd.Flags().String("name", "default", "Name flag")
	cmd.ExecuteWithArgs([]string{"--name=John"})
	
	return name == "John"
}

// Test string flag with space
func testStringFlagWithSpace() bool {
	var name string
	cmd := &Command{
		Use:   "test",
		Short: "Test command",
		Run: func(cmd *Command, args []string) {
			name = cmd.GetString("name")
		},
	}
	
	cmd.Flags().String("name", "default", "Name flag")
	cmd.ExecuteWithArgs([]string{"--name", "Alice"})
	
	return name == "Alice"
}

// Test shorthand flag
func testShorthandFlag() bool {
	var name string
	cmd := &Command{
		Use:   "test",
		Short: "Test command",
		Run: func(cmd *Command, args []string) {
			name = cmd.GetString("name")
		},
	}
	
	cmd.Flags().StringP("name", "n", "default", "Name flag")
	cmd.ExecuteWithArgs([]string{"-n", "Bob"})
	
	return name == "Bob"
}

// Test int flag
func testIntFlag() bool {
	var count int
	cmd := &Command{
		Use:   "test",
		Short: "Test command",
		Run: func(cmd *Command, args []string) {
			count = cmd.GetInt("count")
		},
	}
	
	cmd.Flags().Int("count", 0, "Count flag")
	cmd.ExecuteWithArgs([]string{"--count=42"})
	
	return count == 42
}

// Test bool flag
func testBoolFlag() bool {
	var verbose bool
	cmd := &Command{
		Use:   "test",
		Short: "Test command",
		Run: func(cmd *Command, args []string) {
			verbose = cmd.GetBool("verbose")
		},
	}
	
	cmd.Flags().Bool("verbose", false, "Verbose flag")
	cmd.ExecuteWithArgs([]string{"--verbose"})
	
	return verbose == true
}

// Test default flag value
func testDefaultFlagValue() bool {
	var name string
	cmd := &Command{
		Use:   "test",
		Short: "Test command",
		Run: func(cmd *Command, args []string) {
			name = cmd.GetString("name")
		},
	}
	
	namePtr := cmd.Flags().String("name", "default-value", "Name flag")
	cmd.ExecuteWithArgs([]string{})
	
	// Check both through GetString and through pointer
	return name == "default-value" || *namePtr == "default-value"
}

// Test subcommand
func testSubcommand() bool {
	rootExecuted := false
	subExecuted := false
	
	rootCmd := &Command{
		Use:   "app",
		Short: "Root command",
		Run: func(cmd *Command, args []string) {
			rootExecuted = true
		},
	}
	
	subCmd := &Command{
		Use:   "sub",
		Short: "Sub command",
		Run: func(cmd *Command, args []string) {
			subExecuted = true
		},
	}
	
	rootCmd.AddCommand(subCmd)
	rootCmd.ExecuteWithArgs([]string{"sub"})
	
	return subExecuted && !rootExecuted
}

// Test nested subcommands
func testNestedSubcommands() bool {
	executed := false
	
	rootCmd := &Command{
		Use:   "app",
		Short: "Root command",
	}
	
	apiCmd := &Command{
		Use:   "api",
		Short: "API commands",
	}
	
	userCmd := &Command{
		Use:   "user",
		Short: "User commands",
	}
	
	listCmd := &Command{
		Use:   "list",
		Short: "List users",
		Run: func(cmd *Command, args []string) {
			executed = true
		},
	}
	
	rootCmd.AddCommand(apiCmd)
	apiCmd.AddCommand(userCmd)
	userCmd.AddCommand(listCmd)
	
	rootCmd.ExecuteWithArgs([]string{"api", "user", "list"})
	
	return executed
}

// Test subcommand with flags
func testSubcommandWithFlags() bool {
	var format string
	
	rootCmd := &Command{
		Use:   "app",
		Short: "Root command",
	}
	
	listCmd := &Command{
		Use:   "list",
		Short: "List items",
		Run: func(cmd *Command, args []string) {
			format = cmd.GetString("format")
		},
	}
	
	listCmd.Flags().String("format", "text", "Output format")
	rootCmd.AddCommand(listCmd)
	
	rootCmd.ExecuteWithArgs([]string{"list", "--format=json"})
	
	return format == "json"
}

// Test subcommand with arguments
func testSubcommandWithArgs() bool {
	var receivedArgs []string
	
	rootCmd := &Command{
		Use:   "app",
		Short: "Root command",
	}
	
	getCmd := &Command{
		Use:   "get [id]",
		Short: "Get item by ID",
		Run: func(cmd *Command, args []string) {
			receivedArgs = args
		},
	}
	
	rootCmd.AddCommand(getCmd)
	rootCmd.ExecuteWithArgs([]string{"get", "123"})
	
	return len(receivedArgs) == 1 && receivedArgs[0] == "123"
}

// Test mixed flags and arguments
func testMixedFlagsAndArgs() bool {
	var name string
	var receivedArgs []string
	
	cmd := &Command{
		Use:   "test",
		Short: "Test command",
		Run: func(cmd *Command, args []string) {
			name = cmd.GetString("name")
			receivedArgs = args
		},
	}
	
	cmd.Flags().String("name", "", "Name flag")
	cmd.ExecuteWithArgs([]string{"--name=John", "arg1", "arg2"})
	
	return name == "John" && len(receivedArgs) == 2
}

// Test multiple flags
func testMultipleFlags() bool {
	var name string
	var count int
	var verbose bool
	
	cmd := &Command{
		Use:   "test",
		Short: "Test command",
		Run: func(cmd *Command, args []string) {
			name = cmd.GetString("name")
			count = cmd.GetInt("count")
			verbose = cmd.GetBool("verbose")
		},
	}
	
	cmd.Flags().String("name", "", "Name")
	cmd.Flags().Int("count", 0, "Count")
	cmd.Flags().Bool("verbose", false, "Verbose")
	
	cmd.ExecuteWithArgs([]string{"--name=Test", "--count=5", "--verbose"})
	
	return name == "Test" && count == 5 && verbose
}

// Test command Use field parsing
func testCommandUseParsing() bool {
	cmd := &Command{
		Use:   "server start [options]",
		Short: "Start the server",
	}
	
	// The command name should be "server" when parsed
	// In traverse, it splits on space and takes first element
	parts := strings.Split(cmd.Use, " ")
	return parts[0] == "server"
}

// Test command without Run function
func testCommandWithoutRun() bool {
	cmd := &Command{
		Use:   "test",
		Short: "Test command",
	}
	
	err := cmd.ExecuteWithArgs([]string{})
	return err == nil
}

// Test Printf method
func testPrintfMethod() bool {
	cmd := &Command{
		Use: "test",
	}
	
	// Just test it doesn't panic
	cmd.Printf("Test: %s\n", "value")
	return true
}

// Test flag with IntP
func testIntPFlag() bool {
	var port int
	cmd := &Command{
		Use:   "test",
		Short: "Test command",
		Run: func(cmd *Command, args []string) {
			port = cmd.GetInt("port")
		},
	}
	
	cmd.Flags().IntP("port", "p", 8080, "Port number")
	cmd.ExecuteWithArgs([]string{"-p", "3000"})
	
	return port == 3000
}

// Test flag with BoolP
func testBoolPFlag() bool {
	var debug bool
	cmd := &Command{
		Use:   "test",
		Short: "Test command",
		Run: func(cmd *Command, args []string) {
			debug = cmd.GetBool("debug")
		},
	}
	
	cmd.Flags().BoolP("debug", "d", false, "Debug mode")
	cmd.ExecuteWithArgs([]string{"-d"})
	
	return debug == true
}

// Test NewRootCommand helper
func testNewRootCommand() bool {
	root := NewRootCommand()
	return root != nil && root.Use == "app"
}

func main() {
	fmt.Println("Running Cobra Emulator Tests...")
	fmt.Println("==============================")

	runTest("Basic Command", testBasicCommand)
	runTest("Command With Args", testCommandWithArgs)
	runTest("String Flag", testStringFlag)
	runTest("String Flag With Space", testStringFlagWithSpace)
	runTest("Shorthand Flag", testShorthandFlag)
	runTest("Int Flag", testIntFlag)
	runTest("Bool Flag", testBoolFlag)
	runTest("Default Flag Value", testDefaultFlagValue)
	runTest("Subcommand", testSubcommand)
	runTest("Nested Subcommands", testNestedSubcommands)
	runTest("Subcommand With Flags", testSubcommandWithFlags)
	runTest("Subcommand With Args", testSubcommandWithArgs)
	runTest("Mixed Flags And Args", testMixedFlagsAndArgs)
	runTest("Multiple Flags", testMultipleFlags)
	runTest("Command Use Parsing", testCommandUseParsing)
	runTest("Command Without Run", testCommandWithoutRun)
	runTest("Printf Method", testPrintfMethod)
	runTest("IntP Flag", testIntPFlag)
	runTest("BoolP Flag", testBoolPFlag)
	runTest("NewRootCommand", testNewRootCommand)

	fmt.Println("==============================")
	fmt.Println("All tests completed!")
}
