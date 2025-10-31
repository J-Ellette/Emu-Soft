"""
Developed by PowerShield, as an alternative to PyYAML


PyYAML Emulator - YAML Parser and Emitter
Emulates the PyYAML library for parsing and generating YAML data
"""

import re
from typing import Any, Dict, List, Union, IO, Optional
from io import StringIO


class YAMLError(Exception):
    """Base exception for YAML errors"""
    pass


class ParserError(YAMLError):
    """Exception for parsing errors"""
    pass


class EmitterError(YAMLError):
    """Exception for emission errors"""
    pass


class YAMLParser:
    """
    YAML parser implementation
    Supports basic YAML syntax including:
    - Mappings (key: value)
    - Sequences (- item)
    - Scalars (strings, numbers, booleans, null)
    - Nested structures
    - Multi-line strings
    - Comments
    """
    
    def __init__(self, text: str):
        self.lines = text.split('\n')
        self.line_idx = 0
        self.indent_stack = [0]
    
    def parse(self) -> Any:
        """Parse YAML text into Python objects"""
        result = self._parse_value(0)
        return result
    
    def _current_line(self) -> Optional[str]:
        """Get current line"""
        if self.line_idx < len(self.lines):
            return self.lines[self.line_idx]
        return None
    
    def _skip_empty_and_comments(self) -> None:
        """Skip empty lines and comments"""
        while self.line_idx < len(self.lines):
            line = self.lines[self.line_idx].strip()
            if line and not line.startswith('#'):
                break
            self.line_idx += 1
    
    def _get_indent(self, line: str) -> int:
        """Get indentation level of a line"""
        return len(line) - len(line.lstrip())
    
    def _parse_value(self, min_indent: int) -> Any:
        """Parse a value at the current position"""
        self._skip_empty_and_comments()
        
        if self.line_idx >= len(self.lines):
            return None
        
        line = self._current_line()
        indent = self._get_indent(line)
        
        if indent < min_indent:
            return None
        
        stripped = line.strip()
        
        # Check if it's a list item
        if stripped.startswith('- '):
            return self._parse_list(indent)
        
        # Check if it's a mapping
        if ':' in stripped and not stripped.startswith('"') and not stripped.startswith("'"):
            # Find the colon not in quotes
            colon_pos = self._find_colon(stripped)
            if colon_pos != -1:
                return self._parse_mapping(indent)
        
        # It's a scalar value
        return self._parse_scalar(stripped)
    
    def _find_colon(self, text: str) -> int:
        """Find colon position outside of quotes"""
        in_single = False
        in_double = False
        
        for i, char in enumerate(text):
            if char == "'" and not in_double:
                in_single = not in_single
            elif char == '"' and not in_single:
                in_double = not in_double
            elif char == ':' and not in_single and not in_double:
                return i
        
        return -1
    
    def _parse_mapping(self, base_indent: int) -> Dict:
        """Parse a mapping/dictionary"""
        result = {}
        
        while self.line_idx < len(self.lines):
            self._skip_empty_and_comments()
            
            if self.line_idx >= len(self.lines):
                break
            
            line = self._current_line()
            indent = self._get_indent(line)
            
            if indent < base_indent:
                break
            
            if indent > base_indent:
                # This shouldn't happen at the start of a mapping
                break
            
            stripped = line.strip()
            
            # Check for list item (end of mapping)
            if stripped.startswith('- '):
                break
            
            # Find the colon
            colon_pos = self._find_colon(stripped)
            if colon_pos == -1:
                break
            
            key = stripped[:colon_pos].strip()
            value_part = stripped[colon_pos + 1:].strip()
            
            # Remove quotes from key if present
            key = self._unquote(key)
            
            self.line_idx += 1
            
            if value_part:
                # Inline value
                if value_part.startswith('['):
                    # Inline list
                    result[key] = self._parse_inline_list(value_part)
                elif value_part.startswith('{'):
                    # Inline mapping
                    result[key] = self._parse_inline_mapping(value_part)
                else:
                    result[key] = self._parse_scalar(value_part)
            else:
                # Value on next line(s)
                value = self._parse_value(base_indent + 1)
                result[key] = value
        
        return result
    
    def _parse_list(self, base_indent: int) -> List:
        """Parse a list/sequence"""
        result = []
        
        while self.line_idx < len(self.lines):
            self._skip_empty_and_comments()
            
            if self.line_idx >= len(self.lines):
                break
            
            line = self._current_line()
            indent = self._get_indent(line)
            
            if indent < base_indent:
                break
            
            if indent > base_indent:
                # Continuation of previous item - shouldn't happen at start
                break
            
            stripped = line.strip()
            
            if not stripped.startswith('- '):
                break
            
            # Get the value after the dash
            value_part = stripped[2:].strip()
            
            self.line_idx += 1
            
            if value_part:
                # Inline value - check if it's a mapping key-value pair
                colon_pos = self._find_colon(value_part)
                if colon_pos != -1 and not (value_part.startswith('"') or value_part.startswith("'")):
                    # This is "- key: value" - need to parse as a single-item mapping then continue
                    # Collect all key-value pairs at this indent level that belong to this list item
                    item_dict = {}
                    
                    # Parse first key-value pair
                    key = value_part[:colon_pos].strip()
                    val_part = value_part[colon_pos + 1:].strip()
                    key = self._unquote(key)
                    
                    if val_part:
                        item_dict[key] = self._parse_scalar(val_part)
                    else:
                        item_dict[key] = None
                    
                    # Check for more keys at higher indent
                    while self.line_idx < len(self.lines):
                        self._skip_empty_and_comments()
                        if self.line_idx >= len(self.lines):
                            break
                        
                        next_line = self._current_line()
                        next_indent = self._get_indent(next_line)
                        next_stripped = next_line.strip()
                        
                        # If it's another list item, we're done with this item
                        if next_stripped.startswith('- '):
                            break
                        
                        # If indent is same or less than list indent, we're done
                        if next_indent <= base_indent:
                            break
                        
                        # Check if this is a continuation key-value pair
                        if ':' in next_stripped:
                            colon_pos2 = self._find_colon(next_stripped)
                            if colon_pos2 != -1:
                                key2 = next_stripped[:colon_pos2].strip()
                                val_part2 = next_stripped[colon_pos2 + 1:].strip()
                                key2 = self._unquote(key2)
                                
                                if val_part2:
                                    item_dict[key2] = self._parse_scalar(val_part2)
                                else:
                                    item_dict[key2] = None
                                
                                self.line_idx += 1
                            else:
                                break
                        else:
                            break
                    
                    result.append(item_dict)
                elif value_part.startswith('['):
                    result.append(self._parse_inline_list(value_part))
                elif value_part.startswith('{'):
                    result.append(self._parse_inline_mapping(value_part))
                else:
                    result.append(self._parse_scalar(value_part))
            else:
                # Value on next line(s) - check if it's a mapping
                # Peek at next non-empty line
                self._skip_empty_and_comments()
                if self.line_idx < len(self.lines):
                    next_line = self._current_line()
                    next_indent = self._get_indent(next_line)
                    next_stripped = next_line.strip()
                    
                    # Check if this is a mapping continuation
                    if ':' in next_stripped and not next_stripped.startswith('- '):
                        value = self._parse_mapping(next_indent)
                    else:
                        value = self._parse_value(base_indent + 2)
                    
                    result.append(value)
        
        return result
    
    def _parse_scalar(self, value: str) -> Any:
        """Parse a scalar value (string, number, boolean, null)"""
        value = value.strip()
        
        # Check if it's an inline empty structure
        if value == '{}':
            return {}
        if value == '[]':
            return []
        
        # Check if it's an inline structure (will be parsed elsewhere)
        if value.startswith('{') and value.endswith('}'):
            return self._parse_inline_mapping(value)
        if value.startswith('[') and value.endswith(']'):
            return self._parse_inline_list(value)
        
        # Remove inline comments
        if '#' in value:
            # Check if # is not in quotes
            in_quotes = False
            quote_char = None
            for i, char in enumerate(value):
                if char in ('"', "'") and (i == 0 or value[i-1] != '\\'):
                    if not in_quotes:
                        in_quotes = True
                        quote_char = char
                    elif char == quote_char:
                        in_quotes = False
                elif char == '#' and not in_quotes:
                    value = value[:i].strip()
                    break
        
        # Null values
        if value in ('null', 'Null', 'NULL', '~', ''):
            return None
        
        # Boolean values
        if value in ('true', 'True', 'TRUE'):
            return True
        if value in ('false', 'False', 'FALSE'):
            return False
        
        # Quoted strings
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return self._unquote(value)
        
        # Try to parse as number
        try:
            if '.' in value or 'e' in value.lower():
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _unquote(self, value: str) -> str:
        """Remove quotes from a quoted string"""
        if len(value) >= 2:
            if (value[0] == '"' and value[-1] == '"') or \
               (value[0] == "'" and value[-1] == "'"):
                value = value[1:-1]
                # Unescape
                value = value.replace('\\n', '\n')
                value = value.replace('\\t', '\t')
                value = value.replace('\\"', '"')
                value = value.replace("\\'", "'")
                value = value.replace('\\\\', '\\')
        return value
    
    def _parse_inline_list(self, text: str) -> List:
        """Parse inline list [item1, item2, ...]"""
        if not text.startswith('[') or not text.endswith(']'):
            raise ParserError(f"Invalid inline list: {text}")
        
        content = text[1:-1].strip()
        if not content:
            return []
        
        items = []
        current = []
        depth = 0
        in_quotes = False
        quote_char = None
        
        for char in content:
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
                current.append(char)
            elif char == quote_char and in_quotes:
                in_quotes = False
                current.append(char)
            elif char in ('[', '{') and not in_quotes:
                depth += 1
                current.append(char)
            elif char in (']', '}') and not in_quotes:
                depth -= 1
                current.append(char)
            elif char == ',' and depth == 0 and not in_quotes:
                items.append(self._parse_scalar(''.join(current).strip()))
                current = []
            else:
                current.append(char)
        
        if current:
            items.append(self._parse_scalar(''.join(current).strip()))
        
        return items
    
    def _parse_inline_mapping(self, text: str) -> Dict:
        """Parse inline mapping {key1: value1, key2: value2, ...}"""
        if not text.startswith('{') or not text.endswith('}'):
            raise ParserError(f"Invalid inline mapping: {text}")
        
        content = text[1:-1].strip()
        if not content:
            return {}
        
        result = {}
        current = []
        depth = 0
        in_quotes = False
        quote_char = None
        
        for char in content:
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
                current.append(char)
            elif char == quote_char and in_quotes:
                in_quotes = False
                current.append(char)
            elif char in ('[', '{') and not in_quotes:
                depth += 1
                current.append(char)
            elif char in (']', '}') and not in_quotes:
                depth -= 1
                current.append(char)
            elif char == ',' and depth == 0 and not in_quotes:
                key, value = self._parse_inline_pair(''.join(current))
                result[key] = value
                current = []
            else:
                current.append(char)
        
        if current:
            key, value = self._parse_inline_pair(''.join(current))
            result[key] = value
        
        return result
    
    def _parse_inline_pair(self, text: str) -> tuple:
        """Parse a key: value pair"""
        colon_pos = self._find_colon(text)
        if colon_pos == -1:
            raise ParserError(f"Invalid key-value pair: {text}")
        
        key = text[:colon_pos].strip()
        value = text[colon_pos + 1:].strip()
        
        key = self._unquote(key)
        
        # Handle inline lists and mappings in values
        if value.startswith('[') and value.endswith(']'):
            value = self._parse_inline_list(value)
        elif value.startswith('{') and value.endswith('}'):
            value = self._parse_inline_mapping(value)
        else:
            value = self._parse_scalar(value)
        
        return key, value


class YAMLEmitter:
    """
    YAML emitter implementation
    Converts Python objects to YAML format
    """
    
    def __init__(self, data: Any, indent: int = 2):
        self.data = data
        self.indent_size = indent
    
    def emit(self) -> str:
        """Emit YAML from Python objects"""
        return self._emit_value(self.data, 0)
    
    def _emit_value(self, value: Any, indent: int) -> str:
        """Emit a value with proper indentation"""
        if value is None:
            return 'null'
        elif isinstance(value, bool):
            return 'true' if value else 'false'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            return self._emit_string(value)
        elif isinstance(value, dict):
            return self._emit_mapping(value, indent)
        elif isinstance(value, list):
            return self._emit_list(value, indent)
        else:
            return str(value)
    
    def _emit_string(self, value: str) -> str:
        """Emit a string, quoting if necessary"""
        # Check if string needs quoting
        needs_quotes = (
            not value or
            value[0] in (' ', '\t') or
            value[-1] in (' ', '\t') or
            ':' in value or
            '#' in value or
            value in ('true', 'false', 'null', 'yes', 'no', 'True', 'False') or
            '\n' in value or
            value.startswith(('-', '&', '*', '!', '|', '>', '%', '@', '`'))
        )
        
        if needs_quotes:
            # Escape special characters
            value = value.replace('\\', '\\\\')
            value = value.replace('"', '\\"')
            value = value.replace('\n', '\\n')
            value = value.replace('\t', '\\t')
            return f'"{value}"'
        
        return value
    
    def _emit_mapping(self, mapping: Dict, indent: int) -> str:
        """Emit a mapping/dictionary"""
        if not mapping:
            return '{}'
        
        lines = []
        
        for i, (key, value) in enumerate(mapping.items()):
            key_str = str(key)
            is_first = (i == 0)
            
            # Check if value can be on same line
            if isinstance(value, (str, int, float, bool, type(None))):
                value_str = self._emit_value(value, indent)
                if is_first:
                    lines.append(f"{key_str}: {value_str}")
                else:
                    lines.append(f"{' ' * indent}{key_str}: {value_str}")
            else:
                # Value needs to be on next line
                if is_first:
                    lines.append(f"{key_str}:")
                else:
                    lines.append(f"{' ' * indent}{key_str}:")
                
                # Emit value with increased indent (value returns lines without prefix indent)
                value_str = self._emit_value(value, 0)  # Get value without indent prefix
                for line in value_str.split('\n'):
                    lines.append(f"{' ' * (indent + self.indent_size)}{line}")
        
        return '\n'.join(lines)
    
    def _emit_list(self, items: List, indent: int) -> str:
        """Emit a list/sequence"""
        if not items:
            return '[]'
        
        lines = []
        
        for item in items:
            if isinstance(item, (str, int, float, bool, type(None))):
                value_str = self._emit_value(item, indent)
                lines.append(f"- {value_str}")
            elif isinstance(item, dict):
                # Emit dict items inline with dash
                first_key = True
                for key, value in item.items():
                    key_str = str(key)
                    value_str = self._emit_value(value, 0)
                    
                    if first_key:
                        lines.append(f"- {key_str}: {value_str}")
                        first_key = False
                    else:
                        lines.append(f"  {key_str}: {value_str}")
            else:
                # Complex item
                value_str = self._emit_value(item, 0)
                lines.append("-")
                for line in value_str.split('\n'):
                    lines.append(f"  {line}")
        
        # Add indentation to all lines except first
        result_lines = []
        for i, line in enumerate(lines):
            if i == 0:
                result_lines.append(line)
            else:
                result_lines.append(f"{' ' * indent}{line}")
        
        return '\n'.join(result_lines)


def load(stream: Union[str, IO]) -> Any:
    """
    Load YAML from a string or file-like object
    
    Args:
        stream: YAML string or file-like object
        
    Returns:
        Parsed Python object
    """
    if isinstance(stream, str):
        text = stream
    else:
        text = stream.read()
    
    parser = YAMLParser(text)
    return parser.parse()


def safe_load(stream: Union[str, IO]) -> Any:
    """
    Safely load YAML from a string or file-like object
    Alias for load() in this implementation
    
    Args:
        stream: YAML string or file-like object
        
    Returns:
        Parsed Python object
    """
    return load(stream)


def dump(data: Any, stream: Optional[IO] = None, indent: int = 2) -> Optional[str]:
    """
    Serialize Python object to YAML
    
    Args:
        data: Python object to serialize
        stream: Optional file-like object to write to
        indent: Indentation size (default 2)
        
    Returns:
        YAML string if stream is None, otherwise None
    """
    emitter = YAMLEmitter(data, indent)
    result = emitter.emit()
    
    if stream is not None:
        stream.write(result)
        return None
    
    return result


def safe_dump(data: Any, stream: Optional[IO] = None, indent: int = 2) -> Optional[str]:
    """
    Safely serialize Python object to YAML
    Alias for dump() in this implementation
    
    Args:
        data: Python object to serialize
        stream: Optional file-like object to write to
        indent: Indentation size (default 2)
        
    Returns:
        YAML string if stream is None, otherwise None
    """
    return dump(data, stream, indent)
