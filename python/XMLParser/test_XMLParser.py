"""
Tests for lxml emulator
"""

import unittest
from io import StringIO, BytesIO
from XMLParser import (
    Element,
    SubElement,
    ElementTree,
    parse,
    fromstring,
    tostring,
    XML,
    HTML,
    XMLSyntaxError,
    etree
)


class TestElementCreation(unittest.TestCase):
    """Test element creation and basic properties"""
    
    def test_create_element(self):
        elem = Element('root')
        self.assertEqual(elem.tag, 'root')
        self.assertIsNone(elem.text)
    
    def test_element_with_attributes(self):
        elem = Element('root', attrib={'id': '1', 'name': 'test'})
        self.assertEqual(elem.get('id'), '1')
        self.assertEqual(elem.get('name'), 'test')
    
    def test_element_text(self):
        elem = Element('root')
        elem.text = 'Hello, World!'
        self.assertEqual(elem.text, 'Hello, World!')
    
    def test_element_tail(self):
        elem = Element('root')
        elem.tail = 'tail text'
        self.assertEqual(elem.tail, 'tail text')
    
    def test_subelement(self):
        root = Element('root')
        child = SubElement(root, 'child')
        self.assertEqual(len(root), 1)
        self.assertEqual(child.tag, 'child')


class TestElementAttributes(unittest.TestCase):
    """Test element attribute operations"""
    
    def test_get_attribute(self):
        elem = Element('root', {'id': '1'})
        self.assertEqual(elem.get('id'), '1')
        self.assertIsNone(elem.get('missing'))
        self.assertEqual(elem.get('missing', 'default'), 'default')
    
    def test_set_attribute(self):
        elem = Element('root')
        elem.set('id', '1')
        self.assertEqual(elem.get('id'), '1')
    
    def test_attribute_keys(self):
        elem = Element('root', {'id': '1', 'name': 'test'})
        keys = elem.keys()
        self.assertIn('id', keys)
        self.assertIn('name', keys)
    
    def test_attribute_items(self):
        elem = Element('root', {'id': '1', 'name': 'test'})
        items = dict(elem.items())
        self.assertEqual(items['id'], '1')
        self.assertEqual(items['name'], 'test')
    
    def test_attrib_dict(self):
        elem = Element('root')
        elem.attrib['id'] = '1'
        elem.attrib['name'] = 'test'
        self.assertEqual(elem.get('id'), '1')
        self.assertEqual(elem.get('name'), 'test')


class TestElementHierarchy(unittest.TestCase):
    """Test element parent-child relationships"""
    
    def test_append_child(self):
        root = Element('root')
        child = Element('child')
        root.append(child)
        self.assertEqual(len(root), 1)
        self.assertEqual(root[0].tag, 'child')
    
    def test_insert_child(self):
        root = Element('root')
        child1 = Element('child1')
        child2 = Element('child2')
        root.append(child1)
        root.insert(0, child2)
        self.assertEqual(root[0].tag, 'child2')
        self.assertEqual(root[1].tag, 'child1')
    
    def test_remove_child(self):
        root = Element('root')
        child = Element('child')
        root.append(child)
        self.assertEqual(len(root), 1)
        root.remove(child)
        self.assertEqual(len(root), 0)
    
    def test_clear(self):
        root = Element('root', {'id': '1'})
        root.text = 'text'
        child = Element('child')
        root.append(child)
        
        root.clear()
        self.assertEqual(len(root), 0)
        self.assertIsNone(root.text)
        self.assertEqual(len(root.attrib), 0)
    
    def test_iteration(self):
        root = Element('root')
        for i in range(3):
            SubElement(root, f'child{i}')
        
        tags = [child.tag for child in root]
        self.assertEqual(tags, ['child0', 'child1', 'child2'])
    
    def test_indexing(self):
        root = Element('root')
        child1 = SubElement(root, 'child1')
        child2 = SubElement(root, 'child2')
        
        self.assertEqual(root[0].tag, 'child1')
        self.assertEqual(root[1].tag, 'child2')
    
    def test_length(self):
        root = Element('root')
        self.assertEqual(len(root), 0)
        SubElement(root, 'child1')
        self.assertEqual(len(root), 1)
        SubElement(root, 'child2')
        self.assertEqual(len(root), 2)


class TestElementSearch(unittest.TestCase):
    """Test element search operations"""
    
    def test_find(self):
        root = Element('root')
        child = SubElement(root, 'child')
        child.text = 'text'
        
        found = root.find('child')
        self.assertIsNotNone(found)
        self.assertEqual(found.tag, 'child')
    
    def test_find_not_found(self):
        root = Element('root')
        found = root.find('missing')
        self.assertIsNone(found)
    
    def test_findall(self):
        root = Element('root')
        SubElement(root, 'child')
        SubElement(root, 'child')
        SubElement(root, 'other')
        
        children = root.findall('child')
        self.assertEqual(len(children), 2)
    
    def test_findtext(self):
        root = Element('root')
        child = SubElement(root, 'child')
        child.text = 'Hello'
        
        text = root.findtext('child')
        self.assertEqual(text, 'Hello')
    
    def test_iter(self):
        root = Element('root')
        SubElement(root, 'child1')
        SubElement(root, 'child2')
        
        tags = [elem.tag for elem in root.iter()]
        self.assertIn('root', tags)
        self.assertIn('child1', tags)
        self.assertIn('child2', tags)
    
    def test_iter_with_tag(self):
        root = Element('root')
        SubElement(root, 'child')
        SubElement(root, 'child')
        SubElement(root, 'other')
        
        children = list(root.iter('child'))
        self.assertEqual(len(children), 2)


class TestParsing(unittest.TestCase):
    """Test XML parsing from strings"""
    
    def test_fromstring_simple(self):
        xml = '<root>text</root>'
        elem = fromstring(xml)
        self.assertEqual(elem.tag, 'root')
        self.assertEqual(elem.text, 'text')
    
    def test_fromstring_with_attributes(self):
        xml = '<root id="1" name="test">text</root>'
        elem = fromstring(xml)
        self.assertEqual(elem.get('id'), '1')
        self.assertEqual(elem.get('name'), 'test')
    
    def test_fromstring_nested(self):
        xml = '<root><child1>text1</child1><child2>text2</child2></root>'
        elem = fromstring(xml)
        self.assertEqual(len(elem), 2)
        self.assertEqual(elem[0].tag, 'child1')
        self.assertEqual(elem[1].tag, 'child2')
    
    def test_fromstring_bytes(self):
        xml = b'<root>text</root>'
        elem = fromstring(xml)
        self.assertEqual(elem.tag, 'root')
    
    def test_fromstring_invalid(self):
        xml = '<root><unclosed>'
        with self.assertRaises(XMLSyntaxError):
            fromstring(xml)
    
    def test_XML(self):
        xml = '<root>text</root>'
        elem = XML(xml)
        self.assertEqual(elem.tag, 'root')
        self.assertEqual(elem.text, 'text')


class TestSerialization(unittest.TestCase):
    """Test XML serialization to strings"""
    
    def test_tostring_simple(self):
        elem = Element('root')
        elem.text = 'text'
        xml = tostring(elem)
        self.assertIn('root', xml)
        self.assertIn('text', xml)
    
    def test_tostring_with_attributes(self):
        elem = Element('root', {'id': '1'})
        xml = tostring(elem)
        self.assertIn('root', xml)
        self.assertIn('id', xml)
    
    def test_tostring_nested(self):
        root = Element('root')
        child = SubElement(root, 'child')
        child.text = 'text'
        xml = tostring(root)
        self.assertIn('root', xml)
        self.assertIn('child', xml)
    
    def test_tostring_encoding(self):
        elem = Element('root')
        elem.text = 'text'
        xml = tostring(elem, encoding='utf-8')
        self.assertIsInstance(xml, bytes)
    
    def test_tostring_pretty_print(self):
        root = Element('root')
        child = SubElement(root, 'child')
        xml = tostring(root, pretty_print=True)
        # Should have some formatting
        self.assertIn('\n', xml)


class TestElementTree(unittest.TestCase):
    """Test ElementTree operations"""
    
    def test_create_tree(self):
        root = Element('root')
        tree = ElementTree(root)
        self.assertEqual(tree.getroot().tag, 'root')
    
    def test_tree_find(self):
        root = Element('root')
        child = SubElement(root, 'child')
        tree = ElementTree(root)
        
        found = tree.find('child')
        self.assertIsNotNone(found)
        self.assertEqual(found.tag, 'child')
    
    def test_tree_findall(self):
        root = Element('root')
        SubElement(root, 'child')
        SubElement(root, 'child')
        tree = ElementTree(root)
        
        children = tree.findall('child')
        self.assertEqual(len(children), 2)
    
    def test_tree_iter(self):
        root = Element('root')
        SubElement(root, 'child')
        tree = ElementTree(root)
        
        tags = [elem.tag for elem in tree.iter()]
        self.assertIn('root', tags)
        self.assertIn('child', tags)


class TestFileIO(unittest.TestCase):
    """Test file I/O operations"""
    
    def test_parse_stringio(self):
        xml = '<root><child>text</child></root>'
        stream = StringIO(xml)
        tree = parse(stream)
        root = tree.getroot()
        self.assertEqual(root.tag, 'root')
        self.assertEqual(len(root), 1)
    
    def test_write_stringio(self):
        root = Element('root')
        child = SubElement(root, 'child')
        child.text = 'text'
        tree = ElementTree(root)
        
        stream = BytesIO()
        tree.write(stream)
        result = stream.getvalue()
        self.assertIn(b'root', result)
        self.assertIn(b'child', result)


class TestXPath(unittest.TestCase):
    """Test XPath-like queries"""
    
    def test_xpath_self(self):
        elem = Element('root')
        results = elem.xpath('.')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].tag, 'root')
    
    def test_xpath_descendants(self):
        root = Element('root')
        SubElement(root, 'child')
        child2 = SubElement(root, 'wrapper')
        SubElement(child2, 'child')
        
        results = root.xpath('//child')
        self.assertEqual(len(results), 2)
    
    def test_xpath_direct_children(self):
        root = Element('root')
        SubElement(root, 'child')
        SubElement(root, 'child')
        SubElement(root, 'other')
        
        results = root.xpath('./child')
        self.assertEqual(len(results), 2)


class TestHTML(unittest.TestCase):
    """Test HTML parsing"""
    
    def test_html_simple(self):
        html = '<html><body>text</body></html>'
        elem = HTML(html)
        self.assertEqual(elem.tag, 'html')
    
    def test_html_fragment(self):
        # Should handle HTML fragments gracefully
        html = '<div>text</div>'
        elem = HTML(html)
        self.assertIsNotNone(elem)


class TestCompatibility(unittest.TestCase):
    """Test compatibility with lxml.etree API"""
    
    def test_etree_module(self):
        self.assertIsNotNone(etree.Element)
        self.assertIsNotNone(etree.SubElement)
        self.assertIsNotNone(etree.ElementTree)
        self.assertIsNotNone(etree.parse)
        self.assertIsNotNone(etree.fromstring)
        self.assertIsNotNone(etree.tostring)
    
    def test_etree_usage(self):
        elem = etree.Element('root')
        child = etree.SubElement(elem, 'child')
        xml = etree.tostring(elem)
        self.assertIn('root', xml)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestElementCreation))
    suite.addTests(loader.loadTestsFromTestCase(TestElementAttributes))
    suite.addTests(loader.loadTestsFromTestCase(TestElementHierarchy))
    suite.addTests(loader.loadTestsFromTestCase(TestElementSearch))
    suite.addTests(loader.loadTestsFromTestCase(TestParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestSerialization))
    suite.addTests(loader.loadTestsFromTestCase(TestElementTree))
    suite.addTests(loader.loadTestsFromTestCase(TestFileIO))
    suite.addTests(loader.loadTestsFromTestCase(TestXPath))
    suite.addTests(loader.loadTestsFromTestCase(TestHTML))
    suite.addTests(loader.loadTestsFromTestCase(TestCompatibility))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
