#!/usr/bin/env python3
"""
Tests for MkDocs Emulator
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mkdocs_emulator_tool.mkdocs_emulator import (
    MarkdownConverter,
    MarkdownPage,
    MkDocsBuilder,
    MinimalYAMLParser
)


class TestMinimalYAMLParser:
    """Test YAML parser"""
    
    @staticmethod
    def test_simple_key_value():
        """Test simple key-value parsing"""
        yaml = """
site_name: My Site
site_author: John Doe
        """
        result = MinimalYAMLParser.parse(yaml)
        assert result['site_name'] == 'My Site'
        assert result['site_author'] == 'John Doe'
        print("✓ Simple key-value parsing works")
    
    @staticmethod
    def test_list_parsing():
        """Test list parsing"""
        yaml = """
pages:
  - Home
  - About
  - Contact
        """
        result = MinimalYAMLParser.parse(yaml)
        assert 'pages' in result
        assert 'Home' in result['pages']
        print("✓ List parsing works")
    
    @staticmethod
    def test_comments():
        """Test comment handling"""
        yaml = """
# This is a comment
site_name: My Site
# Another comment
site_author: John Doe
        """
        result = MinimalYAMLParser.parse(yaml)
        assert result['site_name'] == 'My Site'
        print("✓ Comment handling works")


class TestMarkdownConverter:
    """Test Markdown to HTML conversion"""
    
    @staticmethod
    def test_headers():
        """Test header conversion"""
        md = "# Header 1\n## Header 2\n### Header 3"
        html = MarkdownConverter.convert(md)
        assert '<h1>Header 1</h1>' in html
        assert '<h2>Header 2</h2>' in html
        assert '<h3>Header 3</h3>' in html
        print("✓ Header conversion works")
    
    @staticmethod
    def test_bold_italic():
        """Test bold and italic"""
        md = "**bold** *italic* __also bold__ _also italic_"
        html = MarkdownConverter.convert(md)
        assert '<strong>bold</strong>' in html
        assert '<em>italic</em>' in html
        print("✓ Bold and italic conversion works")
    
    @staticmethod
    def test_links():
        """Test link conversion"""
        md = "[Link Text](https://example.com)"
        html = MarkdownConverter.convert(md)
        assert '<a href="https://example.com">Link Text</a>' in html
        print("✓ Link conversion works")
    
    @staticmethod
    def test_code():
        """Test code formatting"""
        md = "`inline code`"
        html = MarkdownConverter.convert(md)
        assert '<code>inline code</code>' in html
        print("✓ Inline code conversion works")
    
    @staticmethod
    def test_code_block():
        """Test code block"""
        md = "```python\ndef hello():\n    print('Hello')\n```"
        html = MarkdownConverter.convert(md)
        assert '<pre>' in html
        assert '<code' in html
        print("✓ Code block conversion works")
    
    @staticmethod
    def test_lists():
        """Test list conversion"""
        md = "- Item 1\n- Item 2\n- Item 3"
        html = MarkdownConverter.convert(md)
        assert '<ul>' in html
        assert '<li>Item 1</li>' in html
        print("✓ List conversion works")
    
    @staticmethod
    def test_ordered_lists():
        """Test ordered list conversion"""
        md = "1. First\n2. Second\n3. Third"
        html = MarkdownConverter.convert(md)
        assert '<ol>' in html
        assert '<li>First</li>' in html
        print("✓ Ordered list conversion works")
    
    @staticmethod
    def test_images():
        """Test image conversion"""
        md = "![Alt text](image.png)"
        html = MarkdownConverter.convert(md)
        assert '<img src="image.png" alt="Alt text"' in html
        print("✓ Image conversion works")


class TestMarkdownPage:
    """Test MarkdownPage class"""
    
    @staticmethod
    def test_page_creation():
        """Test page creation"""
        page = MarkdownPage(
            title="Test Page",
            path="test.md",
            content="# Test\nContent"
        )
        assert page.title == "Test Page"
        assert page.path == "test.md"
        assert "# Test" in page.content
        print("✓ MarkdownPage creation works")
    
    @staticmethod
    def test_page_with_children():
        """Test page with children"""
        parent = MarkdownPage(title="Parent", path="parent.md", content="Parent content")
        child = MarkdownPage(title="Child", path="child.md", content="Child content")
        parent.children.append(child)
        assert len(parent.children) == 1
        assert parent.children[0].title == "Child"
        print("✓ MarkdownPage with children works")


class TestMkDocsBuilder:
    """Test MkDocs builder"""
    
    @staticmethod
    def test_default_config():
        """Test default configuration"""
        builder = MkDocsBuilder()
        assert builder.config['site_name'] == 'My Documentation'
        assert builder.config['docs_dir'] == 'docs'
        assert builder.config['site_dir'] == 'site'
        print("✓ Default configuration works")
    
    @staticmethod
    def test_markdown_to_html():
        """Test Markdown to HTML conversion"""
        page = MarkdownPage(
            title="Test",
            path="test.md",
            content="# Hello\nThis is a test."
        )
        builder = MkDocsBuilder()
        navigation = "<ul><li><a href='index.html'>Home</a></li></ul>"
        html = builder.generate_page_html(page, navigation)
        
        assert '<!DOCTYPE html>' in html
        assert '<title>Test - My Documentation</title>' in html
        assert '<h1>Hello</h1>' in html
        print("✓ Markdown to HTML generation works")
    
    @staticmethod
    def test_build_navigation():
        """Test navigation building"""
        builder = MkDocsBuilder()
        pages = [
            MarkdownPage(title="Home", path="index.md", content="Home"),
            MarkdownPage(title="About", path="about.md", content="About"),
            MarkdownPage(title="Contact", path="contact.md", content="Contact")
        ]
        
        nav = builder.build_navigation(pages)
        assert 'index.html' in nav
        assert 'about.html' in nav
        assert 'contact.html' in nav
        print("✓ Navigation building works")
    
    @staticmethod
    def test_new_project():
        """Test creating new project"""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = MkDocsBuilder()
            project_name = "test_project"
            success = builder.new(project_name, tmpdir)
            
            assert success
            project_path = Path(tmpdir) / project_name
            assert project_path.exists()
            assert (project_path / 'mkdocs.yml').exists()
            assert (project_path / 'docs').exists()
            assert (project_path / 'docs' / 'index.md').exists()
            
            print("✓ New project creation works")
    
    @staticmethod
    def test_build_simple_site():
        """Test building a simple site"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create project structure
            docs_dir = Path(tmpdir) / 'docs'
            docs_dir.mkdir()
            
            # Create config
            config_path = Path(tmpdir) / 'mkdocs.yml'
            with open(config_path, 'w') as f:
                f.write("site_name: Test Site\n")
            
            # Create index page
            index_path = docs_dir / 'index.md'
            with open(index_path, 'w') as f:
                f.write("# Welcome\n\nThis is a test site.")
            
            # Create another page
            about_path = docs_dir / 'about.md'
            with open(about_path, 'w') as f:
                f.write("# About\n\nAbout this site.")
            
            # Build site
            builder = MkDocsBuilder()
            output_dir = str(Path(tmpdir) / 'site')
            success = builder.build(tmpdir, output_dir)
            
            assert success
            assert Path(output_dir).exists()
            assert (Path(output_dir) / 'index.html').exists()
            assert (Path(output_dir) / 'about.html').exists()
            
            # Check content
            with open(Path(output_dir) / 'index.html', 'r') as f:
                content = f.read()
                assert 'Welcome' in content
                assert 'Test Site' in content
            
            print("✓ Site building works")


def run_all_tests():
    """Run all tests"""
    print("Testing MkDocs Emulator\n")
    print("=" * 50)
    
    # YAML Parser tests
    print("\nTesting MinimalYAMLParser:")
    TestMinimalYAMLParser.test_simple_key_value()
    TestMinimalYAMLParser.test_list_parsing()
    TestMinimalYAMLParser.test_comments()
    
    # Markdown Converter tests
    print("\nTesting MarkdownConverter:")
    TestMarkdownConverter.test_headers()
    TestMarkdownConverter.test_bold_italic()
    TestMarkdownConverter.test_links()
    TestMarkdownConverter.test_code()
    TestMarkdownConverter.test_code_block()
    TestMarkdownConverter.test_lists()
    TestMarkdownConverter.test_ordered_lists()
    TestMarkdownConverter.test_images()
    
    # MarkdownPage tests
    print("\nTesting MarkdownPage:")
    TestMarkdownPage.test_page_creation()
    TestMarkdownPage.test_page_with_children()
    
    # MkDocs Builder tests
    print("\nTesting MkDocsBuilder:")
    TestMkDocsBuilder.test_default_config()
    TestMkDocsBuilder.test_markdown_to_html()
    TestMkDocsBuilder.test_build_navigation()
    TestMkDocsBuilder.test_new_project()
    TestMkDocsBuilder.test_build_simple_site()
    
    print("\n" + "=" * 50)
    print("All tests passed! ✓")


if __name__ == '__main__':
    run_all_tests()
