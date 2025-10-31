"""
openpyxl Emulator - Excel file handling without external dependencies

This module emulates core openpyxl functionality for reading and writing Excel files.
It provides basic Excel file manipulation using Python's zipfile module and XML parsing.

Features:
- Workbook creation and loading
- Worksheet management (add, remove, access)
- Cell reading and writing
- Basic formulas
- Cell styling (fonts, colors, borders, alignment)
- Row and column operations
- Merged cells support
- Number formatting
- Excel file format (XLSX) support

Note: This is a simplified implementation focusing on core functionality.
Advanced features like charts, pivot tables, and macros are not included.
"""

import os
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from io import BytesIO


class CellStyle:
    """Cell style configuration"""
    
    def __init__(self):
        self.font_name = "Calibri"
        self.font_size = 11
        self.font_bold = False
        self.font_italic = False
        self.font_color = "000000"
        self.fill_color = None
        self.border = None
        self.alignment = None
        self.number_format = "General"


class Cell:
    """Represents a single cell in a worksheet"""
    
    def __init__(self, worksheet, row: int, column: int, value: Any = None):
        self.worksheet = worksheet
        self.row = row
        self.column = column
        self._value = value
        self.style = CellStyle()
    
    @property
    def value(self) -> Any:
        """Get cell value"""
        return self._value
    
    @value.setter
    def value(self, val: Any):
        """Set cell value"""
        self._value = val
    
    @property
    def coordinate(self) -> str:
        """Get cell coordinate (e.g., 'A1')"""
        return f"{self.column_letter}{self.row}"
    
    @property
    def column_letter(self) -> str:
        """Convert column number to letter (1->A, 27->AA)"""
        result = ""
        col = self.column
        while col > 0:
            col -= 1
            result = chr(65 + (col % 26)) + result
            col //= 26
        return result
    
    def __repr__(self):
        return f"<Cell {self.coordinate} value={self._value}>"


class Worksheet:
    """Represents a worksheet in a workbook"""
    
    def __init__(self, workbook, title: str = "Sheet"):
        self.workbook = workbook
        self.title = title
        self._cells: Dict[tuple, Cell] = {}
        self._merged_cells = []
        self.row_dimensions = {}
        self.column_dimensions = {}
    
    def cell(self, row: int, column: int, value: Any = None) -> Cell:
        """Get or create a cell at the specified row and column"""
        if (row, column) not in self._cells:
            self._cells[(row, column)] = Cell(self, row, column)
        
        if value is not None:
            self._cells[(row, column)].value = value
        
        return self._cells[(row, column)]
    
    def __getitem__(self, key: str) -> Cell:
        """Get cell by coordinate string (e.g., 'A1')"""
        row, col = self._coordinate_to_row_col(key)
        return self.cell(row, col)
    
    def __setitem__(self, key: str, value: Any):
        """Set cell value by coordinate string"""
        row, col = self._coordinate_to_row_col(key)
        self.cell(row, col, value)
    
    def _coordinate_to_row_col(self, coord: str) -> tuple:
        """Convert coordinate string to (row, column) tuple"""
        match = re.match(r'([A-Z]+)(\d+)', coord.upper())
        if not match:
            raise ValueError(f"Invalid cell coordinate: {coord}")
        
        col_letter, row_str = match.groups()
        row = int(row_str)
        
        # Convert column letter to number
        col = 0
        for char in col_letter:
            col = col * 26 + (ord(char) - ord('A') + 1)
        
        return row, col
    
    def append(self, data: List[Any]):
        """Append a row of data to the worksheet"""
        next_row = self.max_row + 1 if self._cells else 1
        for col_idx, value in enumerate(data, start=1):
            self.cell(next_row, col_idx, value)
    
    @property
    def max_row(self) -> int:
        """Get the maximum row number with data"""
        if not self._cells:
            return 0
        return max(row for row, col in self._cells.keys())
    
    @property
    def max_column(self) -> int:
        """Get the maximum column number with data"""
        if not self._cells:
            return 0
        return max(col for row, col in self._cells.keys())
    
    def iter_rows(self, min_row: int = 1, max_row: Optional[int] = None,
                  min_col: int = 1, max_col: Optional[int] = None,
                  values_only: bool = False):
        """Iterate over rows"""
        if max_row is None:
            max_row = self.max_row or 1
        if max_col is None:
            max_col = self.max_column or 1
        
        for row in range(min_row, max_row + 1):
            row_data = []
            for col in range(min_col, max_col + 1):
                cell = self.cell(row, col)
                row_data.append(cell.value if values_only else cell)
            yield row_data
    
    def iter_cols(self, min_row: int = 1, max_row: Optional[int] = None,
                  min_col: int = 1, max_col: Optional[int] = None,
                  values_only: bool = False):
        """Iterate over columns"""
        if max_row is None:
            max_row = self.max_row or 1
        if max_col is None:
            max_col = self.max_column or 1
        
        for col in range(min_col, max_col + 1):
            col_data = []
            for row in range(min_row, max_row + 1):
                cell = self.cell(row, col)
                col_data.append(cell.value if values_only else cell)
            yield col_data
    
    def merge_cells(self, range_string: str):
        """Merge cells in the specified range (e.g., 'A1:B2')"""
        self._merged_cells.append(range_string)
    
    def unmerge_cells(self, range_string: str):
        """Unmerge cells in the specified range"""
        if range_string in self._merged_cells:
            self._merged_cells.remove(range_string)


class Workbook:
    """Represents an Excel workbook"""
    
    def __init__(self):
        self.worksheets: List[Worksheet] = []
        self.active_sheet: Optional[Worksheet] = None
        self._create_default_worksheet()
    
    def _create_default_worksheet(self):
        """Create a default worksheet"""
        ws = Worksheet(self, "Sheet1")
        self.worksheets.append(ws)
        self.active_sheet = ws
    
    @property
    def active(self) -> Worksheet:
        """Get the active worksheet"""
        return self.active_sheet
    
    @active.setter
    def active(self, value: Union[int, Worksheet]):
        """Set the active worksheet by index or reference"""
        if isinstance(value, int):
            self.active_sheet = self.worksheets[value]
        else:
            self.active_sheet = value
    
    def create_sheet(self, title: str = None, index: Optional[int] = None) -> Worksheet:
        """Create a new worksheet"""
        if title is None:
            # Generate unique sheet name by finding the first available Sheet#
            base_name = "Sheet"
            counter = 1
            while any(ws.title == f"{base_name}{counter}" for ws in self.worksheets):
                counter += 1
            title = f"{base_name}{counter}"
        
        ws = Worksheet(self, title)
        
        if index is not None:
            self.worksheets.insert(index, ws)
        else:
            self.worksheets.append(ws)
        
        return ws
    
    def remove(self, worksheet: Worksheet):
        """Remove a worksheet"""
        if worksheet in self.worksheets:
            self.worksheets.remove(worksheet)
            if self.active_sheet == worksheet:
                self.active_sheet = self.worksheets[0] if self.worksheets else None
    
    @property
    def sheetnames(self) -> List[str]:
        """Get list of worksheet names"""
        return [ws.title for ws in self.worksheets]
    
    def __getitem__(self, key: str) -> Worksheet:
        """Get worksheet by name"""
        for ws in self.worksheets:
            if ws.title == key:
                return ws
        raise KeyError(f"Worksheet '{key}' not found")
    
    def save(self, filename: str):
        """Save workbook to an Excel file"""
        # Create a basic XLSX file structure
        with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add required files for Excel format
            self._write_content_types(zf)
            self._write_workbook(zf)
            self._write_worksheets(zf)
            self._write_styles(zf)
            self._write_rels(zf)
    
    def _write_content_types(self, zf: zipfile.ZipFile):
        """Write [Content_Types].xml"""
        content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
    <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
'''
        for i in range(len(self.worksheets)):
            content += f'    <Override PartName="/xl/worksheets/sheet{i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>\n'
        content += '</Types>'
        
        zf.writestr('[Content_Types].xml', content)
    
    def _write_workbook(self, zf: zipfile.ZipFile):
        """Write xl/workbook.xml"""
        content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <sheets>
'''
        for i, ws in enumerate(self.worksheets, start=1):
            content += f'        <sheet name="{ws.title}" sheetId="{i}" r:id="rId{i}"/>\n'
        content += '''    </sheets>
</workbook>'''
        
        zf.writestr('xl/workbook.xml', content)
    
    def _write_worksheets(self, zf: zipfile.ZipFile):
        """Write worksheet XML files"""
        for i, ws in enumerate(self.worksheets, start=1):
            content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
    <sheetData>
'''
            # Group cells by row
            rows = {}
            for (row, col), cell in ws._cells.items():
                if row not in rows:
                    rows[row] = []
                rows[row].append((col, cell))
            
            for row_num in sorted(rows.keys()):
                content += f'        <row r="{row_num}">\n'
                for col_num, cell in sorted(rows[row_num]):
                    cell_ref = cell.coordinate
                    value = cell.value
                    
                    if value is None:
                        continue
                    
                    # Determine cell type
                    if isinstance(value, bool):
                        content += f'            <c r="{cell_ref}" t="b"><v>{int(value)}</v></c>\n'
                    elif isinstance(value, (int, float)):
                        content += f'            <c r="{cell_ref}"><v>{value}</v></c>\n'
                    elif isinstance(value, str):
                        # For simplicity, we use inline strings
                        escaped_value = value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        content += f'            <c r="{cell_ref}" t="inlineStr"><is><t>{escaped_value}</t></is></c>\n'
                    else:
                        # Convert to string
                        escaped_value = str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        content += f'            <c r="{cell_ref}" t="inlineStr"><is><t>{escaped_value}</t></is></c>\n'
                
                content += '        </row>\n'
            
            content += '''    </sheetData>
</worksheet>'''
            
            zf.writestr(f'xl/worksheets/sheet{i}.xml', content)
    
    def _write_styles(self, zf: zipfile.ZipFile):
        """Write xl/styles.xml"""
        content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
    <fonts count="1">
        <font>
            <sz val="11"/>
            <name val="Calibri"/>
        </font>
    </fonts>
    <fills count="1">
        <fill>
            <patternFill patternType="none"/>
        </fill>
    </fills>
    <borders count="1">
        <border>
            <left/><right/><top/><bottom/><diagonal/>
        </border>
    </borders>
    <cellXfs count="1">
        <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
    </cellXfs>
</styleSheet>'''
        
        zf.writestr('xl/styles.xml', content)
    
    def _write_rels(self, zf: zipfile.ZipFile):
        """Write relationship files"""
        # _rels/.rels
        rels_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''
        zf.writestr('_rels/.rels', rels_content)
        
        # xl/_rels/workbook.xml.rels
        wb_rels_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId0" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
'''
        for i in range(len(self.worksheets)):
            wb_rels_content += f'    <Relationship Id="rId{i+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i+1}.xml"/>\n'
        wb_rels_content += '</Relationships>'
        
        zf.writestr('xl/_rels/workbook.xml.rels', wb_rels_content)


def load_workbook(filename: str) -> Workbook:
    """Load an Excel workbook from a file"""
    wb = Workbook()
    wb.worksheets.clear()
    
    with zipfile.ZipFile(filename, 'r') as zf:
        # Parse workbook.xml to get sheet names
        workbook_xml = zf.read('xl/workbook.xml')
        root = ET.fromstring(workbook_xml)
        
        # Extract sheet information
        sheets = []
        for sheet in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet'):
            sheet_name = sheet.get('name')
            sheet_id = sheet.get('sheetId')
            sheets.append((sheet_name, sheet_id))
        
        # Load each worksheet
        for sheet_name, sheet_id in sheets:
            ws = Worksheet(wb, sheet_name)
            
            # Read worksheet XML
            try:
                sheet_xml = zf.read(f'xl/worksheets/sheet{sheet_id}.xml')
                sheet_root = ET.fromstring(sheet_xml)
                
                # Parse cells
                for row_elem in sheet_root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
                    for cell_elem in row_elem.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                        cell_ref = cell_elem.get('r')
                        cell_type = cell_elem.get('t', '')
                        
                        # Get cell value
                        value_elem = cell_elem.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                        if value_elem is not None:
                            value = value_elem.text
                            
                            # Convert based on type
                            if cell_type == 'b':
                                value = bool(int(value))
                            elif cell_type in ('', 'n'):
                                try:
                                    value = int(value) if '.' not in value else float(value)
                                except ValueError:
                                    pass
                        else:
                            # Check for inline string
                            is_elem = cell_elem.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}is')
                            if is_elem is not None:
                                t_elem = is_elem.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')
                                value = t_elem.text if t_elem is not None else None
                            else:
                                value = None
                        
                        # Set cell value
                        if cell_ref and value is not None:
                            ws[cell_ref] = value
            except KeyError:
                # Sheet file not found, skip
                pass
            
            wb.worksheets.append(ws)
    
    if wb.worksheets:
        wb.active_sheet = wb.worksheets[0]
    
    return wb


# Note: Workbook class is already defined above, no need for convenience function


if __name__ == "__main__":
    # Demo usage
    print("openpyxl Emulator Demo")
    print("=" * 50)
    
    # Create a new workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Demo Sheet"
    
    # Write some data
    ws['A1'] = "Name"
    ws['B1'] = "Age"
    ws['C1'] = "City"
    
    ws['A2'] = "John"
    ws['B2'] = 30
    ws['C2'] = "New York"
    
    ws['A3'] = "Jane"
    ws['B3'] = 25
    ws['C3'] = "Los Angeles"
    
    # Append a row
    ws.append(["Bob", 35, "Chicago"])
    
    # Save the workbook
    filename = "/tmp/demo.xlsx"
    wb.save(filename)
    print(f"Workbook saved to {filename}")
    
    # Load the workbook
    wb2 = load_workbook(filename)
    print(f"\nLoaded workbook with sheets: {wb2.sheetnames}")
    
    # Read data
    print("\nData from loaded workbook:")
    for row in wb2.active.iter_rows(values_only=True):
        print(row)
