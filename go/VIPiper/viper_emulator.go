package main

// Developed by PowerShield, as an alternative to Viper
import (
	"encoding/json"
	"fmt"
	"os"
)

// Viper is the main configuration manager
type Viper struct {
	config    map[string]interface{}
	defaults  map[string]interface{}
	env       map[string]string
	configFile string
	configType string
}

// New creates a new Viper instance
func New() *Viper {
	return &Viper{
		config:   make(map[string]interface{}),
		defaults: make(map[string]interface{}),
		env:      make(map[string]string),
	}
}

// Global viper instance for convenience functions
var globalViper = New()

// Set sets a configuration value
func (v *Viper) Set(key string, value interface{}) {
	v.config[key] = value
}

// Get retrieves a configuration value
func (v *Viper) Get(key string) interface{} {
	// Check environment variables first (highest priority)
	if envKey, ok := v.env[key]; ok {
		if envVal := os.Getenv(envKey); envVal != "" {
			return envVal
		}
	}
	
	// Check config
	if val, ok := v.config[key]; ok {
		return val
	}
	
	// Check defaults
	if val, ok := v.defaults[key]; ok {
		return val
	}
	
	return nil
}

// GetString gets a string configuration value
func (v *Viper) GetString(key string) string {
	val := v.Get(key)
	if val == nil {
		return ""
	}
	if str, ok := val.(string); ok {
		return str
	}
	return fmt.Sprintf("%v", val)
}

// GetInt gets an integer configuration value
// Note: String to int conversion errors are silently ignored, returning 0
func (v *Viper) GetInt(key string) int {
	val := v.Get(key)
	if val == nil {
		return 0
	}
	
	switch v := val.(type) {
	case int:
		return v
	case float64:
		return int(v)
	case string:
		var result int
		fmt.Sscanf(v, "%d", &result) // Parse errors return 0
		return result
	default:
		return 0
	}
}

// GetBool gets a boolean configuration value
func (v *Viper) GetBool(key string) bool {
	val := v.Get(key)
	if val == nil {
		return false
	}
	
	switch v := val.(type) {
	case bool:
		return v
	case string:
		return v == "true" || v == "1" || v == "yes"
	default:
		return false
	}
}

// GetFloat64 gets a float64 configuration value
// Note: String to float conversion errors are silently ignored, returning 0.0
func (v *Viper) GetFloat64(key string) float64 {
	val := v.Get(key)
	if val == nil {
		return 0.0
	}
	
	switch v := val.(type) {
	case float64:
		return v
	case int:
		return float64(v)
	case string:
		var result float64
		fmt.Sscanf(v, "%f", &result) // Parse errors return 0.0
		return result
	default:
		return 0.0
	}
}

// GetStringSlice gets a string slice configuration value
func (v *Viper) GetStringSlice(key string) []string {
	val := v.Get(key)
	if val == nil {
		return []string{}
	}
	
	if slice, ok := val.([]string); ok {
		return slice
	}
	
	if slice, ok := val.([]interface{}); ok {
		result := make([]string, len(slice))
		for i, item := range slice {
			result[i] = fmt.Sprintf("%v", item)
		}
		return result
	}
	
	return []string{}
}

// GetStringMap gets a string map configuration value
func (v *Viper) GetStringMap(key string) map[string]interface{} {
	val := v.Get(key)
	if val == nil {
		return make(map[string]interface{})
	}
	
	if m, ok := val.(map[string]interface{}); ok {
		return m
	}
	
	return make(map[string]interface{})
}

// SetDefault sets a default value
func (v *Viper) SetDefault(key string, value interface{}) {
	v.defaults[key] = value
}

// BindEnv binds a configuration key to an environment variable
func (v *Viper) BindEnv(key string, envVars ...string) error {
	envKey := key
	if len(envVars) > 0 {
		envKey = envVars[0]
	}
	v.env[key] = envKey
	return nil
}

// SetEnvPrefix sets a prefix for environment variables
// In this simplified emulator, the prefix is not used in automatic binding
func (v *Viper) SetEnvPrefix(prefix string) {
	// Simplified: In a full implementation, this would affect automatic environment variable binding
	// For this emulator, use explicit BindEnv() calls instead
}

// AutomaticEnv enables automatic environment variable binding
// In this simplified emulator, use explicit BindEnv() calls for environment variable binding
func (v *Viper) AutomaticEnv() {
	// Simplified: In a full implementation, this would automatically bind all config keys to environment variables
	// For this emulator, use explicit BindEnv() for specific keys instead
}

// SetConfigFile sets the configuration file path
func (v *Viper) SetConfigFile(in string) {
	v.configFile = in
}

// SetConfigName sets the configuration file name (without extension)
func (v *Viper) SetConfigName(in string) {
	v.configFile = in
}

// SetConfigType sets the configuration file type
func (v *Viper) SetConfigType(in string) {
	v.configType = in
}

// AddConfigPath adds a path to search for config files
func (v *Viper) AddConfigPath(in string) {
	// In a full implementation, this would add to a list of search paths
}

// ReadInConfig reads the configuration file
func (v *Viper) ReadInConfig() error {
	if v.configFile == "" {
		return fmt.Errorf("config file not set")
	}
	
	data, err := os.ReadFile(v.configFile)
	if err != nil {
		return err
	}
	
	// Parse based on config type
	switch v.configType {
	case "json":
		return v.readJSON(data)
	default:
		// Try JSON as default
		return v.readJSON(data)
	}
}

// readJSON reads JSON configuration
func (v *Viper) readJSON(data []byte) error {
	var config map[string]interface{}
	err := json.Unmarshal(data, &config)
	if err != nil {
		return err
	}
	
	// Merge with existing config
	for k, val := range config {
		v.config[k] = val
	}
	
	return nil
}

// WriteConfig writes the current configuration to file
func (v *Viper) WriteConfig() error {
	return v.WriteConfigAs(v.configFile)
}

// WriteConfigAs writes the configuration to a specific file
func (v *Viper) WriteConfigAs(filename string) error {
	data, err := json.MarshalIndent(v.config, "", "  ")
	if err != nil {
		return err
	}
	
	return os.WriteFile(filename, data, 0644)
}

// SafeWriteConfig writes config if file doesn't exist
func (v *Viper) SafeWriteConfig() error {
	if _, err := os.Stat(v.configFile); err == nil {
		return fmt.Errorf("config file already exists")
	}
	return v.WriteConfig()
}

// IsSet checks if a key is set
func (v *Viper) IsSet(key string) bool {
	return v.Get(key) != nil
}

// AllKeys returns all keys in the config
func (v *Viper) AllKeys() []string {
	keys := make(map[string]bool)
	
	for k := range v.config {
		keys[k] = true
	}
	for k := range v.defaults {
		keys[k] = true
	}
	
	result := make([]string, 0, len(keys))
	for k := range keys {
		result = append(result, k)
	}
	
	return result
}

// AllSettings returns all settings as a map
func (v *Viper) AllSettings() map[string]interface{} {
	result := make(map[string]interface{})
	
	// Copy defaults first
	for k, v := range v.defaults {
		result[k] = v
	}
	
	// Override with config
	for k, v := range v.config {
		result[k] = v
	}
	
	return result
}

// Sub returns a sub-configuration
func (v *Viper) Sub(key string) *Viper {
	val := v.Get(key)
	if val == nil {
		return nil
	}
	
	if m, ok := val.(map[string]interface{}); ok {
		sub := New()
		sub.config = m
		return sub
	}
	
	return nil
}

// Unmarshal unmarshals config into a struct
func (v *Viper) Unmarshal(rawVal interface{}) error {
	// Convert config to JSON and back to unmarshal into struct
	data, err := json.Marshal(v.AllSettings())
	if err != nil {
		return err
	}
	
	return json.Unmarshal(data, rawVal)
}

// UnmarshalKey unmarshals a specific key into a struct
func (v *Viper) UnmarshalKey(key string, rawVal interface{}) error {
	val := v.Get(key)
	if val == nil {
		return fmt.Errorf("key not found: %s", key)
	}
	
	data, err := json.Marshal(val)
	if err != nil {
		return err
	}
	
	return json.Unmarshal(data, rawVal)
}

// Reset clears all configuration
func (v *Viper) Reset() {
	v.config = make(map[string]interface{})
	v.defaults = make(map[string]interface{})
	v.env = make(map[string]string)
	v.configFile = ""
	v.configType = ""
}

// GetViper returns the global viper instance
func GetViper() *Viper {
	return globalViper
}

// Convenience functions using the global instance

func Set(key string, value interface{}) {
	globalViper.Set(key, value)
}

func Get(key string) interface{} {
	return globalViper.Get(key)
}

func GetString(key string) string {
	return globalViper.GetString(key)
}

func GetInt(key string) int {
	return globalViper.GetInt(key)
}

func GetBool(key string) bool {
	return globalViper.GetBool(key)
}

func GetFloat64(key string) float64 {
	return globalViper.GetFloat64(key)
}

func GetStringSlice(key string) []string {
	return globalViper.GetStringSlice(key)
}

func GetStringMap(key string) map[string]interface{} {
	return globalViper.GetStringMap(key)
}

func SetDefault(key string, value interface{}) {
	globalViper.SetDefault(key, value)
}

func BindEnv(key string, envVars ...string) error {
	return globalViper.BindEnv(key, envVars...)
}

func SetEnvPrefix(prefix string) {
	globalViper.SetEnvPrefix(prefix)
}

func AutomaticEnv() {
	globalViper.AutomaticEnv()
}

func SetConfigFile(in string) {
	globalViper.SetConfigFile(in)
}

func SetConfigName(in string) {
	globalViper.SetConfigName(in)
}

func SetConfigType(in string) {
	globalViper.SetConfigType(in)
}

func AddConfigPath(in string) {
	globalViper.AddConfigPath(in)
}

func ReadInConfig() error {
	return globalViper.ReadInConfig()
}

func WriteConfig() error {
	return globalViper.WriteConfig()
}

func WriteConfigAs(filename string) error {
	return globalViper.WriteConfigAs(filename)
}

func SafeWriteConfig() error {
	return globalViper.SafeWriteConfig()
}

func IsSet(key string) bool {
	return globalViper.IsSet(key)
}

func AllKeys() []string {
	return globalViper.AllKeys()
}

func AllSettings() map[string]interface{} {
	return globalViper.AllSettings()
}

func Sub(key string) *Viper {
	return globalViper.Sub(key)
}

func Unmarshal(rawVal interface{}) error {
	return globalViper.Unmarshal(rawVal)
}

func UnmarshalKey(key string, rawVal interface{}) error {
	return globalViper.UnmarshalKey(key, rawVal)
}

func Reset() {
	globalViper.Reset()
}
