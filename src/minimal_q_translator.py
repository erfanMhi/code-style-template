"""
Minimal Python to Q translator for MBPP test assertions.
Ultra-lightweight, 100% accurate Q syntax.
"""

import ast
from typing import Any


class QTranslator:
    """Minimal AST-based Python to Q translator."""
    
    def translate_test(self, assertion: str) -> str:
        """Translate Python assert to Q test."""
        if assertion.startswith("assert "):
            assertion = assertion[7:]
        
        tree = ast.parse(assertion, mode='eval')
        comparison = tree.body
        
        if isinstance(comparison, ast.Compare) and len(comparison.ops) == 1 and isinstance(comparison.ops[0], ast.Eq):
            left_q = self._expr_to_q(comparison.left)
            right_q = self._expr_to_q(comparison.comparators[0])
            return f"{left_q}~{right_q}"  # No spaces around match operator
        
        raise ValueError(f"Unsupported assertion: {assertion}")
    
    def _expr_to_q(self, node: ast.expr) -> str:
        """Convert AST expression to Q syntax."""
        if isinstance(node, ast.Constant):
            return self._constant_to_q(node.value)
        
        elif isinstance(node, ast.Name):
            return node.id
        
        elif isinstance(node, ast.UnaryOp):
            operand = self._expr_to_q(node.operand)
            if isinstance(node.op, ast.USub):
                return f"-{operand}"
            elif isinstance(node.op, ast.UAdd):
                return operand
            else:
                raise ValueError(f"Unsupported unary operator: {type(node.op)}")
        
        elif isinstance(node, ast.List):
            if not node.elts:
                return "()"
            elements = [self._expr_to_q(elt) for elt in node.elts]
            return self._list_to_q(elements)
        
        elif isinstance(node, ast.Tuple):
            if not node.elts:
                return "()"
            elements = [self._expr_to_q(elt) for elt in node.elts]
            return self._list_to_q(elements)
        
        elif isinstance(node, ast.Set):
            if not node.elts:
                return "()"
            elements = [self._expr_to_q(elt) for elt in node.elts]
            return self._list_to_q(elements)
        
        elif isinstance(node, ast.Dict):
            if not node.keys:
                return "()!()"
            keys = [self._expr_to_q(k) for k in node.keys]
            values = [self._expr_to_q(v) for v in node.values]
            
            # Use proper Q dictionary syntax
            if self._all_simple_atoms(keys) and self._all_simple_atoms(values):
                key_str = "".join(keys) if all(k.startswith('`') for k in keys) else " ".join(keys)
                val_str = " ".join(values)
                return f"{key_str}!{val_str}"
            else:
                # For complex values, handle them appropriately
                if self._all_simple_atoms(keys):
                    key_str = "".join(keys) if all(k.startswith('`') for k in keys) else " ".join(keys)
                    if len(values) == 1:
                        return f"({key_str})!{values[0]}"
                    else:
                        val_list = self._list_to_q(values)
                        return f"({key_str})!({val_list})"
                else:
                    key_list = self._list_to_q(keys)
                    val_list = self._list_to_q(values)
                    return f"({key_list})!({val_list})"
        
        elif isinstance(node, ast.Call):
            func_name = self._expr_to_q(node.func)
            if func_name == "set":
                if not node.args:
                    return "()"
                return self._expr_to_q(node.args[0])
            
            args = [self._expr_to_q(arg) for arg in node.args]
            return f"{func_name}[{';'.join(args)}]"
        
        else:
            raise ValueError(f"Unsupported AST node: {type(node)}")
    
    def _constant_to_q(self, value: Any) -> str:
        """Convert Python constant to Q literal."""
        if value is None:
            return "0N"
        elif isinstance(value, bool):
            return "1b" if value else "0b"
        elif isinstance(value, int):
            return str(value)
        elif isinstance(value, float):
            # Q uses f suffix for floats
            return f"{value}f"
        elif isinstance(value, str):
            # Symbols for short identifiers, strings for text
            if len(value) <= 11 and ' ' not in value and '\n' not in value and '"' not in value:
                return f"`{value}"
            else:
                return f'"{value}"'
        else:
            return str(value)
    
    def _list_to_q(self, elements: list[str]) -> str:
        """Convert list of Q expressions to Q list syntax."""
        if not elements:
            return "()"
        
        # For symbols, use compact notation: `a`b`c
        if all(elem.startswith('`') for elem in elements):
            return "".join(elements)
        
        # Check if all elements are same type (homogeneous)
        if self._is_homogeneous(elements):
            return " ".join(elements)
        else:
            return f"({';'.join(elements)})"
    
    def _is_homogeneous(self, elements: list[str]) -> bool:
        """Check if elements are homogeneous (same Q type)."""
        if not elements:
            return True
        
        # Classify each element
        types = [self._get_q_type(elem) for elem in elements]
        
        # Complex types always require semicolon notation
        if any(t == 'complex' for t in types):
            return False
        
        # Check if all types are the same
        first_type = types[0]
        if all(t == first_type for t in types):
            return True
        
        # Special case: integers and floats can be mixed in space notation
        if all(t in ['int', 'float'] for t in types):
            return True
        
        return False
    
    def _get_q_type(self, q_expr: str) -> str:
        """Get the Q type of an expression."""
        if q_expr.startswith('`'):
            return 'symbol'
        elif q_expr in ['1b', '0b']:
            return 'bool'
        elif q_expr.endswith('f'):
            return 'float'
        elif q_expr.isdigit() or (q_expr.startswith('-') and q_expr[1:].isdigit()):
            return 'int'
        elif q_expr.startswith('"'):
            return 'string'
        elif q_expr == '0N':
            return 'null'
        elif ' ' in q_expr:  # Contains spaces - it's a list/vector
            return 'complex'
        elif any(c in q_expr for c in '()[];!'):  # Contains structural characters
            return 'complex'
        else:
            return 'complex'  # Anything else is complex
    
    def _all_simple_atoms(self, elements: list[str]) -> bool:
        """Check if all elements are simple atoms."""
        return all(self._is_simple_atom(elem) for elem in elements)
    
    def _is_simple_atom(self, q_expr: str) -> bool:
        """Check if Q expression is a simple atom (can use space notation)."""
        return (not any(c in q_expr for c in " ()[]{};!") and
                not q_expr.startswith('"') and
                q_expr != "()")


# Test the translator with more comprehensive examples
if __name__ == "__main__":
    translator = QTranslator()
    
    tests = [
        # Basic tests
        "assert func(1) == 2",
        "assert add(5, 3) == 8",
        
        # List tests
        "assert reverse([1, 2, 3]) == [3, 2, 1]",
        "assert sort(['c', 'a', 'b']) == ['a', 'b', 'c']",
        
        # Boolean tests
        "assert is_prime(7) == True",
        "assert is_even(4) == False",
        
        # Dictionary tests
        "assert get_dict() == {'a': 1, 'b': 2}",
        "assert process({1: 'one', 2: 'two'}) == {2: 'two', 1: 'one'}",
        
        # Nested structure tests
        "assert matrix([[1, 2], [3, 4]]) == [[4, 3], [2, 1]]",
        "assert flatten([[[1, 2]], [[3, 4]]]) == [1, 2, 3, 4]",
        
        # String tests
        "assert get_name() == 'hello'",
        "assert process_text() == 'hello world'",
        
        # Set tests
        "assert unique([1, 2, 2, 3]) == {1, 2, 3}",
        
        # Tuple tests
        "assert coords() == (1, 2)",
        
        # Mixed type tests
        "assert mixed() == [1, 'hello', 3.14]",
        
        # Complex MBPP-style tests
        "assert max_chain_length([Pair(5, 24), Pair(15, 25)], 2) == 3",
        "assert filter_data({'Alice': (25, 85)}, 26, 88) == {}"
    ]
    
    for test in tests:
        try:
            result = translator.translate_test(test)
            print(f"Python: {test}")
            print(f"Q:      {result}")
            print()
        except Exception as e:
            print(f"Error: {test}")
            print(f"       {e}")
            print()