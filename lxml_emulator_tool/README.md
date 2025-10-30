# lxml Emulator - XML and HTML Processing

This module emulates the **lxml** library, providing XML and HTML processing capabilities using Python's built-in `xml.etree.ElementTree`.

## What is lxml?

lxml is a Pythonic binding for the C libraries libxml2 and libxslt. It's one of the most feature-rich and easy-to-use libraries for processing XML and HTML in Python. Common uses include:
- XML parsing and generation
- HTML scraping and manipulation
- XPath queries
- XSLT transformations
- Schema validation

## Features

This emulator implements core lxml functionality:

### Element Operations
- **Element creation** - Create XML elements with tags and attributes
- **Tree building** - Build XML trees programmatically
- **Element properties** - text, tail, tag, attrib
- **Hierarchy manipulation** - append, insert, remove children
- **Searching** - find, findall, findtext, iter
- **XPath queries** - simplified XPath support

### Parsing
- **fromstring()** - Parse XML from string
- **parse()** - Parse XML from file
- **XML()** - Parse XML with stricter validation
- **HTML()** - Parse HTML (simplified)

### Serialization
- **tostring()** - Serialize element to string
- **ElementTree.write()** - Write to file
- **Pretty printing** - Format with indentation

### Compatibility
- **lxml.etree** module interface
- Element and SubElement factories
- ElementTree wrapper class

## Usage Examples

### Creating Elements

```python
from lxml_emulator import Element, SubElement

# Create root element
root = Element('root')
root.text = 'This is the root element'

# Add attributes
root.set('id', '1')
root.set('type', 'container')

# Create subelements
child1 = SubElement(root, 'child1')
child1.text = 'First child'

child2 = SubElement(root, 'child2', attrib={'name': 'second'})
child2.text = 'Second child'

print(len(root))  # 2 children
print(root[0].tag)  # 'child1'
```

### Parsing XML

```python
from lxml_emulator import fromstring, XML

# Parse from string
xml_string = '''
<books>
    <book id="1">
        <title>Python Programming</title>
        <author>John Doe</author>
        <price>29.99</price>
    </book>
    <book id="2">
        <title>Web Development</title>
        <author>Jane Smith</author>
        <price>34.99</price>
    </book>
</books>
'''

root = fromstring(xml_string)
print(root.tag)  # 'books'
print(len(root))  # 2

# Alternative
root = XML(xml_string)
```

### Accessing Elements

```python
# Get element attributes
book = root[0]
print(book.get('id'))  # '1'

# Get element text
title = book.find('title')
print(title.text)  # 'Python Programming'

# Find specific element
author = book.findtext('author')  # 'John Doe'
```

### Searching and Iteration

```python
# Find first matching element
first_book = root.find('book')
print(first_book.get('id'))  # '1'

# Find all matching elements
all_books = root.findall('book')
print(len(all_books))  # 2

# Iterate over elements
for book in root.iter('book'):
    title = book.findtext('title')
    price = book.findtext('price')
    print(f"{title}: ${price}")
```

### XPath Queries

```python
from lxml_emulator import fromstring

xml = '''
<library>
    <section name="programming">
        <book>Python</book>
        <book>JavaScript</book>
    </section>
    <section name="science">
        <book>Physics</book>
        <book>Chemistry</book>
    </section>
</library>
'''

root = fromstring(xml)

# Find all books in tree
all_books = root.xpath('//book')
print(len(all_books))  # 4

# Find direct children
sections = root.xpath('./section')
print(len(sections))  # 2

# Current element
self_ref = root.xpath('.')
print(self_ref[0].tag)  # 'library'
```

### Modifying XML

```python
from lxml_emulator import Element, SubElement

root = Element('users')

# Add new user
user = SubElement(root, 'user', attrib={'id': '1'})
SubElement(user, 'name').text = 'Alice'
SubElement(user, 'email').text = 'alice@example.com'

# Modify element
user.set('active', 'true')

# Remove element
email = user.find('email')
user.remove(email)

# Clear element
user.clear()  # Removes all children and attributes
```

### Serialization

```python
from lxml_emulator import Element, SubElement, tostring

root = Element('config')
database = SubElement(root, 'database')
database.text = 'mydb'

# Serialize to string
xml_string = tostring(root)
print(xml_string)
# <config><database>mydb</database></config>

# Pretty print
pretty_xml = tostring(root, pretty_print=True)
print(pretty_xml)
# <config>
#   <database>mydb</database>
# </config>

# With XML declaration
with_decl = tostring(root, xml_declaration=True, encoding='utf-8')
print(with_decl)
# <?xml version="1.0" encoding="utf-8"?>
# <config><database>mydb</database></config>

# Encode as bytes
bytes_xml = tostring(root, encoding='utf-8')
print(type(bytes_xml))  # <class 'bytes'>
```

### File I/O

```python
from lxml_emulator import parse, ElementTree, Element, SubElement

# Parse from file
tree = parse('config.xml')
root = tree.getroot()

# Modify and save
new_elem = SubElement(root, 'setting')
new_elem.text = 'value'

tree.write('modified_config.xml', pretty_print=True)

# Create and save new document
root = Element('document')
root.text = 'Content'

tree = ElementTree(root)
tree.write('new_document.xml', xml_declaration=True)
```

### Using etree Module

```python
# Compatible with lxml.etree interface
from lxml_emulator import etree

root = etree.Element('root')
child = etree.SubElement(root, 'child')
xml = etree.tostring(root)

tree = etree.parse('file.xml')
root = tree.getroot()
```

### Building Complex Documents

```python
from lxml_emulator import Element, SubElement, tostring

# Build RSS feed
rss = Element('rss', attrib={'version': '2.0'})
channel = SubElement(rss, 'channel')

SubElement(channel, 'title').text = 'My Blog'
SubElement(channel, 'link').text = 'https://example.com'
SubElement(channel, 'description').text = 'A sample blog'

# Add items
for i in range(3):
    item = SubElement(channel, 'item')
    SubElement(item, 'title').text = f'Post {i+1}'
    SubElement(item, 'link').text = f'https://example.com/post-{i+1}'
    SubElement(item, 'description').text = f'Description for post {i+1}'

# Output
xml = tostring(rss, pretty_print=True, xml_declaration=True)
print(xml)
```

### HTML Parsing

```python
from lxml_emulator import HTML

html = '<html><body><h1>Hello</h1><p>World</p></body></html>'
root = HTML(html)

# Access elements
h1 = root.find('.//h1')
print(h1.text)  # 'Hello'

# Note: HTML parsing is simplified in this emulator
```

## API Reference

### Core Classes

- **Element** - Represents an XML element
- **SubElement** - Create and append a child element
- **ElementTree** - Represents an XML document tree

### Parsing Functions

- **fromstring(text)** - Parse XML from string
- **parse(source)** - Parse XML from file or file-like object
- **XML(text)** - Parse XML (strict)
- **HTML(text)** - Parse HTML (lenient)

### Serialization Functions

- **tostring(element, encoding='unicode', pretty_print=False)** - Serialize to string

### Element Methods

- **find(path)** - Find first matching child
- **findall(path)** - Find all matching children
- **findtext(path, default=None)** - Get text of first match
- **iter(tag=None)** - Iterate over tree
- **xpath(path)** - Simple XPath queries
- **get(key, default=None)** - Get attribute
- **set(key, value)** - Set attribute
- **append(child)** - Append child element
- **insert(index, child)** - Insert child at index
- **remove(child)** - Remove child element
- **clear()** - Remove all children and attributes

## Testing

Run the comprehensive test suite:

```bash
python test_lxml_emulator.py
```

Tests cover:
- Element creation and manipulation
- Attribute operations
- Tree hierarchy
- Element searching
- XML parsing
- Serialization
- File I/O
- XPath queries
- HTML parsing
- API compatibility

## Integration with Existing Code

This emulator is designed to be compatible with lxml:

```python
# Instead of:
# from lxml import etree
# root = etree.fromstring(xml)

# Use:
from lxml_emulator import etree
root = etree.fromstring(xml)

# Or:
from lxml_emulator import fromstring
root = fromstring(xml)
```

## Use Cases

Perfect for:
- **Configuration Files**: Parse and generate XML configs
- **Web Scraping**: Extract data from HTML/XML
- **Data Exchange**: Read and write XML data formats
- **Document Generation**: Create XML documents programmatically
- **Testing**: Test XML processing without external dependencies
- **RSS/Atom Feeds**: Parse and generate feeds

## Supported Features

- ✅ Element creation and manipulation
- ✅ Attribute access and modification
- ✅ Tree traversal and searching
- ✅ XML parsing from strings and files
- ✅ XML serialization
- ✅ Pretty printing
- ✅ Simplified XPath queries
- ✅ HTML parsing (basic)
- ✅ lxml.etree API compatibility

## Limitations

This emulator implements commonly used lxml features. Some advanced features not included:
- Full XPath 1.0/2.0 support
- XSLT transformations
- XML Schema validation
- DTD validation
- Namespaces (limited support)
- C-level performance optimizations
- HTML5 parsing

For most XML processing tasks, the implemented features provide comprehensive functionality.

## Compatibility

Emulates core features of:
- lxml 4.x/5.x API
- lxml.etree module interface
- ElementTree-compatible operations

## License

Part of the Emu-Soft project. See main repository LICENSE.
