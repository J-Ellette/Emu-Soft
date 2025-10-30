"""
pdoc Emulator - Automatic API documentation generator without external dependencies

This module emulates pdoc functionality for generating API documentation
from Python source code without requiring external dependencies.

Features:
- Automatic API documentation from Python modules
- Docstring extraction and parsing
- HTML documentation generation
- Module, class, function, and method documentation
- Search functionality (basic)
- Source code linking
- Clean, modern HTML output
- Command-line interface

Note: This is a simplified implementation focusing on core functionality.
Advanced features like live reload and custom templates are simplified.
"""

import ast
import os
import sys
import inspect
import importlib
import pkgutil
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from html import escape
import re


@dataclass
class DocItem:
    """Represents a documented Python object"""
    name: str
    type: str  # module, class, function, method, attribute
    qualname: str  # Fully qualified name
    docstring: Optional[str] = None
    signature: Optional[str] = None
    source: Optional[str] = None
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    members: List['DocItem'] = field(default_factory=list)
    is_private: bool = False
    
    def get_anchor(self) -> str:
        """Get HTML anchor ID for this item"""
        return self.qualname.replace('.', '-')


class PythonInspector:
    """Extract documentation from Python modules"""
    
    def __init__(self, show_private: bool = False, show_source: bool = True):
        self.show_private = show_private
        self.show_source = show_source
    
    def inspect_module(self, module_name: str) -> Optional[DocItem]:
        """Inspect a Python module and extract documentation"""
        try:
            # Import the module
            module = importlib.import_module(module_name)
            
            # Get module info
            doc_item = DocItem(
                name=module_name,
                type='module',
                qualname=module_name,
                docstring=inspect.getdoc(module),
                source_file=inspect.getfile(module) if hasattr(module, '__file__') else None
            )
            
            # Extract members
            for name, obj in inspect.getmembers(module):
                # Skip private unless requested
                if name.startswith('_') and not self.show_private:
                    continue
                
                # Skip imported modules
                if inspect.ismodule(obj):
                    continue
                
                # Only document items defined in this module
                if hasattr(obj, '__module__') and obj.__module__ != module_name:
                    continue
                
                member_item = self._inspect_object(name, obj, module_name)
                if member_item:
                    doc_item.members.append(member_item)
            
            return doc_item
        
        except Exception as e:
            print(f"Error inspecting module {module_name}: {e}")
            return None
    
    def _inspect_object(self, name: str, obj: Any, parent_qualname: str) -> Optional[DocItem]:
        """Inspect a Python object"""
        qualname = f"{parent_qualname}.{name}"
        is_private = name.startswith('_')
        
        # Determine type
        if inspect.isclass(obj):
            return self._inspect_class(name, obj, qualname, is_private)
        elif inspect.isfunction(obj) or inspect.ismethod(obj):
            return self._inspect_function(name, obj, qualname, is_private)
        else:
            # Attribute or other
            return DocItem(
                name=name,
                type='attribute',
                qualname=qualname,
                docstring=None,
                is_private=is_private
            )
    
    def _inspect_class(self, name: str, cls: type, qualname: str, is_private: bool) -> DocItem:
        """Inspect a class"""
        doc_item = DocItem(
            name=name,
            type='class',
            qualname=qualname,
            docstring=inspect.getdoc(cls),
            is_private=is_private
        )
        
        # Get class signature (inheritance)
        bases = [base.__name__ for base in cls.__bases__ if base != object]
        if bases:
            doc_item.signature = f"class {name}({', '.join(bases)})"
        else:
            doc_item.signature = f"class {name}"
        
        # Get source if requested
        if self.show_source:
            try:
                doc_item.source = inspect.getsource(cls)
            except:
                pass
        
        # Inspect methods
        for method_name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if method_name.startswith('_') and not self.show_private:
                continue
            
            method_qualname = f"{qualname}.{method_name}"
            method_item = self._inspect_function(method_name, method, method_qualname, method_name.startswith('_'))
            method_item.type = 'method'
            doc_item.members.append(method_item)
        
        return doc_item
    
    def _inspect_function(self, name: str, func: Any, qualname: str, is_private: bool) -> DocItem:
        """Inspect a function or method"""
        doc_item = DocItem(
            name=name,
            type='function',
            qualname=qualname,
            docstring=inspect.getdoc(func),
            is_private=is_private
        )
        
        # Get signature
        try:
            sig = inspect.signature(func)
            doc_item.signature = f"{name}{sig}"
        except:
            doc_item.signature = f"{name}(...)"
        
        # Get source if requested
        if self.show_source:
            try:
                doc_item.source = inspect.getsource(func)
            except:
                pass
        
        # Get source location
        try:
            doc_item.source_file = inspect.getfile(func)
            doc_item.line_number = inspect.getsourcelines(func)[1]
        except:
            pass
        
        return doc_item


class HTMLGenerator:
    """Generate HTML documentation"""
    
    def __init__(self):
        self.all_items: List[DocItem] = []
    
    def generate_html(self, doc_item: DocItem) -> str:
        """Generate HTML for a documentation item"""
        if doc_item.type == 'module':
            return self._generate_module_html(doc_item)
        elif doc_item.type == 'class':
            return self._generate_class_html(doc_item)
        elif doc_item.type == 'function' or doc_item.type == 'method':
            return self._generate_function_html(doc_item)
        elif doc_item.type == 'attribute':
            return self._generate_attribute_html(doc_item)
        return ''
    
    def _generate_module_html(self, module: DocItem) -> str:
        """Generate HTML for a module"""
        self.all_items = [module]
        self._collect_all_items(module)
        
        html_parts = []
        
        # Module header
        html_parts.append(f'<div class="module-header">')
        html_parts.append(f'<h1 id="{module.get_anchor()}" class="module-name">Module: {escape(module.name)}</h1>')
        
        if module.source_file:
            html_parts.append(f'<p class="source-file">Source: <code>{escape(module.source_file)}</code></p>')
        
        if module.docstring:
            html_parts.append(f'<div class="docstring">{self._format_docstring(module.docstring)}</div>')
        
        html_parts.append('</div>')
        
        # Table of contents
        html_parts.append(self._generate_toc(module))
        
        # Classes
        classes = [m for m in module.members if m.type == 'class']
        if classes:
            html_parts.append('<h2>Classes</h2>')
            for cls in classes:
                html_parts.append(self._generate_class_html(cls))
        
        # Functions
        functions = [m for m in module.members if m.type == 'function']
        if functions:
            html_parts.append('<h2>Functions</h2>')
            for func in functions:
                html_parts.append(self._generate_function_html(func))
        
        # Attributes
        attributes = [m for m in module.members if m.type == 'attribute']
        if attributes:
            html_parts.append('<h2>Module Attributes</h2>')
            for attr in attributes:
                html_parts.append(self._generate_attribute_html(attr))
        
        return '\n'.join(html_parts)
    
    def _generate_class_html(self, cls: DocItem) -> str:
        """Generate HTML for a class"""
        html_parts = []
        
        html_parts.append(f'<div class="class-doc" id="{cls.get_anchor()}">')
        html_parts.append(f'<h3 class="class-name">{escape(cls.name)}</h3>')
        
        if cls.signature:
            html_parts.append(f'<pre class="signature"><code>{escape(cls.signature)}</code></pre>')
        
        if cls.docstring:
            html_parts.append(f'<div class="docstring">{self._format_docstring(cls.docstring)}</div>')
        
        # Methods
        if cls.members:
            html_parts.append('<h4>Methods</h4>')
            for method in cls.members:
                html_parts.append(self._generate_method_html(method))
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _generate_function_html(self, func: DocItem) -> str:
        """Generate HTML for a function"""
        html_parts = []
        
        html_parts.append(f'<div class="function-doc" id="{func.get_anchor()}">')
        html_parts.append(f'<h3 class="function-name">{escape(func.name)}</h3>')
        
        if func.signature:
            html_parts.append(f'<pre class="signature"><code>{escape(func.signature)}</code></pre>')
        
        if func.source_file and func.line_number:
            html_parts.append(f'<p class="source-location">Defined in <code>{escape(func.source_file)}</code> at line {func.line_number}</p>')
        
        if func.docstring:
            html_parts.append(f'<div class="docstring">{self._format_docstring(func.docstring)}</div>')
        
        if func.source:
            html_parts.append('<details class="source-code">')
            html_parts.append('<summary>View Source</summary>')
            html_parts.append(f'<pre><code>{escape(func.source)}</code></pre>')
            html_parts.append('</details>')
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _generate_method_html(self, method: DocItem) -> str:
        """Generate HTML for a method (similar to function but indented)"""
        html_parts = []
        
        html_parts.append(f'<div class="method-doc" id="{method.get_anchor()}">')
        html_parts.append(f'<h4 class="method-name">{escape(method.name)}</h4>')
        
        if method.signature:
            html_parts.append(f'<pre class="signature"><code>{escape(method.signature)}</code></pre>')
        
        if method.docstring:
            html_parts.append(f'<div class="docstring">{self._format_docstring(method.docstring)}</div>')
        
        if method.source:
            html_parts.append('<details class="source-code">')
            html_parts.append('<summary>View Source</summary>')
            html_parts.append(f'<pre><code>{escape(method.source)}</code></pre>')
            html_parts.append('</details>')
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _generate_attribute_html(self, attr: DocItem) -> str:
        """Generate HTML for an attribute"""
        return f'<div class="attribute-doc"><code>{escape(attr.name)}</code></div>'
    
    def _format_docstring(self, docstring: str) -> str:
        """Format docstring with basic HTML"""
        # Convert to paragraphs
        paragraphs = docstring.split('\n\n')
        html_parts = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Code blocks (indented)
            if para.startswith('    '):
                code = '\n'.join(line[4:] if line.startswith('    ') else line 
                               for line in para.split('\n'))
                html_parts.append(f'<pre><code>{escape(code)}</code></pre>')
            else:
                # Regular paragraph
                html_parts.append(f'<p>{escape(para)}</p>')
        
        return '\n'.join(html_parts)
    
    def _collect_all_items(self, item: DocItem):
        """Recursively collect all documentation items"""
        for member in item.members:
            self.all_items.append(member)
            self._collect_all_items(member)
    
    def _generate_toc(self, module: DocItem) -> str:
        """Generate table of contents"""
        html_parts = ['<div class="toc">', '<h2>Contents</h2>', '<ul>']
        
        # Classes
        classes = [m for m in module.members if m.type == 'class']
        if classes:
            html_parts.append('<li><strong>Classes</strong><ul>')
            for cls in classes:
                html_parts.append(f'<li><a href="#{cls.get_anchor()}">{escape(cls.name)}</a></li>')
            html_parts.append('</ul></li>')
        
        # Functions
        functions = [m for m in module.members if m.type == 'function']
        if functions:
            html_parts.append('<li><strong>Functions</strong><ul>')
            for func in functions:
                html_parts.append(f'<li><a href="#{func.get_anchor()}">{escape(func.name)}</a></li>')
            html_parts.append('</ul></li>')
        
        html_parts.append('</ul></div>')
        return '\n'.join(html_parts)
    
    def generate_page(self, doc_item: DocItem, title: str) -> str:
        """Generate a complete HTML page"""
        content = self.generate_html(doc_item)
        
        css = self._get_css()
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)}</title>
    <style>
{css}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1 class="site-title">API Documentation</h1>
        </header>
        <main>
            {content}
        </main>
        <footer>
            <p>Generated by pdoc emulator</p>
        </footer>
    </div>
</body>
</html>"""
        
        return html
    
    def _get_css(self) -> str:
        """Get CSS styling"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            min-height: 100vh;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
        }
        
        .site-title {
            font-size: 2rem;
            font-weight: 600;
        }
        
        main {
            padding: 2rem;
        }
        
        .module-header {
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #667eea;
        }
        
        .module-name {
            font-size: 2.5rem;
            color: #667eea;
            margin-bottom: 0.5rem;
        }
        
        .source-file {
            color: #666;
            font-size: 0.9rem;
            margin: 0.5rem 0;
        }
        
        .toc {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 1.5rem;
            margin: 2rem 0;
        }
        
        .toc h2 {
            font-size: 1.25rem;
            margin-bottom: 1rem;
            color: #495057;
        }
        
        .toc ul {
            list-style: none;
            padding-left: 0;
        }
        
        .toc li {
            margin: 0.5rem 0;
            padding-left: 1rem;
        }
        
        .toc a {
            color: #667eea;
            text-decoration: none;
        }
        
        .toc a:hover {
            text-decoration: underline;
        }
        
        h2 {
            font-size: 2rem;
            color: #495057;
            margin: 2rem 0 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #dee2e6;
        }
        
        .class-doc, .function-doc {
            background-color: #fff;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 1.5rem;
            margin: 1.5rem 0;
        }
        
        .class-name, .function-name {
            font-size: 1.5rem;
            color: #667eea;
            margin-bottom: 0.5rem;
        }
        
        .method-doc {
            background-color: #f8f9fa;
            border-left: 3px solid #667eea;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        .method-name {
            font-size: 1.25rem;
            color: #764ba2;
            margin-bottom: 0.5rem;
        }
        
        .signature {
            background-color: #2d3748;
            color: #e2e8f0;
            padding: 1rem;
            border-radius: 5px;
            overflow-x: auto;
            margin: 1rem 0;
        }
        
        .signature code {
            color: #e2e8f0;
            font-family: 'Courier New', Courier, monospace;
        }
        
        .docstring {
            margin: 1rem 0;
            color: #495057;
        }
        
        .docstring p {
            margin: 0.75rem 0;
        }
        
        .docstring pre {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 3px;
            padding: 1rem;
            overflow-x: auto;
        }
        
        .docstring code {
            background-color: #f8f9fa;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9em;
        }
        
        .source-location {
            font-size: 0.9rem;
            color: #666;
            margin: 0.5rem 0;
        }
        
        .source-code {
            margin: 1rem 0;
        }
        
        .source-code summary {
            cursor: pointer;
            color: #667eea;
            font-weight: 500;
            padding: 0.5rem;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 3px;
        }
        
        .source-code summary:hover {
            background-color: #e9ecef;
        }
        
        .source-code pre {
            background-color: #2d3748;
            color: #e2e8f0;
            padding: 1rem;
            border-radius: 5px;
            overflow-x: auto;
            margin-top: 0.5rem;
        }
        
        .source-code code {
            color: #e2e8f0;
            font-family: 'Courier New', Courier, monospace;
        }
        
        .attribute-doc {
            padding: 0.5rem;
            margin: 0.5rem 0;
        }
        
        code {
            font-family: 'Courier New', Courier, monospace;
        }
        
        footer {
            background-color: #f8f9fa;
            border-top: 1px solid #dee2e6;
            padding: 1.5rem;
            text-align: center;
            color: #666;
            margin-top: 2rem;
        }
        
        @media (max-width: 768px) {
            main {
                padding: 1rem;
            }
            
            .module-name {
                font-size: 2rem;
            }
        }
        """


class PdocEmulator:
    """Main pdoc emulator class"""
    
    def __init__(self, show_private: bool = False, show_source: bool = True):
        self.inspector = PythonInspector(show_private, show_source)
        self.generator = HTMLGenerator()
    
    def document_module(self, module_name: str, output_file: Optional[str] = None) -> bool:
        """Generate documentation for a module"""
        # Inspect module
        doc_item = self.inspector.inspect_module(module_name)
        
        if not doc_item:
            print(f"Failed to inspect module: {module_name}")
            return False
        
        # Generate HTML
        html = self.generator.generate_page(doc_item, f"{module_name} - API Documentation")
        
        # Write to file or stdout
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f"Documentation generated: {output_file}")
        else:
            print(html)
        
        return True


def main():
    """Command-line interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("pdoc Emulator - Automatic API documentation generator")
        print("\nUsage:")
        print("  python pdoc_emulator.py <module_name> [output_file]")
        print("\nExamples:")
        print("  python pdoc_emulator.py mymodule")
        print("  python pdoc_emulator.py mymodule docs/mymodule.html")
        print("  python pdoc_emulator.py mypackage.submodule")
        return
    
    module_name = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Add current directory to path
    sys.path.insert(0, os.getcwd())
    
    emulator = PdocEmulator()
    emulator.document_module(module_name, output_file)


if __name__ == '__main__':
    main()
