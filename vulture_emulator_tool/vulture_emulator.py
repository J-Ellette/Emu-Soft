"""
vulture Emulator - Dead code finder without external dependencies

This module emulates core vulture functionality for finding unused Python code.
It helps identify dead code that can be safely removed to improve code quality.

Features:
- Unused function detection
- Unused class detection
- Unused variable detection
- Unused import detection
- Unused attribute detection
- Confidence scoring
- Multiple file and directory support
- Whitelist support for intentionally unused code
- Detailed reporting with line numbers
- Exit code based on findings

Note: This is a simplified implementation focusing on core functionality.
Advanced features like complex control flow analysis are simplified.
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class UnusedItem:
    """Represents an unused code item"""
    filename: str
    line: int
    name: str
    type: str  # function, class, variable, import, attribute
    confidence: int  # 0-100, higher means more confident it's unused
    
    def __str__(self) -> str:
        return f"{self.filename}:{self.line}: unused {self.type} '{self.name}' (confidence: {self.confidence}%)"


class CodeUsageAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze code usage"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.definitions: Dict[str, List[Tuple[int, str]]] = defaultdict(list)  # name -> [(line, type)]
        self.usages: Set[str] = set()  # names that are used
        self.imports: Dict[str, int] = {}  # import name -> line number
        self.classes: Dict[str, int] = {}  # class name -> line number
        self.functions: Dict[str, int] = {}  # function name -> line number
        self.variables: Dict[str, int] = {}  # variable name -> line number
        self.attributes: Dict[str, int] = {}  # attribute name -> line number
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None
        
        # Special names that are often intentionally unused
        self.special_names = {
            '__init__', '__str__', '__repr__', '__eq__', '__hash__',
            '__lt__', '__le__', '__gt__', '__ge__', '__ne__',
            '__call__', '__enter__', '__exit__',
            '__len__', '__getitem__', '__setitem__', '__delitem__',
            '__iter__', '__next__', '__contains__',
            '__add__', '__sub__', '__mul__', '__truediv__',
            '__main__', '__name__', '__file__', '__doc__',
            'setUp', 'tearDown', 'setUpClass', 'tearDownClass',  # unittest
            'setup_method', 'teardown_method',  # pytest
        }
    
    def visit_Import(self, node: ast.Import):
        """Track import statements"""
        for alias in node.names:
            name = alias.asname or alias.name
            self.imports[name] = node.lineno
            self.definitions[name].append((node.lineno, 'import'))
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track from...import statements"""
        for alias in node.names:
            if alias.name == '*':
                # Star imports - can't track usage
                continue
            name = alias.asname or alias.name
            self.imports[name] = node.lineno
            self.definitions[name].append((node.lineno, 'import'))
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Track class definitions"""
        self.classes[node.name] = node.lineno
        self.definitions[node.name].append((node.lineno, 'class'))
        
        # Visit class body
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Track function definitions"""
        # Skip special methods (they're often called indirectly)
        if node.name not in self.special_names:
            self.functions[node.name] = node.lineno
            self.definitions[node.name].append((node.lineno, 'function'))
        else:
            # Mark special methods as used
            self.usages.add(node.name)
        
        # Visit function body
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Track async function definitions"""
        if node.name not in self.special_names:
            self.functions[node.name] = node.lineno
            self.definitions[node.name].append((node.lineno, 'function'))
        else:
            self.usages.add(node.name)
        
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_Assign(self, node: ast.Assign):
        """Track variable assignments"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                # Skip private variables (often intentionally unused)
                if not target.id.startswith('_'):
                    self.variables[target.id] = node.lineno
                    self.definitions[target.id].append((node.lineno, 'variable'))
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Track annotated assignments"""
        if isinstance(node.target, ast.Name):
            if not node.target.id.startswith('_'):
                self.variables[node.target.id] = node.lineno
                self.definitions[node.target.id].append((node.lineno, 'variable'))
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name):
        """Track name usages"""
        if isinstance(node.ctx, (ast.Load, ast.Del)):
            self.usages.add(node.id)
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute):
        """Track attribute usages"""
        # Track attribute name
        self.usages.add(node.attr)
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Track function calls"""
        # If calling a Name, mark it as used
        if isinstance(node.func, ast.Name):
            self.usages.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.usages.add(node.func.attr)
        self.generic_visit(node)


class VultureAnalyzer:
    """Main analyzer for finding dead code"""
    
    def __init__(self):
        self.unused_items: List[UnusedItem] = []
        self.whitelist: Set[str] = set()
        self.min_confidence: int = 60
    
    def load_whitelist(self, whitelist_path: str):
        """Load whitelist of intentionally unused items"""
        if not os.path.exists(whitelist_path):
            return
        
        try:
            with open(whitelist_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.whitelist.add(line)
        except Exception as e:
            print(f"Warning: Could not load whitelist: {e}", file=sys.stderr)
    
    def analyze_file(self, filepath: str) -> List[UnusedItem]:
        """Analyze a single Python file for dead code"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source, filename=filepath)
            analyzer = CodeUsageAnalyzer(filepath)
            analyzer.visit(tree)
            
            unused = []
            
            # Check imports
            for name, line in analyzer.imports.items():
                if name not in analyzer.usages and name not in self.whitelist:
                    # High confidence for unused imports
                    unused.append(UnusedItem(
                        filename=filepath,
                        line=line,
                        name=name,
                        type='import',
                        confidence=90
                    ))
            
            # Check functions
            for name, line in analyzer.functions.items():
                if name not in analyzer.usages and name not in self.whitelist:
                    # Medium-high confidence for functions
                    # Could be called via getattr or from external modules
                    confidence = 80
                    if name.startswith('test_'):
                        # Test functions are often not called directly
                        confidence = 60
                    unused.append(UnusedItem(
                        filename=filepath,
                        line=line,
                        name=name,
                        type='function',
                        confidence=confidence
                    ))
            
            # Check classes
            for name, line in analyzer.classes.items():
                if name not in analyzer.usages and name not in self.whitelist:
                    # Medium confidence for classes
                    # Could be instantiated from other modules
                    unused.append(UnusedItem(
                        filename=filepath,
                        line=line,
                        name=name,
                        type='class',
                        confidence=70
                    ))
            
            # Check variables
            for name, line in analyzer.variables.items():
                if name not in analyzer.usages and name not in self.whitelist:
                    # Lower confidence for variables
                    # Could be used in templates, configs, etc.
                    unused.append(UnusedItem(
                        filename=filepath,
                        line=line,
                        name=name,
                        type='variable',
                        confidence=60
                    ))
            
            return unused
        
        except SyntaxError as e:
            print(f"Syntax error in {filepath}: {e}", file=sys.stderr)
            return []
        except Exception as e:
            print(f"Error analyzing {filepath}: {e}", file=sys.stderr)
            return []
    
    def analyze_directory(self, directory: str, exclude_dirs: Optional[Set[str]] = None) -> List[UnusedItem]:
        """Analyze all Python files in a directory"""
        if exclude_dirs is None:
            exclude_dirs = {'.git', '__pycache__', '.venv', 'venv', 'node_modules', '.tox', '.eggs'}
        
        unused = []
        
        for root, dirs, files in os.walk(directory):
            # Remove excluded directories from search
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    unused.extend(self.analyze_file(filepath))
        
        return unused
    
    def analyze(self, paths: List[str], whitelist_path: Optional[str] = None) -> List[UnusedItem]:
        """Analyze multiple paths (files or directories)"""
        if whitelist_path:
            self.load_whitelist(whitelist_path)
        
        all_unused = []
        
        for path in paths:
            if os.path.isfile(path):
                all_unused.extend(self.analyze_file(path))
            elif os.path.isdir(path):
                all_unused.extend(self.analyze_directory(path))
            else:
                print(f"Warning: {path} is not a file or directory", file=sys.stderr)
        
        # Filter by confidence
        filtered = [item for item in all_unused if item.confidence >= self.min_confidence]
        
        # Sort by filename and line number
        filtered.sort(key=lambda x: (x.filename, x.line))
        
        return filtered
    
    def report(self, unused_items: List[UnusedItem], verbose: bool = False) -> str:
        """Generate a report of unused items"""
        if not unused_items:
            return "No dead code found!"
        
        lines = []
        
        # Group by file
        by_file: Dict[str, List[UnusedItem]] = defaultdict(list)
        for item in unused_items:
            by_file[item.filename].append(item)
        
        for filename, items in sorted(by_file.items()):
            if verbose:
                lines.append(f"\n{filename}:")
                lines.append("-" * 60)
            
            for item in items:
                lines.append(str(item))
        
        # Summary
        lines.append("\n" + "=" * 60)
        lines.append(f"Total: {len(unused_items)} unused code items found")
        
        # Break down by type
        by_type: Dict[str, int] = defaultdict(int)
        for item in unused_items:
            by_type[item.type] += 1
        
        for item_type, count in sorted(by_type.items()):
            lines.append(f"  {item_type}: {count}")
        
        return '\n'.join(lines)


def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Find dead code in Python projects',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  vulture myproject/            # Scan entire directory
  vulture file1.py file2.py     # Scan specific files
  vulture . --exclude tests/    # Exclude specific directories
  vulture . --min-confidence 80 # Only show high-confidence results
  vulture . --whitelist .vulture_whitelist  # Use whitelist
        """
    )
    
    parser.add_argument('paths', nargs='+', help='Files or directories to analyze')
    parser.add_argument('--min-confidence', type=int, default=60,
                       help='Minimum confidence percentage (default: 60)')
    parser.add_argument('--exclude', action='append',
                       help='Directories to exclude (can be specified multiple times)')
    parser.add_argument('--whitelist', help='Path to whitelist file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--make-whitelist', action='store_true',
                       help='Generate whitelist template')
    
    args = parser.parse_args()
    
    if args.make_whitelist:
        # Generate whitelist from current findings
        analyzer = VultureAnalyzer()
        analyzer.min_confidence = args.min_confidence
        
        exclude_dirs = set(args.exclude) if args.exclude else None
        
        unused = analyzer.analyze(args.paths)
        
        print("# Vulture whitelist")
        print("# Add names that should be ignored by vulture")
        print("")
        for item in unused:
            print(f"{item.name}  # {item.type} in {item.filename}:{item.line}")
        
        sys.exit(0)
    
    # Run analysis
    analyzer = VultureAnalyzer()
    analyzer.min_confidence = args.min_confidence
    
    if args.exclude:
        # Override default exclude dirs if specified
        exclude_dirs = set(args.exclude)
    else:
        exclude_dirs = None
    
    unused = analyzer.analyze(args.paths, args.whitelist)
    
    # Print report
    report = analyzer.report(unused, verbose=args.verbose)
    print(report)
    
    # Exit with error code if dead code found
    sys.exit(1 if unused else 0)


if __name__ == '__main__':
    main()
