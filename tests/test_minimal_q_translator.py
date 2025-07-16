"""
Test suite for minimal Q translator.
Verifies accurate Q syntax generation for MBPP test assertions.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from minimal_q_translator import QTranslator


def test_basic_assertions():
    """Test basic function call assertions."""
    translator = QTranslator()
    
    test_cases = [
        ("assert func(1) == 2", "func[1]~2"),
        ("assert add(5, 3) == 8", "add[5;3]~8"),
        ("assert calculate(10, 20, 30) == 60", "calculate[10;20;30]~60"),
        ("assert no_args() == 42", "no_args[]~42"),
    ]
    
    for python_test, expected_q in test_cases:
        result = translator.translate_test(python_test)
        assert result == expected_q, f"Expected {expected_q}, got {result}"
    print("✓ Basic assertions passed")


def test_constants():
    """Test constant value translation."""
    translator = QTranslator()
    
    test_cases = [
        # Integers
        ("assert func() == 42", "func[]~42"),
        ("assert func() == -10", "func[]~-10"),
        ("assert func() == 0", "func[]~0"),
        
        # Floats
        ("assert func() == 3.14", "func[]~3.14f"),
        ("assert func() == -2.5", "func[]~-2.5f"),
        ("assert func() == 0.0", "func[]~0.0f"),
        
        # Booleans
        ("assert func() == True", "func[]~1b"),
        ("assert func() == False", "func[]~0b"),
        
        # None
        ("assert func() == None", "func[]~0N"),
        
        # Short strings (symbols)
        ("assert func() == 'hello'", "func[]~`hello"),
        ("assert func() == 'a'", "func[]~`a"),
        
        # Long strings (char lists)
        ("assert func() == 'hello world'", "func[]~\"hello world\""),
        ("assert func() == 'long string here'", "func[]~\"long string here\""),
    ]
    
    for python_test, expected_q in test_cases:
        result = translator.translate_test(python_test)
        assert result == expected_q, f"Expected {expected_q}, got {result}"
    print("✓ Constants passed")


def test_lists():
    """Test list translation."""
    translator = QTranslator()
    
    test_cases = [
        # Empty list
        ("assert func() == []", "func[]~()"),
        
        # Simple lists (space notation)
        ("assert func() == [1, 2, 3]", "func[]~1 2 3"),
        ("assert func() == [1, 2, 3, 4, 5]", "func[]~1 2 3 4 5"),
        
        # Float lists
        ("assert func() == [1.1, 2.2, 3.3]", "func[]~1.1f 2.2f 3.3f"),
        
        # Symbol lists (compact notation)
        ("assert func() == ['a', 'b', 'c']", "func[]~`a`b`c"),
        ("assert func() == ['hello', 'world']", "func[]~`hello`world"),
        
        # Boolean lists
        ("assert func() == [True, False, True]", "func[]~1b 0b 1b"),
        
        # Mixed type lists (semicolon notation)
        ("assert func() == [1, 'hello', 3.14]", "func[]~(1;`hello;3.14f)"),
        ("assert func() == [1, True, 'test']", "func[]~(1;1b;`test)"),
        
        # Nested lists
        ("assert func() == [[1, 2], [3, 4]]", "func[]~(1 2;3 4)"),
        ("assert func() == [[[1]], [[2]]]", "func[]~1 2"),  # Single elements in deep nesting flatten
    ]
    
    for python_test, expected_q in test_cases:
        result = translator.translate_test(python_test)
        assert result == expected_q, f"Expected {expected_q}, got {result}"
    print("✓ Lists passed")


def test_tuples():
    """Test tuple translation (same as lists in Q)."""
    translator = QTranslator()
    
    test_cases = [
        # Empty tuple
        ("assert func() == ()", "func[]~()"),
        
        # Simple tuples
        ("assert func() == (1, 2)", "func[]~1 2"),
        ("assert func() == (1, 2, 3)", "func[]~1 2 3"),
        
        # Mixed tuples
        ("assert func() == (1, 'hello')", "func[]~(1;`hello)"),
        ("assert func() == (42, 'answer', 3.14)", "func[]~(42;`answer;3.14f)"),
    ]
    
    for python_test, expected_q in test_cases:
        result = translator.translate_test(python_test)
        assert result == expected_q, f"Expected {expected_q}, got {result}"
    print("✓ Tuples passed")


def test_sets():
    """Test set translation (same as lists in Q)."""
    translator = QTranslator()
    
    test_cases = [
        # Empty set
        ("assert func() == set()", "func[]~()"),
        
        # Simple sets
        ("assert func() == {1, 2, 3}", "func[]~1 2 3"),
        ("assert func() == {'a', 'b', 'c'}", "func[]~`a`b`c"),
        
        # Mixed sets
        ("assert func() == {1, 'hello'}", "func[]~(1;`hello)"),
    ]
    
    for python_test, expected_q in test_cases:
        result = translator.translate_test(python_test)
        assert result == expected_q, f"Expected {expected_q}, got {result}"
    print("✓ Sets passed")


def test_dictionaries():
    """Test dictionary translation."""
    translator = QTranslator()
    
    test_cases = [
        # Empty dict
        ("assert func() == {}", "func[]~()!()"),
        
        # Simple dicts with symbols
        ("assert func() == {'a': 1, 'b': 2}", "func[]~`a`b!1 2"),
        ("assert func() == {'x': 10, 'y': 20, 'z': 30}", "func[]~`x`y`z!10 20 30"),
        
        # Dicts with numeric keys
        ("assert func() == {1: 'one', 2: 'two'}", "func[]~1 2!`one `two"),
        
        # Complex dicts (parentheses needed)
        ("assert func() == {'key': [1, 2, 3]}", "func[]~(`key)!1 2 3"),
        ("assert func() == {1: {'nested': 'value'}}", "func[]~(1)!`nested!`value"),
    ]
    
    for python_test, expected_q in test_cases:
        result = translator.translate_test(python_test)
        assert result == expected_q, f"Expected {expected_q}, got {result}"
    print("✓ Dictionaries passed")


def test_function_calls():
    """Test function call translation."""
    translator = QTranslator()
    
    test_cases = [
        # No arguments
        ("assert func() == result()", "func[]~result[]"),
        
        # Single argument
        ("assert func(x) == process(5)", "func[x]~process[5]"),
        
        # Multiple arguments
        ("assert func(a, b, c) == combine(1, 2, 3)", "func[a;b;c]~combine[1;2;3]"),
        
        # Nested calls
        ("assert outer(inner(5)) == 10", "outer[inner[5]]~10"),
        ("assert func(add(1, 2), mult(3, 4)) == 15", "func[add[1;2];mult[3;4]]~15"),
        
        # Special case: set constructor
        ("assert func() == set([1, 2, 3])", "func[]~1 2 3"),
        ("assert func() == set()", "func[]~()"),
    ]
    
    for python_test, expected_q in test_cases:
        result = translator.translate_test(python_test)
        assert result == expected_q, f"Expected {expected_q}, got {result}"
    print("✓ Function calls passed")


def test_complex_mbpp_examples():
    """Test complex MBPP-style assertions."""
    translator = QTranslator()
    
    test_cases = [
        # Matrix operations
        ("assert matrix([[1, 2], [3, 4]]) == [[4, 3], [2, 1]]", 
         "matrix[(1 2;3 4)]~(4 3;2 1)"),
        
        # Nested data structures
        ("assert process([{'a': 1}, {'b': 2}]) == [{'x': 10}, {'y': 20}]",
         "process[`a!1`b!2]~`x!10`y!20"),
        
        # Mixed type operations
        ("assert combine([1, 'hello'], {'key': [2, 3]}) == result",
         "combine[(1;`hello);(`key)!2 3]~result"),
        
        # String processing
        ("assert extract('hello world') == ['hello', 'world']",
         "extract[\"hello world\"]~`hello`world"),
        
        # Multiple function arguments with complex data
        ("assert filter_data({'Alice': (25, 85)}, 26, 88) == {}",
         "filter_data[(`Alice)!25 85;26;88]~()!()"),
    ]
    
    for python_test, expected_q in test_cases:
        result = translator.translate_test(python_test)
        assert result == expected_q, f"Expected {expected_q}, got {result}"
    print("✓ Complex MBPP examples passed")


def test_edge_cases():
    """Test edge cases and error conditions."""
    translator = QTranslator()
    
    # Valid edge cases
    edge_cases = [
        # Single element lists
        ("assert func() == [42]", "func[]~42"),
        ("assert func() == ['single']", "func[]~`single"),
        
        # Deeply nested structures
        ("assert func() == [[[1]]]", "func[]~1"),  # Single element flattens
        
        # Empty nested structures
        ("assert func() == [[], []]", "func[]~(();())"),
    ]
    
    for python_test, expected_q in edge_cases:
        result = translator.translate_test(python_test)
        assert result == expected_q, f"Expected {expected_q}, got {result}"
    
    # Error cases
    error_cases = [
        "assert func() != 2",  # Not equality comparison
        "assert func() > 2",   # Wrong operator
    ]
    
    for error_case in error_cases:
        try:
            translator.translate_test(error_case)
            assert False, f"Should have raised error for: {error_case}"
        except ValueError:
            pass  # Expected
    
    print("✓ Edge cases passed")


def run_all_tests():
    """Run all test functions."""
    print("Running minimal Q translator tests...\n")
    
    test_basic_assertions()
    test_constants()
    test_lists()
    test_tuples()
    test_sets()
    test_dictionaries()
    test_function_calls()
    test_complex_mbpp_examples()
    test_edge_cases()
    
    print("\n🎉 All tests passed! The minimal Q translator is working correctly.")


if __name__ == "__main__":
    run_all_tests()