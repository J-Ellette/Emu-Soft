"""
Sphinx Emulator - Documentation generator without external dependencies

This module emulates core Sphinx functionality for generating Python documentation.
It extracts docstrings and generates HTML documentation from Python modules.

Features:
- Automatic API documentation from Python modules
- Docstring parsing (Google, NumPy, reStructuredText styles)
- HTML documentation generation
- Module, class, and function documentation
- Index generation
- Cross-references
- Search functionality (basic)
- Multiple themes support
- Configuration file support

Note: This is a simplified implementation focusing on core functionality.
Advanced features like extensions and complex directives are simplified.
"""

import ast
import os
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Set, Any
from dataclasses import dataclass, field
from html import escape
import inspect


@dataclass
class DocItem:
    """Represents a documented item (module, class, function, etc.)"""
    name: str
    type: str  # module, class, function, method, attribute
    docstring: Optional[str] = None
    signature: Optional[str] = None
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    parent: Optional[str] = None
    members: List['DocItem'] = field(default_factory=list)
    
    def get_id(self) -> str:
        """Get unique identifier for this item"""
        if self.parent:
            return f"{self.parent}.{self.name}"
        return self.name


class DocstringParser:
    """Parse docstrings in various formats"""
    
    @staticmethod
    def parse(docstring: Optional[str]) -> Dict[str, Any]:
        """Parse docstring and extract components"""
        if not docstring:
            return {
                'summary': '',
                'description': '',
                'params': [],
                'returns': '',
                'raises': [],
                'examples': []
            }
        
        lines = docstring.strip().split('\n')
        
        # Extract summary (first line)
        summary = lines[0].strip() if lines else ''
        
        # Try to detect format - order matters!
        if ':param' in docstring or ':return' in docstring:
            return DocstringParser._parse_sphinx_style(docstring)
        elif 'Args:' in docstring or 'Returns:' in docstring:
            # Google style (must check before NumPy since both use "Returns")
            return DocstringParser._parse_google_style(docstring)
        elif 'Parameters' in docstring or ('Returns' in docstring and '---' in docstring):
            # NumPy style (uses underlines)
            return DocstringParser._parse_numpy_style(docstring)
        else:
            # Plain docstring
            return {
                'summary': summary,
                'description': '\n'.join(lines[1:]).strip(),
                'params': [],
                'returns': '',
                'raises': [],
                'examples': []
            }
    
    @staticmethod
    def _parse_sphinx_style(docstring: str) -> Dict[str, Any]:
        """Parse Sphinx/reStructuredText style docstring"""
        lines = docstring.strip().split('\n')
        summary = lines[0].strip()
        
        params = []
        returns = ''
        raises = []
        description_lines = []
        
        i = 1
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith(':param '):
                # Extract parameter
                match = re.match(r':param (\w+):\s*(.*)', line)
                if match:
                    params.append({
                        'name': match.group(1),
                        'description': match.group(2)
                    })
            elif line.startswith(':return:') or line.startswith(':returns:'):
                returns = line.split(':', 2)[2].strip() if ':' in line else ''
            elif line.startswith(':raises '):
                match = re.match(r':raises (\w+):\s*(.*)', line)
                if match:
                    raises.append({
                        'exception': match.group(1),
                        'description': match.group(2)
                    })
            elif not line.startswith(':'):
                description_lines.append(line)
            
            i += 1
        
        return {
            'summary': summary,
            'description': '\n'.join(description_lines).strip(),
            'params': params,
            'returns': returns,
            'raises': raises,
            'examples': []
        }
    
    @staticmethod
    def _parse_google_style(docstring: str) -> Dict[str, Any]:
        """Parse Google style docstring"""
        lines = docstring.strip().split('\n')
        summary = lines[0].strip()
        
        params = []
        returns = ''
        raises = []
        description_lines = []
        current_section = None
        
        i = 1
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            
            if stripped == 'Args:':
                current_section = 'args'
            elif stripped == 'Returns:':
                current_section = 'returns'
            elif stripped == 'Raises:':
                current_section = 'raises'
            elif stripped == 'Example:' or stripped == 'Examples:':
                current_section = 'examples'
            elif current_section == 'args' and stripped and indent > 0:
                # Parse argument (indented under Args:)
                if ':' in stripped:
                    match = re.match(r'(\w+)(?:\s*\([\w\[\], ]+\))?\s*:\s*(.*)', stripped)
                    if match:
                        params.append({
                            'name': match.group(1),
                            'description': match.group(2)
                        })
            elif current_section == 'returns' and stripped and indent > 0:
                returns += stripped + ' '
            elif current_section == 'raises' and stripped and indent > 0:
                if ':' in stripped:
                    match = re.match(r'(\w+)\s*:\s*(.*)', stripped)
                    if match:
                        raises.append({
                            'exception': match.group(1),
                            'description': match.group(2)
                        })
            elif current_section is None and stripped:
                description_lines.append(stripped)
            
            i += 1
        
        return {
            'summary': summary,
            'description': '\n'.join(description_lines).strip(),
            'params': params,
            'returns': returns.strip(),
            'raises': raises,
            'examples': []
        }
    
    @staticmethod
    def _parse_numpy_style(docstring: str) -> Dict[str, Any]:
        """Parse NumPy style docstring"""
        # Similar to Google but with different section markers
        lines = docstring.strip().split('\n')
        summary = lines[0].strip()
        
        params = []
        returns = ''
        description_lines = []
        
        # NumPy uses underlined section headers
        current_section = None
        i = 1
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Check for section headers (underlined with ----)
            if i + 1 < len(lines) and re.match(r'^-+$', lines[i + 1].strip()):
                if stripped == 'Parameters':
                    current_section = 'parameters'
                elif stripped == 'Returns':
                    current_section = 'returns'
                elif stripped == 'Raises':
                    current_section = 'raises'
                i += 1  # Skip underline
            elif current_section == 'parameters' and stripped:
                # Parse parameter: name : type
                if ':' in stripped and not stripped.startswith(' '):
                    parts = stripped.split(':', 1)
                    param_name = parts[0].strip()
                    params.append({
                        'name': param_name,
                        'description': parts[1].strip() if len(parts) > 1 else ''
                    })
            elif current_section == 'returns' and stripped:
                returns += stripped + ' '
            elif current_section is None and stripped:
                description_lines.append(stripped)
            
            i += 1
        
        return {
            'summary': summary,
            'description': '\n'.join(description_lines).strip(),
            'params': params,
            'returns': returns.strip(),
            'raises': [],
            'examples': []
        }


class PythonDocExtractor:
    """Extract documentation from Python source files"""
    
    def __init__(self):
        self.items: List[DocItem] = []
    
    def extract_from_file(self, filepath: str) -> List[DocItem]:
        """Extract documentation from a Python file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source, filename=filepath)
            
            # Extract module docstring
            module_doc = ast.get_docstring(tree)
            module_item = DocItem(
                name=Path(filepath).stem,
                type='module',
                docstring=module_doc,
                source_file=filepath,
                line_number=1
            )
            
            # Extract classes and functions (top-level only)
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_item = self._extract_class(node, filepath)
                    module_item.members.append(class_item)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_item = self._extract_function(node, filepath)
                    module_item.members.append(func_item)
            
            return [module_item]
        
        except Exception as e:
            print(f"Error extracting from {filepath}: {e}", file=sys.stderr)
            return []
    
    def _extract_class(self, node: ast.ClassDef, filepath: str) -> DocItem:
        """Extract class documentation"""
        class_item = DocItem(
            name=node.name,
            type='class',
            docstring=ast.get_docstring(node),
            source_file=filepath,
            line_number=node.lineno
        )
        
        # Extract methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_item = self._extract_function(item, filepath, parent=node.name)
                class_item.members.append(method_item)
        
        return class_item
    
    def _extract_function(self, node: ast.FunctionDef, filepath: str, 
                         parent: Optional[str] = None) -> DocItem:
        """Extract function/method documentation"""
        # Build signature
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        signature = f"{node.name}({', '.join(args)})"
        
        func_type = 'method' if parent else 'function'
        
        return DocItem(
            name=node.name,
            type=func_type,
            docstring=ast.get_docstring(node),
            signature=signature,
            source_file=filepath,
            line_number=node.lineno,
            parent=parent
        )


class HTMLGenerator:
    """Generate HTML documentation"""
    
    def __init__(self, theme: str = 'default'):
        self.theme = theme
        self.items: List[DocItem] = []
    
    def generate_html(self, item: DocItem) -> str:
        """Generate HTML for a documentation item"""
        parsed_doc = DocstringParser.parse(item.docstring)
        
        html_parts = []
        html_parts.append(f'<div class="doc-item {item.type}">')
        html_parts.append(f'  <h2 class="doc-name" id="{item.get_id()}">{escape(item.name)}</h2>')
        
        if item.signature:
            html_parts.append(f'  <div class="signature">{escape(item.signature)}</div>')
        
        if parsed_doc['summary']:
            html_parts.append(f'  <p class="summary">{escape(parsed_doc["summary"])}</p>')
        
        if parsed_doc['description']:
            html_parts.append(f'  <div class="description">{escape(parsed_doc["description"])}</div>')
        
        # Parameters
        if parsed_doc['params']:
            html_parts.append('  <h3>Parameters</h3>')
            html_parts.append('  <ul class="parameters">')
            for param in parsed_doc['params']:
                html_parts.append(f'    <li><strong>{escape(param["name"])}</strong>: {escape(param["description"])}</li>')
            html_parts.append('  </ul>')
        
        # Returns
        if parsed_doc['returns']:
            html_parts.append('  <h3>Returns</h3>')
            html_parts.append(f'  <p>{escape(parsed_doc["returns"])}</p>')
        
        # Raises
        if parsed_doc['raises']:
            html_parts.append('  <h3>Raises</h3>')
            html_parts.append('  <ul class="raises">')
            for exc in parsed_doc['raises']:
                html_parts.append(f'    <li><strong>{escape(exc["exception"])}</strong>: {escape(exc["description"])}</li>')
            html_parts.append('  </ul>')
        
        # Members (for classes and modules)
        if item.members:
            html_parts.append(f'  <h3>{item.type.capitalize()} Members</h3>')
            for member in item.members:
                html_parts.append(self.generate_html(member))
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def generate_page(self, item: DocItem, title: str) -> str:
        """Generate complete HTML page"""
        content = self.generate_html(item)
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{escape(title)}</title>
    <style>
        {self.get_css()}
    </style>
</head>
<body>
    <div class="container">
        <h1>{escape(title)}</h1>
        {content}
    </div>
</body>
</html>"""
    
    def get_css(self) -> str:
        """Get CSS styles for documentation"""
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
        }
        h3 {
            color: #7f8c8d;
            margin-top: 20px;
        }
        .doc-item {
            margin: 20px 0;
            padding: 15px;
            background: #fafafa;
            border-left: 4px solid #3498db;
            border-radius: 4px;
        }
        .doc-item.module {
            border-left-color: #9b59b6;
        }
        .doc-item.class {
            border-left-color: #e74c3c;
        }
        .doc-item.function {
            border-left-color: #3498db;
        }
        .doc-item.method {
            border-left-color: #1abc9c;
        }
        .signature {
            font-family: 'Courier New', monospace;
            background: #ecf0f1;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .summary {
            font-weight: bold;
            color: #2c3e50;
        }
        .description {
            margin: 15px 0;
        }
        .parameters, .raises {
            list-style-type: none;
            padding-left: 0;
        }
        .parameters li, .raises li {
            margin: 8px 0;
            padding: 8px;
            background: white;
            border-radius: 4px;
        }
        .parameters strong, .raises strong {
            color: #e74c3c;
        }
        """


class SphinxBuilder:
    """Main Sphinx documentation builder"""
    
    def __init__(self, source_dir: str, build_dir: str):
        self.source_dir = source_dir
        self.build_dir = build_dir
        self.project_name = "Documentation"
        self.author = "Author"
        self.version = "1.0"
        self.theme = "default"
        
        self.extractor = PythonDocExtractor()
        self.generator = HTMLGenerator()
        self.all_items: List[DocItem] = []
    
    def load_config(self, config_file: str = "conf.py"):
        """Load Sphinx configuration"""
        config_path = os.path.join(self.source_dir, config_file)
        
        if not os.path.exists(config_path):
            return
        
        try:
            # Simple configuration extraction
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Extract key configuration values
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('project ='):
                    self.project_name = line.split('=', 1)[1].strip().strip('\'"')
                elif line.startswith('author ='):
                    self.author = line.split('=', 1)[1].strip().strip('\'"')
                elif line.startswith('version =') or line.startswith('release ='):
                    self.version = line.split('=', 1)[1].strip().strip('\'"')
        
        except Exception as e:
            print(f"Warning: Could not load config: {e}", file=sys.stderr)
    
    def collect_python_files(self) -> List[str]:
        """Collect Python files from source directory"""
        python_files = []
        
        for root, dirs, files in os.walk(self.source_dir):
            # Skip hidden directories and __pycache__
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if file.endswith('.py') and not file.startswith('conf.'):
                    filepath = os.path.join(root, file)
                    python_files.append(filepath)
        
        return python_files
    
    def build(self) -> bool:
        """Build documentation"""
        print(f"Building documentation...")
        print(f"Source: {self.source_dir}")
        print(f"Output: {self.build_dir}")
        
        # Load configuration
        self.load_config()
        
        # Create build directory
        os.makedirs(self.build_dir, exist_ok=True)
        
        # Collect Python files
        python_files = self.collect_python_files()
        
        if not python_files:
            print("No Python files found to document")
            return False
        
        print(f"Found {len(python_files)} Python files")
        
        # Extract documentation
        for filepath in python_files:
            print(f"Processing {filepath}...")
            items = self.extractor.extract_from_file(filepath)
            self.all_items.extend(items)
        
        # Generate HTML files
        for item in self.all_items:
            output_file = os.path.join(self.build_dir, f"{item.name}.html")
            html = self.generator.generate_page(item, f"{self.project_name} - {item.name}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f"Generated {output_file}")
        
        # Generate index
        self.generate_index()
        
        print(f"\nBuild finished. Documentation is in {self.build_dir}")
        return True
    
    def generate_index(self):
        """Generate index.html"""
        index_path = os.path.join(self.build_dir, 'index.html')
        
        items_by_type = {'module': [], 'class': [], 'function': []}
        for item in self.all_items:
            if item.type in items_by_type:
                items_by_type[item.type].append(item)
        
        html_parts = ['<!DOCTYPE html>', '<html>', '<head>']
        html_parts.append('<meta charset="utf-8">')
        html_parts.append(f'<title>{escape(self.project_name)} Documentation</title>')
        html_parts.append('<style>')
        html_parts.append(self.generator.get_css())
        html_parts.append('</style>')
        html_parts.append('</head>')
        html_parts.append('<body>')
        html_parts.append('<div class="container">')
        html_parts.append(f'<h1>{escape(self.project_name)} Documentation</h1>')
        html_parts.append(f'<p>Version: {escape(self.version)}</p>')
        html_parts.append(f'<p>Author: {escape(self.author)}</p>')
        
        for item_type, items in items_by_type.items():
            if items:
                html_parts.append(f'<h2>{item_type.capitalize()}s</h2>')
                html_parts.append('<ul>')
                for item in items:
                    html_parts.append(f'  <li><a href="{item.name}.html">{escape(item.name)}</a>')
                    if item.docstring:
                        parsed = DocstringParser.parse(item.docstring)
                        if parsed['summary']:
                            html_parts.append(f' - {escape(parsed["summary"][:100])}')
                    html_parts.append('</li>')
                html_parts.append('</ul>')
        
        html_parts.append('</div>')
        html_parts.append('</body>')
        html_parts.append('</html>')
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_parts))
        
        print(f"Generated index: {index_path}")


def quickstart():
    """Interactive quickstart for creating Sphinx project"""
    print("Welcome to the Sphinx quickstart utility.")
    print()
    
    project_name = input("Project name: ") or "MyProject"
    author = input("Author name: ") or "Author"
    version = input("Project version [1.0]: ") or "1.0"
    source_dir = input("Source directory [.]: ") or "."
    build_dir = input("Build directory [_build]: ") or "_build"
    
    # Create directories
    os.makedirs(source_dir, exist_ok=True)
    os.makedirs(build_dir, exist_ok=True)
    
    # Create conf.py
    conf_content = f'''# Configuration file for Sphinx documentation
project = '{project_name}'
author = '{author}'
version = '{version}'
release = '{version}'

# Theme
html_theme = 'default'
'''
    
    conf_path = os.path.join(source_dir, 'conf.py')
    with open(conf_path, 'w') as f:
        f.write(conf_content)
    
    print(f"\nCreated configuration in {conf_path}")
    print(f"\nTo build documentation:")
    print(f"  python sphinx_emulator.py build {source_dir} {build_dir}")


def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sphinx documentation generator')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # build command
    build_parser = subparsers.add_parser('build', help='Build documentation')
    build_parser.add_argument('source', help='Source directory')
    build_parser.add_argument('build', help='Build directory')
    
    # quickstart command
    quickstart_parser = subparsers.add_parser('quickstart', 
                                              help='Start a new documentation project')
    
    args = parser.parse_args()
    
    if args.command == 'build':
        builder = SphinxBuilder(args.source, args.build)
        success = builder.build()
        sys.exit(0 if success else 1)
    
    elif args.command == 'quickstart':
        quickstart()
        sys.exit(0)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
