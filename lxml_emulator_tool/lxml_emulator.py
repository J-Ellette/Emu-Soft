"""
lxml Emulator - XML and HTML Processing
Emulates the lxml library using Python's xml.etree.ElementTree
"""

import xml.etree.ElementTree as ET
from typing import Union, Optional, Dict, List, Any
from io import StringIO, BytesIO


class XMLSyntaxError(Exception):
    """Exception raised for XML syntax errors"""
    pass



class _Element:
    """
    XML Element wrapper that provides lxml-like interface
    """
    
    def __init__(self, tag: str, attrib: Dict[str, str] = None, nsmap: Dict[str, str] = None):
        """
        Create a new element
        
        Args:
            tag: Element tag name
            attrib: Dictionary of attributes
            nsmap: Namespace map (not fully implemented)
        """
        if attrib is None:
            attrib = {}
        self._element = ET.Element(tag, attrib)
        self.nsmap = nsmap or {}
    
    @property
    def tag(self) -> str:
        """Get element tag"""
        return self._element.tag
    
    @tag.setter
    def tag(self, value: str):
        """Set element tag"""
        self._element.tag = value
    
    @property
    def text(self) -> Optional[str]:
        """Get element text content"""
        return self._element.text
    
    @text.setter
    def text(self, value: Optional[str]):
        """Set element text content"""
        self._element.text = value
    
    @property
    def tail(self) -> Optional[str]:
        """Get tail text (text after element)"""
        return self._element.tail
    
    @tail.setter
    def tail(self, value: Optional[str]):
        """Set tail text"""
        self._element.tail = value
    
    @property
    def attrib(self) -> Dict[str, str]:
        """Get element attributes"""
        return self._element.attrib
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get attribute value"""
        return self._element.get(key, default)
    
    def set(self, key: str, value: str) -> None:
        """Set attribute value"""
        self._element.set(key, value)
    
    def keys(self) -> List[str]:
        """Get attribute keys"""
        return list(self._element.attrib.keys())
    
    def items(self) -> List[tuple]:
        """Get attribute items"""
        return list(self._element.attrib.items())
    
    def append(self, subelement: '_Element') -> None:
        """Append a subelement"""
        if isinstance(subelement, _Element):
            self._element.append(subelement._element)
        else:
            self._element.append(subelement)
    
    def insert(self, index: int, subelement: '_Element') -> None:
        """Insert a subelement at index"""
        if isinstance(subelement, _Element):
            self._element.insert(index, subelement._element)
        else:
            self._element.insert(index, subelement)
    
    def remove(self, subelement: '_Element') -> None:
        """Remove a subelement"""
        if isinstance(subelement, _Element):
            self._element.remove(subelement._element)
        else:
            self._element.remove(subelement)
    
    def clear(self) -> None:
        """Clear element content and attributes"""
        self._element.clear()
    
    def find(self, path: str) -> Optional['_Element']:
        """Find first matching subelement"""
        result = self._element.find(path)
        if result is not None:
            elem = _Element.__new__(_Element)
            elem._element = result
            return elem
        return None
    
    def findall(self, path: str) -> List['_Element']:
        """Find all matching subelements"""
        results = self._element.findall(path)
        return [self._wrap_element(e) for e in results]
    
    def findtext(self, path: str, default: str = None) -> Optional[str]:
        """Find text of first matching subelement"""
        return self._element.findtext(path, default)
    
    def iter(self, tag: str = None) -> 'ElementIterator':
        """Iterate over tree"""
        return ElementIterator(self, tag)
    
    def iterchildren(self, tag: str = None, reversed: bool = False):
        """Iterate over direct children"""
        children = list(self)
        if tag:
            children = [c for c in children if c.tag == tag]
        if reversed:
            children = children[::-1]
        return iter(children)
    
    def iterdescendants(self, tag: str = None):
        """Iterate over all descendants"""
        for elem in self.iter():
            if elem is not self:
                if tag is None or elem.tag == tag:
                    yield elem
    
    def xpath(self, path: str) -> List['_Element']:
        """Simple XPath-like query (limited implementation)"""
        # Very simplified XPath support
        if path == '.':
            return [self]
        elif path == '..':
            return []  # Parent not easily accessible
        elif path.startswith('//'):
            # Descendant search
            tag = path[2:]
            return list(self.iter(tag))
        elif path.startswith('./'):
            # Direct children
            tag = path[2:]
            return [c for c in self if c.tag == tag]
        else:
            # Direct children with tag
            return [c for c in self if c.tag == path]
    
    def getparent(self) -> Optional['_Element']:
        """Get parent element (not available in ElementTree)"""
        return None
    
    def getchildren(self) -> List['_Element']:
        """Get all children (deprecated but included for compatibility)"""
        return list(self)
    
    def __len__(self) -> int:
        """Number of subelements"""
        return len(self._element)
    
    def __getitem__(self, index: int) -> '_Element':
        """Get subelement by index"""
        child = self._element[index]
        return self._wrap_element(child)
    
    def __setitem__(self, index: int, value: '_Element'):
        """Set subelement by index"""
        if isinstance(value, _Element):
            self._element[index] = value._element
        else:
            self._element[index] = value
    
    def __delitem__(self, index: int):
        """Delete subelement by index"""
        del self._element[index]
    
    def __iter__(self):
        """Iterate over subelements"""
        for child in self._element:
            yield self._wrap_element(child)
    
    def __repr__(self) -> str:
        return f"<Element {self.tag} at {hex(id(self))}>"
    
    @staticmethod
    def _wrap_element(et_elem):
        """Wrap an ElementTree element"""
        elem = _Element.__new__(_Element)
        elem._element = et_elem
        return elem


class ElementIterator:
    """Iterator over elements in tree"""
    
    def __init__(self, element: _Element, tag: str = None):
        self.tag = tag
        self._iter = element._element.iter(tag)
    
    def __iter__(self):
        return self
    
    def __next__(self):
        et_elem = next(self._iter)
        return _Element._wrap_element(et_elem)


class ElementTree:
    """
    ElementTree wrapper that provides lxml-like interface
    """
    
    def __init__(self, element: _Element = None):
        """Create ElementTree from root element"""
        if element is None:
            self._tree = ET.ElementTree()
        else:
            if isinstance(element, _Element):
                self._tree = ET.ElementTree(element._element)
            else:
                self._tree = ET.ElementTree(element)
    
    def getroot(self) -> _Element:
        """Get root element"""
        root = self._tree.getroot()
        if root is not None:
            return _Element._wrap_element(root)
        return None
    
    def write(self, file, encoding: str = 'utf-8', xml_declaration: bool = False,
              pretty_print: bool = False, method: str = 'xml') -> None:
        """Write tree to file"""
        if pretty_print:
            self._indent(self.getroot()._element)
        
        if hasattr(file, 'write'):
            # File-like object
            self._tree.write(file, encoding=encoding, xml_declaration=xml_declaration,
                           method=method)
        else:
            # Filename
            with open(file, 'wb') as f:
                self._tree.write(f, encoding=encoding, xml_declaration=xml_declaration,
                               method=method)
    
    def _indent(self, elem, level=0):
        """Add pretty-print indentation"""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    def find(self, path: str) -> Optional[_Element]:
        """Find first matching element"""
        result = self._tree.find(path)
        if result is not None:
            return _Element._wrap_element(result)
        return None
    
    def findall(self, path: str) -> List[_Element]:
        """Find all matching elements"""
        results = self._tree.findall(path)
        return [_Element._wrap_element(e) for e in results]
    
    def iter(self, tag: str = None):
        """Iterate over tree"""
        for elem in self._tree.iter(tag):
            yield _Element._wrap_element(elem)
    
    def xpath(self, path: str) -> List[_Element]:
        """Simple XPath-like query"""
        root = self.getroot()
        if root:
            return root.xpath(path)
        return []


# Public API functions
def Element(tag: str, attrib: Dict[str, str] = None, nsmap: Dict[str, str] = None) -> _Element:
    """Create a new element"""
    return _Element(tag, attrib, nsmap)


def SubElement(parent: _Element, tag: str, attrib: Dict[str, str] = None) -> _Element:
    """Create a subelement"""
    if attrib is None:
        attrib = {}
    elem = _Element(tag, attrib)
    parent.append(elem)
    return elem


def parse(source: Union[str, Any], parser=None) -> ElementTree:
    """
    Parse XML from file or file-like object
    
    Args:
        source: Filename or file-like object
        parser: Parser instance (not used in this implementation)
        
    Returns:
        ElementTree object
    """
    try:
        if isinstance(source, str):
            # Filename
            tree = ET.parse(source)
        else:
            # File-like object
            tree = ET.parse(source)
        
        # Wrap in our ElementTree
        et = ElementTree.__new__(ElementTree)
        et._tree = tree
        return et
    except ET.ParseError as e:
        raise XMLSyntaxError(str(e))


def fromstring(text: Union[str, bytes], parser=None) -> _Element:
    """
    Parse XML from string
    
    Args:
        text: XML string or bytes
        parser: Parser instance (not used)
        
    Returns:
        Element object (root element)
    """
    try:
        if isinstance(text, bytes):
            text = text.decode('utf-8')
        et_elem = ET.fromstring(text)
        return _Element._wrap_element(et_elem)
    except ET.ParseError as e:
        raise XMLSyntaxError(str(e))


def tostring(element: _Element, encoding: str = 'unicode', method: str = 'xml',
             xml_declaration: bool = False, pretty_print: bool = False) -> Union[str, bytes]:
    """
    Serialize element to string
    
    Args:
        element: Element to serialize
        encoding: Output encoding
        method: Serialization method ('xml', 'html', 'text')
        xml_declaration: Include XML declaration
        pretty_print: Format with indentation
        
    Returns:
        Serialized XML as string or bytes
    """
    if isinstance(element, _Element):
        et_elem = element._element
    else:
        et_elem = element
    
    if pretty_print:
        # Create a copy to avoid modifying original
        import copy
        et_elem = copy.deepcopy(et_elem)
        ElementTree()._indent(et_elem)
    
    if encoding == 'unicode':
        result = ET.tostring(et_elem, encoding='unicode', method=method)
    else:
        result = ET.tostring(et_elem, encoding=encoding, method=method)
    
    if xml_declaration and isinstance(result, str):
        result = f'<?xml version="1.0" encoding="{encoding}"?>\n' + result
    elif xml_declaration and isinstance(result, bytes):
        declaration = f'<?xml version="1.0" encoding="{encoding}"?>\n'.encode(encoding)
        result = declaration + result
    
    return result


def HTML(text: Union[str, bytes]) -> _Element:
    """
    Parse HTML from string (simplified - uses XML parser)
    
    Args:
        text: HTML string or bytes
        
    Returns:
        Element object (root element)
    """
    # Simplified HTML parsing - just wraps in <html> if needed
    if isinstance(text, bytes):
        text = text.decode('utf-8')
    
    # Try to parse as-is
    try:
        return fromstring(text)
    except XMLSyntaxError:
        # Wrap in html tags and try again
        try:
            return fromstring(f"<html>{text}</html>")
        except XMLSyntaxError:
            # Return a simple element with the text
            elem = _Element('html')
            elem.text = text
            return elem


def XML(text: Union[str, bytes]) -> _Element:
    """
    Parse XML from string (alias for fromstring)
    
    Args:
        text: XML string or bytes
        
    Returns:
        Element object (root element)
    """
    return fromstring(text)


# Compatibility imports
class etree:
    """Compatibility module for lxml.etree"""
    Element = Element
    SubElement = SubElement
    ElementTree = ElementTree
    parse = parse
    fromstring = fromstring
    tostring = tostring
    XML = XML
    HTML = HTML
    XMLSyntaxError = XMLSyntaxError
