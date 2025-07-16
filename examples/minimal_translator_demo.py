#!/usr/bin/env python3
"""
Demonstration of the minimal Python to Q translator for MBPP test assertions.
Shows accurate Q syntax generation with minimal code complexity.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from minimal_q_translator import QTranslator


def demo_basic_translations():
    """Show basic function call translations."""
    print("=== Basic Function Call Translations ===")
    
    translator = QTranslator()
    
    examples = [
        "assert add(1, 2) == 3",
        "assert factorial(5) == 120", 
        "assert is_prime(7) == True",
        "assert reverse_string('hello') == 'olleh'",
        "assert max_of_three(1, 5, 3) == 5"
    ]
    
    for test in examples:
        q_result = translator.translate_test(test)
        print(f"Python: {test}")
        print(f"Q:      {q_result}")
        print()


def demo_data_structure_translations():
    """Show data structure translations."""
    print("=== Data Structure Translations ===")
    
    translator = QTranslator()
    
    examples = [
        # Lists and vectors
        "assert sort_list([3, 1, 4, 1, 5]) == [1, 1, 3, 4, 5]",
        "assert reverse_list(['a', 'b', 'c']) == ['c', 'b', 'a']",
        
        # Tuples (treated as lists in Q)  
        "assert get_coordinates() == (10, 20)",
        "assert parse_tuple('(1,2,3)') == (1, 2, 3)",
        
        # Dictionaries
        "assert word_count('hello') == {'h': 1, 'e': 1, 'l': 2, 'o': 1}",
        "assert invert_dict({1: 'a', 2: 'b'}) == {'a': 1, 'b': 2}",
        
        # Sets (treated as lists in Q)
        "assert unique_elements([1, 2, 2, 3, 3, 3]) == {1, 2, 3}",
        "assert set_intersection({1, 2, 3}, {2, 3, 4}) == {2, 3}",
        
        # Nested structures
        "assert matrix_transpose([[1, 2], [3, 4]]) == [[1, 3], [2, 4]]",
        "assert group_by_key([{'type': 'A', 'val': 1}, {'type': 'B', 'val': 2}]) == {'A': [1], 'B': [2]}"
    ]
    
    for test in examples:
        q_result = translator.translate_test(test)
        print(f"Python: {test}")
        print(f"Q:      {q_result}")
        print()


def demo_complex_mbpp_examples():
    """Show complex MBPP-style test translations."""
    print("=== Complex MBPP Examples ===")
    
    translator = QTranslator()
    
    examples = [
        # String processing
        "assert extract_words('hello world test') == ['hello', 'world', 'test']",
        "assert remove_vowels('programming') == 'prgrmmng'",
        "assert capitalize_first('hello world') == 'Hello World'",
        
        # Mathematical operations
        "assert fibonacci_up_to(10) == [0, 1, 1, 2, 3, 5, 8]",
        "assert prime_factors(12) == [2, 2, 3]",
        "assert gcd_list([12, 18, 24]) == 6",
        
        # List operations
        "assert flatten_nested([[1, 2], [3, [4, 5]], 6]) == [1, 2, 3, 4, 5, 6]",
        "assert chunk_list([1, 2, 3, 4, 5, 6], 2) == [[1, 2], [3, 4], [5, 6]]",
        "assert remove_duplicates([1, 2, 2, 3, 1, 4]) == [1, 2, 3, 4]",
        
        # Mixed type operations
        "assert validate_data([1, 'valid', True, None]) == [True, True, True, False]",
        "assert convert_types(['1', '2.5', 'true', 'hello']) == [1, 2.5, True, 'hello']",
        
        # Complex nested operations
        "assert process_students([{'name': 'Alice', 'grades': [85, 90]}, {'name': 'Bob', 'grades': [78, 82]}]) == [{'name': 'Alice', 'avg': 87.5}, {'name': 'Bob', 'avg': 80.0}]",
        "assert merge_sorted_lists([[1, 3, 5], [2, 4, 6], [0, 7, 8]]) == [0, 1, 2, 3, 4, 5, 6, 7, 8]"
    ]
    
    for test in examples:
        q_result = translator.translate_test(test)
        print(f"Python: {test}")
        print(f"Q:      {q_result}")
        print()


def demo_q_syntax_features():
    """Demonstrate specific Q syntax features generated."""
    print("=== Q Syntax Features Demonstrated ===")
    
    translator = QTranslator()
    
    print("1. Space notation for homogeneous lists:")
    print(f"   {translator.translate_test('assert func() == [1, 2, 3, 4, 5]')}")
    print()
    
    print("2. Compact symbol notation:")
    print(f"   {translator.translate_test('assert func() == [\"a\", \"b\", \"c\"]')}")
    print()
    
    print("3. Semicolon notation for mixed types:")
    print(f"   {translator.translate_test('assert func() == [1, \"hello\", 3.14, True]')}")
    print()
    
    print("4. Dictionary syntax with symbols:")
    print(f"   {translator.translate_test('assert func() == {\"key1\": \"val1\", \"key2\": \"val2\"}')}")
    print()
    
    print("5. Nested list syntax:")
    print(f"   {translator.translate_test('assert func() == [[1, 2], [3, 4], [5, 6]]')}")
    print()
    
    print("6. Function call syntax:")
    print(f"   {translator.translate_test('assert outer(inner(1, 2), 3) == result')}")
    print()
    
    print("7. Boolean and null handling:")
    print(f"   {translator.translate_test('assert func() == [True, False, None]')}")
    print()
    
    print("8. Float notation with 'f' suffix:")
    print(f"   {translator.translate_test('assert func() == [1.5, 2.7, 3.14159]')}")
    print()


def main():
    """Run all demonstration examples."""
    print("Minimal Python to Q (KDB+) Translator Demonstration")
    print("=" * 60)
    print()
    
    demo_basic_translations()
    print("\n" + "=" * 60 + "\n")
    
    demo_data_structure_translations()
    print("\n" + "=" * 60 + "\n")
    
    demo_complex_mbpp_examples()
    print("\n" + "=" * 60 + "\n")
    
    demo_q_syntax_features()
    
    print("=" * 60)
    print("\nKey Q Syntax Features:")
    print("• Match operator (~) for equality testing")
    print("• Space notation for homogeneous atoms: 1 2 3")
    print("• Semicolon notation for mixed types: (1;`hello;3.14f)")
    print("• Compact symbol notation: `a`b`c")
    print("• Dictionary syntax: key!value")
    print("• Function calls: func[arg1;arg2;arg3]")
    print("• Proper type suffixes: 1b (bool), 3.14f (float), 0N (null)")
    print("\nThe generated Q code is ready to run in any KDB+ environment!")


if __name__ == "__main__":
    main()