# Hypothesis Emulator

A pure Python implementation that emulates Hypothesis functionality for property-based testing without external dependencies.

## What This Emulates

**Emulates:** Hypothesis (Property-based testing framework)
**Original:** https://hypothesis.readthedocs.io/

## Overview

This module provides property-based testing capabilities, allowing you to write tests that verify properties hold across many randomly generated inputs, making your tests more thorough and finding edge cases you might not think of.

## Features

- **Property-Based Testing**
  - Test properties instead of specific examples
  - Automatic test case generation
  - Finds edge cases automatically
  - Reproducible with seeds

- **Data Generation Strategies**
  - Integers, floats, booleans
  - Text strings with customizable alphabets
  - Lists, tuples, dictionaries
  - Composite strategies
  - Custom strategies

- **Strategy Transformations**
  - Map: Transform generated values
  - Filter: Filter generated values
  - Combine multiple strategies

- **Test Utilities**
  - @given decorator for easy testing
  - Example generation
  - Failure reporting
  - Statistics collection

## Usage

### Basic Property Test

```python
from hypothesis_emulator_tool.hypothesis_emulator import given, integers

@given(integers(min_value=0, max_value=100))
def test_square_positive(x):
    """Property: square of positive number is positive"""
    assert x * x >= 0

test_square_positive()
```

### Multiple Arguments

```python
from hypothesis_emulator_tool.hypothesis_emulator import given, integers

@given(integers(), integers())
def test_addition_commutative(a, b):
    """Property: a + b == b + a"""
    assert a + b == b + a

test_addition_commutative()
```

### Testing with Lists

```python
from hypothesis_emulator_tool.hypothesis_emulator import given, lists, integers

@given(lists(integers()))
def test_reverse_twice(lst):
    """Property: reversing twice gives original"""
    assert list(reversed(list(reversed(lst)))) == lst

test_reverse_twice()
```

## Strategies

### Integer Strategy

```python
from hypothesis_emulator_tool.hypothesis_emulator import integers

# Generate integers from 0 to 100
strategy = integers(min_value=0, max_value=100)

# Get examples
values = strategy.examples(10)  # Generate 10 values
```

### Float Strategy

```python
from hypothesis_emulator_tool.hypothesis_emulator import floats

# Generate floats from 0.0 to 1.0
strategy = floats(min_value=0.0, max_value=1.0)
values = strategy.examples(10)
```

### Boolean Strategy

```python
from hypothesis_emulator_tool.hypothesis_emulator import booleans

strategy = booleans()
values = strategy.examples(10)  # Mix of True and False
```

### Text Strategy

```python
from hypothesis_emulator_tool.hypothesis_emulator import text

# Generate strings up to 50 characters
strategy = text(max_size=50)
values = strategy.examples(10)

# Custom alphabet
strategy = text(max_size=10, alphabet='abc123')
```

### List Strategy

```python
from hypothesis_emulator_tool.hypothesis_emulator import lists, integers

# Lists of integers
strategy = lists(integers(), min_size=0, max_size=10)
values = strategy.examples(10)

# Lists of strings
from hypothesis_emulator_tool.hypothesis_emulator import text
strategy = lists(text(), max_size=5)
```

### Tuple Strategy

```python
from hypothesis_emulator_tool.hypothesis_emulator import tuples, integers, text, booleans

# Tuple with different types
strategy = tuples(integers(), text(), booleans())
values = strategy.examples(10)  # [(42, "hello", True), ...]
```

### Dictionary Strategy

```python
from hypothesis_emulator_tool.hypothesis_emulator import dictionaries, text, integers

# Dictionaries with string keys and integer values
strategy = dictionaries(text(max_size=5), integers(), max_size=10)
values = strategy.examples(10)
```

### Just Strategy

```python
from hypothesis_emulator_tool.hypothesis_emulator import just

# Always return the same value
strategy = just(42)
values = strategy.examples(10)  # [42, 42, 42, ...]
```

### Sampled From Strategy

```python
from hypothesis_emulator_tool.hypothesis_emulator import sampled_from

# Sample from a collection
strategy = sampled_from(['red', 'green', 'blue'])
values = strategy.examples(10)
```

### One Of Strategy

```python
from hypothesis_emulator_tool.hypothesis_emulator import one_of, integers, text

# Choose from multiple strategies
strategy = one_of(integers(), text())
values = strategy.examples(10)  # Mix of ints and strings
```

## Strategy Transformations

### Map

Transform generated values:

```python
from hypothesis_emulator_tool.hypothesis_emulator import integers

# Generate even numbers
strategy = integers(0, 10).map(lambda x: x * 2)
values = strategy.examples(10)  # [0, 2, 4, 6, ...]
```

### Filter

Filter generated values:

```python
from hypothesis_emulator_tool.hypothesis_emulator import integers

# Generate only even numbers
strategy = integers(0, 10).filter(lambda x: x % 2 == 0)
values = strategy.examples(10)
```

## Examples

### Example 1: Testing List Operations

```python
from hypothesis_emulator_tool.hypothesis_emulator import given, lists, integers

@given(lists(integers()), integers())
def test_append_increases_length(lst, x):
    """Property: appending increases length by 1"""
    original_length = len(lst)
    lst.append(x)
    assert len(lst) == original_length + 1

test_append_increases_length()
```

### Example 2: Testing String Operations

```python
from hypothesis_emulator_tool.hypothesis_emulator import given, text

@given(text(), text())
def test_string_concat_length(a, b):
    """Property: len(a + b) == len(a) + len(b)"""
    assert len(a + b) == len(a) + len(b)

test_string_concat_length()
```

### Example 3: Testing Sorting

```python
from hypothesis_emulator_tool.hypothesis_emulator import given, lists, integers

@given(lists(integers()))
def test_sort_idempotent(lst):
    """Property: sorting twice is same as sorting once"""
    assert sorted(sorted(lst)) == sorted(lst)

test_sort_idempotent()
```

### Example 4: Testing Mathematical Properties

```python
from hypothesis_emulator_tool.hypothesis_emulator import given, integers

@given(integers(), integers(), integers())
def test_addition_associative(a, b, c):
    """Property: (a + b) + c == a + (b + c)"""
    assert (a + b) + c == a + (b + c)

test_addition_associative()
```

## Configuration

### Max Examples

Control how many examples to generate:

```python
@given(integers())
def test_something(x):
    assert x >= 0

# Run with more examples
test_something(max_examples=1000)
```

### Seed

Make tests reproducible:

```python
@given(integers())
def test_something(x):
    assert x >= 0

# Use fixed seed for reproducibility
test_something(seed=12345)
```

## Testing

Run the test suite:

```bash
python test_hypothesis_emulator.py
```

Test coverage:
- Strategy tests (10 tests)
- Transformation tests (2 tests)
- Property runner tests (3 tests)
- @given decorator tests (3 tests)
- Real property tests (4 tests)
- Statistics tests (1 test)
- TestCase tests (1 test)

## Use Cases

- **Find Edge Cases**: Discover bugs you didn't think of
- **Thorough Testing**: Test many inputs automatically
- **Property Verification**: Verify mathematical properties
- **Algorithm Testing**: Test algorithm correctness
- **Data Structure Testing**: Verify data structure invariants
- **API Testing**: Test API behavior across inputs

## Benefits

### Self-Contained

No external dependencies - uses only Python standard library.

### Automatic

Generates test cases automatically, no manual example writing.

### Comprehensive

Tests many cases you might not think of manually.

### Edge Cases

Automatically includes edge cases like 0, -1, empty lists, etc.

## Advanced Usage

### Manual Property Testing

```python
from hypothesis_emulator_tool.hypothesis_emulator import PropertyTest, integers

def my_test(x):
    assert x >= 0

runner = PropertyTest(max_examples=100, seed=42)
success = runner.run_test(my_test, [integers(min_value=0)])

if not success:
    print(runner.report())
```

### Generate Examples

```python
from hypothesis_emulator_tool.hypothesis_emulator import integers

strategy = integers(0, 100)

# Generate single example
value = strategy.example()

# Generate multiple examples
values = strategy.examples(50)
```

### Statistics

```python
from hypothesis_emulator_tool.hypothesis_emulator import Statistics

stats = Statistics()

for i in range(100):
    stats.record(i)

summary = stats.summary()
print(f"Count: {summary['count']}")
print(f"Min: {summary['min']}")
print(f"Max: {summary['max']}")
print(f"Mean: {summary['mean']}")
```

## Integration

### With pytest

Use in pytest tests:

```python
# test_mymodule.py
from hypothesis_emulator_tool.hypothesis_emulator import given, integers

@given(integers())
def test_my_function(x):
    result = my_function(x)
    assert result >= 0

# Run with: pytest test_mymodule.py
```

### With unittest

```python
import unittest
from hypothesis_emulator_tool.hypothesis_emulator import given, integers

class TestMyCode(unittest.TestCase):
    @given(integers())
    def test_something(self, x):
        self.assertGreaterEqual(x * x, 0)
```

### In CI/CD

GitHub Actions example:

```yaml
- name: Run Property-Based Tests
  run: |
    python -m pytest tests/property_tests.py
```

## Best Practices

### 1. Test Properties, Not Examples

Instead of:
```python
def test_square():
    assert square(2) == 4
    assert square(3) == 9
```

Do:
```python
@given(integers())
def test_square_nonnegative(x):
    assert square(x) >= 0
```

### 2. Start Simple

Begin with simple properties and add complexity:

```python
# Simple
@given(integers())
def test_abs_nonnegative(x):
    assert abs(x) >= 0

# More complex
@given(lists(integers()))
def test_sort_preserves_elements(lst):
    sorted_lst = sorted(lst)
    assert sorted(sorted_lst) == sorted_lst
    assert len(sorted_lst) == len(lst)
```

### 3. Use Appropriate Ranges

Limit ranges to reasonable values:

```python
# Good
@given(integers(min_value=0, max_value=1000))
def test_factorial(n):
    result = factorial(n)
    assert result >= 1

# Bad (would take forever or cause overflow)
@given(integers(min_value=0, max_value=10000000))
def test_factorial(n):
    ...
```

### 4. Think About Invariants

What should always be true?

```python
@given(lists(integers()))
def test_list_invariants(lst):
    # Length invariant
    assert len(lst) >= 0
    
    # Append invariant
    lst_copy = lst[:]
    lst_copy.append(42)
    assert len(lst_copy) == len(lst) + 1
```

### 5. Combine Strategies

Build complex test data:

```python
from hypothesis_emulator_tool.hypothesis_emulator import tuples, integers, text

@given(tuples(text(), integers(), integers()))
def test_database_record(record):
    name, age, id = record
    assert isinstance(name, str)
    assert isinstance(age, int)
    assert isinstance(id, int)
```

## Limitations

Compared to full Hypothesis:

- **No shrinking**: Doesn't minimize failing examples
- **No database**: Doesn't persist examples
- **Simpler strategies**: Fewer built-in strategies
- **Basic reporting**: Simplified failure reports
- **No stateful testing**: Simplified state machine support
- **No composite strategies**: Limited strategy composition
- **No deadlines**: No timeout handling
- **No health checks**: No health check system

These limitations keep the implementation simple while providing core property-based testing capabilities.

## Property Examples

### Commutativity

```python
@given(integers(), integers())
def test_addition_commutative(a, b):
    assert a + b == b + a
```

### Associativity

```python
@given(integers(), integers(), integers())
def test_addition_associative(a, b, c):
    assert (a + b) + c == a + (b + c)
```

### Identity

```python
@given(integers())
def test_addition_identity(x):
    assert x + 0 == x
```

### Idempotence

```python
@given(lists(integers()))
def test_sort_idempotent(lst):
    assert sorted(sorted(lst)) == sorted(lst)
```

### Inverse

```python
@given(lists(integers()))
def test_reverse_inverse(lst):
    assert list(reversed(list(reversed(lst)))) == lst
```

## How It Works

1. **Strategy Selection**: Choose appropriate strategies
2. **Value Generation**: Generate random values
3. **Test Execution**: Run test function with values
4. **Failure Detection**: Catch assertion errors
5. **Reporting**: Report failures with examples

## Troubleshooting

### "Could not generate valid example"

This happens when a filter is too restrictive:

```python
# Bad - too restrictive
strategy = integers(0, 10).filter(lambda x: x > 1000)

# Good
strategy = integers(1001, 2000)
```

### Test takes too long

Reduce max_examples:

```python
@given(lists(integers()))
def test_something(lst):
    ...

# Run faster
test_something(max_examples=10)
```

### Need reproducibility

Use a fixed seed:

```python
test_something(seed=12345)
```

## Contributing

This is part of the Emu-Soft repository's collection of emulated tools. Improvements welcome!

## License

Part of the Emu-Soft project. See project license for terms.
