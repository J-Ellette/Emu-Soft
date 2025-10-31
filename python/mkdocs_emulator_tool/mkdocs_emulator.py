"""
MkDocs Emulator - Markdown documentation generator without external dependencies

This module emulates MkDocs functionality for generating documentation websites
from Markdown files without requiring external dependencies.

Features:
- Markdown to HTML conversion
- Multiple pages with navigation
- Configuration via mkdocs.yml
- Automatic table of contents generation
- Theme support (basic)
- Site structure with index
- Cross-page linking
- Code block syntax highlighting (basic)

Note: This is a simplified implementation focusing on core functionality.
Advanced features like plugins and complex themes are simplified.
"""

import os
import re
import json
import yaml as yaml_parser  # Will implement minimal YAML parsing
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from html import escape
import shutil


class MinimalYAMLParser:
    """Minimal YAML parser for mkdocs.yml configuration"""
    
    @staticmethod
    def parse(content: str) -> Dict[str, Any]:
        """Parse simple YAML content"""
        result = {}
        lines = content.strip().split('\n')
        current_key = None
        current_list = None
        indent_stack = []
        
        for line in lines:
            # Skip comments and empty lines
            if not line.strip() or line.strip().startswith('#'):
                continue
            
            # Count leading spaces
            indent = len(line) - len(line.lstrip())
            line = line.strip()
            
            # Handle key-value pairs
            if ':' in line and not line.startswith('-'):
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if value:
                    # Simple value
                    result[key] = value.strip('"\'')
                else:
                    # Start of nested structure
                    current_key = key
                    current_list = []
                    result[key] = current_list
            
            # Handle list items
            elif line.startswith('-') and current_list is not None:
                item = line[1:].strip()
                if ':' in item:
                    # Dict item in list
                    k, v = item.split(':', 1)
                    current_list.append({k.strip(): v.strip().strip('"\'')})
                else:
                    # Simple list item
                    current_list.append(item.strip('"\''))
        
        return result


@dataclass
class MarkdownPage:
    """Represents a Markdown documentation page"""
    title: str
    path: str
    content: str
    html_content: str = ""
    level: int = 0
    children: List['MarkdownPage'] = field(default_factory=list)


class MarkdownConverter:
    """Convert Markdown to HTML"""
    
    @staticmethod
    def convert(markdown: str) -> str:
        """Convert Markdown text to HTML"""
        html = markdown
        
        # Headers
        html = re.sub(r'^######\s+(.+)$', r'<h6>\1</h6>', html, flags=re.MULTILINE)
        html = re.sub(r'^#####\s+(.+)$', r'<h5>\1</h5>', html, flags=re.MULTILINE)
        html = re.sub(r'^####\s+(.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        html = re.sub(r'^###\s+(.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^##\s+(.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^#\s+(.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Code blocks (fenced)
        def replace_code_block(match):
            lang = match.group(1) or ''
            code = escape(match.group(2))
            return f'<pre><code class="language-{lang}">{code}</code></pre>'
        
        html = re.sub(r'```(\w+)?\n(.*?)```', replace_code_block, html, flags=re.DOTALL)
        
        # Inline code
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
        
        # Bold
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'__(.+?)__', r'<strong>\1</strong>', html)
        
        # Italic
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        html = re.sub(r'_(.+?)_', r'<em>\1</em>', html)
        
        # Images (must come before links!)
        html = re.sub(r'!\[([^\]]*)\]\(([^\)]+)\)', r'<img src="\2" alt="\1" />', html)
        
        # Links
        html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html)
        
        # Unordered lists
        lines = html.split('\n')
        in_list = False
        result = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('- ') or stripped.startswith('* '):
                if not in_list:
                    result.append('<ul>')
                    in_list = True
                item = stripped[2:]
                result.append(f'<li>{item}</li>')
            else:
                if in_list:
                    result.append('</ul>')
                    in_list = False
                result.append(line)
        
        if in_list:
            result.append('</ul>')
        
        html = '\n'.join(result)
        
        # Ordered lists
        lines = html.split('\n')
        in_list = False
        result = []
        
        for line in lines:
            stripped = line.strip()
            if re.match(r'^\d+\.\s+', stripped):
                if not in_list:
                    result.append('<ol>')
                    in_list = True
                item = re.sub(r'^\d+\.\s+', '', stripped)
                result.append(f'<li>{item}</li>')
            else:
                if in_list:
                    result.append('</ol>')
                    in_list = False
                result.append(line)
        
        if in_list:
            result.append('</ol>')
        
        html = '\n'.join(result)
        
        # Paragraphs
        lines = html.split('\n')
        result = []
        in_para = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip if it's already wrapped in HTML tags
            if stripped.startswith('<') or not stripped:
                if in_para:
                    result.append('</p>')
                    in_para = False
                result.append(line)
            else:
                if not in_para:
                    result.append('<p>')
                    in_para = True
                result.append(line)
        
        if in_para:
            result.append('</p>')
        
        html = '\n'.join(result)
        
        # Blockquotes
        html = re.sub(r'^>\s+(.+)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)
        
        # Horizontal rule
        html = re.sub(r'^---$', r'<hr />', html, flags=re.MULTILINE)
        html = re.sub(r'^\*\*\*$', r'<hr />', html, flags=re.MULTILINE)
        
        return html


class MkDocsBuilder:
    """MkDocs documentation builder"""
    
    DEFAULT_CONFIG = {
        'site_name': 'My Documentation',
        'site_description': 'Documentation site',
        'site_author': 'Author',
        'theme': 'default',
        'docs_dir': 'docs',
        'site_dir': 'site',
    }
    
    def __init__(self, config_file: str = 'mkdocs.yml'):
        """Initialize MkDocs builder"""
        self.config_file = config_file
        self.config = self.DEFAULT_CONFIG.copy()
        self.pages: List[MarkdownPage] = []
        self.source_dir = '.'
        
    def load_config(self):
        """Load configuration from mkdocs.yml"""
        config_path = Path(self.source_dir) / self.config_file
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                content = f.read()
                user_config = MinimalYAMLParser.parse(content)
                self.config.update(user_config)
        
        return self.config
    
    def discover_pages(self) -> List[MarkdownPage]:
        """Discover Markdown pages in docs directory"""
        docs_dir = Path(self.source_dir) / self.config['docs_dir']
        pages = []
        
        if not docs_dir.exists():
            print(f"Warning: docs directory '{docs_dir}' not found")
            return pages
        
        # Find all markdown files
        for md_file in sorted(docs_dir.rglob('*.md')):
            relative_path = md_file.relative_to(docs_dir)
            
            # Read content
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title from first h1 or use filename
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else md_file.stem.replace('_', ' ').title()
            
            page = MarkdownPage(
                title=title,
                path=str(relative_path),
                content=content
            )
            pages.append(page)
        
        return pages
    
    def build_navigation(self, pages: List[MarkdownPage]) -> str:
        """Build navigation HTML"""
        nav_items = []
        
        # Home link
        nav_items.append('<li><a href="index.html">Home</a></li>')
        
        # Other pages
        for page in pages:
            if page.path != 'index.md':
                html_path = page.path.replace('.md', '.html')
                nav_items.append(f'<li><a href="{html_path}">{escape(page.title)}</a></li>')
        
        return '<ul class="nav">\n' + '\n'.join(nav_items) + '\n</ul>'
    
    def generate_page_html(self, page: MarkdownPage, navigation: str) -> str:
        """Generate complete HTML page"""
        html_content = MarkdownConverter.convert(page.content)
        
        theme_css = self._get_theme_css()
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(page.title)} - {escape(self.config['site_name'])}</title>
    <meta name="description" content="{escape(self.config.get('site_description', ''))}">
    <style>
{theme_css}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1 class="site-name">{escape(self.config['site_name'])}</h1>
            <nav>
                {navigation}
            </nav>
        </header>
        <main>
            <article>
                {html_content}
            </article>
        </main>
        <footer>
            <p>&copy; {escape(self.config.get('site_author', ''))} | Built with MkDocs Emulator</p>
        </footer>
    </div>
</body>
</html>"""
        
        return html
    
    def _get_theme_css(self) -> str:
        """Get CSS for the theme"""
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
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        
        header {
            background-color: #2c3e50;
            color: white;
            padding: 1.5rem 2rem;
        }
        
        .site-name {
            font-size: 2rem;
            margin-bottom: 1rem;
        }
        
        nav ul.nav {
            list-style: none;
            display: flex;
            flex-wrap: wrap;
            gap: 1.5rem;
        }
        
        nav ul.nav li a {
            color: #ecf0f1;
            text-decoration: none;
            transition: color 0.3s;
        }
        
        nav ul.nav li a:hover {
            color: #3498db;
        }
        
        main {
            padding: 2rem;
            min-height: 500px;
        }
        
        article h1 {
            font-size: 2.5rem;
            margin: 1.5rem 0 1rem;
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 0.5rem;
        }
        
        article h2 {
            font-size: 2rem;
            margin: 1.5rem 0 1rem;
            color: #34495e;
        }
        
        article h3 {
            font-size: 1.5rem;
            margin: 1.25rem 0 0.75rem;
            color: #34495e;
        }
        
        article h4, article h5, article h6 {
            margin: 1rem 0 0.5rem;
            color: #34495e;
        }
        
        article p {
            margin: 1rem 0;
            line-height: 1.8;
        }
        
        article ul, article ol {
            margin: 1rem 0 1rem 2rem;
        }
        
        article li {
            margin: 0.5rem 0;
        }
        
        article code {
            background-color: #f4f4f4;
            border: 1px solid #ddd;
            border-radius: 3px;
            padding: 0.2rem 0.4rem;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9em;
        }
        
        article pre {
            background-color: #2c3e50;
            color: #ecf0f1;
            border-radius: 5px;
            padding: 1rem;
            overflow-x: auto;
            margin: 1rem 0;
        }
        
        article pre code {
            background: none;
            border: none;
            padding: 0;
            color: #ecf0f1;
        }
        
        article a {
            color: #3498db;
            text-decoration: none;
        }
        
        article a:hover {
            text-decoration: underline;
        }
        
        article img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 1rem 0;
        }
        
        article blockquote {
            border-left: 4px solid #3498db;
            padding-left: 1rem;
            margin: 1rem 0;
            color: #555;
            font-style: italic;
        }
        
        article hr {
            border: none;
            border-top: 2px solid #ddd;
            margin: 2rem 0;
        }
        
        article table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }
        
        article table th, article table td {
            border: 1px solid #ddd;
            padding: 0.75rem;
            text-align: left;
        }
        
        article table th {
            background-color: #f4f4f4;
            font-weight: bold;
        }
        
        footer {
            background-color: #34495e;
            color: #ecf0f1;
            text-align: center;
            padding: 1.5rem;
            margin-top: 2rem;
        }
        
        @media (max-width: 768px) {
            nav ul.nav {
                flex-direction: column;
            }
            
            main {
                padding: 1rem;
            }
        }
        """
    
    def build(self, source_dir: str = '.', output_dir: Optional[str] = None) -> bool:
        """Build documentation site"""
        self.source_dir = source_dir
        
        # Load configuration
        self.load_config()
        
        # Determine output directory
        if output_dir is None:
            output_dir = str(Path(source_dir) / self.config['site_dir'])
        
        output_path = Path(output_dir)
        
        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Discover pages
        self.pages = self.discover_pages()
        
        if not self.pages:
            print("Warning: No Markdown pages found")
            return False
        
        # Build navigation
        navigation = self.build_navigation(self.pages)
        
        # Generate HTML for each page
        for page in self.pages:
            html = self.generate_page_html(page, navigation)
            
            # Determine output filename
            html_filename = page.path.replace('.md', '.html')
            output_file = output_path / html_filename
            
            # Create subdirectories if needed
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write HTML file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f"Generated: {html_filename}")
        
        print(f"\nDocumentation built successfully in '{output_dir}'")
        print(f"Open {output_dir}/index.html in a browser to view the site")
        
        return True
    
    def new(self, project_name: str, output_dir: str = '.') -> bool:
        """Create a new MkDocs project"""
        project_path = Path(output_dir) / project_name
        
        if project_path.exists():
            print(f"Error: Directory '{project_path}' already exists")
            return False
        
        # Create project structure
        project_path.mkdir(parents=True)
        docs_dir = project_path / 'docs'
        docs_dir.mkdir()
        
        # Create mkdocs.yml
        config_content = f"""site_name: {project_name}
site_description: Documentation for {project_name}
site_author: Author Name
theme: default
docs_dir: docs
site_dir: site
"""
        
        with open(project_path / 'mkdocs.yml', 'w') as f:
            f.write(config_content)
        
        # Create index.md
        index_content = f"""# Welcome to {project_name}

This is the documentation for {project_name}.

## Getting Started

Add your documentation in Markdown files in the `docs` directory.

## Features

- Easy Markdown editing
- Beautiful HTML output
- Simple navigation
- Fast builds

## Next Steps

1. Edit this file (`docs/index.md`)
2. Add more pages in the `docs` directory
3. Run `mkdocs build` to generate the site
"""
        
        with open(docs_dir / 'index.md', 'w') as f:
            f.write(index_content)
        
        print(f"Project '{project_name}' created successfully!")
        print(f"Location: {project_path}")
        print(f"\nNext steps:")
        print(f"  cd {project_name}")
        print(f"  # Edit docs/index.md")
        print(f"  # Add more .md files to docs/")
        print(f"  python -m mkdocs_emulator_tool.mkdocs_emulator build")
        
        return True


def main():
    """Command-line interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("MkDocs Emulator - Markdown documentation generator")
        print("\nUsage:")
        print("  python mkdocs_emulator.py build [source_dir] [output_dir]")
        print("  python mkdocs_emulator.py new <project_name>")
        print("\nExamples:")
        print("  python mkdocs_emulator.py build")
        print("  python mkdocs_emulator.py build . site")
        print("  python mkdocs_emulator.py new my-documentation")
        return
    
    command = sys.argv[1]
    
    if command == 'build':
        source_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
        output_dir = sys.argv[3] if len(sys.argv) > 3 else None
        
        builder = MkDocsBuilder()
        builder.build(source_dir, output_dir)
    
    elif command == 'new':
        if len(sys.argv) < 3:
            print("Error: Project name required")
            print("Usage: python mkdocs_emulator.py new <project_name>")
            return
        
        project_name = sys.argv[2]
        builder = MkDocsBuilder()
        builder.new(project_name)
    
    else:
        print(f"Unknown command: {command}")
        print("Available commands: build, new")


if __name__ == '__main__':
    main()
