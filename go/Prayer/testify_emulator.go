// Developed by PowerShield, as an alternative to Testify

// Testify Emulator - Testing Toolkit for Go
//
// This module emulates Testify, a toolkit with common assertions and mocks
// that plays nicely with the standard library. Testify provides a rich set
// of assertion methods and mocking capabilities for Go testing.
//
// Key Features:
// - Assertions (Equal, NotEqual, Nil, NotNil, True, False, etc.)
// - Error checking (NoError, Error)
// - Collection assertions (Contains, Len, Empty)
// - Type assertions (IsType)
// - Panic assertions (Panics, NotPanics)
// - Mock objects and expectations
// - Suite testing support

package main

import (
	"fmt"
	"reflect"
	"strings"
)

// TestingT is an interface wrapper around *testing.T
type TestingT interface {
	Errorf(format string, args ...interface{})
	FailNow()
	Failed() bool
}

// Assertions provides assertion methods
type Assertions struct {
	t TestingT
}

// New creates a new Assertions object
func New(t TestingT) *Assertions {
	return &Assertions{t: t}
}

// Equal asserts that two values are equal
func (a *Assertions) Equal(expected, actual interface{}, msgAndArgs ...interface{}) bool {
	if !objectsAreEqual(expected, actual) {
		return a.fail(fmt.Sprintf("Not equal: \n"+
			"expected: %v\n"+
			"actual  : %v", expected, actual), msgAndArgs...)
	}
	return true
}

// NotEqual asserts that two values are not equal
func (a *Assertions) NotEqual(expected, actual interface{}, msgAndArgs ...interface{}) bool {
	if objectsAreEqual(expected, actual) {
		return a.fail(fmt.Sprintf("Should not be equal: %v", actual), msgAndArgs...)
	}
	return true
}

// Nil asserts that the value is nil
func (a *Assertions) Nil(object interface{}, msgAndArgs ...interface{}) bool {
	if !isNil(object) {
		return a.fail(fmt.Sprintf("Expected nil, but got: %v", object), msgAndArgs...)
	}
	return true
}

// NotNil asserts that the value is not nil
func (a *Assertions) NotNil(object interface{}, msgAndArgs ...interface{}) bool {
	if isNil(object) {
		return a.fail("Expected value not to be nil", msgAndArgs...)
	}
	return true
}

// True asserts that the value is true
func (a *Assertions) True(value bool, msgAndArgs ...interface{}) bool {
	if !value {
		return a.fail("Should be true", msgAndArgs...)
	}
	return true
}

// False asserts that the value is false
func (a *Assertions) False(value bool, msgAndArgs ...interface{}) bool {
	if value {
		return a.fail("Should be false", msgAndArgs...)
	}
	return true
}

// Empty asserts that the value is empty
func (a *Assertions) Empty(object interface{}, msgAndArgs ...interface{}) bool {
	if !isEmpty(object) {
		return a.fail(fmt.Sprintf("Should be empty, but was %v", object), msgAndArgs...)
	}
	return true
}

// NotEmpty asserts that the value is not empty
func (a *Assertions) NotEmpty(object interface{}, msgAndArgs ...interface{}) bool {
	if isEmpty(object) {
		return a.fail("Should NOT be empty", msgAndArgs...)
	}
	return true
}

// Len asserts that the length of an object is correct
func (a *Assertions) Len(object interface{}, length int, msgAndArgs ...interface{}) bool {
	l := getLength(object)
	if l != length {
		return a.fail(fmt.Sprintf("Length should be %d, but was %d", length, l), msgAndArgs...)
	}
	return true
}

// Contains asserts that the haystack contains the needle
func (a *Assertions) Contains(haystack, needle interface{}, msgAndArgs ...interface{}) bool {
	if !contains(haystack, needle) {
		return a.fail(fmt.Sprintf("%v does not contain %v", haystack, needle), msgAndArgs...)
	}
	return true
}

// NotContains asserts that the haystack does not contain the needle
func (a *Assertions) NotContains(haystack, needle interface{}, msgAndArgs ...interface{}) bool {
	if contains(haystack, needle) {
		return a.fail(fmt.Sprintf("%v should not contain %v", haystack, needle), msgAndArgs...)
	}
	return true
}

// NoError asserts that the error is nil
func (a *Assertions) NoError(err error, msgAndArgs ...interface{}) bool {
	if err != nil {
		return a.fail(fmt.Sprintf("Expected no error, but got: %v", err), msgAndArgs...)
	}
	return true
}

// Error asserts that the error is not nil
func (a *Assertions) Error(err error, msgAndArgs ...interface{}) bool {
	if err == nil {
		return a.fail("Expected an error but got nil", msgAndArgs...)
	}
	return true
}

// EqualError asserts that the error message equals the expected string
func (a *Assertions) EqualError(err error, errString string, msgAndArgs ...interface{}) bool {
	if err == nil {
		return a.fail("Expected an error but got nil", msgAndArgs...)
	}
	if err.Error() != errString {
		return a.fail(fmt.Sprintf("Error message not equal:\n"+
			"expected: %s\n"+
			"actual  : %s", errString, err.Error()), msgAndArgs...)
	}
	return true
}

// IsType asserts that the object is of the specified type
func (a *Assertions) IsType(expectedType, object interface{}, msgAndArgs ...interface{}) bool {
	if !isSameType(expectedType, object) {
		return a.fail(fmt.Sprintf("Expected type %T, but got %T", expectedType, object), msgAndArgs...)
	}
	return true
}

// Panics asserts that the function panics
func (a *Assertions) Panics(f func(), msgAndArgs ...interface{}) (success bool) {
	defer func() {
		if r := recover(); r != nil {
			success = true
		} else {
			a.fail("Expected panic but function did not panic", msgAndArgs...)
			success = false
		}
	}()
	f()
	return false // If we reach here, function didn't panic
}

// NotPanics asserts that the function does not panic
func (a *Assertions) NotPanics(f func(), msgAndArgs ...interface{}) bool {
	panicked := false
	defer func() {
		if r := recover(); r != nil {
			panicked = true
			a.fail(fmt.Sprintf("Function panicked: %v", r), msgAndArgs...)
		}
	}()
	f()
	
	if panicked {
		return false
	}
	return true
}

// Greater asserts that the first value is greater than the second
func (a *Assertions) Greater(e1, e2 interface{}, msgAndArgs ...interface{}) bool {
	cmp, ok := compare(e1, e2)
	if !ok {
		return a.fail("Cannot compare values", msgAndArgs...)
	}
	if cmp <= 0 {
		return a.fail(fmt.Sprintf("%v is not greater than %v", e1, e2), msgAndArgs...)
	}
	return true
}

// Less asserts that the first value is less than the second
func (a *Assertions) Less(e1, e2 interface{}, msgAndArgs ...interface{}) bool {
	cmp, ok := compare(e1, e2)
	if !ok {
		return a.fail("Cannot compare values", msgAndArgs...)
	}
	if cmp >= 0 {
		return a.fail(fmt.Sprintf("%v is not less than %v", e1, e2), msgAndArgs...)
	}
	return true
}

// fail reports a failure
func (a *Assertions) fail(message string, msgAndArgs ...interface{}) bool {
	if len(msgAndArgs) > 0 {
		if format, ok := msgAndArgs[0].(string); ok {
			message = fmt.Sprintf(format, msgAndArgs[1:]...) + "\n" + message
		}
	}
	a.t.Errorf("\n%s", message)
	return false
}

// Helper functions

func objectsAreEqual(expected, actual interface{}) bool {
	if expected == nil || actual == nil {
		return expected == actual
	}
	return reflect.DeepEqual(expected, actual)
}

func isNil(object interface{}) bool {
	if object == nil {
		return true
	}

	value := reflect.ValueOf(object)
	kind := value.Kind()
	
	if kind >= reflect.Chan && kind <= reflect.Slice && value.IsNil() {
		return true
	}

	return false
}

func isEmpty(object interface{}) bool {
	if object == nil {
		return true
	}

	objValue := reflect.ValueOf(object)

	switch objValue.Kind() {
	case reflect.Array, reflect.Chan, reflect.Map, reflect.Slice:
		return objValue.Len() == 0
	case reflect.String:
		return objValue.Len() == 0
	case reflect.Ptr:
		if objValue.IsNil() {
			return true
		}
		return isEmpty(objValue.Elem().Interface())
	default:
		return false
	}
}

func getLength(object interface{}) int {
	objValue := reflect.ValueOf(object)

	switch objValue.Kind() {
	case reflect.Array, reflect.Chan, reflect.Map, reflect.Slice, reflect.String:
		return objValue.Len()
	default:
		return 0
	}
}

func contains(haystack, needle interface{}) bool {
	haystackValue := reflect.ValueOf(haystack)
	
	switch haystackValue.Kind() {
	case reflect.String:
		return strings.Contains(haystackValue.String(), reflect.ValueOf(needle).String())
	case reflect.Slice, reflect.Array:
		for i := 0; i < haystackValue.Len(); i++ {
			if objectsAreEqual(haystackValue.Index(i).Interface(), needle) {
				return true
			}
		}
	case reflect.Map:
		for _, key := range haystackValue.MapKeys() {
			if objectsAreEqual(haystackValue.MapIndex(key).Interface(), needle) {
				return true
			}
		}
	}
	
	return false
}

func isSameType(expectedType, object interface{}) bool {
	return reflect.TypeOf(expectedType) == reflect.TypeOf(object)
}

func compare(e1, e2 interface{}) (int, bool) {
	e1Value := reflect.ValueOf(e1)
	e2Value := reflect.ValueOf(e2)
	
	if e1Value.Kind() != e2Value.Kind() {
		return 0, false
	}
	
	switch e1Value.Kind() {
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
		v1 := e1Value.Int()
		v2 := e2Value.Int()
		if v1 < v2 {
			return -1, true
		} else if v1 > v2 {
			return 1, true
		}
		return 0, true
	case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64:
		v1 := e1Value.Uint()
		v2 := e2Value.Uint()
		if v1 < v2 {
			return -1, true
		} else if v1 > v2 {
			return 1, true
		}
		return 0, true
	case reflect.Float32, reflect.Float64:
		v1 := e1Value.Float()
		v2 := e2Value.Float()
		if v1 < v2 {
			return -1, true
		} else if v1 > v2 {
			return 1, true
		}
		return 0, true
	case reflect.String:
		v1 := e1Value.String()
		v2 := e2Value.String()
		if v1 < v2 {
			return -1, true
		} else if v1 > v2 {
			return 1, true
		}
		return 0, true
	}
	
	return 0, false
}

// Mock provides a simple mock object
type Mock struct {
	Calls       []Call
	ExpectedCalls []Call
}

// Call represents a method call
type Call struct {
	Method    string
	Arguments []interface{}
	ReturnValues []interface{}
}

// On sets up an expectation for a method call
func (m *Mock) On(method string, args ...interface{}) *Call {
	call := Call{
		Method:    method,
		Arguments: args,
	}
	m.ExpectedCalls = append(m.ExpectedCalls, call)
	return &m.ExpectedCalls[len(m.ExpectedCalls)-1]
}

// Return sets the return values for the call
func (c *Call) Return(values ...interface{}) *Call {
	c.ReturnValues = values
	return c
}

// Called records a method call and returns the expected return values
func (m *Mock) Called(method string, args ...interface{}) []interface{} {
	call := Call{
		Method:    method,
		Arguments: args,
	}
	m.Calls = append(m.Calls, call)
	
	// Find matching expected call
	for _, expected := range m.ExpectedCalls {
		if expected.Method == method && objectsAreEqual(expected.Arguments, args) {
			return expected.ReturnValues
		}
	}
	
	return nil
}

// AssertExpectations checks that all expected calls were made
func (m *Mock) AssertExpectations(t TestingT) bool {
	success := true
	
	for _, expected := range m.ExpectedCalls {
		found := false
		for _, actual := range m.Calls {
			if actual.Method == expected.Method && objectsAreEqual(actual.Arguments, expected.Arguments) {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Expected method %s with args %v was not called", expected.Method, expected.Arguments)
			success = false
		}
	}
	
	return success
}

// AssertNotCalled checks that a method was not called
func (m *Mock) AssertNotCalled(t TestingT, method string) bool {
	for _, call := range m.Calls {
		if call.Method == method {
			t.Errorf("Method %s should not have been called", method)
			return false
		}
	}
	return true
}

// AssertCalled checks that a method was called
func (m *Mock) AssertCalled(t TestingT, method string, args ...interface{}) bool {
	for _, call := range m.Calls {
		if call.Method == method && objectsAreEqual(call.Arguments, args) {
			return true
		}
	}
	t.Errorf("Method %s with args %v was not called", method, args)
	return false
}

// Suite provides a test suite structure
type Suite struct {
	*Assertions
}

// SetupSuite runs before all tests in the suite
func (s *Suite) SetupSuite() {
	// Override in test suites
}

// TearDownSuite runs after all tests in the suite
func (s *Suite) TearDownSuite() {
	// Override in test suites
}

// SetupTest runs before each test
func (s *Suite) SetupTest() {
	// Override in test suites
}

// TearDownTest runs after each test
func (s *Suite) TearDownTest() {
	// Override in test suites
}

// Run executes the test suite
func (s *Suite) Run(t TestingT, suiteName string) {
	s.Assertions = New(t)
	
	s.SetupSuite()
	defer s.TearDownSuite()
	
	// In a real implementation, this would use reflection to find and run all Test* methods
	fmt.Printf("Running suite: %s\n", suiteName)
}

// Package-level functions for convenience

// Equal is a convenience function
func Equal(t TestingT, expected, actual interface{}, msgAndArgs ...interface{}) bool {
	return New(t).Equal(expected, actual, msgAndArgs...)
}

// NotEqual is a convenience function
func NotEqual(t TestingT, expected, actual interface{}, msgAndArgs ...interface{}) bool {
	return New(t).NotEqual(expected, actual, msgAndArgs...)
}

// Nil is a convenience function
func Nil(t TestingT, object interface{}, msgAndArgs ...interface{}) bool {
	return New(t).Nil(object, msgAndArgs...)
}

// NotNil is a convenience function
func NotNil(t TestingT, object interface{}, msgAndArgs ...interface{}) bool {
	return New(t).NotNil(object, msgAndArgs...)
}

// True is a convenience function
func True(t TestingT, value bool, msgAndArgs ...interface{}) bool {
	return New(t).True(value, msgAndArgs...)
}

// False is a convenience function
func False(t TestingT, value bool, msgAndArgs ...interface{}) bool {
	return New(t).False(value, msgAndArgs...)
}

// NoError is a convenience function
func NoError(t TestingT, err error, msgAndArgs ...interface{}) bool {
	return New(t).NoError(err, msgAndArgs...)
}

// Error is a convenience function
func Error(t TestingT, err error, msgAndArgs ...interface{}) bool {
	return New(t).Error(err, msgAndArgs...)
}

// Contains is a convenience function
func Contains(t TestingT, haystack, needle interface{}, msgAndArgs ...interface{}) bool {
	return New(t).Contains(haystack, needle, msgAndArgs...)
}

// Empty is a convenience function
func Empty(t TestingT, object interface{}, msgAndArgs ...interface{}) bool {
	return New(t).Empty(object, msgAndArgs...)
}

// NotEmpty is a convenience function
func NotEmpty(t TestingT, object interface{}, msgAndArgs ...interface{}) bool {
	return New(t).NotEmpty(object, msgAndArgs...)
}

