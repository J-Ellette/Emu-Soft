# Testify Emulator - Testing Toolkit for Go

This module emulates **Testify**, a toolkit with common assertions and mocks that plays nicely with the standard library. Testify provides a rich set of assertion methods and mocking capabilities for Go testing.

## What is Testify?

Testify is one of the most popular testing toolkits for Go, providing:
- A comprehensive set of assertion methods
- Mocking and test doubles
- Suite-based testing
- Clean and readable test code
- Integration with standard Go testing
- Extensive error messaging

## Features

This emulator implements core Testify functionality:

### Assertions
- **Equality**: Equal, NotEqual
- **Nil Checks**: Nil, NotNil
- **Boolean**: True, False
- **Collections**: Empty, NotEmpty, Len, Contains, NotContains
- **Errors**: NoError, Error, EqualError
- **Types**: IsType
- **Panics**: Panics, NotPanics
- **Comparison**: Greater, Less

### Mocking
- **Mock Objects**: Track method calls
- **Expectations**: Set expected method calls
- **Return Values**: Configure mock return values
- **Assertions**: Verify mock expectations

### Test Suites
- **Suite Structure**: Organized test suites
- **Setup/Teardown**: Before and after hooks
- **Suite Methods**: Setup, TearDown, etc.

## Usage Examples

### Basic Assertions

```go
package main

import (
    "testing"
)

func TestExample(t *testing.T) {
    assert := New(t)
    
    // Equal assertion
    assert.Equal(5, 5, "values should be equal")
    
    // NotEqual assertion
    assert.NotEqual(5, 6, "values should not be equal")
    
    // True/False assertions
    assert.True(true, "should be true")
    assert.False(false, "should be false")
}
```

### Nil Assertions

```go
func TestNil(t *testing.T) {
    assert := New(t)
    
    var nilPtr *int
    assert.Nil(nilPtr, "pointer should be nil")
    
    value := 5
    assert.NotNil(&value, "pointer should not be nil")
}
```

### Collection Assertions

```go
func TestCollections(t *testing.T) {
    assert := New(t)
    
    // Empty/NotEmpty
    emptySlice := []int{}
    assert.Empty(emptySlice, "slice should be empty")
    
    nonEmptySlice := []int{1, 2, 3}
    assert.NotEmpty(nonEmptySlice, "slice should not be empty")
    
    // Len
    assert.Len(nonEmptySlice, 3, "slice should have 3 elements")
    
    // Contains
    assert.Contains(nonEmptySlice, 2, "slice should contain 2")
    assert.NotContains(nonEmptySlice, 5, "slice should not contain 5")
}
```

### String Operations

```go
func TestStrings(t *testing.T) {
    assert := New(t)
    
    // Empty string
    assert.Empty("", "string should be empty")
    
    // String length
    assert.Len("hello", 5, "string should have 5 characters")
    
    // String contains
    assert.Contains("hello world", "world", "string should contain 'world'")
}
```

### Error Assertions

```go
func TestErrors(t *testing.T) {
    assert := New(t)
    
    // NoError
    err := someFunction()
    assert.NoError(err, "function should not return error")
    
    // Error
    err = failingFunction()
    assert.Error(err, "function should return error")
    
    // EqualError
    err = errors.New("specific error")
    assert.EqualError(err, "specific error", "error message should match")
}
```

### Type Assertions

```go
func TestTypes(t *testing.T) {
    assert := New(t)
    
    // IsType
    var i int = 42
    assert.IsType(0, i, "should be int type")
    
    var s string = "hello"
    assert.IsType("", s, "should be string type")
}
```

### Panic Assertions

```go
func TestPanics(t *testing.T) {
    assert := New(t)
    
    // Panics
    panicFunc := func() {
        panic("something went wrong")
    }
    assert.Panics(panicFunc, "function should panic")
    
    // NotPanics
    normalFunc := func() {
        // Normal code
    }
    assert.NotPanics(normalFunc, "function should not panic")
}
```

### Comparison Assertions

```go
func TestComparisons(t *testing.T) {
    assert := New(t)
    
    // Greater
    assert.Greater(10, 5, "10 should be greater than 5")
    
    // Less
    assert.Less(5, 10, "5 should be less than 10")
    
    // Works with different types
    assert.Greater(3.14, 2.71, "pi should be greater than e")
    assert.Less("apple", "banana", "apple should be less than banana")
}
```

### Convenience Functions

```go
func TestConvenienceFunctions(t *testing.T) {
    // Package-level functions (no need to create Assertions object)
    
    Equal(t, 5, 5, "values should be equal")
    NotEqual(t, 5, 6, "values should not be equal")
    Nil(t, nil, "should be nil")
    True(t, true, "should be true")
    False(t, false, "should be false")
    NoError(t, nil, "should have no error")
    Empty(t, []int{}, "should be empty")
}
```

### Mock Objects

```go
func TestMocking(t *testing.T) {
    // Create mock
    mock := &Mock{}
    
    // Set expectations
    mock.On("GetValue", 5).Return(10)
    mock.On("DoSomething", "arg1", "arg2").Return(true)
    
    // Use mock
    result := mock.Called("GetValue", 5)
    value := result[0].(int) // value == 10
    
    mock.Called("DoSomething", "arg1", "arg2")
    
    // Verify expectations
    mock.AssertExpectations(t)
}
```

### Mock Example

```go
// Define interface
type Calculator interface {
    Add(a, b int) int
    Subtract(a, b int) int
}

// Create mock implementation
type MockCalculator struct {
    Mock
}

func (m *MockCalculator) Add(a, b int) int {
    args := m.Called("Add", a, b)
    return args[0].(int)
}

func (m *MockCalculator) Subtract(a, b int) int {
    args := m.Called("Subtract", a, b)
    return args[0].(int)
}

// Use in test
func TestCalculator(t *testing.T) {
    assert := New(t)
    mockCalc := &MockCalculator{}
    
    // Set expectations
    mockCalc.On("Add", 2, 3).Return(5)
    mockCalc.On("Subtract", 10, 4).Return(6)
    
    // Test
    result1 := mockCalc.Add(2, 3)
    assert.Equal(5, result1, "addition should work")
    
    result2 := mockCalc.Subtract(10, 4)
    assert.Equal(6, result2, "subtraction should work")
    
    // Verify all expectations were met
    mockCalc.AssertExpectations(t)
}
```

### Verify Method Calls

```go
func TestMockVerification(t *testing.T) {
    mock := &Mock{}
    
    // Make some calls
    mock.Called("MethodA", "arg1")
    mock.Called("MethodB", 123)
    
    // Verify specific calls were made
    mock.AssertCalled(t, "MethodA", "arg1")
    mock.AssertCalled(t, "MethodB", 123)
    
    // Verify a method was NOT called
    mock.AssertNotCalled(t, "UnusedMethod")
}
```

### Test Suite

```go
type MyTestSuite struct {
    Suite
    db *Database
}

func (s *MyTestSuite) SetupSuite() {
    // Runs once before all tests
    s.db = OpenDatabase()
}

func (s *MyTestSuite) TearDownSuite() {
    // Runs once after all tests
    s.db.Close()
}

func (s *MyTestSuite) SetupTest() {
    // Runs before each test
    s.db.BeginTransaction()
}

func (s *MyTestSuite) TearDownTest() {
    // Runs after each test
    s.db.Rollback()
}

func (s *MyTestSuite) TestExample() {
    s.Equal(1, 1)
    // Use s.db for database operations
}

func TestMyTestSuite(t *testing.T) {
    suite := &MyTestSuite{}
    suite.Run(t, "MyTestSuite")
}
```

### Map Contains

```go
func TestMapContains(t *testing.T) {
    assert := New(t)
    
    m := map[string]int{
        "a": 1,
        "b": 2,
        "c": 3,
    }
    
    // Check if map contains value
    assert.Contains(m, 2, "map should contain value 2")
    assert.NotContains(m, 5, "map should not contain value 5")
}
```

### Complex Assertions

```go
func TestComplexAssertions(t *testing.T) {
    assert := New(t)
    
    // Slice equality (deep comparison)
    slice1 := []int{1, 2, 3}
    slice2 := []int{1, 2, 3}
    assert.Equal(slice1, slice2, "slices should be equal")
    
    // Struct equality
    type Person struct {
        Name string
        Age  int
    }
    person1 := Person{"Alice", 30}
    person2 := Person{"Alice", 30}
    assert.Equal(person1, person2, "persons should be equal")
    
    // Map equality
    map1 := map[string]int{"a": 1, "b": 2}
    map2 := map[string]int{"a": 1, "b": 2}
    assert.Equal(map1, map2, "maps should be equal")
}
```

## Testing

Run the comprehensive test suite:

```bash
go run test_testify_emulator.go testify_emulator.go
```

Tests cover:
- Equal and NotEqual assertions
- Nil and NotNil assertions
- True and False assertions
- Empty and NotEmpty assertions
- Len assertions
- Contains and NotContains assertions
- NoError, Error, and EqualError assertions
- IsType assertions
- Panics and NotPanics assertions
- Greater and Less comparisons
- String operations
- Map operations
- Mock functionality
- Mock expectations and verification
- Convenience functions
- Complex type comparisons

Total: 39 tests

## Integration with Existing Code

This emulator is designed to be compatible with testify/assert API:

```go
// Instead of:
// import "github.com/stretchr/testify/assert"

// Use your emulator (assuming it's in the same package)
// The API is the same

func TestSomething(t *testing.T) {
    assert := New(t)
    assert.Equal(expected, actual)
    assert.NoError(err)
}
```

## Use Cases

Perfect for:
- **Learning**: Understand testing patterns in Go
- **Testing**: Write tests without external dependencies
- **Prototyping**: Quickly prototype test code
- **Education**: Teach testing concepts
- **Development**: Develop code with inline testing
- **CI/CD**: Run tests in minimal environments

## Limitations

This is an emulator for learning and testing purposes:
- Simplified implementation compared to real testify
- No test suite runner (suite methods must be called manually)
- Basic mock implementation (no argument matchers)
- No require package (only assert)
- No http package
- Simplified comparison logic
- No custom error messages formatting
- No integration with testing frameworks beyond basic TestingT

## Supported Features

### Assertions
- ✅ Equal, NotEqual
- ✅ Nil, NotNil
- ✅ True, False
- ✅ Empty, NotEmpty
- ✅ Len
- ✅ Contains, NotContains
- ✅ NoError, Error, EqualError
- ✅ IsType
- ✅ Panics, NotPanics
- ✅ Greater, Less

### Mocking
- ✅ Mock objects
- ✅ Method call tracking
- ✅ Return value configuration
- ✅ AssertExpectations
- ✅ AssertCalled
- ✅ AssertNotCalled

### Convenience
- ✅ Package-level assertion functions
- ✅ TestingT interface compatibility

### Types Supported
- ✅ Primitives (int, string, bool, float, etc.)
- ✅ Slices and arrays
- ✅ Maps
- ✅ Structs
- ✅ Pointers
- ✅ Interfaces

## Real-World Testing Concepts

This emulator teaches the following concepts:

1. **Assertion-Based Testing**: Using assertions instead of manual checks
2. **Test Organization**: Structuring tests effectively
3. **Mocking**: Creating test doubles for dependencies
4. **Error Testing**: Proper error handling verification
5. **Type Safety**: Type-aware assertions
6. **Panic Recovery**: Testing panic scenarios safely
7. **Collection Testing**: Working with slices, maps, arrays
8. **Deep Equality**: Comparing complex data structures
9. **Test Readability**: Writing clear, maintainable tests
10. **Test Doubles**: Understanding mocks and expectations

## Compatibility

Emulates core features of:
- testify/assert package
- testify/mock package
- testify/suite package (basic structure)
- Standard Go testing.T interface

## License

Part of the Emu-Soft project. See main repository LICENSE.
