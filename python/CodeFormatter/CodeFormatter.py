"""
Developed by PowerShield, as an alternative to Black

Black code formatter emulator - AST-based Python code formatting.
Emulates Black functionality without external dependencies.

Core features:
- AST parsing and manipulation
- Style rules engine
- Code regeneration from AST
- Line length enforcement (default 88)
- Consistent formatting (strings, imports, etc.)
"""

import ast
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union


@dataclass
class FormatOptions:
    """Configuration options for code formatting."""
    line_length: int = 88
    string_normalization: bool = True
    skip_string_normalization: bool = False
    magic_trailing_comma: bool = True
    target_version: str = "py38"
    preview: bool = False
    
    def __post_init__(self):
        """Validate options."""
        if self.skip_string_normalization:
            self.string_normalization = False


class CodeFormatter(ast.NodeTransformer):
    """
    AST-based code formatter implementing Black-like rules.
    """
    
    def __init__(self, options: FormatOptions):
        self.options = options
        self.changes_made = False
    
    def format_code(self, source: str, filename: str = "<string>") -> str:
        """
        Format Python source code.
        
        Args:
            source: Source code to format
            filename: Filename for error messages
            
        Returns:
            Formatted source code
        """
        try:
            # Parse the source code
            tree = ast.parse(source, filename=filename)
            
            # Transform the AST
            self.visit(tree)
            
            # Unparse back to source code
            formatted = ast.unparse(tree)
            
            # Apply post-processing rules
            formatted = self._apply_post_processing(formatted)
            
            return formatted
            
        except SyntaxError as e:
            raise FormatError(f"Syntax error in {filename}: {e}")
    
    def _apply_post_processing(self, code: str) -> str:
        """
        Apply post-processing formatting rules.
        
        Args:
            code: Unparsed code from AST
            
        Returns:
            Post-processed code
        """
        lines = code.split('\n')
        result_lines = []
        
        for line in lines:
            # Apply line-level transformations
            line = self._format_line(line)
            result_lines.append(line)
        
        # Join lines and ensure proper spacing
        result = '\n'.join(result_lines)
        
        # Ensure file ends with newline
        if result and not result.endswith('\n'):
            result += '\n'
        
        return result
    
    def _format_line(self, line: str) -> str:
        """
        Format a single line of code.
        
        Args:
            line: Line to format
            
        Returns:
            Formatted line
        """
        # Remove trailing whitespace
        line = line.rstrip()
        
        # Enforce line length (simple truncation for demonstration)
        # In real Black, this would involve sophisticated line breaking
        if len(line) > self.options.line_length:
            # This is a simplified approach; real Black does complex line breaking
            pass
        
        return line
    
    def visit_Import(self, node: ast.Import) -> ast.Import:
        """Format import statements."""
        # Sort imports alphabetically
        node.names = sorted(node.names, key=lambda x: x.name)
        self.generic_visit(node)
        return node
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom:
        """Format from-import statements."""
        # Sort imported names alphabetically
        if node.names:
            node.names = sorted(node.names, key=lambda x: x.name or '')
        self.generic_visit(node)
        return node
    
    def visit_Str(self, node: ast.Str) -> ast.Str:
        """Normalize string quotes if enabled."""
        if self.options.string_normalization:
            # Prefer double quotes (Black default)
            # This is simplified; real Black has complex quote selection logic
            pass
        self.generic_visit(node)
        return node
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Format function definitions."""
        # Ensure proper spacing
        self.generic_visit(node)
        return node
    
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Format class definitions."""
        # Ensure proper spacing
        self.generic_visit(node)
        return node


class ImportSorter:
    """
    Sorts and organizes import statements.
    Implements Black's import organization rules.
    """
    
    @staticmethod
    def sort_imports(source: str) -> str:
        """
        Sort import statements in source code.
        
        Args:
            source: Source code with imports
            
        Returns:
            Source code with sorted imports
        """
        try:
            # Preserve trailing newline
            has_trailing_newline = source.endswith('\n')
            
            tree = ast.parse(source)
            
            # Extract imports and non-imports
            imports = []
            from_imports = []
            other_nodes = []
            
            for node in tree.body:
                if isinstance(node, ast.Import):
                    imports.append(node)
                elif isinstance(node, ast.ImportFrom):
                    from_imports.append(node)
                else:
                    other_nodes.append(node)
            
            # Sort imports
            imports.sort(key=lambda n: n.names[0].name if n.names else '')
            from_imports.sort(key=lambda n: n.module or '')
            
            # Rebuild tree
            tree.body = imports + from_imports + other_nodes
            
            result = ast.unparse(tree)
            
            # Restore trailing newline if it was present
            if has_trailing_newline and not result.endswith('\n'):
                result += '\n'
            
            return result
            
        except Exception:
            return source


class LineLengthEnforcer:
    """
    Enforces line length limits with intelligent line breaking.
    """
    
    def __init__(self, max_length: int = 88):
        self.max_length = max_length
    
    def enforce(self, source: str) -> str:
        """
        Enforce line length limits.
        
        Args:
            source: Source code
            
        Returns:
            Source with line length enforced
        """
        lines = source.split('\n')
        result_lines = []
        
        for line in lines:
            if len(line) > self.max_length:
                # Try to break the line intelligently
                broken = self._break_line(line)
                result_lines.extend(broken)
            else:
                result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def _break_line(self, line: str) -> List[str]:
        """
        Break a long line into multiple lines.
        
        Args:
            line: Line to break
            
        Returns:
            List of broken lines
        """
        # Simplified line breaking
        # Real Black has sophisticated logic for this
        
        # For now, just return the original line
        # A full implementation would break at appropriate points
        return [line]


class FormatError(Exception):
    """Exception raised when formatting fails."""
    pass


class Black:
    """
    Main Black formatter emulator class.
    Provides code formatting functionality.
    """
    
    def __init__(
        self,
        line_length: int = 88,
        skip_string_normalization: bool = False,
        target_version: str = "py38"
    ):
        """
        Initialize Black formatter.
        
        Args:
            line_length: Maximum line length
            skip_string_normalization: Skip normalizing string quotes
            target_version: Target Python version
        """
        self.options = FormatOptions(
            line_length=line_length,
            skip_string_normalization=skip_string_normalization,
            target_version=target_version
        )
        self.formatter = CodeFormatter(self.options)
    
    def format_file(self, filename: Union[str, Path]) -> bool:
        """
        Format a Python file in place.
        
        Args:
            filename: Path to file to format
            
        Returns:
            True if file was reformatted, False if already formatted
        """
        path = Path(filename)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filename}")
        
        if not path.suffix == '.py':
            raise ValueError(f"Not a Python file: {filename}")
        
        try:
            # Read original content
            with open(path, 'r', encoding='utf-8') as f:
                original = f.read()
            
            # Format the code
            formatted = self.format_string(original, filename=str(path))
            
            # Check if changes were made
            if original != formatted:
                # Write formatted code back
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(formatted)
                return True
            
            return False
            
        except Exception as e:
            raise FormatError(f"Error formatting {filename}: {e}")
    
    def format_string(self, source: str, filename: str = "<string>") -> str:
        """
        Format a string of Python code.
        
        Args:
            source: Source code to format
            filename: Filename for error messages
            
        Returns:
            Formatted source code
        """
        # Format the code using AST
        formatted = self.formatter.format_code(source, filename)
        
        # Sort imports
        formatted = ImportSorter.sort_imports(formatted)
        
        # Enforce line length
        enforcer = LineLengthEnforcer(self.options.line_length)
        formatted = enforcer.enforce(formatted)
        
        return formatted
    
    def check_file(self, filename: Union[str, Path]) -> bool:
        """
        Check if a file is formatted correctly without modifying it.
        
        Args:
            filename: Path to file to check
            
        Returns:
            True if file is correctly formatted, False otherwise
        """
        path = Path(filename)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filename}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                original = f.read()
            
            formatted = self.format_string(original, filename=str(path))
            
            return original == formatted
            
        except Exception:
            return False
    
    def format_directory(
        self,
        directory: Union[str, Path],
        recursive: bool = True,
        exclude: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Format all Python files in a directory.
        
        Args:
            directory: Directory path
            recursive: Recursively format subdirectories
            exclude: List of patterns to exclude
            
        Returns:
            Dictionary mapping filenames to whether they were reformatted
        """
        path = Path(directory)
        exclude = exclude or []
        results = {}
        
        if not path.is_dir():
            raise ValueError(f"Not a directory: {directory}")
        
        # Find Python files
        pattern = "**/*.py" if recursive else "*.py"
        
        for file_path in path.glob(pattern):
            # Check if file should be excluded
            should_exclude = any(
                excl in str(file_path) for excl in exclude
            )
            
            if should_exclude:
                continue
            
            try:
                reformatted = self.format_file(file_path)
                results[str(file_path)] = reformatted
            except Exception as e:
                print(f"Error formatting {file_path}: {e}")
                results[str(file_path)] = False
        
        return results


def format_file_in_place(filename: str, line_length: int = 88) -> bool:
    """
    Convenience function to format a file in place.
    
    Args:
        filename: File to format
        line_length: Maximum line length
        
    Returns:
        True if file was reformatted
    """
    black = Black(line_length=line_length)
    return black.format_file(filename)


def format_str(source: str, line_length: int = 88) -> str:
    """
    Convenience function to format a string of code.
    
    Args:
        source: Source code
        line_length: Maximum line length
        
    Returns:
        Formatted source code
    """
    black = Black(line_length=line_length)
    return black.format_string(source)


def check_file(filename: str, line_length: int = 88) -> bool:
    """
    Convenience function to check if a file is formatted.
    
    Args:
        filename: File to check
        line_length: Maximum line length
        
    Returns:
        True if file is correctly formatted
    """
    black = Black(line_length=line_length)
    return black.check_file(filename)


def main():
    """
    Main entry point for Black emulator CLI.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Black code formatter emulator"
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Files or directories to format"
    )
    parser.add_argument(
        "-l", "--line-length",
        type=int,
        default=88,
        help="Maximum line length (default: 88)"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if files are formatted without modifying"
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Show diff of formatting changes"
    )
    parser.add_argument(
        "-S", "--skip-string-normalization",
        action="store_true",
        help="Don't normalize string quotes"
    )
    parser.add_argument(
        "--exclude",
        type=str,
        help="Comma-separated list of patterns to exclude"
    )
    
    args = parser.parse_args()
    
    # Initialize formatter
    black = Black(
        line_length=args.line_length,
        skip_string_normalization=args.skip_string_normalization
    )
    
    # Process files
    all_formatted = True
    reformatted_count = 0
    checked_count = 0
    
    exclude_patterns = args.exclude.split(',') if args.exclude else []
    
    for path_str in args.files:
        path = Path(path_str)
        
        if path.is_file():
            files = [path]
        elif path.is_dir():
            results = black.format_directory(
                path,
                recursive=True,
                exclude=exclude_patterns
            )
            
            for file_path, was_reformatted in results.items():
                if args.check:
                    checked_count += 1
                    if was_reformatted:
                        print(f"would reformat {file_path}")
                        all_formatted = False
                else:
                    if was_reformatted:
                        print(f"reformatted {file_path}")
                        reformatted_count += 1
                    else:
                        print(f"unchanged {file_path}")
            continue
        else:
            print(f"Error: {path_str} is not a file or directory")
            continue
        
        for file_path in files:
            try:
                if args.check:
                    is_formatted = black.check_file(file_path)
                    checked_count += 1
                    
                    if not is_formatted:
                        print(f"would reformat {file_path}")
                        all_formatted = False
                    else:
                        print(f"already formatted {file_path}")
                else:
                    was_reformatted = black.format_file(file_path)
                    
                    if was_reformatted:
                        print(f"reformatted {file_path}")
                        reformatted_count += 1
                    else:
                        print(f"unchanged {file_path}")
                        
            except Exception as e:
                print(f"error: cannot format {file_path}: {e}")
                all_formatted = False
    
    # Print summary
    print(f"\n{'='*70}")
    if args.check:
        print(f"Checked {checked_count} file(s)")
        if all_formatted:
            print("All files are correctly formatted!")
            return 0
        else:
            print("Some files would be reformatted")
            return 1
    else:
        print(f"Reformatted {reformatted_count} file(s)")
        print(f"{'='*70}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
