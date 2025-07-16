"""
Comprehensive test suite for the AST-based Python to Q translator.

Tests focus on MBPP dataset compatibility and correct Q code generation
with proper type handling and syntax.
"""

import pytest
import ast
from typing import Any, List, Tuple
from src.q_translator import QTranslator, TranslatorQ, QType, QExpression


@pytest.fixture
def translator() -> TranslatorQ:
    """Create a fresh translator instance for each test."""
    return TranslatorQ()


@pytest.fixture
def new_translator() -> QTranslator:
    """Create a fresh new translator instance for each test."""
    return QTranslator()


# ========== Core AST Translation Tests ==========

@pytest.mark.parametrize(
    "value,expected_code,expected_type",
    [
        # Boolean literals
        (True, "1b", QType.ATOM_BOOL),
        (False, "0b", QType.ATOM_BOOL),
        
        # Integer literals
        (42, "42", QType.ATOM_LONG),
        (-10, "-10", QType.ATOM_LONG),
        (0, "0", QType.ATOM_LONG),
        
        # Float literals
        (3.14, "3.14", QType.ATOM_FLOAT),
        (-2.5, "-2.5", QType.ATOM_FLOAT),
        (0.0, "0.0", QType.ATOM_FLOAT),
        
        # String literals - symbols
        ("abc", "`abc", QType.ATOM_SYMBOL),
        ("test123", "`test123", QType.ATOM_SYMBOL),
        ("x", "`x", QType.ATOM_SYMBOL),
        
        # String literals - char lists
        ("hello world", '"hello world"', QType.ATOM_CHAR),
        ("line1\nline2", '"line1\nline2"', QType.ATOM_CHAR),
        ("has`backtick", '"has`backtick"', QType.ATOM_CHAR),
        ("very_long_string_that_exceeds_symbol_limit", '"very_long_string_that_exceeds_symbol_limit"', QType.ATOM_CHAR),
        
        # None/null
        (None, "::", QType.NULL),
    ]
)
def test_constant_translation(new_translator: QTranslator, value: Any, expected_code: str, expected_type: QType) -> None:
    """Test basic constant translation using AST walker."""
    walker = new_translator.walker
    node = ast.Constant(value=value)
    result = walker.visit_Constant(node)
    
    assert result.code == expected_code
    assert result.qtype == expected_type
    assert result.is_scalar == True


@pytest.mark.parametrize(
    "python_expr,expected_q",
    [
        # Empty collections
        ("[]", "()"),
        ("{}", "()!()"),
        ("set()", "()"),
        
        # Homogeneous lists
        ("[1, 2, 3]", "1 2 3"),
        ("[1.0, 2.5, 3.14]", "1.0 2.5 3.14"),
        ("['a', 'b', 'c']", "`a `b `c"),
        ("[True, False, True]", "1b 0b 1b"),
        
        # Heterogeneous lists
        ("[1, 'hello', 3.14]", '(1;`hello;3.14)'),
        ("[1, [2, 3], 'test']", '(1;2 3;`test)'),
        
        # Tuples (same as lists in Q)
        ("(1, 2, 3)", "1 2 3"),
        ("(1, 'hello', 3.14)", '(1;`hello;3.14)'),
        
        # Sets (same as lists in Q)
        ("{1, 2, 3}", "1 2 3"),
        ("{'a', 'b', 'c'}", "`a `b `c"),
        
        # Dictionaries
        ("{'a': 1, 'b': 2}", "(`a `b)!(1 2)"),
        ("{1: 'one', 2: 'two'}", "(1 2)!(`one `two)"),
        
        # Function calls
        ("func(1, 2, 3)", "func[1;2;3]"),
        ("set([1, 2, 3])", "1 2 3"),
        ("max(a, b)", "max[a;b]"),
        
        # Variables
        ("x", "x"),
        ("variable_name", "variable_name"),
        
        # Complex nested structures
        ("[[1, 2], [3, 4]]", "(1 2;3 4)"),
        ("[{'a': 1}, {'b': 2}]", "((`a)!(1);(`b)!(2))"),
    ]
)
def test_expression_translation(new_translator: QTranslator, python_expr: str, expected_q: str) -> None:
    """Test complete expression translation from Python to Q."""
    result = new_translator.translate_expression(python_expr)
    assert result == expected_q


# ========== MBPP Test Assertion Translation ==========

@pytest.mark.parametrize(
    "assert_stmt,expected_contains",
    [
        # Simple equality tests
        ("assert func(1) == 2", [".qunit.assertEquals", "func[1]", "2", "equality test"]),
        ("assert add(5, 3) == 8", [".qunit.assertEquals", "add[5;3]", "8", "equality test"]),
        
        # String comparisons
        ('assert get_name("test") == "result"', [".qunit.assertEquals", "get_name[`test]", '"result"', "equality test"]),
        ("assert first_char('hello') == 'h'", [".qunit.assertEquals", "first_char[`hello]", "`h", "equality test"]),
        
        # List comparisons
        ("assert sort_list([3, 1, 2]) == [1, 2, 3]", [".qunit.assertEquals", "sort_list[3 1 2]", "1 2 3", "equality test"]),
        ("assert reverse(['a', 'b', 'c']) == ['c', 'b', 'a']", [".qunit.assertEquals", "reverse[`a `b `c]", "`c `b `a", "equality test"]),
        
        # Boolean comparisons
        ("assert is_prime(7) == True", [".qunit.assertEquals", "is_prime[7]", "1b", "equality test"]),
        ("assert is_even(3) == False", [".qunit.assertEquals", "is_even[3]", "0b", "equality test"]),
        
        # Complex data structures
        ("assert get_dict() == {'key': 'value'}", [".qunit.assertEquals", "get_dict[]", "(`key)!(`value)", "equality test"]),
        ("assert matrix_op([[1, 2], [3, 4]]) == [[4, 3], [2, 1]]", [".qunit.assertEquals", "matrix_op[(1 2;3 4)]", "(4 3;2 1)", "equality test"]),
    ]
)
def test_assertion_translation(new_translator: QTranslator, assert_stmt: str, expected_contains: List[str]) -> None:
    """Test MBPP assertion translation to Q test syntax."""
    result = new_translator.translate_assertion(assert_stmt)
    
    for expected in expected_contains:
        assert expected in result
    
    # Should be indented
    assert result.startswith("\t")


def test_test_suite_generation(new_translator: QTranslator) -> None:
    """Test complete test suite generation."""
    test_list = [
        "assert func(1) == 2",
        "assert func(2) == 4", 
        "assert func(3) == 6"
    ]
    
    result = new_translator.translate_test_suite(test_list, "func")
    
    # Check structure
    assert ")" in result  # Closes previous definition
    assert "test:{[func]" in result
    assert "}" in result  # Closes test function
    
    # Check test content
    assert ".qunit.assertEquals[func[1]; 2; \"equality test\"]" in result
    assert ".qunit.assertEquals[func[2]; 4; \"equality test\"]" in result
    assert ".qunit.assertEquals[func[3]; 6; \"equality test\"]" in result
    
    # Check comments
    assert "/ Test 1" in result
    assert "/ Test 2" in result
    assert "/ Test 3" in result


# ========== Legacy Compatibility Tests ==========

@pytest.mark.parametrize(
    "value,expected,ast_type",
    [
        (True, "1b", "bool"),
        (False, "0b", "bool"),
        (42, "42", "int"),
        (-10, "-10", "int"),
        (3.14, "3.14", "float"),
        (-2.5, "-2.5", "float"),
        ("abc", "`abc", "str"),
        ("hello world", '"hello world"', "str"),
        (None, "::", "None"),
    ]
)
def test_legacy_gen_literal(translator: TranslatorQ, value: Any, expected: str, ast_type: str) -> None:
    """Test legacy literal generation for backward compatibility."""
    result, typ = translator.gen_literal(value)
    assert result == expected
    assert isinstance(typ, ast.Name)
    assert typ.id == ast_type


@pytest.mark.parametrize(
    "items,expected",
    [
        ([], "()"),
        ([("1", ast.Name("int")), ("2", ast.Name("int")), ("3", ast.Name("int"))], "1 2 3"),
        ([("1.0", ast.Name("float")), ("2.5", ast.Name("float")), ("3.14", ast.Name("float"))], "1.0 2.5 3.14"),
        ([("`a", ast.Name("str")), ("`b", ast.Name("str")), ("`c", ast.Name("str"))], "`a `b `c"),
        ([("1", ast.Name("int")), ("`two", ast.Name("str")), ("3.0", ast.Name("float"))], "(1;`two;3.0)"),
        ([("1", ast.Name("int"))], "1"),
    ]
)
def test_legacy_gen_list(translator: TranslatorQ, items: Any, expected: str) -> None:
    """Test legacy list generation."""
    result, _ = translator.gen_list(items)
    assert result == expected


@pytest.mark.parametrize(
    "keys,vals,expected",
    [
        ([("`a", ast.Name("str")), ("`b", ast.Name("str"))],
         [("1", ast.Name("int")), ("2", ast.Name("int"))],
         "(`a `b)!(1 2)"),
        ([], [], "()!()"),
    ]
)
def test_legacy_gen_dict(translator: TranslatorQ, keys: Any, vals: Any, expected: str) -> None:
    """Test legacy dictionary generation."""
    result, _ = translator.gen_dict(keys, vals)
    assert result == expected


@pytest.mark.parametrize(
    "func,args,expected",
    [
        (("f", None), [("1", ast.Name("int")), ("2", ast.Name("int"))], "f[1;2]"),
        (("func", None), [("`hello", ast.Name("str")), ("`world", ast.Name("str"))], "func[`hello;`world]"),
    ]
)
def test_legacy_gen_call(translator: TranslatorQ, func: Any, args: Any, expected: str) -> None:
    """Test legacy function call generation."""
    result, typ = translator.gen_call(func, args)
    assert result == expected
    assert typ is None


# ========== Advanced MBPP Test Cases ==========

@pytest.mark.parametrize(
    "test_str,expected_contains",
    [
        # Complex nested structures
        ("assert matrix_to_list([[(4, 5), (7, 8)], [(10, 13), (18, 17)]]) == '[(4, 7, 10, 18), (5, 8, 13, 17)]'",
         ["matrix_to_list", "equality test"]),
        
        # Dictionary operations
        ("assert filter_data({'Cierra Vega': (6.2, 70), 'Alden Cantrell': (5.9, 65)}, 6.0, 70) == {'Cierra Vega': (6.2, 70)}",
         ["filter_data", "equality test"]),
        
        # String processing with special characters
        ("assert remove_extra_char('**//Google Android// - 12. ') == 'GoogleAndroid12'",
         ["remove_extra_char", "equality test"]),
        
        # Mixed type operations
        ("assert increment_numerics(['MSM', '234', 'is', '98'], 6) == ['MSM', '240', 'is', '104']",
         ["increment_numerics", "equality test"]),
        
        # Boolean returns
        ("assert prime_num(13) == True",
         ["prime_num[13]", "1b", "equality test"]),
        
        # Set operations  
        ("assert tuple_intersection([(3, 4), (5, 6)], [(5, 4), (3, 4)]) == {(3, 4)}",
         ["tuple_intersection", "equality test"]),
        
        # Nested function calls
        ("assert max_of_two(min_of_three(1, 2, 3), max_of_three(4, 5, 6)) == 6",
         ["max_of_two[min_of_three[1;2;3];max_of_three[4;5;6]]", "6", "equality test"]),
    ]
)
def test_complex_mbpp_assertions(translator: TranslatorQ, test_str: str, expected_contains: List[str]) -> None:
    """Test complex MBPP assertion patterns."""
    result = translator.compile_mbpp_test(test_str)
    for expected in expected_contains:
        assert expected in result


# ========== Edge Cases and Error Handling ==========

def test_empty_test_suite(new_translator: QTranslator) -> None:
    """Test handling of empty test suite."""
    result = new_translator.translate_test_suite([], "func")
    assert "test:{[func]" in result
    assert "}" in result


def test_function_header_generation(new_translator: QTranslator) -> None:
    """Test Q function header generation."""
    result = new_translator.translate_function_header(
        "add", 
        ["x", "y"], 
        "Add two numbers\nReturns their sum"
    )
    
    assert "/ Add two numbers" in result
    assert "/ Returns their sum" in result
    assert "add:{[x;y]" in result


def test_invalid_expression_error(new_translator: QTranslator) -> None:
    """Test error handling for invalid expressions."""
    with pytest.raises(ValueError, match="Translation error"):
        new_translator.translate_expression("invalid syntax !!!")


def test_homogeneity_detection(new_translator: QTranslator) -> None:
    """Test homogeneity detection for vector vs list generation."""
    walker = new_translator.walker
    
    # Homogeneous integers
    int_exprs = [
        QExpression("1", QType.ATOM_LONG),
        QExpression("2", QType.ATOM_LONG),
        QExpression("3", QType.ATOM_LONG)
    ]
    assert walker._is_homogeneous(int_exprs) == True
    
    # Mixed types
    mixed_exprs = [
        QExpression("1", QType.ATOM_LONG),
        QExpression("`hello", QType.ATOM_SYMBOL),
        QExpression("3.14", QType.ATOM_FLOAT)
    ]
    assert walker._is_homogeneous(mixed_exprs) == False
    
    # Compatible numeric types
    numeric_exprs = [
        QExpression("1", QType.ATOM_LONG),
        QExpression("2.5", QType.ATOM_FLOAT),
        QExpression("3", QType.ATOM_LONG)
    ]
    assert walker._is_homogeneous(numeric_exprs) == True


# ========== Utility Function Tests ==========

@pytest.mark.parametrize(
    "args_str,expected",
    [
        ("a, b, c", ["a", "b", "c"]),
        ("  a  ,  b  ,  c  ", ["a", "b", "c"]),
        ("func(1, 2), [3, 4], {5: 6}", ["func(1, 2)", "[3, 4]", "{5: 6}"]),
        ("'hello, world', \"test\"", ["'hello, world'", '"test"']),
        ("(1, 2), [3, 4, 5]", ["(1, 2)", "[3, 4, 5]"]),
        ("nested_func(a, b, c), dict(x=1, y=2)", ["nested_func(a, b, c)", "dict(x=1, y=2)"]),
        ("", []),
        ("   ", []),
    ]
)
def test_argument_parsing(translator: TranslatorQ, args_str: str, expected: List[str]) -> None:
    """Test robust argument parsing with nested structures."""
    assert translator._parse_arguments(args_str) == expected


@pytest.mark.parametrize(
    "qcode,expected",
    [
        ("`abc", "symbol"),
        ("`test_symbol", "symbol"),
        ("42", "int"),
        ("-10", "int"),
        ("3.14", "float"),
        ("-2.5", "float"),
        ("1 2 3", "vector"),
        ("1.0 2.5 3.14", "vector"),
        ("(`a;`b)!(1;2)", "dict"),
        ("(1;`two;3.0)", "list"),
        ("(1 2 3)", "nested"),
        ("func[1;2]", "other"),
    ]
)
def test_atom_kind_classification(translator: TranslatorQ, qcode: str, expected: str) -> None:
    """Test Q code classification for proper syntax generation."""
    assert translator._atom_kind(qcode) == expected


def test_file_extension(translator: TranslatorQ) -> None:
    """Test file extension methods."""
    assert translator.file_ext() == "q"
    assert translator.file_extension() == "q"


def test_translator_reset(translator: TranslatorQ) -> None:
    """Test translator state reset."""
    translator.reset()
    assert len(translator.walker.errors) == 0
    assert len(translator.walker.context) == 0


# ========== Integration Tests ==========

def test_complete_translation_workflow(new_translator: QTranslator) -> None:
    """Test a complete translation workflow from Python to Q."""
    
    # Test function header
    header = new_translator.translate_function_header(
        "factorial",
        ["n"],
        "Calculate factorial of n"
    )
    
    # Test individual assertions
    tests = [
        "assert factorial(0) == 1",
        "assert factorial(1) == 1", 
        "assert factorial(5) == 120"
    ]
    
    # Test complete suite
    suite = new_translator.translate_test_suite(tests, "factorial")
    
    # Verify structure
    assert "/ Calculate factorial of n" in header
    assert "factorial:{[n]" in header
    assert ".qunit.assertEquals[factorial[0]; 1; \"equality test\"]" in suite
    assert ".qunit.assertEquals[factorial[5]; 120; \"equality test\"]" in suite


def test_real_world_mbpp_examples(translator: TranslatorQ) -> None:
    """Test with real MBPP-style examples."""
    
    examples = [
        "assert max_chain_length([Pair(5, 24), Pair(15, 25), Pair(27, 40), Pair(50, 60)], 4) == 3",
        "assert first_repeated_char(\"abcabc\") == \"a\"",
        "assert get_ludic(10) == [1, 2, 3, 5, 7]",
        "assert grouping_dictionary([('yellow', 1), ('blue', 2), ('yellow', 3)]) == {'yellow': [1, 3], 'blue': [2]}"
    ]
    
    for example in examples:
        result = translator.compile_mbpp_test(example)
        
        # Should generate valid Q test syntax
        assert ".qunit.assertEquals" in result
        assert "equality test" in result
        assert result.startswith("\t")  # Proper indentation
        
        # Should not raise exceptions
        assert len(result) > 20  # Reasonable length for translated test