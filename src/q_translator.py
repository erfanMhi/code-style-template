"""
Minimal AST-based Python to Q (KDB+) translator for MBPP test assertions.

This translator follows minimal compiler design principles:
1. Lexical Analysis: AST parsing (handled by Python's ast module)
2. Semantic Analysis: Type inference and validation
3. Code Generation: Q code emission with proper syntax

Focus: MBPP dataset test assertions (assert func(...) == expected_value)
"""

import ast
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum


class QType(Enum):
    """Q/KDB+ type system representation."""
    ATOM_BOOL = "boolean"
    ATOM_LONG = "long" 
    ATOM_FLOAT = "float"
    ATOM_SYMBOL = "symbol"
    ATOM_CHAR = "char"
    LIST_HOMOGENEOUS = "list_homo"
    LIST_MIXED = "list_mixed"
    DICT = "dict"
    NULL = "null"
    UNKNOWN = "unknown"


@dataclass
class QExpression:
    """Represents a translated Q expression with type information."""
    code: str
    qtype: QType
    is_scalar: bool = True
    
    def __str__(self) -> str:
        return self.code


class ASTWalker(ast.NodeVisitor):
    """AST visitor for Python to Q translation."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset translator state."""
        self.errors: List[str] = []
        self.context: Dict[str, Any] = {}
    
    def visit_Constant(self, node: ast.Constant) -> QExpression:
        """Translate Python constants to Q literals."""
        value = node.value
        
        if isinstance(value, bool):
            return QExpression(
                code="1b" if value else "0b",
                qtype=QType.ATOM_BOOL
            )
        elif isinstance(value, int):
            return QExpression(
                code=str(value),
                qtype=QType.ATOM_LONG
            )
        elif isinstance(value, float):
            return QExpression(
                code=str(value),
                qtype=QType.ATOM_FLOAT
            )
        elif isinstance(value, str):
            # Symbol for short identifiers, char list for text
            if self._is_symbol_candidate(value):
                return QExpression(
                    code=f"`{value}",
                    qtype=QType.ATOM_SYMBOL
                )
            else:
                return QExpression(
                    code=f'"{value}"',
                    qtype=QType.ATOM_CHAR
                )
        elif value is None:
            return QExpression(
                code="::",
                qtype=QType.NULL
            )
        else:
            raise ValueError(f"Unsupported constant type: {type(value)}")
    
    def visit_List(self, node: ast.List) -> QExpression:
        """Translate Python lists to Q lists/vectors."""
        if not node.elts:
            return QExpression(
                code="()",
                qtype=QType.LIST_MIXED,
                is_scalar=False
            )
        
        # Translate all elements
        elements = [self.visit(elt) for elt in node.elts]
        
        # Check for homogeneity
        if self._is_homogeneous(elements):
            # Emit compact vector notation
            codes = [elem.code for elem in elements]
            return QExpression(
                code=" ".join(codes),
                qtype=QType.LIST_HOMOGENEOUS,
                is_scalar=False
            )
        else:
            # Emit general list notation
            codes = [elem.code for elem in elements]
            return QExpression(
                code="(" + ";".join(codes) + ")",
                qtype=QType.LIST_MIXED,
                is_scalar=False
            )
    
    def visit_Tuple(self, node: ast.Tuple) -> QExpression:
        """Translate Python tuples to Q lists (Q has no tuple type)."""
        # Delegate to list handling since Q treats them the same
        list_node = ast.List(elts=node.elts, ctx=node.ctx)
        return self.visit_List(list_node)
    
    def visit_Set(self, node: ast.Set) -> QExpression:
        """Translate Python sets to Q lists (Q has no set type)."""
        # Convert to list and delegate
        list_node = ast.List(elts=list(node.elts), ctx=ast.Load())
        return self.visit_List(list_node)
    
    def visit_Dict(self, node: ast.Dict) -> QExpression:
        """Translate Python dictionaries to Q dictionaries."""
        if not node.keys:
            return QExpression(
                code="()!()",
                qtype=QType.DICT,
                is_scalar=False
            )
        
        keys = [self.visit(key) for key in node.keys]
        values = [self.visit(value) for value in node.values]
        
        # Build key and value lists
        key_codes = [k.code for k in keys]
        val_codes = [v.code for v in values]
        
        # Emit dictionary syntax
        key_part = " ".join(key_codes) if self._is_homogeneous(keys) else "(" + ";".join(key_codes) + ")"
        val_part = " ".join(val_codes) if self._is_homogeneous(values) else "(" + ";".join(val_codes) + ")"
        
        return QExpression(
            code=f"({key_part})!({val_part})",
            qtype=QType.DICT,
            is_scalar=False
        )
    
    def visit_Name(self, node: ast.Name) -> QExpression:
        """Translate variable names."""
        return QExpression(
            code=node.id,
            qtype=QType.UNKNOWN
        )
    
    def visit_Call(self, node: ast.Call) -> QExpression:
        """Translate function calls to Q syntax."""
        # Handle function name
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        else:
            func_name = self.visit(node.func).code
        
        # Handle special cases
        if func_name == "set":
            # set() constructor
            if not node.args:
                return QExpression(code="()", qtype=QType.LIST_MIXED, is_scalar=False)
            arg = self.visit(node.args[0])
            return arg  # Just return the argument for now
        
        # Translate arguments
        args = [self.visit(arg) for arg in node.args]
        arg_codes = [arg.code for arg in args]
        
        # Emit Q function call syntax: f[arg1;arg2;...]
        return QExpression(
            code=f"{func_name}[{';'.join(arg_codes)}]",
            qtype=QType.UNKNOWN
        )
    
    def visit_Compare(self, node: ast.Compare) -> QExpression:
        """Translate comparison operations."""
        left = self.visit(node.left)
        
        # For MBPP tests, we only care about equality
        if len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq):
            right = self.visit(node.comparators[0])
            # Return as QUnit assertion
            return QExpression(
                code=f".qunit.assertEquals[{left.code}; {right.code}; \"equality test\"]",
                qtype=QType.UNKNOWN
            )
        else:
            raise ValueError(f"Unsupported comparison operation: {ast.dump(node)}")
    
    def _is_symbol_candidate(self, s: str) -> bool:
        """Determine if string should be a Q symbol vs char list."""
        return (len(s) <= 20 and 
                not any(c.isspace() for c in s) and
                not any(c in '`"\\' for c in s))
    
    def _is_homogeneous(self, expressions: List[QExpression]) -> bool:
        """Check if all expressions have compatible types for vector notation."""
        if not expressions:
            return True
        
        # Group compatible types
        first_type = expressions[0].qtype
        compatible_atomics = {QType.ATOM_LONG, QType.ATOM_FLOAT}
        compatible_symbols = {QType.ATOM_SYMBOL}
        
        if first_type in compatible_atomics:
            return all(expr.qtype in compatible_atomics for expr in expressions)
        elif first_type in compatible_symbols:
            return all(expr.qtype in compatible_symbols for expr in expressions)
        else:
            return all(expr.qtype == first_type for expr in expressions)


class QTranslator:
    """Main translator interface for Python to Q conversion."""
    
    def __init__(self):
        self.walker = ASTWalker()
    
    def translate_expression(self, expr_str: str) -> str:
        """Translate a Python expression string to Q code."""
        try:
            # Parse the expression
            tree = ast.parse(expr_str, mode='eval')
            
            # Translate using AST walker
            self.walker.reset()
            result = self.walker.visit(tree.body)
            
            return result.code
        except Exception as e:
            raise ValueError(f"Translation error for '{expr_str}': {e}")
    
    def translate_assertion(self, assert_stmt: str) -> str:
        """Translate a Python assert statement to Q test code."""
        # Remove 'assert ' prefix
        if assert_stmt.startswith("assert "):
            expr_str = assert_stmt[7:]
        else:
            expr_str = assert_stmt
        
        try:
            # Parse the assertion
            tree = ast.parse(expr_str, mode='eval')
            
            # Translate using AST walker
            self.walker.reset()
            result = self.walker.visit(tree.body)
            
            return f"\t{result.code}"
        except Exception as e:
            raise ValueError(f"Assertion translation error for '{assert_stmt}': {e}")
    
    def translate_test_suite(self, test_list: List[str], entry_point: str) -> str:
        """Translate a complete MBPP test suite to Q syntax."""
        lines = []
        
        # Test suite header
        lines.append(")")  # Close previous definition
        lines.append("/ ─── Test suite ──────────────────────────────────────")
        lines.append(f"test:{{[{entry_point}]")
        
        # Translate each test
        for i, test in enumerate(test_list):
            lines.append(f"\t/ Test {i+1}")
            test_q = self.translate_assertion(test)
            lines.append(test_q)
            lines.append("")
        
        # Test suite footer
        lines.append("}")
        
        return "\n".join(lines)
    
    def translate_function_header(self, name: str, args: List[str], description: str) -> str:
        """Generate Q function header with documentation."""
        # Convert multiline docstring to Q comments
        comment_lines = []
        for line in description.strip().split('\n'):
            comment_lines.append(f"/ {line}")
        
        comment = "\n".join(comment_lines)
        arg_list = ";".join(args)
        header = f"{comment}\n{name}:{{[{arg_list}]"
        
        return header + "\n"
    
    def file_extension(self) -> str:
        """Return Q file extension."""
        return "q"


# Legacy compatibility interface
class TranslatorQ(QTranslator):
    """Legacy interface for backward compatibility."""
    
    def __init__(self):
        super().__init__()
        self.stop = ["\n)"]
        self.reset()
    
    def reset(self):
        """Reset translator state."""
        self.walker.reset()
    
    def file_ext(self) -> str:
        """Legacy method name for file extension."""
        return self.file_extension()
    
    def translate_prompt(self, name: str, args: List[ast.arg], 
                        returns: Union[ast.expr, None], description: str) -> str:
        """Legacy interface for function header generation."""
        arg_names = [arg.arg for arg in args]
        return self.translate_function_header(name, arg_names, description)
    
    def compile_mbpp_test(self, test_str: str) -> str:
        """Legacy interface for single test compilation."""
        return self.translate_assertion(test_str)
    
    def compile_mbpp_test_suite(self, test_list: List[str], entry_point: str) -> str:
        """Legacy interface for test suite compilation."""
        return self.translate_test_suite(test_list, entry_point)
    
    def finalize(self, expr: Tuple[str, ast.expr], context: Union[str, None]) -> str:
        """Legacy method for expression finalization."""
        return expr[0]
    
    def deep_equality(self, left: str, right: str) -> str:
        """Legacy method for equality testing."""
        return f"\t.qunit.assertEquals[{left}; {right}; \"equality test\"]"
    
    def test_suite_prefix_lines(self, entry_point: str) -> List[str]:
        """Legacy method for test suite prefix."""
        return [")", 
                "/ ─── Test suite ──────────────────────────────────────",
                f"test:{{[{entry_point}]"]
    
    def test_suite_suffix_lines(self) -> List[str]:
        """Legacy method for test suite suffix."""
        return ["}"]
    
    # Legacy expression translation methods
    def _translate_python_expr(self, expr: str) -> str:
        """Legacy method for expression translation."""
        return self.translate_expression(expr)
    
    def _parse_arguments(self, args_str: str) -> List[str]:
        """Parse function arguments with proper nesting handling."""
        if not args_str.strip():
            return []
        
        args = []
        current_arg = ""
        paren_count = 0
        bracket_count = 0
        brace_count = 0
        in_string = False
        string_char = None
        
        for char in args_str:
            if in_string:
                if char == string_char:
                    in_string = False
                current_arg += char
                continue
            
            if char in ['"', "'"]:
                in_string = True
                string_char = char
                current_arg += char
                continue
            
            if char == "(":
                paren_count += 1
            elif char == ")":
                paren_count -= 1
            elif char == "[":
                bracket_count += 1
            elif char == "]":
                bracket_count -= 1
            elif char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
            elif (char == "," and paren_count == 0 and
                  bracket_count == 0 and brace_count == 0):
                args.append(current_arg.strip())
                current_arg = ""
                continue
            
            current_arg += char
        
        if current_arg:
            args.append(current_arg.strip())
        
        return args
    
    # Maintain other legacy methods for compatibility
    def gen_literal(self, value: Any) -> Tuple[str, ast.expr]:
        """Legacy literal generation."""
        expr = self.walker.visit_Constant(ast.Constant(value=value))
        type_map = {
            QType.ATOM_BOOL: "bool",
            QType.ATOM_LONG: "int", 
            QType.ATOM_FLOAT: "float",
            QType.ATOM_SYMBOL: "str",
            QType.ATOM_CHAR: "str",
            QType.NULL: "None"
        }
        ast_type = ast.Name(id=type_map.get(expr.qtype, "unknown"))
        return (expr.code, ast_type)
    
    def gen_list(self, items: List[Tuple[str, ast.expr]]) -> Tuple[str, ast.expr]:
        """Legacy list generation."""
        if not items:
            return ("()", ast.List([ast.Name("None")]))
        
        # Create QExpression objects from items
        expressions = []
        for code, ast_type in items:
            # Map AST type to QType
            if hasattr(ast_type, 'id'):
                type_map = {
                    "int": QType.ATOM_LONG,
                    "float": QType.ATOM_FLOAT,
                    "str": QType.ATOM_SYMBOL,
                    "bool": QType.ATOM_BOOL
                }
                qtype = type_map.get(ast_type.id, QType.UNKNOWN)
            else:
                qtype = QType.UNKNOWN
            
            expressions.append(QExpression(code=code, qtype=qtype))
        
        # Check homogeneity and generate appropriate code
        if self.walker._is_homogeneous(expressions):
            code = " ".join(expr.code for expr in expressions)
        else:
            code = "(" + ";".join(expr.code for expr in expressions) + ")"
        
        return (code, ast.List([items[0][1]]))
    
    def gen_tuple(self, items: List[Tuple[str, ast.expr]]) -> Tuple[str, ast.expr]:
        """Legacy tuple generation (same as list in Q)."""
        return self.gen_list(items)
    
    def gen_dict(self, keys: List[Tuple[str, ast.expr]], 
                 vals: List[Tuple[str, ast.expr]]) -> Tuple[str, ast.expr]:
        """Legacy dictionary generation."""
        if not keys:
            return ("()!()", ast.Dict(keys=[], values=[]))
        
        key_codes = [k[0] for k in keys]
        val_codes = [v[0] for v in vals]
        
        key_part = " ".join(key_codes)
        val_part = " ".join(val_codes)
        
        return (f"({key_part})!({val_part})", 
                ast.Dict(keys=[k[1] for k in keys], values=[v[1] for v in vals]))
    
    def gen_var(self, v: str) -> Tuple[str, None]:
        """Legacy variable generation."""
        return (v, None)
    
    def gen_call(self, func: Tuple[str, None], 
                 args: List[Tuple[str, ast.expr]]) -> Tuple[str, None]:
        """Legacy function call generation."""
        arg_codes = [a[0] for a in args]
        return (f"{func[0]}[{';'.join(arg_codes)}]", None)
    
    def translate_pytype(self, ann: Union[ast.expr, None]) -> str:
        """Legacy Python type translation."""
        if ann is None:
            return ""
        if isinstance(ann, ast.Name):
            type_map = {
                "str": "symbol",
                "int": "long", 
                "float": "float",
                "bool": "boolean",
                "None": "null"
            }
            return type_map.get(ann.id, "generic")
        return "generic"
    
    def _atom_kind(self, qcode: str) -> str:
        """Legacy atom kind classification."""
        if qcode.startswith('`'):
            return "symbol"
        elif re.match(r'-?\d+$', qcode):
            return "int"
        elif re.match(r'-?\d+\.\d+$', qcode):
            return "float"
        elif re.match(r'-?\d+(?:\.\d+)?(?:\s+-?\d+(?:\.\d+)?)+$', qcode):
            return "vector"
        elif qcode.startswith("(") and "!" in qcode:
            return "dict"
        elif qcode.startswith("(") and ";" in qcode:
            return "list"
        elif qcode.startswith("("):
            return "nested"
        else:
            return "other"