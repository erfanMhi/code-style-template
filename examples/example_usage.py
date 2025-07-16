#!/usr/bin/env python3
"""
Example usage of the AST-based Python to Q translator for MBPP tests.

This demonstrates how to translate Python test assertions to Q (KDB+) syntax
with proper type handling and syntax generation.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from q_translator import QTranslator, TranslatorQ


def example_basic_translation():
    """Demonstrate basic expression translation."""
    print("=== Basic Expression Translation ===")
    
    translator = QTranslator()
    
    examples = [
        "[1, 2, 3]",
        "{'key': 'value', 'num': 42}",
        "(1, 'hello', 3.14)",
        "func(1, 2, 3)",
        "set([1, 2, 3])"
    ]
    
    for expr in examples:
        q_code = translator.translate_expression(expr)
        print(f"Python: {expr}")
        print(f"Q:      {q_code}")
        print()


def example_mbpp_tests():
    """Demonstrate MBPP test translation."""
    print("=== MBPP Test Translation ===")
    
    translator = QTranslator()
    
    test_cases = [
        "assert add_numbers(5, 3) == 8",
        "assert reverse_list([1, 2, 3]) == [3, 2, 1]",
        "assert is_prime(7) == True",
        "assert get_dict() == {'a': 1, 'b': 2}",
        "assert matrix_multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]]) == [[19, 22], [43, 50]]"
    ]
    
    for test in test_cases:
        q_test = translator.translate_assertion(test)
        print(f"Python: {test}")
        print(f"Q:      {q_test.strip()}")
        print()


def example_test_suite():
    """Demonstrate complete test suite generation."""
    print("=== Complete Test Suite ===")
    
    translator = QTranslator()
    
    # Function header
    header = translator.translate_function_header(
        "factorial",
        ["n"],
        "Calculate the factorial of a non-negative integer.\nReturns n! = n * (n-1) * ... * 1"
    )
    
    print("Function Header:")
    print(header)
    
    # Test cases
    tests = [
        "assert factorial(0) == 1",
        "assert factorial(1) == 1",
        "assert factorial(5) == 120",
        "assert factorial(6) == 720"
    ]
    
    # Generate test suite
    suite = translator.translate_test_suite(tests, "factorial")
    
    print("Test Suite:")
    print(suite)


def example_complex_mbpp():
    """Demonstrate complex MBPP-style test cases."""
    print("=== Complex MBPP Examples ===")
    
    translator = TranslatorQ()  # Using legacy interface for compatibility
    
    complex_tests = [
        # Matrix operations
        "assert matrix_to_list([[(4, 5), (7, 8)], [(10, 13), (18, 17)]]) == [(4, 7, 10, 18), (5, 8, 13, 17)]",
        
        # Dictionary operations  
        "assert filter_data({'Alice': (25, 85), 'Bob': (30, 90)}, 26, 88) == {'Bob': (30, 90)}",
        
        # String processing
        "assert remove_spaces('Hello World Test') == 'HelloWorldTest'",
        
        # Mixed type operations
        "assert increment_numbers(['abc', '123', 'def', '456'], 10) == ['abc', '133', 'def', '466']",
        
        # Boolean operations
        "assert all_prime([2, 3, 5, 7]) == True",
        
        # Set operations
        "assert unique_elements([1, 2, 2, 3, 3, 3]) == {1, 2, 3}",
        
        # Nested function calls
        "assert max_value(min_list([1, 2, 3]), max_list([4, 5, 6])) == 6"
    ]
    
    for test in complex_tests:
        try:
            q_test = translator.compile_mbpp_test(test)
            print(f"✓ Translated: {test[:50]}...")
            print(f"  Q: {q_test.strip()}")
            print()
        except Exception as e:
            print(f"✗ Failed: {test[:50]}...")
            print(f"  Error: {e}")
            print()


def example_data_structure_handling():
    """Demonstrate advanced data structure handling."""
    print("=== Data Structure Handling ===")
    
    translator = QTranslator()
    
    structures = [
        # Empty collections
        ("[]", "Empty list"),
        ("{}", "Empty dict"),
        ("set()", "Empty set"),
        
        # Homogeneous collections
        ("[1, 2, 3, 4, 5]", "Integer list"),
        ("[1.1, 2.2, 3.3]", "Float list"),
        ("['a', 'b', 'c']", "String list"),
        ("[True, False, True]", "Boolean list"),
        
        # Heterogeneous collections
        ("[1, 'hello', 3.14, True]", "Mixed list"),
        ("(42, 'answer', [1, 2, 3])", "Mixed tuple"),
        
        # Nested structures
        ("[[1, 2], [3, 4], [5, 6]]", "Matrix"),
        ("[{'name': 'Alice', 'age': 25}, {'name': 'Bob', 'age': 30}]", "List of dicts"),
        ("{'matrix': [[1, 2], [3, 4]], 'vector': [1, 2, 3]}", "Dict with nested data"),
        
        # Complex nesting
        ("[[[1, 2], [3, 4]], [[5, 6], [7, 8]]]", "3D structure")
    ]
    
    for expr, description in structures:
        try:
            q_code = translator.translate_expression(expr)
            print(f"{description}:")
            print(f"  Python: {expr}")
            print(f"  Q:      {q_code}")
            print()
        except Exception as e:
            print(f"{description}: FAILED - {e}")
            print()


def main():
    """Run all examples."""
    print("Python to Q (KDB+) Translator Examples")
    print("=" * 50)
    print()
    
    example_basic_translation()
    print("\n" + "=" * 50 + "\n")
    
    example_mbpp_tests()
    print("\n" + "=" * 50 + "\n")
    
    example_test_suite()
    print("\n" + "=" * 50 + "\n")
    
    example_data_structure_handling()
    print("\n" + "=" * 50 + "\n")
    
    example_complex_mbpp()
    
    print("\nTranslation complete! The Q code can be executed in a KDB+/q environment.")


if __name__ == "__main__":
    main()