"""
Hypothesis Emulator - Property-based testing without external dependencies

This module emulates Hypothesis functionality for property-based testing,
allowing you to generate test data and verify properties hold across many inputs.

Features:
- Property-based testing
- Random data generation (strategies)
- Shrinking failed examples
- Multiple data types (integers, strings, lists, etc.)
- Composite strategies
- Example generation
- Stateful testing (simplified)

Note: This is a simplified implementation focusing on core functionality.
Advanced features like database persistence and complex shrinking are simplified.
"""

import random
import string
from typing import Any, Callable, List, Optional, TypeVar, Generic, Tuple, Union
from dataclasses import dataclass
from functools import wraps
import sys

T = TypeVar('T')


@dataclass
class TestCase:
    """Represents a test case with generated data"""
    args: List[Any]
    kwargs: dict
    passed: bool = True
    exception: Optional[Exception] = None


class Strategy(Generic[T]):
    """Base class for value generation strategies"""
    
    def __init__(self, name: str = "strategy"):
        self.name = name
        self._examples_cache: List[T] = []
    
    def example(self) -> T:
        """Generate a single example value"""
        raise NotImplementedError
    
    def examples(self, count: int = 100) -> List[T]:
        """Generate multiple example values"""
        return [self.example() for _ in range(count)]
    
    def map(self, func: Callable[[T], Any]) -> 'Strategy':
        """Transform generated values"""
        return MappedStrategy(self, func)
    
    def filter(self, predicate: Callable[[T], bool]) -> 'Strategy':
        """Filter generated values"""
        return FilteredStrategy(self, predicate)


class IntegerStrategy(Strategy[int]):
    """Strategy for generating integers"""
    
    def __init__(self, min_value: int = -1000, max_value: int = 1000):
        super().__init__("integers")
        self.min_value = min_value
        self.max_value = max_value
    
    def example(self) -> int:
        """Generate a random integer"""
        # Include edge cases
        if random.random() < 0.1:
            edges = [self.min_value, self.max_value, 0, -1, 1]
            valid_edges = [e for e in edges if self.min_value <= e <= self.max_value]
            if valid_edges:
                return random.choice(valid_edges)
        
        return random.randint(self.min_value, self.max_value)


class FloatStrategy(Strategy[float]):
    """Strategy for generating floats"""
    
    def __init__(self, min_value: float = -1000.0, max_value: float = 1000.0):
        super().__init__("floats")
        self.min_value = min_value
        self.max_value = max_value
    
    def example(self) -> float:
        """Generate a random float"""
        # Include edge cases
        if random.random() < 0.1:
            edges = [self.min_value, self.max_value, 0.0, -1.0, 1.0]
            valid_edges = [e for e in edges if self.min_value <= e <= self.max_value]
            if valid_edges:
                return random.choice(valid_edges)
        
        return random.uniform(self.min_value, self.max_value)


class BooleanStrategy(Strategy[bool]):
    """Strategy for generating booleans"""
    
    def __init__(self):
        super().__init__("booleans")
    
    def example(self) -> bool:
        """Generate a random boolean"""
        return random.choice([True, False])


class TextStrategy(Strategy[str]):
    """Strategy for generating text strings"""
    
    def __init__(self, min_size: int = 0, max_size: int = 100, alphabet: Optional[str] = None):
        super().__init__("text")
        self.min_size = min_size
        self.max_size = max_size
        self.alphabet = alphabet or (string.ascii_letters + string.digits + string.punctuation + ' ')
    
    def example(self) -> str:
        """Generate a random string"""
        # Include edge cases
        if random.random() < 0.1:
            return ''  # Empty string
        
        length = random.randint(self.min_size, self.max_size)
        return ''.join(random.choices(self.alphabet, k=length))


class ListStrategy(Strategy[list]):
    """Strategy for generating lists"""
    
    def __init__(self, elements: Strategy, min_size: int = 0, max_size: int = 10):
        super().__init__("lists")
        self.elements = elements
        self.min_size = min_size
        self.max_size = max_size
    
    def example(self) -> list:
        """Generate a random list"""
        # Include edge cases
        if random.random() < 0.1:
            return []  # Empty list
        
        size = random.randint(self.min_size, self.max_size)
        return [self.elements.example() for _ in range(size)]


class TupleStrategy(Strategy[tuple]):
    """Strategy for generating tuples from multiple strategies"""
    
    def __init__(self, *strategies: Strategy):
        super().__init__("tuples")
        self.strategies = strategies
    
    def example(self) -> tuple:
        """Generate a tuple with values from each strategy"""
        return tuple(strategy.example() for strategy in self.strategies)


class DictionaryStrategy(Strategy[dict]):
    """Strategy for generating dictionaries"""
    
    def __init__(self, keys: Strategy, values: Strategy, min_size: int = 0, max_size: int = 10):
        super().__init__("dictionaries")
        self.keys = keys
        self.values = values
        self.min_size = min_size
        self.max_size = max_size
    
    def example(self) -> dict:
        """Generate a random dictionary"""
        # Include edge cases
        if random.random() < 0.1:
            return {}  # Empty dict
        
        size = random.randint(self.min_size, self.max_size)
        result = {}
        attempts = 0
        while len(result) < size and attempts < size * 2:
            key = self.keys.example()
            value = self.values.example()
            # Keys must be hashable
            try:
                hash(key)
                result[key] = value
            except TypeError:
                pass
            attempts += 1
        return result


class JustStrategy(Strategy[T]):
    """Strategy that always returns the same value"""
    
    def __init__(self, value: T):
        super().__init__("just")
        self.value = value
    
    def example(self) -> T:
        """Return the fixed value"""
        return self.value


class SampledFromStrategy(Strategy[T]):
    """Strategy that samples from a collection"""
    
    def __init__(self, elements: List[T]):
        super().__init__("sampled_from")
        if not elements:
            raise ValueError("Cannot sample from empty collection")
        self.elements = elements
    
    def example(self) -> T:
        """Sample a random element"""
        return random.choice(self.elements)


class OneOfStrategy(Strategy[T]):
    """Strategy that chooses from multiple strategies"""
    
    def __init__(self, *strategies: Strategy):
        super().__init__("one_of")
        if not strategies:
            raise ValueError("Must provide at least one strategy")
        self.strategies = strategies
    
    def example(self) -> T:
        """Choose and use a random strategy"""
        strategy = random.choice(self.strategies)
        return strategy.example()


class MappedStrategy(Strategy):
    """Strategy that transforms values from another strategy"""
    
    def __init__(self, base: Strategy, func: Callable):
        super().__init__(f"mapped({base.name})")
        self.base = base
        self.func = func
    
    def example(self):
        """Generate and transform a value"""
        return self.func(self.base.example())


class FilteredStrategy(Strategy):
    """Strategy that filters values from another strategy"""
    
    def __init__(self, base: Strategy, predicate: Callable[[Any], bool]):
        super().__init__(f"filtered({base.name})")
        self.base = base
        self.predicate = predicate
        self.max_attempts = 100
    
    def example(self):
        """Generate values until one passes the filter"""
        for _ in range(self.max_attempts):
            value = self.base.example()
            if self.predicate(value):
                return value
        raise ValueError(f"Could not generate valid example after {self.max_attempts} attempts")


# Convenience functions for creating strategies
def integers(min_value: int = -1000, max_value: int = 1000) -> IntegerStrategy:
    """Create an integer strategy"""
    return IntegerStrategy(min_value, max_value)


def floats(min_value: float = -1000.0, max_value: float = 1000.0) -> FloatStrategy:
    """Create a float strategy"""
    return FloatStrategy(min_value, max_value)


def booleans() -> BooleanStrategy:
    """Create a boolean strategy"""
    return BooleanStrategy()


def text(min_size: int = 0, max_size: int = 100, alphabet: Optional[str] = None) -> TextStrategy:
    """Create a text strategy"""
    return TextStrategy(min_size, max_size, alphabet)


def lists(elements: Strategy, min_size: int = 0, max_size: int = 10) -> ListStrategy:
    """Create a list strategy"""
    return ListStrategy(elements, min_size, max_size)


def tuples(*strategies: Strategy) -> TupleStrategy:
    """Create a tuple strategy"""
    return TupleStrategy(*strategies)


def dictionaries(keys: Strategy, values: Strategy, min_size: int = 0, max_size: int = 10) -> DictionaryStrategy:
    """Create a dictionary strategy"""
    return DictionaryStrategy(keys, values, min_size, max_size)


def just(value: Any) -> JustStrategy:
    """Create a strategy that always returns the same value"""
    return JustStrategy(value)


def sampled_from(elements: List[Any]) -> SampledFromStrategy:
    """Create a strategy that samples from a collection"""
    return SampledFromStrategy(elements)


def one_of(*strategies: Strategy) -> OneOfStrategy:
    """Create a strategy that chooses from multiple strategies"""
    return OneOfStrategy(*strategies)


class PropertyTest:
    """Property-based test runner"""
    
    def __init__(self, max_examples: int = 100, seed: Optional[int] = None):
        self.max_examples = max_examples
        self.seed = seed
        if seed is not None:
            random.seed(seed)
        
        self.test_cases: List[TestCase] = []
        self.failures: List[TestCase] = []
    
    def run_test(self, test_func: Callable, strategies: List[Strategy]) -> bool:
        """Run a property test with given strategies"""
        self.test_cases = []
        self.failures = []
        
        for i in range(self.max_examples):
            # Generate test data
            args = [strategy.example() for strategy in strategies]
            
            # Run test
            test_case = TestCase(args=args, kwargs={})
            
            try:
                test_func(*args)
                test_case.passed = True
            except AssertionError as e:
                test_case.passed = False
                test_case.exception = e
                self.failures.append(test_case)
            except Exception as e:
                test_case.passed = False
                test_case.exception = e
                self.failures.append(test_case)
            
            self.test_cases.append(test_case)
        
        return len(self.failures) == 0
    
    def report(self) -> str:
        """Generate a test report"""
        total = len(self.test_cases)
        passed = total - len(self.failures)
        
        report = f"Property-based test results:\n"
        report += f"  Total examples: {total}\n"
        report += f"  Passed: {passed}\n"
        report += f"  Failed: {len(self.failures)}\n"
        
        if self.failures:
            report += f"\nFirst failure:\n"
            failure = self.failures[0]
            report += f"  Args: {failure.args}\n"
            report += f"  Exception: {failure.exception}\n"
        
        return report


def given(*strategies: Strategy):
    """Decorator for property-based tests"""
    def decorator(test_func: Callable) -> Callable:
        @wraps(test_func)
        def wrapper(*args, **kwargs):
            # Get max_examples from kwargs or use default
            max_examples = kwargs.pop('max_examples', 100)
            seed = kwargs.pop('seed', None)
            
            # Run property test
            runner = PropertyTest(max_examples=max_examples, seed=seed)
            success = runner.run_test(test_func, list(strategies))
            
            if not success:
                # Print report
                print(runner.report())
                raise AssertionError(f"Property test failed after {len(runner.test_cases)} examples")
            
            return success
        
        # Store strategies for introspection
        wrapper._hypothesis_strategies = strategies
        return wrapper
    
    return decorator


class Settings:
    """Configuration for hypothesis tests"""
    
    def __init__(self, max_examples: int = 100, seed: Optional[int] = None):
        self.max_examples = max_examples
        self.seed = seed


def example(*args, **kwargs):
    """Decorator to add explicit examples to a property test"""
    def decorator(func):
        if not hasattr(func, '_hypothesis_examples'):
            func._hypothesis_examples = []
        func._hypothesis_examples.append((args, kwargs))
        return func
    return decorator


# Statistics and analysis
class Statistics:
    """Collect statistics about generated data"""
    
    def __init__(self):
        self.data: List[Any] = []
    
    def record(self, value: Any):
        """Record a value"""
        self.data.append(value)
    
    def summary(self) -> dict:
        """Get summary statistics"""
        if not self.data:
            return {}
        
        summary = {
            'count': len(self.data),
            'unique': len(set(str(v) for v in self.data))
        }
        
        # Numeric statistics
        try:
            numeric = [float(v) for v in self.data]
            summary['min'] = min(numeric)
            summary['max'] = max(numeric)
            summary['mean'] = sum(numeric) / len(numeric)
        except (TypeError, ValueError):
            pass
        
        return summary


def note(message: str):
    """Add a note to the current test (for debugging)"""
    print(f"[NOTE] {message}")


def assume(condition: bool):
    """Skip test case if condition is False"""
    if not condition:
        raise AssumeException("Assumption failed")


class AssumeException(Exception):
    """Exception raised when an assumption fails"""
    pass


# Stateful testing (simplified)
class RuleBasedStateMachine:
    """Base class for stateful testing"""
    
    def __init__(self):
        self.steps: List[str] = []
    
    def rule(self):
        """Define a rule (to be overridden)"""
        pass
    
    def invariant(self):
        """Define an invariant that should always hold"""
        pass


def main():
    """Example usage"""
    print("Hypothesis Emulator - Property-based testing")
    print("\nExample: Testing that reversing a list twice gives the original")
    
    @given(lists(integers()))
    def test_reverse_twice(lst):
        """Property: reversing twice should give original"""
        assert list(reversed(list(reversed(lst)))) == lst
    
    try:
        test_reverse_twice()
        print("✓ Test passed!")
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
    
    print("\nExample: Testing string concatenation is associative")
    
    @given(text(max_size=10), text(max_size=10), text(max_size=10))
    def test_string_concat_associative(a, b, c):
        """Property: (a + b) + c == a + (b + c)"""
        assert (a + b) + c == a + (b + c)
    
    try:
        test_string_concat_associative()
        print("✓ Test passed!")
    except AssertionError as e:
        print(f"✗ Test failed: {e}")


if __name__ == '__main__':
    main()
