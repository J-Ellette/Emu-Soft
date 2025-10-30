# openpyxl Emulator

A pure Python implementation that emulates the core functionality of openpyxl for Excel file handling without external dependencies.

## Overview

This module provides Excel file (.xlsx) reading and writing capabilities using only Python's standard library (zipfile and xml.etree.ElementTree). It emulates the essential features of openpyxl for creating, modifying, and reading Excel workbooks.

## Features

- **Workbook Management**
  - Create new workbooks
  - Load existing XLSX files
  - Save workbooks to file
  - Multiple worksheet support

- **Worksheet Operations**
  - Create and remove worksheets
  - Access worksheets by name or index
  - Set active worksheet
  - Get worksheet names

- **Cell Operations**
  - Read and write cell values
  - Access cells by coordinate (e.g., 'A1') or row/column numbers
  - Cell coordinate conversion (column letters to numbers and vice versa)
  - Support for multiple data types (strings, numbers, booleans)

- **Row and Column Operations**
  - Append rows of data
  - Iterate over rows and columns
  - Get max row and column counts
  - Access row and column dimensions

- **Data Types Supported**
  - Strings
  - Integers
  - Floats
  - Booleans
  - None/Empty cells

- **Advanced Features**
  - Merged cells (basic support)
  - Cell styling infrastructure (CellStyle class)
  - Inline string support for better XML handling

## Usage

### Creating a New Workbook

```python
from openpyxl_emulator import Workbook

# Create a new workbook
wb = Workbook()
ws = wb.active
ws.title = "My Sheet"

# Write data to cells
ws['A1'] = "Name"
ws['B1'] = "Age"
ws['A2'] = "John"
ws['B2'] = 30

# Save the workbook
wb.save("output.xlsx")
```

### Loading an Existing Workbook

```python
from openpyxl_emulator import load_workbook

# Load an existing workbook
wb = load_workbook("input.xlsx")
ws = wb.active

# Read cell values
name = ws['A2'].value
age = ws['B2'].value

print(f"{name} is {age} years old")
```

### Working with Multiple Sheets

```python
wb = Workbook()

# Create additional sheets
ws1 = wb.active
ws1.title = "Summary"

ws2 = wb.create_sheet("Details")
ws3 = wb.create_sheet("Archive", index=1)  # Insert at specific position

# Access sheets by name
summary_sheet = wb["Summary"]

# Get all sheet names
print(wb.sheetnames)  # ['Summary', 'Archive', 'Details']
```

### Appending Rows

```python
wb = Workbook()
ws = wb.active

# Append header row
ws.append(["Name", "Age", "City"])

# Append data rows
ws.append(["John", 30, "New York"])
ws.append(["Jane", 25, "Los Angeles"])
ws.append(["Bob", 35, "Chicago"])

wb.save("people.xlsx")
```

### Iterating Over Rows and Columns

```python
# Iterate over rows (values only)
for row in ws.iter_rows(min_row=1, max_row=5, values_only=True):
    print(row)

# Iterate over columns
for col in ws.iter_cols(min_col=1, max_col=3, values_only=True):
    print(col)

# Iterate over cells (not just values)
for row in ws.iter_rows(min_row=1, max_row=5):
    for cell in row:
        print(f"{cell.coordinate}: {cell.value}")
```

### Accessing Cells

```python
# By coordinate string
ws['A1'] = "Hello"
value = ws['A1'].value

# By row and column numbers
ws.cell(row=1, column=1, value="Hello")
cell = ws.cell(row=1, column=1)
value = cell.value

# Get cell coordinate
print(cell.coordinate)  # "A1"
```

### Working with Data Types

```python
# String
ws['A1'] = "Text"

# Integer
ws['A2'] = 42

# Float
ws['A3'] = 3.14159

# Boolean
ws['A4'] = True

# None/Empty
ws['A5'] = None
```

## Implementation Details

### XLSX File Format

The emulator creates valid XLSX files by:
1. Using zipfile to create the XLSX container
2. Generating required XML files:
   - `[Content_Types].xml` - MIME types
   - `xl/workbook.xml` - Workbook structure
   - `xl/worksheets/sheet*.xml` - Worksheet data
   - `xl/styles.xml` - Basic styles
   - `_rels/.rels` - Root relationships
   - `xl/_rels/workbook.xml.rels` - Workbook relationships

### XML Parsing

When loading files:
1. Extracts XML from XLSX ZIP archive
2. Parses XML using ElementTree
3. Extracts sheet names and data
4. Reconstructs cell values with proper types

### Limitations

Compared to the full openpyxl library, this emulator:
- Does not support charts or images
- Does not support formulas (formula text is stored but not calculated)
- Has basic cell styling support (infrastructure only)
- Does not support data validation
- Does not support conditional formatting
- Does not support pivot tables
- Does not support macros
- Does not support comments
- Does not support shared strings table (uses inline strings)

These limitations keep the implementation simple while covering the most common use cases for Excel file manipulation.

## Testing

Run the test suite:

```bash
python test_openpyxl_emulator.py
```

The test suite includes:
- Cell operations (creation, coordinates, values)
- Worksheet operations (creation, access, iteration)
- Workbook operations (sheets, active sheet)
- File operations (save, load)
- Data type handling
- Large dataset handling

## Use Cases

This emulator is ideal for:
- Reading data from Excel files
- Writing data to Excel files
- Converting data between Excel and other formats
- Generating reports in Excel format
- Processing Excel files in environments without openpyxl
- Learning about the XLSX file format
- Testing code that uses openpyxl without the full library

## Compatibility

- Pure Python implementation
- Uses only standard library modules (zipfile, xml.etree.ElementTree)
- Compatible with Python 3.6+
- Generated files are compatible with Microsoft Excel, LibreOffice Calc, and other spreadsheet applications

## Example: Data Export

```python
from openpyxl_emulator import Workbook

# Sample data
data = [
    ["Product", "Quantity", "Price"],
    ["Apples", 50, 0.50],
    ["Bananas", 100, 0.30],
    ["Oranges", 75, 0.60],
]

# Create workbook and write data
wb = Workbook()
ws = wb.active
ws.title = "Inventory"

for row in data:
    ws.append(row)

# Save
wb.save("inventory.xlsx")
```

## Example: Data Import

```python
from openpyxl_emulator import load_workbook

# Load workbook
wb = load_workbook("inventory.xlsx")
ws = wb.active

# Read data
inventory = []
for row in ws.iter_rows(min_row=2, values_only=True):  # Skip header
    product, quantity, price = row
    inventory.append({
        'product': product,
        'quantity': quantity,
        'price': price,
        'total': quantity * price
    })

# Process data
for item in inventory:
    print(f"{item['product']}: ${item['total']:.2f}")
```

## Contributing

This is part of the Emu-Soft repository's collection of emulated tools. Improvements and bug fixes are welcome!

## License

This implementation is part of the Emu-Soft project and follows the same license terms.
