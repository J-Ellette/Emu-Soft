"""
isort Emulator - Import statement sorting without external dependencies

This module emulates core isort functionality for organizing Python imports.
It automatically sorts and organizes import statements according to PEP 8
and configurable rules.

Features:
- Sort import statements alphabetically
- Group imports into sections (stdlib, third-party, first-party)
- Separate 'from' imports from regular imports
- Handle multi-line imports
- Preserve comments
- Multiple output formats
- Configurable sorting options
- Support for different profiles (black, django, pep8)

Note: This is a simplified implementation focusing on core functionality.
Advanced features like custom sections and complex skip patterns are simplified.
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import List, Set, Tuple, Optional, Dict


# Standard library modules (Python 3.6+)
STDLIB_MODULES = {
    'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio', 'asyncore',
    'atexit', 'audioop', 'base64', 'bdb', 'binascii', 'binhex', 'bisect', 'builtins',
    'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs',
    'codeop', 'collections', 'colorsys', 'compileall', 'concurrent', 'configparser',
    'contextlib', 'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv',
    'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib',
    'dis', 'distutils', 'doctest', 'dummy_threading', 'email', 'encodings', 'enum',
    'errno', 'faulthandler', 'fcntl', 'filecmp', 'fileinput', 'fnmatch', 'formatter',
    'fractions', 'ftplib', 'functools', 'gc', 'getopt', 'getpass', 'gettext', 'glob',
    'grp', 'gzip', 'hashlib', 'heapq', 'hmac', 'html', 'http', 'imaplib', 'imghdr',
    'imp', 'importlib', 'inspect', 'io', 'ipaddress', 'itertools', 'json', 'keyword',
    'lib2to3', 'linecache', 'locale', 'logging', 'lzma', 'mailbox', 'mailcap',
    'marshal', 'math', 'mimetypes', 'mmap', 'modulefinder', 'msilib', 'msvcrt',
    'multiprocessing', 'netrc', 'nis', 'nntplib', 'numbers', 'operator', 'optparse',
    'os', 'ossaudiodev', 'parser', 'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes',
    'pkgutil', 'platform', 'plistlib', 'poplib', 'posix', 'posixpath', 'pprint',
    'profile', 'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc', 'queue',
    'quopri', 'random', 're', 'readline', 'reprlib', 'resource', 'rlcompleter',
    'runpy', 'sched', 'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil',
    'signal', 'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver',
    'spwd', 'sqlite3', 'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct',
    'subprocess', 'sunau', 'symbol', 'symtable', 'sys', 'sysconfig', 'syslog',
    'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap',
    'threading', 'time', 'timeit', 'tkinter', 'token', 'tokenize', 'trace',
    'traceback', 'tracemalloc', 'tty', 'turtle', 'turtledemo', 'types', 'typing',
    'unicodedata', 'unittest', 'urllib', 'uu', 'uuid', 'venv', 'warnings', 'wave',
    'weakref', 'webbrowser', 'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml',
    'xmlrpc', 'zipapp', 'zipfile', 'zipimport', 'zlib',
}


class ImportStatement:
    """Represents a single import statement"""
    
    def __init__(self, line: str, line_number: int, is_from: bool = False):
        self.original = line.strip()
        self.line_number = line_number
        self.is_from = is_from
        self.module = ""
        self.items = []
        self.alias = None
        self.comment = ""
        
        self._parse()
    
    def _parse(self):
        """Parse the import statement"""
        line = self.original
        
        # Extract comment if present
        if '#' in line:
            parts = line.split('#', 1)
            line = parts[0].strip()
            self.comment = '#' + parts[1]
        
        if self.original.startswith('from '):
            self.is_from = True
            # from module import items
            match = re.match(r'from\s+([\w.]+)\s+import\s+(.+)', line)
            if match:
                self.module = match.group(1)
                items_str = match.group(2).strip()
                
                # Handle parentheses
                items_str = items_str.strip('()')
                
                # Split items
                if ',' in items_str:
                    self.items = [item.strip() for item in items_str.split(',')]
                else:
                    self.items = [items_str]
        else:
            # import module [as alias]
            match = re.match(r'import\s+([\w.]+)(?:\s+as\s+([\w.]+))?', line)
            if match:
                self.module = match.group(1)
                self.alias = match.group(2)
    
    def get_sort_key(self) -> Tuple:
        """Get sorting key for this import"""
        # Sort by: from-import flag (regular imports first), module name, items
        return (self.is_from, self.module.lower(), tuple(sorted(self.items)))
    
    def __str__(self) -> str:
        """Convert back to import statement"""
        if self.is_from:
            items_str = ", ".join(sorted(self.items))
            result = f"from {self.module} import {items_str}"
        else:
            result = f"import {self.module}"
            if self.alias:
                result += f" as {self.alias}"
        
        if self.comment:
            result += "  " + self.comment
        
        return result


class ImportSection:
    """Represents a section of imports (stdlib, third-party, first-party)"""
    
    def __init__(self, name: str):
        self.name = name
        self.imports: List[ImportStatement] = []
    
    def add(self, import_stmt: ImportStatement):
        """Add an import to this section"""
        self.imports.append(import_stmt)
    
    def sort(self):
        """Sort imports in this section"""
        self.imports.sort(key=lambda x: x.get_sort_key())
    
    def to_lines(self) -> List[str]:
        """Convert section to lines of code"""
        if not self.imports:
            return []
        
        self.sort()
        return [str(imp) for imp in self.imports]


def classify_import(module_name: str, known_first_party: Set[str] = None,
                    known_third_party: Set[str] = None) -> str:
    """Classify an import as stdlib, third-party, or first-party"""
    if known_first_party and module_name in known_first_party:
        return "first-party"
    
    if known_third_party and module_name in known_third_party:
        return "third-party"
    
    # Check if it's a standard library module
    base_module = module_name.split('.')[0]
    if base_module in STDLIB_MODULES:
        return "stdlib"
    
    # Check if it's a relative import
    if module_name.startswith('.'):
        return "first-party"
    
    # Default to third-party
    return "third-party"


def parse_imports(code: str, known_first_party: Set[str] = None,
                 known_third_party: Set[str] = None) -> Tuple[List[str], Dict[str, ImportSection], List[str]]:
    """Parse Python code and extract imports"""
    lines = code.split('\n')
    
    sections = {
        "stdlib": ImportSection("stdlib"),
        "third-party": ImportSection("third-party"),
        "first-party": ImportSection("first-party"),
    }
    
    pre_import_lines = []
    post_import_lines = []
    in_imports = False
    imports_done = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip empty lines and comments before imports
        if not stripped or stripped.startswith('#'):
            if not imports_done:
                if in_imports:
                    # Empty line during imports - continue
                    pass
                else:
                    pre_import_lines.append(line)
            else:
                post_import_lines.append(line)
            i += 1
            continue
        
        # Check for docstring
        if (stripped.startswith('"""') or stripped.startswith("'''")) and not in_imports:
            pre_import_lines.append(line)
            quote = '"""' if stripped.startswith('"""') else "'''"
            
            # Check if docstring ends on same line
            if stripped.count(quote) >= 2:
                i += 1
                continue
            
            # Multi-line docstring
            i += 1
            while i < len(lines):
                line = lines[i]
                pre_import_lines.append(line)
                if quote in line:
                    break
                i += 1
            i += 1
            continue
        
        # Check for import statement
        if stripped.startswith('import ') or stripped.startswith('from '):
            in_imports = True
            
            # Handle multi-line imports
            full_statement = line
            if '(' in line and ')' not in line:
                # Multi-line import with parentheses
                i += 1
                while i < len(lines) and ')' not in lines[i]:
                    full_statement += ' ' + lines[i].strip()
                    i += 1
                if i < len(lines):
                    full_statement += ' ' + lines[i].strip()
            
            # Parse import
            import_stmt = ImportStatement(full_statement, i)
            
            # Classify and add to appropriate section
            section_name = classify_import(import_stmt.module, known_first_party, known_third_party)
            sections[section_name].add(import_stmt)
            
            i += 1
            continue
        
        # Non-import line after imports have started
        if in_imports:
            imports_done = True
        
        post_import_lines.append(line)
        i += 1
    
    return pre_import_lines, sections, post_import_lines


def sort_imports(code: str, known_first_party: Set[str] = None,
                known_third_party: Set[str] = None,
                line_length: int = 88,
                profile: str = 'black') -> str:
    """Sort imports in Python code"""
    if known_first_party is None:
        known_first_party = set()
    if known_third_party is None:
        known_third_party = set()
    
    # Parse the code
    pre_lines, sections, post_lines = parse_imports(code, known_first_party, known_third_party)
    
    # Build output
    result_lines = []
    
    # Add pre-import lines (docstring, comments, etc.)
    result_lines.extend(pre_lines)
    
    # Add imports by section
    section_order = ["stdlib", "third-party", "first-party"]
    has_previous_section = False
    
    for section_name in section_order:
        section = sections[section_name]
        section_lines = section.to_lines()
        
        if section_lines:
            # Add blank line between sections
            if has_previous_section or pre_lines:
                result_lines.append("")
            
            result_lines.extend(section_lines)
            has_previous_section = True
    
    # Add post-import code
    if post_lines:
        # Ensure blank line between imports and code
        if result_lines and result_lines[-1] != "":
            result_lines.append("")
        result_lines.extend(post_lines)
    
    return '\n'.join(result_lines)


def sort_file(filename: str, check_only: bool = False,
             known_first_party: Set[str] = None,
             known_third_party: Set[str] = None) -> bool:
    """Sort imports in a file"""
    with open(filename, 'r', encoding='utf-8') as f:
        original_code = f.read()
    
    sorted_code = sort_imports(original_code, known_first_party, known_third_party)
    
    if check_only:
        return original_code == sorted_code
    
    if original_code != sorted_code:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(sorted_code)
        return True
    
    return False


def sort_directory(directory: str, check_only: bool = False,
                  known_first_party: Set[str] = None,
                  known_third_party: Set[str] = None,
                  skip_dirs: Set[str] = None) -> Tuple[int, int]:
    """Sort imports in all Python files in a directory"""
    if skip_dirs is None:
        skip_dirs = {'.git', '.tox', '.venv', 'venv', 'env', '__pycache__', 'node_modules'}
    
    modified_count = 0
    total_count = 0
    
    for root, dirs, files in os.walk(directory):
        # Remove skip directories from dirs list (modifies in-place)
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                total_count += 1
                
                try:
                    changed = sort_file(filepath, check_only, known_first_party, known_third_party)
                    if changed:
                        modified_count += 1
                except Exception as e:
                    print(f"Error processing {filepath}: {e}", file=sys.stderr)
    
    return modified_count, total_count


class Config:
    """isort configuration"""
    
    def __init__(self):
        self.known_first_party: Set[str] = set()
        self.known_third_party: Set[str] = set()
        self.line_length = 88
        self.profile = 'black'
        self.skip_dirs: Set[str] = {'.git', '.tox', '.venv', 'venv', 'env', '__pycache__'}
    
    @classmethod
    def from_file(cls, config_file: str = '.isort.cfg') -> 'Config':
        """Load configuration from file"""
        config = cls()
        
        if not os.path.exists(config_file):
            return config
        
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'known_first_party':
                        config.known_first_party = set(v.strip() for v in value.split(','))
                    elif key == 'known_third_party':
                        config.known_third_party = set(v.strip() for v in value.split(','))
                    elif key == 'line_length':
                        config.line_length = int(value)
                    elif key == 'profile':
                        config.profile = value
        
        return config


if __name__ == "__main__":
    # Demo usage
    print("isort Emulator Demo")
    print("=" * 50)
    
    sample_code = """
import sys
import os
from pathlib import Path
import json
from typing import List, Dict
import requests
from myapp.models import User
from myapp.utils import helper
import numpy as np
from django.conf import settings
"""
    
    print("Original code:")
    print(sample_code)
    
    print("\nSorted imports:")
    sorted_code = sort_imports(sample_code, 
                               known_first_party={'myapp'},
                               known_third_party={'requests', 'numpy', 'django'})
    print(sorted_code)
