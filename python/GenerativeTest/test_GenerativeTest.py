"""
Developed by PowerShield, as an alternative to Hypothesis
"""

#!/usr/bin/env python3
"""
Tests for Hypothesis Emulator
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hypothesis_emulator_tool.hypothesis_emulator import (
    Strategy,
    IntegerStrategy,
    FloatStrategy,
    BooleanStrategy,
    TextStrategy,
    ListStrategy,
    TupleStrategy,
    DictionaryStrategy,
    JustStrategy,
    SampledFromStrategy,
    OneOfStrategy,
    integers,
    floats,
    booleans,
    text,
    lists,
    tuples,
    dictionaries,
    just,
    sampled_from,
    one_of,
    given,
    PropertyTest,
    TestCase,
    Statistics
)


class TestStrategies:
    """Test basic strategies"""
    
    @staticmethod
    def test_integer_strategy():
        """Test integer generation"""
        strategy = integers(min_value=0, max_value=10)
        values = strategy.examples(50)
        
        assert all(isinstance(v, int) for v in values)
        assert all(0 <= v <= 10 for v in values)
        print("✓ Integer strategy works")
    
    @staticmethod
    def test_float_strategy():
        """Test float generation"""
        strategy = floats(min_value=0.0, max_value=1.0)
        values = strategy.examples(50)
        
        assert all(isinstance(v, float) for v in values)
        assert all(0.0 <= v <= 1.0 for v in values)
        print("✓ Float strategy works")
    
    @staticmethod
    def test_boolean_strategy():
        """Test boolean generation"""
        strategy = booleans()
        values = strategy.examples(50)
        
        assert all(isinstance(v, bool) for v in values)
        assert True in values
        assert False in values
        print("✓ Boolean strategy works")
    
    @staticmethod
    def test_text_strategy():
        """Test text generation"""
        strategy = text(min_size=0, max_size=20)
        values = strategy.examples(50)
        
        assert all(isinstance(v, str) for v in values)
        assert all(len(v) <= 20 for v in values)
        print("✓ Text strategy works")
    
    @staticmethod
    def test_list_strategy():
        """Test list generation"""
        strategy = lists(integers(), min_size=0, max_size=5)
        values = strategy.examples(50)
        
        assert all(isinstance(v, list) for v in values)
        assert all(len(v) <= 5 for v in values)
        assert all(all(isinstance(x, int) for x in v) for v in values)
        print("✓ List strategy works")
    
    @staticmethod
    def test_tuple_strategy():
        """Test tuple generation"""
        strategy = tuples(integers(), text(), booleans())
        values = strategy.examples(50)
        
        assert all(isinstance(v, tuple) for v in values)
        assert all(len(v) == 3 for v in values)
        assert all(isinstance(v[0], int) for v in values)
        assert all(isinstance(v[1], str) for v in values)
        assert all(isinstance(v[2], bool) for v in values)
        print("✓ Tuple strategy works")
    
    @staticmethod
    def test_dictionary_strategy():
        """Test dictionary generation"""
        strategy = dictionaries(text(max_size=5), integers(), max_size=5)
        values = strategy.examples(50)
        
        assert all(isinstance(v, dict) for v in values)
        assert all(len(v) <= 5 for v in values)
        print("✓ Dictionary strategy works")
    
    @staticmethod
    def test_just_strategy():
        """Test just strategy"""
        strategy = just(42)
        values = strategy.examples(50)
        
        assert all(v == 42 for v in values)
        print("✓ Just strategy works")
    
    @staticmethod
    def test_sampled_from_strategy():
        """Test sampled_from strategy"""
        choices = [1, 2, 3, 4, 5]
        strategy = sampled_from(choices)
        values = strategy.examples(50)
        
        assert all(v in choices for v in values)
        print("✓ Sampled_from strategy works")
    
    @staticmethod
    def test_one_of_strategy():
        """Test one_of strategy"""
        strategy = one_of(just(1), just(2), just(3))
        values = strategy.examples(50)
        
        assert all(v in [1, 2, 3] for v in values)
        print("✓ One_of strategy works")


class TestStrategyTransformations:
    """Test strategy transformations"""
    
    @staticmethod
    def test_map():
        """Test map transformation"""
        strategy = integers(0, 10).map(lambda x: x * 2)
        values = strategy.examples(50)
        
        assert all(v % 2 == 0 for v in values)
        assert all(0 <= v <= 20 for v in values)
        print("✓ Map transformation works")
    
    @staticmethod
    def test_filter():
        """Test filter transformation"""
        strategy = integers(0, 10).filter(lambda x: x % 2 == 0)
        values = strategy.examples(10)
        
        assert all(v % 2 == 0 for v in values)
        print("✓ Filter transformation works")


class TestPropertyTest:
    """Test property-based testing"""
    
    @staticmethod
    def test_property_runner():
        """Test running a property test"""
        def test_func(x):
            assert x >= 0
        
        runner = PropertyTest(max_examples=50)
        success = runner.run_test(test_func, [integers(min_value=0)])
        
        assert success
        assert len(runner.test_cases) == 50
        assert len(runner.failures) == 0
        print("✓ Property test runner works")
    
    @staticmethod
    def test_property_failure():
        """Test detecting failures"""
        def test_func(x):
            assert x < 5  # This will fail for large values
        
        runner = PropertyTest(max_examples=50)
        success = runner.run_test(test_func, [integers(min_value=0, max_value=10)])
        
        assert not success
        assert len(runner.failures) > 0
        print("✓ Property test failure detection works")
    
    @staticmethod
    def test_report():
        """Test report generation"""
        def test_func(x):
            assert x < 5
        
        runner = PropertyTest(max_examples=50)
        runner.run_test(test_func, [integers(min_value=0, max_value=10)])
        
        report = runner.report()
        assert 'Total examples' in report
        assert 'Passed' in report
        assert 'Failed' in report
        print("✓ Report generation works")


class TestGivenDecorator:
    """Test @given decorator"""
    
    @staticmethod
    def test_given_basic():
        """Test basic @given usage"""
        test_passed = False
        
        @given(integers(0, 10))
        def test_positive(x):
            nonlocal test_passed
            assert x >= 0
            test_passed = True
        
        test_positive(max_examples=10)
        assert test_passed
        print("✓ @given decorator works")
    
    @staticmethod
    def test_given_multiple_args():
        """Test @given with multiple arguments"""
        @given(integers(), integers())
        def test_addition_commutative(a, b):
            assert a + b == b + a
        
        test_addition_commutative(max_examples=50)
        print("✓ @given with multiple args works")
    
    @staticmethod
    def test_given_with_lists():
        """Test @given with list strategy"""
        @given(lists(integers()))
        def test_list_length_nonnegative(lst):
            assert len(lst) >= 0
        
        test_list_length_nonnegative(max_examples=50)
        print("✓ @given with lists works")


class TestRealProperties:
    """Test real mathematical properties"""
    
    @staticmethod
    def test_reverse_twice():
        """Test that reversing twice gives original"""
        @given(lists(integers()))
        def test_prop(lst):
            assert list(reversed(list(reversed(lst)))) == lst
        
        test_prop(max_examples=100)
        print("✓ Reverse twice property works")
    
    @staticmethod
    def test_sort_idempotent():
        """Test that sorting twice is same as sorting once"""
        @given(lists(integers()))
        def test_prop(lst):
            assert sorted(sorted(lst)) == sorted(lst)
        
        test_prop(max_examples=100)
        print("✓ Sort idempotent property works")
    
    @staticmethod
    def test_append_length():
        """Test that appending increases length by 1"""
        @given(lists(integers()), integers())
        def test_prop(lst, x):
            original_length = len(lst)
            lst.append(x)
            assert len(lst) == original_length + 1
        
        test_prop(max_examples=100)
        print("✓ Append length property works")
    
    @staticmethod
    def test_string_concat_associative():
        """Test string concatenation is associative"""
        @given(text(max_size=10), text(max_size=10), text(max_size=10))
        def test_prop(a, b, c):
            assert (a + b) + c == a + (b + c)
        
        test_prop(max_examples=100)
        print("✓ String concatenation associative property works")


class TestStatistics:
    """Test statistics collection"""
    
    @staticmethod
    def test_statistics_basic():
        """Test basic statistics"""
        stats = Statistics()
        
        for i in range(10):
            stats.record(i)
        
        summary = stats.summary()
        assert summary['count'] == 10
        assert summary['min'] == 0
        assert summary['max'] == 9
        print("✓ Statistics collection works")


class TestTestCase:
    """Test TestCase dataclass"""
    
    @staticmethod
    def test_testcase_creation():
        """Test creating test cases"""
        tc = TestCase(args=[1, 2, 3], kwargs={'x': 4})
        
        assert tc.args == [1, 2, 3]
        assert tc.kwargs == {'x': 4}
        assert tc.passed == True
        assert tc.exception is None
        print("✓ TestCase creation works")


def run_all_tests():
    """Run all tests"""
    print("Testing Hypothesis Emulator\n")
    print("=" * 50)
    
    # Strategy tests
    print("\nTesting Strategies:")
    TestStrategies.test_integer_strategy()
    TestStrategies.test_float_strategy()
    TestStrategies.test_boolean_strategy()
    TestStrategies.test_text_strategy()
    TestStrategies.test_list_strategy()
    TestStrategies.test_tuple_strategy()
    TestStrategies.test_dictionary_strategy()
    TestStrategies.test_just_strategy()
    TestStrategies.test_sampled_from_strategy()
    TestStrategies.test_one_of_strategy()
    
    # Transformation tests
    print("\nTesting Strategy Transformations:")
    TestStrategyTransformations.test_map()
    TestStrategyTransformations.test_filter()
    
    # Property test runner tests
    print("\nTesting PropertyTest:")
    TestPropertyTest.test_property_runner()
    TestPropertyTest.test_property_failure()
    TestPropertyTest.test_report()
    
    # @given decorator tests
    print("\nTesting @given Decorator:")
    TestGivenDecorator.test_given_basic()
    TestGivenDecorator.test_given_multiple_args()
    TestGivenDecorator.test_given_with_lists()
    
    # Real property tests
    print("\nTesting Real Properties:")
    TestRealProperties.test_reverse_twice()
    TestRealProperties.test_sort_idempotent()
    TestRealProperties.test_append_length()
    TestRealProperties.test_string_concat_associative()
    
    # Statistics tests
    print("\nTesting Statistics:")
    TestStatistics.test_statistics_basic()
    
    # TestCase tests
    print("\nTesting TestCase:")
    TestTestCase.test_testcase_creation()
    
    print("\n" + "=" * 50)
    print("All tests passed! ✓")


if __name__ == '__main__':
    run_all_tests()
