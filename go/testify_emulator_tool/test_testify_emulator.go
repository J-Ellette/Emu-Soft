// Test Suite for Testify Emulator
package main

import (
	"errors"
	"fmt"
)

// MockT implements TestingT for testing
type MockT struct {
	Errors   []string
	failed   bool
	failedNow bool
}

func (m *MockT) Errorf(format string, args ...interface{}) {
	m.Errors = append(m.Errors, fmt.Sprintf(format, args...))
	m.failed = true
}

func (m *MockT) FailNow() {
	m.failedNow = true
}

func (m *MockT) Failed() bool {
	return m.failed
}

// Test runner
func main() {
	fmt.Println("Running Testify Emulator Tests...\n")
	
	passed := 0
	failed := 0
	
	// Test 1: Equal assertion
	fmt.Println("Test Group: Equal Assertions")
	t1 := &MockT{}
	assert1 := New(t1)
	if assert1.Equal(5, 5) && !t1.Failed() {
		fmt.Println("✓ Equal with matching values")
		passed++
	} else {
		fmt.Println("✗ Equal with matching values")
		failed++
	}
	
	t1b := &MockT{}
	assert1b := New(t1b)
	if !assert1b.Equal(5, 6) && t1b.Failed() {
		fmt.Println("✓ Equal with non-matching values fails")
		passed++
	} else {
		fmt.Println("✗ Equal with non-matching values fails")
		failed++
	}
	
	// Test 2: NotEqual assertion
	fmt.Println("\nTest Group: NotEqual Assertions")
	t2 := &MockT{}
	assert2 := New(t2)
	if assert2.NotEqual(5, 6) && !t2.Failed() {
		fmt.Println("✓ NotEqual with different values")
		passed++
	} else {
		fmt.Println("✗ NotEqual with different values")
		failed++
	}
	
	t2b := &MockT{}
	assert2b := New(t2b)
	if !assert2b.NotEqual(5, 5) && t2b.Failed() {
		fmt.Println("✓ NotEqual with same values fails")
		passed++
	} else {
		fmt.Println("✗ NotEqual with same values fails")
		failed++
	}
	
	// Test 3: Nil assertion
	fmt.Println("\nTest Group: Nil Assertions")
	t3 := &MockT{}
	assert3 := New(t3)
	var nilPtr *int
	if assert3.Nil(nilPtr) && !t3.Failed() {
		fmt.Println("✓ Nil with nil pointer")
		passed++
	} else {
		fmt.Println("✗ Nil with nil pointer")
		failed++
	}
	
	t3b := &MockT{}
	assert3b := New(t3b)
	nonNilPtr := new(int)
	if !assert3b.Nil(nonNilPtr) && t3b.Failed() {
		fmt.Println("✓ Nil with non-nil pointer fails")
		passed++
	} else {
		fmt.Println("✗ Nil with non-nil pointer fails")
		failed++
	}
	
	// Test 4: NotNil assertion
	fmt.Println("\nTest Group: NotNil Assertions")
	t4 := &MockT{}
	assert4 := New(t4)
	value := 5
	if assert4.NotNil(&value) && !t4.Failed() {
		fmt.Println("✓ NotNil with non-nil value")
		passed++
	} else {
		fmt.Println("✗ NotNil with non-nil value")
		failed++
	}
	
	t4b := &MockT{}
	assert4b := New(t4b)
	var nilValue *int
	if !assert4b.NotNil(nilValue) && t4b.Failed() {
		fmt.Println("✓ NotNil with nil value fails")
		passed++
	} else {
		fmt.Println("✗ NotNil with nil value fails")
		failed++
	}
	
	// Test 5: True assertion
	fmt.Println("\nTest Group: True/False Assertions")
	t5 := &MockT{}
	assert5 := New(t5)
	if assert5.True(true) && !t5.Failed() {
		fmt.Println("✓ True with true value")
		passed++
	} else {
		fmt.Println("✗ True with true value")
		failed++
	}
	
	t5b := &MockT{}
	assert5b := New(t5b)
	if assert5b.False(false) && !t5b.Failed() {
		fmt.Println("✓ False with false value")
		passed++
	} else {
		fmt.Println("✗ False with false value")
		failed++
	}
	
	// Test 6: Empty assertion
	fmt.Println("\nTest Group: Empty/NotEmpty Assertions")
	t6 := &MockT{}
	assert6 := New(t6)
	emptySlice := []int{}
	if assert6.Empty(emptySlice) && !t6.Failed() {
		fmt.Println("✓ Empty with empty slice")
		passed++
	} else {
		fmt.Println("✗ Empty with empty slice")
		failed++
	}
	
	t6b := &MockT{}
	assert6b := New(t6b)
	nonEmptySlice := []int{1, 2, 3}
	if assert6b.NotEmpty(nonEmptySlice) && !t6b.Failed() {
		fmt.Println("✓ NotEmpty with non-empty slice")
		passed++
	} else {
		fmt.Println("✗ NotEmpty with non-empty slice")
		failed++
	}
	
	// Test 7: Len assertion
	fmt.Println("\nTest Group: Len Assertions")
	t7 := &MockT{}
	assert7 := New(t7)
	slice := []int{1, 2, 3}
	if assert7.Len(slice, 3) && !t7.Failed() {
		fmt.Println("✓ Len with correct length")
		passed++
	} else {
		fmt.Println("✗ Len with correct length")
		failed++
	}
	
	t7b := &MockT{}
	assert7b := New(t7b)
	if !assert7b.Len(slice, 5) && t7b.Failed() {
		fmt.Println("✓ Len with incorrect length fails")
		passed++
	} else {
		fmt.Println("✗ Len with incorrect length fails")
		failed++
	}
	
	// Test 8: Contains assertion
	fmt.Println("\nTest Group: Contains Assertions")
	t8 := &MockT{}
	assert8 := New(t8)
	haystack := []string{"apple", "banana", "cherry"}
	if assert8.Contains(haystack, "banana") && !t8.Failed() {
		fmt.Println("✓ Contains with present element")
		passed++
	} else {
		fmt.Println("✗ Contains with present element")
		failed++
	}
	
	t8b := &MockT{}
	assert8b := New(t8b)
	if assert8b.NotContains(haystack, "grape") && !t8b.Failed() {
		fmt.Println("✓ NotContains with absent element")
		passed++
	} else {
		fmt.Println("✗ NotContains with absent element")
		failed++
	}
	
	// Test 9: NoError assertion
	fmt.Println("\nTest Group: Error Assertions")
	t9 := &MockT{}
	assert9 := New(t9)
	if assert9.NoError(nil) && !t9.Failed() {
		fmt.Println("✓ NoError with nil error")
		passed++
	} else {
		fmt.Println("✗ NoError with nil error")
		failed++
	}
	
	t9b := &MockT{}
	assert9b := New(t9b)
	err := errors.New("test error")
	if assert9b.Error(err) && !t9b.Failed() {
		fmt.Println("✓ Error with non-nil error")
		passed++
	} else {
		fmt.Println("✗ Error with non-nil error")
		failed++
	}
	
	// Test 10: EqualError assertion
	fmt.Println("\nTest Group: EqualError Assertions")
	t10 := &MockT{}
	assert10 := New(t10)
	testErr := errors.New("specific error")
	if assert10.EqualError(testErr, "specific error") && !t10.Failed() {
		fmt.Println("✓ EqualError with matching error message")
		passed++
	} else {
		fmt.Println("✗ EqualError with matching error message")
		failed++
	}
	
	// Test 11: IsType assertion
	fmt.Println("\nTest Group: IsType Assertions")
	t11 := &MockT{}
	assert11 := New(t11)
	if assert11.IsType(0, 42) && !t11.Failed() {
		fmt.Println("✓ IsType with matching types")
		passed++
	} else {
		fmt.Println("✗ IsType with matching types")
		failed++
	}
	
	t11b := &MockT{}
	assert11b := New(t11b)
	if !assert11b.IsType("", 42) && t11b.Failed() {
		fmt.Println("✓ IsType with different types fails")
		passed++
	} else {
		fmt.Println("✗ IsType with different types fails")
		failed++
	}
	
	// Test 12: Panics assertion
	fmt.Println("\nTest Group: Panics Assertions")
	t12 := &MockT{}
	assert12 := New(t12)
	panicFunc := func() { panic("test panic") }
	if assert12.Panics(panicFunc) && !t12.Failed() {
		fmt.Println("✓ Panics with panicking function")
		passed++
	} else {
		fmt.Println("✗ Panics with panicking function")
		failed++
	}
	
	t12b := &MockT{}
	assert12b := New(t12b)
	normalFunc := func() {}
	if assert12b.NotPanics(normalFunc) && !t12b.Failed() {
		fmt.Println("✓ NotPanics with non-panicking function")
		passed++
	} else {
		fmt.Println("✗ NotPanics with non-panicking function")
		failed++
	}
	
	// Test 13: Greater assertion
	fmt.Println("\nTest Group: Comparison Assertions")
	t13 := &MockT{}
	assert13 := New(t13)
	if assert13.Greater(10, 5) && !t13.Failed() {
		fmt.Println("✓ Greater with larger value")
		passed++
	} else {
		fmt.Println("✗ Greater with larger value")
		failed++
	}
	
	t13b := &MockT{}
	assert13b := New(t13b)
	if assert13b.Less(5, 10) && !t13b.Failed() {
		fmt.Println("✓ Less with smaller value")
		passed++
	} else {
		fmt.Println("✗ Less with smaller value")
		failed++
	}
	
	// Test 14: String contains
	fmt.Println("\nTest Group: String Contains")
	t14 := &MockT{}
	assert14 := New(t14)
	if assert14.Contains("hello world", "world") && !t14.Failed() {
		fmt.Println("✓ Contains with substring")
		passed++
	} else {
		fmt.Println("✗ Contains with substring")
		failed++
	}
	
	// Test 15: Map contains
	fmt.Println("\nTest Group: Map Contains")
	t15 := &MockT{}
	assert15 := New(t15)
	m := map[string]int{"a": 1, "b": 2, "c": 3}
	if assert15.Contains(m, 2) && !t15.Failed() {
		fmt.Println("✓ Contains with map value")
		passed++
	} else {
		fmt.Println("✗ Contains with map value")
		failed++
	}
	
	// Test 16: Mock object
	fmt.Println("\nTest Group: Mock Functionality")
	mock := &Mock{}
	mock.On("GetValue", 5).Return(10)
	result := mock.Called("GetValue", 5)
	if len(result) == 1 && result[0].(int) == 10 {
		fmt.Println("✓ Mock returns expected value")
		passed++
	} else {
		fmt.Println("✗ Mock returns expected value")
		failed++
	}
	
	// Test 17: Mock expectations
	fmt.Println("\nTest Group: Mock Expectations")
	t17 := &MockT{}
	mock17 := &Mock{}
	mock17.On("TestMethod", 1, 2).Return(3)
	mock17.Called("TestMethod", 1, 2)
	if mock17.AssertExpectations(t17) && !t17.Failed() {
		fmt.Println("✓ Mock expectations are met")
		passed++
	} else {
		fmt.Println("✗ Mock expectations are met")
		failed++
	}
	
	// Test 18: Mock AssertCalled
	fmt.Println("\nTest Group: Mock AssertCalled")
	t18 := &MockT{}
	mock18 := &Mock{}
	mock18.Called("MethodA", "arg1")
	if mock18.AssertCalled(t18, "MethodA", "arg1") && !t18.Failed() {
		fmt.Println("✓ AssertCalled detects called method")
		passed++
	} else {
		fmt.Println("✗ AssertCalled detects called method")
		failed++
	}
	
	// Test 19: Mock AssertNotCalled
	fmt.Println("\nTest Group: Mock AssertNotCalled")
	t19 := &MockT{}
	mock19 := &Mock{}
	if mock19.AssertNotCalled(t19, "UnusedMethod") && !t19.Failed() {
		fmt.Println("✓ AssertNotCalled detects uncalled method")
		passed++
	} else {
		fmt.Println("✗ AssertNotCalled detects uncalled method")
		failed++
	}
	
	// Test 20: Convenience functions
	fmt.Println("\nTest Group: Convenience Functions")
	t20 := &MockT{}
	if Equal(t20, 1, 1) && !t20.Failed() {
		fmt.Println("✓ Equal convenience function works")
		passed++
	} else {
		fmt.Println("✗ Equal convenience function works")
		failed++
	}
	
	t20b := &MockT{}
	if True(t20b, true) && !t20b.Failed() {
		fmt.Println("✓ True convenience function works")
		passed++
	} else {
		fmt.Println("✗ True convenience function works")
		failed++
	}
	
	t20c := &MockT{}
	if NoError(t20c, nil) && !t20c.Failed() {
		fmt.Println("✓ NoError convenience function works")
		passed++
	} else {
		fmt.Println("✗ NoError convenience function works")
		failed++
	}
	
	// Test 21: Empty string
	fmt.Println("\nTest Group: Empty String")
	t21 := &MockT{}
	assert21 := New(t21)
	if assert21.Empty("") && !t21.Failed() {
		fmt.Println("✓ Empty detects empty string")
		passed++
	} else {
		fmt.Println("✗ Empty detects empty string")
		failed++
	}
	
	// Test 22: Len with string
	fmt.Println("\nTest Group: Len with String")
	t22 := &MockT{}
	assert22 := New(t22)
	if assert22.Len("hello", 5) && !t22.Failed() {
		fmt.Println("✓ Len works with string")
		passed++
	} else {
		fmt.Println("✗ Len works with string")
		failed++
	}
	
	// Test 23: Slice equality
	fmt.Println("\nTest Group: Slice Equality")
	t23 := &MockT{}
	assert23 := New(t23)
	slice1 := []int{1, 2, 3}
	slice2 := []int{1, 2, 3}
	if assert23.Equal(slice1, slice2) && !t23.Failed() {
		fmt.Println("✓ Equal works with slices")
		passed++
	} else {
		fmt.Println("✗ Equal works with slices")
		failed++
	}
	
	// Test 24: Greater with floats
	fmt.Println("\nTest Group: Greater with Floats")
	t24 := &MockT{}
	assert24 := New(t24)
	if assert24.Greater(3.14, 2.71) && !t24.Failed() {
		fmt.Println("✓ Greater works with floats")
		passed++
	} else {
		fmt.Println("✗ Greater works with floats")
		failed++
	}
	
	// Test 25: Less with strings
	fmt.Println("\nTest Group: Less with Strings")
	t25 := &MockT{}
	assert25 := New(t25)
	if assert25.Less("apple", "banana") && !t25.Failed() {
		fmt.Println("✓ Less works with strings")
		passed++
	} else {
		fmt.Println("✗ Less works with strings")
		failed++
	}
	
	// Final results
	fmt.Println("\n" + "==================================================")
	fmt.Printf("Test Results: %d passed, %d failed\n", passed, failed)
	fmt.Println("==================================================")
	
	if failed == 0 {
		fmt.Println("✓ All tests passed!")
	} else {
		fmt.Printf("✗ %d test(s) failed\n", failed)
	}
}
