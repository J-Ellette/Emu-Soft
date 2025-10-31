"""
Developed by PowerShield, as an alternative to Flake8


Flake8 Emulator - Python Linting Tool
Emulates Flake8 functionality for code style and quality checking
"""

import ast
import re
import sys
from typing import List, Dict, Set, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LintIssue:
    """Represents a linting issue"""
    file_path: str
    line_no: int
    column: int
    code: str
    message: str
    severity: str = "warning"  # warning, error
    
    def __str__(self):
        return f"{self.file_path}:{self.line_no}:{self.column}: {self.code} {self.message}"


@dataclass
class LintResult:
    """Result of linting a file"""
    file_path: str
    issues: List[LintIssue] = field(default_factory=list)
    lines_checked: int = 0
    success: bool = True
    
    def add_issue(self, issue: LintIssue):
        """Add an issue to the result"""
        self.issues.append(issue)
        if issue.severity == "error":
            self.success = False


class Rule:
    """Base class for linting rules"""
    
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
    
    def check(self, node: ast.AST, source_lines: List[str], file_path: str) -> List[LintIssue]:
        """Check a node for violations"""
        return []


class E101_IndentationRule(Rule):
    """E101: indentation contains mixed spaces and tabs"""
    
    def __init__(self):
        super().__init__("E101", "indentation contains mixed spaces and tabs")
    
    def check_line(self, line: str, line_no: int, file_path: str) -> Optional[LintIssue]:
        """Check a line for mixed indentation"""
        leading = line[:len(line) - len(line.lstrip())]
        if '\t' in leading and ' ' in leading:
            return LintIssue(
                file_path=file_path,
                line_no=line_no,
                column=1,
                code=self.code,
                message=self.message,
                severity="error"
            )
        return None


class E201_WhitespaceRule(Rule):
    """E201: whitespace after '(' """
    
    def __init__(self):
        super().__init__("E201", "whitespace after '('")
    
    def check_line(self, line: str, line_no: int, file_path: str) -> List[LintIssue]:
        """Check for whitespace after opening parenthesis"""
        issues = []
        for match in re.finditer(r'\(\s+', line):
            if line[match.end()-1] == ' ':
                issues.append(LintIssue(
                    file_path=file_path,
                    line_no=line_no,
                    column=match.start() + 1,
                    code=self.code,
                    message=self.message
                ))
        return issues


class E202_WhitespaceRule(Rule):
    """E202: whitespace before ')' """
    
    def __init__(self):
        super().__init__("E202", "whitespace before ')'")
    
    def check_line(self, line: str, line_no: int, file_path: str) -> List[LintIssue]:
        """Check for whitespace before closing parenthesis"""
        issues = []
        for match in re.finditer(r'\s+\)', line):
            issues.append(LintIssue(
                file_path=file_path,
                line_no=line_no,
                column=match.start() + 1,
                code=self.code,
                message=self.message
            ))
        return issues


class E501_LineTooLongRule(Rule):
    """E501: line too long"""
    
    def __init__(self, max_line_length: int = 79):
        super().__init__("E501", f"line too long ({max_line_length} > {max_line_length} characters)")
        self.max_line_length = max_line_length
    
    def check_line(self, line: str, line_no: int, file_path: str) -> Optional[LintIssue]:
        """Check line length"""
        if len(line.rstrip()) > self.max_line_length:
            return LintIssue(
                file_path=file_path,
                line_no=line_no,
                column=self.max_line_length + 1,
                code=self.code,
                message=f"line too long ({len(line.rstrip())} > {self.max_line_length} characters)"
            )
        return None


class E701_MultipleStatementsRule(Rule):
    """E701: multiple statements on one line (colon)"""
    
    def __init__(self):
        super().__init__("E701", "multiple statements on one line (colon)")
    
    def check_line(self, line: str, line_no: int, file_path: str) -> Optional[LintIssue]:
        """Check for multiple statements on one line"""
        stripped = line.strip()
        # Simple check: if-statement with body on same line
        if stripped.startswith('if ') and ':' in stripped:
            colon_idx = stripped.index(':')
            after_colon = stripped[colon_idx+1:].strip()
            if after_colon and not after_colon.startswith('#'):
                return LintIssue(
                    file_path=file_path,
                    line_no=line_no,
                    column=colon_idx + 1,
                    code=self.code,
                    message=self.message
                )
        return None


class E702_MultipleStatementsRule(Rule):
    """E702: multiple statements on one line (semicolon)"""
    
    def __init__(self):
        super().__init__("E702", "multiple statements on one line (semicolon)")
    
    def check_line(self, line: str, line_no: int, file_path: str) -> List[LintIssue]:
        """Check for semicolons"""
        issues = []
        # Skip if in string
        if ';' in line and not line.strip().startswith('#'):
            for match in re.finditer(r';', line):
                issues.append(LintIssue(
                    file_path=file_path,
                    line_no=line_no,
                    column=match.start() + 1,
                    code=self.code,
                    message=self.message
                ))
        return issues


class W291_TrailingWhitespaceRule(Rule):
    """W291: trailing whitespace"""
    
    def __init__(self):
        super().__init__("W291", "trailing whitespace")
    
    def check_line(self, line: str, line_no: int, file_path: str) -> Optional[LintIssue]:
        """Check for trailing whitespace"""
        if line.rstrip() != line.rstrip('\n').rstrip('\r'):
            return LintIssue(
                file_path=file_path,
                line_no=line_no,
                column=len(line.rstrip()) + 1,
                code=self.code,
                message=self.message
            )
        return None


class W292_NoNewlineAtEndRule(Rule):
    """W292: no newline at end of file"""
    
    def __init__(self):
        super().__init__("W292", "no newline at end of file")
    
    def check_file(self, content: str, file_path: str) -> Optional[LintIssue]:
        """Check if file ends with newline"""
        if content and not content.endswith('\n'):
            lines = content.split('\n')
            return LintIssue(
                file_path=file_path,
                line_no=len(lines),
                column=len(lines[-1]) + 1,
                code=self.code,
                message=self.message
            )
        return None


class F401_UnusedImportRule(Rule):
    """F401: module imported but unused"""
    
    def __init__(self):
        super().__init__("F401", "imported but unused")
    
    def check_ast(self, tree: ast.AST, file_path: str) -> List[LintIssue]:
        """Check for unused imports"""
        issues = []
        imports = {}
        used_names = set()
        
        # Collect imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports[name] = (node.lineno, alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports[name] = (node.lineno, f"{node.module}.{alias.name}")
            elif isinstance(node, ast.Name):
                used_names.add(node.id)
        
        # Find unused imports
        for name, (line_no, full_name) in imports.items():
            if name not in used_names and name != '_':
                issues.append(LintIssue(
                    file_path=file_path,
                    line_no=line_no,
                    column=1,
                    code=self.code,
                    message=f"'{full_name}' {self.message}"
                ))
        
        return issues


class F841_UnusedVariableRule(Rule):
    """F841: local variable is assigned but never used"""
    
    def __init__(self):
        super().__init__("F841", "local variable assigned but never used")
    
    def check_ast(self, tree: ast.AST, file_path: str) -> List[LintIssue]:
        """Check for unused variables"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                assigned = {}
                used = set()
                
                # Find assignments and uses
                for child in ast.walk(node):
                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Name):
                                assigned[target.id] = child.lineno
                    elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                        used.add(child.id)
                
                # Find unused
                for var, line_no in assigned.items():
                    if var not in used and not var.startswith('_'):
                        issues.append(LintIssue(
                            file_path=file_path,
                            line_no=line_no,
                            column=1,
                            code=self.code,
                            message=f"local variable '{var}' {self.message}"
                        ))
        
        return issues


class C901_ComplexityRule(Rule):
    """C901: function is too complex"""
    
    def __init__(self, max_complexity: int = 10):
        super().__init__("C901", f"is too complex ({max_complexity})")
        self.max_complexity = max_complexity
    
    def calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        
        return complexity
    
    def check_ast(self, tree: ast.AST, file_path: str) -> List[LintIssue]:
        """Check function complexity"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self.calculate_complexity(node)
                if complexity > self.max_complexity:
                    issues.append(LintIssue(
                        file_path=file_path,
                        line_no=node.lineno,
                        column=node.col_offset + 1,
                        code=self.code,
                        message=f"'{node.name}' {self.message} (complexity: {complexity})"
                    ))
        
        return issues


class Flake8Linter:
    """Main linter implementation"""
    
    def __init__(self, max_line_length: int = 79, max_complexity: int = 10):
        self.max_line_length = max_line_length
        self.max_complexity = max_complexity
        
        # Initialize rules
        self.line_rules = [
            E101_IndentationRule(),
            E201_WhitespaceRule(),
            E202_WhitespaceRule(),
            E501_LineTooLongRule(max_line_length),
            E701_MultipleStatementsRule(),
            E702_MultipleStatementsRule(),
            W291_TrailingWhitespaceRule(),
        ]
        
        self.file_rules = [
            W292_NoNewlineAtEndRule(),
        ]
        
        self.ast_rules = [
            F401_UnusedImportRule(),
            F841_UnusedVariableRule(),
            C901_ComplexityRule(max_complexity),
        ]
    
    def lint_file(self, file_path: str) -> LintResult:
        """Lint a single file"""
        result = LintResult(file_path=file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            source_lines = content.split('\n')
            result.lines_checked = len(source_lines)
            
            # Check line-based rules
            for line_no, line in enumerate(source_lines, 1):
                for rule in self.line_rules:
                    if hasattr(rule, 'check_line'):
                        issues = rule.check_line(line, line_no, file_path)
                        if issues:
                            if isinstance(issues, list):
                                for issue in issues:
                                    result.add_issue(issue)
                            else:
                                result.add_issue(issues)
            
            # Check file-based rules
            for rule in self.file_rules:
                if hasattr(rule, 'check_file'):
                    issue = rule.check_file(content, file_path)
                    if issue:
                        result.add_issue(issue)
            
            # Parse AST and check AST-based rules
            try:
                tree = ast.parse(content, filename=file_path)
                for rule in self.ast_rules:
                    if hasattr(rule, 'check_ast'):
                        issues = rule.check_ast(tree, file_path)
                        for issue in issues:
                            result.add_issue(issue)
            except SyntaxError as e:
                result.add_issue(LintIssue(
                    file_path=file_path,
                    line_no=e.lineno or 1,
                    column=e.offset or 1,
                    code="E999",
                    message=f"SyntaxError: {e.msg}",
                    severity="error"
                ))
            
        except Exception as e:
            result.add_issue(LintIssue(
                file_path=file_path,
                line_no=1,
                column=1,
                code="E000",
                message=f"Error reading file: {e}",
                severity="error"
            ))
        
        return result


class Flake8Emulator:
    """Main Flake8 emulator interface"""
    
    def __init__(self, max_line_length: int = 79, max_complexity: int = 10, 
                 verbose: bool = False):
        self.linter = Flake8Linter(max_line_length, max_complexity)
        self.verbose = verbose
    
    def check_files(self, file_paths: List[str]) -> List[LintResult]:
        """Check multiple files"""
        results = []
        for file_path in file_paths:
            result = self.linter.lint_file(file_path)
            results.append(result)
            if self.verbose:
                self._print_result(result)
        return results
    
    def check_directory(self, directory: str, pattern: str = "*.py") -> List[LintResult]:
        """Check all Python files in a directory"""
        path = Path(directory)
        files = list(path.rglob(pattern))
        file_paths = [str(f) for f in files]
        return self.check_files(file_paths)
    
    def _print_result(self, result: LintResult):
        """Print result to console"""
        if result.issues:
            for issue in result.issues:
                print(issue)
    
    def generate_report(self, results: List[LintResult]) -> Dict[str, Any]:
        """Generate summary report"""
        total_files = len(results)
        total_issues = sum(len(r.issues) for r in results)
        total_errors = sum(
            len([i for i in r.issues if i.severity == "error"]) 
            for r in results
        )
        total_warnings = sum(
            len([i for i in r.issues if i.severity == "warning"]) 
            for r in results
        )
        clean_files = sum(1 for r in results if len(r.issues) == 0)
        
        return {
            'total_files': total_files,
            'clean_files': clean_files,
            'files_with_issues': total_files - clean_files,
            'total_issues': total_issues,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'results': results
        }


def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Flake8 Emulator - Python code linter'
    )
    parser.add_argument('files', nargs='+', help='Python files to lint')
    parser.add_argument('--max-line-length', type=int, default=79,
                       help='Maximum line length (default: 79)')
    parser.add_argument('--max-complexity', type=int, default=10,
                       help='Maximum cyclomatic complexity (default: 10)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    emulator = Flake8Emulator(
        max_line_length=args.max_line_length,
        max_complexity=args.max_complexity,
        verbose=True
    )
    
    results = emulator.check_files(args.files)
    report = emulator.generate_report(results)
    
    # Print all issues
    for result in results:
        for issue in result.issues:
            print(issue)
    
    # Print summary
    if report['total_issues'] > 0:
        print(f"\n{report['total_issues']} issue(s) found in {report['files_with_issues']} file(s)")
        sys.exit(1)
    else:
        print(f"\n✓ All {report['total_files']} file(s) passed linting")
        sys.exit(0)


if __name__ == '__main__':
    main()
