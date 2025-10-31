"""
Developed by PowerShield, as an alternative to MyPy


MyPy Emulator - Type Checking Tool
Emulates MyPy functionality for static type checking in Python code
"""

import ast
import sys
from typing import Dict, List, Set, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TypeInfo:
    """Represents type information for a variable or expression"""
    name: str
    type_annotation: Optional[str] = None
    inferred_type: Optional[str] = None
    line_no: int = 0
    is_optional: bool = False


@dataclass
class TypeCheckResult:
    """Result of type checking"""
    file_path: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checked_lines: int = 0
    success: bool = True


class TypeInferenceEngine:
    """Engine for inferring types from Python code"""
    
    def __init__(self):
        self.builtin_types = {
            'int', 'float', 'str', 'bool', 'list', 'dict', 'set', 
            'tuple', 'None', 'Any', 'Optional', 'Union', 'List',
            'Dict', 'Set', 'Tuple'
        }
    
    def infer_from_literal(self, node: ast.AST) -> str:
        """Infer type from a literal value"""
        if isinstance(node, ast.Constant):
            value = node.value
            if value is None:
                return 'None'
            return type(value).__name__
        elif isinstance(node, ast.Num):
            return type(node.n).__name__
        elif isinstance(node, ast.Str):
            return 'str'
        elif isinstance(node, ast.List):
            return 'list'
        elif isinstance(node, ast.Dict):
            return 'dict'
        elif isinstance(node, ast.Set):
            return 'set'
        elif isinstance(node, ast.Tuple):
            return 'tuple'
        elif isinstance(node, ast.NameConstant):
            return type(node.value).__name__
        return 'Any'
    
    def infer_from_operation(self, node: ast.BinOp) -> str:
        """Infer type from binary operation"""
        if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, 
                                ast.FloorDiv, ast.Mod, ast.Pow)):
            # Numeric operations typically return numbers
            return 'Union[int, float]'
        return 'Any'
    
    def parse_annotation(self, annotation: ast.AST) -> str:
        """Parse type annotation node to string"""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        elif isinstance(annotation, ast.Subscript):
            base = self.parse_annotation(annotation.value)
            if isinstance(annotation.slice, ast.Index):
                # Python < 3.9
                args = self.parse_annotation(annotation.slice.value)
            else:
                # Python >= 3.9
                args = self.parse_annotation(annotation.slice)
            return f"{base}[{args}]"
        elif isinstance(annotation, ast.Tuple):
            elts = [self.parse_annotation(e) for e in annotation.elts]
            return ', '.join(elts)
        elif isinstance(annotation, ast.Attribute):
            return f"{self.parse_annotation(annotation.value)}.{annotation.attr}"
        return 'Any'


class TypeChecker:
    """Main type checker implementation"""
    
    def __init__(self, strict: bool = False):
        self.strict = strict
        self.inference_engine = TypeInferenceEngine()
        self.symbol_table: Dict[str, TypeInfo] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.current_file = ""
        self.function_signatures: Dict[str, Dict[str, str]] = {}
    
    def check_file(self, file_path: str) -> TypeCheckResult:
        """Check a single Python file for type errors"""
        self.current_file = file_path
        self.errors = []
        self.warnings = []
        self.symbol_table = {}
        
        try:
            with open(file_path, 'r') as f:
                source = f.read()
            
            tree = ast.parse(source, filename=file_path)
            self._check_module(tree)
            
            result = TypeCheckResult(
                file_path=file_path,
                errors=self.errors.copy(),
                warnings=self.warnings.copy(),
                checked_lines=len(source.split('\n')),
                success=len(self.errors) == 0
            )
            return result
            
        except SyntaxError as e:
            return TypeCheckResult(
                file_path=file_path,
                errors=[f"Syntax error: {e}"],
                success=False
            )
        except Exception as e:
            return TypeCheckResult(
                file_path=file_path,
                errors=[f"Error checking file: {e}"],
                success=False
            )
    
    def _check_module(self, node: ast.Module):
        """Check a module node"""
        for stmt in node.body:
            self._check_statement(stmt)
    
    def _check_statement(self, node: ast.AST):
        """Check a statement node"""
        if isinstance(node, ast.FunctionDef):
            self._check_function(node)
        elif isinstance(node, ast.AsyncFunctionDef):
            self._check_function(node)
        elif isinstance(node, ast.ClassDef):
            self._check_class(node)
        elif isinstance(node, ast.Assign):
            self._check_assignment(node)
        elif isinstance(node, ast.AnnAssign):
            self._check_annotated_assignment(node)
        elif isinstance(node, ast.Return):
            self._check_return(node)
        elif isinstance(node, ast.If):
            self._check_if(node)
        elif isinstance(node, ast.For):
            self._check_for(node)
        elif isinstance(node, ast.While):
            self._check_while(node)
    
    def _check_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]):
        """Check function definition"""
        func_name = node.name
        
        # Check parameter annotations
        param_types = {}
        for arg in node.args.args:
            if arg.annotation:
                param_type = self.inference_engine.parse_annotation(arg.annotation)
                param_types[arg.arg] = param_type
                self.symbol_table[arg.arg] = TypeInfo(
                    name=arg.arg,
                    type_annotation=param_type,
                    line_no=node.lineno
                )
            elif self.strict:
                self.warnings.append(
                    f"Line {node.lineno}: Parameter '{arg.arg}' in function "
                    f"'{func_name}' is missing type annotation"
                )
        
        # Check return type annotation
        if node.returns:
            return_type = self.inference_engine.parse_annotation(node.returns)
            param_types['return'] = return_type
        elif self.strict and func_name != '__init__':
            self.warnings.append(
                f"Line {node.lineno}: Function '{func_name}' is missing "
                f"return type annotation"
            )
        
        self.function_signatures[func_name] = param_types
        
        # Check function body
        for stmt in node.body:
            self._check_statement(stmt)
    
    def _check_class(self, node: ast.ClassDef):
        """Check class definition"""
        for stmt in node.body:
            self._check_statement(stmt)
    
    def _check_assignment(self, node: ast.Assign):
        """Check regular assignment"""
        # Infer type from value
        if node.value:
            inferred_type = self._infer_type(node.value)
            
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id in self.symbol_table:
                        # Check if reassignment is compatible
                        existing = self.symbol_table[target.id]
                        if existing.type_annotation:
                            if not self._is_compatible(inferred_type, 
                                                      existing.type_annotation):
                                self.errors.append(
                                    f"Line {node.lineno}: Type mismatch for "
                                    f"'{target.id}': assigned {inferred_type} but "
                                    f"expected {existing.type_annotation}"
                                )
                    else:
                        self.symbol_table[target.id] = TypeInfo(
                            name=target.id,
                            inferred_type=inferred_type,
                            line_no=node.lineno
                        )
    
    def _check_annotated_assignment(self, node: ast.AnnAssign):
        """Check annotated assignment"""
        if isinstance(node.target, ast.Name):
            var_name = node.target.id
            annotation = self.inference_engine.parse_annotation(node.annotation)
            
            # Store type info
            type_info = TypeInfo(
                name=var_name,
                type_annotation=annotation,
                line_no=node.lineno
            )
            
            # Check if value matches annotation
            if node.value:
                inferred_type = self._infer_type(node.value)
                type_info.inferred_type = inferred_type
                
                if not self._is_compatible(inferred_type, annotation):
                    self.errors.append(
                        f"Line {node.lineno}: Type mismatch for '{var_name}': "
                        f"annotated as {annotation} but assigned {inferred_type}"
                    )
            
            self.symbol_table[var_name] = type_info
    
    def _check_return(self, node: ast.Return):
        """Check return statement"""
        if node.value:
            return_type = self._infer_type(node.value)
            # Would need function context to fully validate return type
    
    def _check_if(self, node: ast.If):
        """Check if statement"""
        for stmt in node.body:
            self._check_statement(stmt)
        for stmt in node.orelse:
            self._check_statement(stmt)
    
    def _check_for(self, node: ast.For):
        """Check for loop"""
        for stmt in node.body:
            self._check_statement(stmt)
        for stmt in node.orelse:
            self._check_statement(stmt)
    
    def _check_while(self, node: ast.While):
        """Check while loop"""
        for stmt in node.body:
            self._check_statement(stmt)
        for stmt in node.orelse:
            self._check_statement(stmt)
    
    def _infer_type(self, node: ast.AST) -> str:
        """Infer type from an expression"""
        if isinstance(node, (ast.Constant, ast.Num, ast.Str, ast.NameConstant)):
            return self.inference_engine.infer_from_literal(node)
        elif isinstance(node, (ast.List, ast.Dict, ast.Set, ast.Tuple)):
            return self.inference_engine.infer_from_literal(node)
        elif isinstance(node, ast.BinOp):
            return self.inference_engine.infer_from_operation(node)
        elif isinstance(node, ast.Name):
            if node.id in self.symbol_table:
                type_info = self.symbol_table[node.id]
                return type_info.type_annotation or type_info.inferred_type or 'Any'
            return 'Any'
        elif isinstance(node, ast.Call):
            # Try to infer from function call
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in self.function_signatures:
                    sig = self.function_signatures[func_name]
                    return sig.get('return', 'Any')
            return 'Any'
        return 'Any'
    
    def _is_compatible(self, actual: str, expected: str) -> bool:
        """Check if actual type is compatible with expected type"""
        if actual == expected:
            return True
        if expected == 'Any' or actual == 'Any':
            return True
        
        # Handle Optional types
        if expected.startswith('Optional['):
            inner = expected[9:-1]
            if actual == 'None' or actual == inner:
                return True
        
        # Handle Union types
        if expected.startswith('Union['):
            types = expected[6:-1].split(', ')
            if actual in types:
                return True
        
        # Numeric compatibility
        if expected in ('int', 'float') and actual in ('int', 'float'):
            return True
        
        # Container types - basic check
        if expected.startswith(actual.split('[')[0]):
            return True
        
        return False


class MypyEmulator:
    """Main MyPy emulator interface"""
    
    def __init__(self, strict: bool = False, verbose: bool = False):
        self.strict = strict
        self.verbose = verbose
        self.checker = TypeChecker(strict=strict)
    
    def check_files(self, file_paths: List[str]) -> List[TypeCheckResult]:
        """Check multiple files"""
        results = []
        for file_path in file_paths:
            result = self.checker.check_file(file_path)
            results.append(result)
            if self.verbose:
                self._print_result(result)
        return results
    
    def check_directory(self, directory: str, pattern: str = "*.py") -> List[TypeCheckResult]:
        """Check all Python files in a directory"""
        path = Path(directory)
        files = list(path.rglob(pattern))
        file_paths = [str(f) for f in files]
        return self.check_files(file_paths)
    
    def _print_result(self, result: TypeCheckResult):
        """Print result to console"""
        print(f"\nChecking: {result.file_path}")
        
        if result.errors:
            print(f"  Errors ({len(result.errors)}):")
            for error in result.errors:
                print(f"    ❌ {error}")
        
        if result.warnings:
            print(f"  Warnings ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"    ⚠️  {warning}")
        
        if result.success and not result.warnings:
            print(f"  ✓ Success: No type errors found")
    
    def generate_report(self, results: List[TypeCheckResult]) -> Dict[str, Any]:
        """Generate summary report"""
        total_files = len(results)
        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)
        successful = sum(1 for r in results if r.success)
        
        return {
            'total_files': total_files,
            'successful': successful,
            'failed': total_files - successful,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'results': results
        }


def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='MyPy Emulator - Static type checker for Python'
    )
    parser.add_argument('files', nargs='+', help='Python files to check')
    parser.add_argument('--strict', action='store_true',
                       help='Enable strict type checking')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    emulator = MypyEmulator(strict=args.strict, verbose=args.verbose)
    results = emulator.check_files(args.files)
    report = emulator.generate_report(results)
    
    print("\n" + "="*60)
    print("Type Checking Report")
    print("="*60)
    print(f"Files checked: {report['total_files']}")
    print(f"Successful: {report['successful']}")
    print(f"Failed: {report['failed']}")
    print(f"Total errors: {report['total_errors']}")
    print(f"Total warnings: {report['total_warnings']}")
    print("="*60)
    
    # Exit with error code if there were type errors
    sys.exit(0 if report['total_errors'] == 0 else 1)


if __name__ == '__main__':
    main()
