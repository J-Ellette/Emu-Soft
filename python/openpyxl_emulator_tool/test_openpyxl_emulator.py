"""
Test suite for openpyxl emulator

Tests Excel file manipulation functionality including:
- Workbook and worksheet creation
- Cell operations (read, write, styling)
- Row and column operations
- File save and load
- Data types and formats
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openpyxl_emulator_tool.openpyxl_emulator import (
    Workbook, Worksheet, Cell, load_workbook
)


class TestCell(unittest.TestCase):
    """Test Cell class"""
    
    def test_cell_creation(self):
        """Test creating a cell"""
        wb = Workbook()
        ws = wb.active
        cell = Cell(ws, 1, 1, "Test")
        
        self.assertEqual(cell.row, 1)
        self.assertEqual(cell.column, 1)
        self.assertEqual(cell.value, "Test")
    
    def test_cell_coordinate(self):
        """Test cell coordinate property"""
        wb = Workbook()
        ws = wb.active
        
        cell1 = Cell(ws, 1, 1)
        self.assertEqual(cell1.coordinate, "A1")
        
        cell2 = Cell(ws, 5, 3)
        self.assertEqual(cell2.coordinate, "C5")
        
        cell3 = Cell(ws, 1, 27)
        self.assertEqual(cell3.coordinate, "AA1")
    
    def test_cell_column_letter(self):
        """Test column number to letter conversion"""
        wb = Workbook()
        ws = wb.active
        
        self.assertEqual(Cell(ws, 1, 1).column_letter, "A")
        self.assertEqual(Cell(ws, 1, 26).column_letter, "Z")
        self.assertEqual(Cell(ws, 1, 27).column_letter, "AA")
        self.assertEqual(Cell(ws, 1, 52).column_letter, "AZ")
        self.assertEqual(Cell(ws, 1, 53).column_letter, "BA")
    
    def test_cell_value_assignment(self):
        """Test setting and getting cell values"""
        wb = Workbook()
        ws = wb.active
        cell = ws.cell(1, 1)
        
        cell.value = 42
        self.assertEqual(cell.value, 42)
        
        cell.value = "Hello"
        self.assertEqual(cell.value, "Hello")
        
        cell.value = 3.14
        self.assertEqual(cell.value, 3.14)


class TestWorksheet(unittest.TestCase):
    """Test Worksheet class"""
    
    def test_worksheet_creation(self):
        """Test creating a worksheet"""
        wb = Workbook()
        ws = Worksheet(wb, "Test Sheet")
        
        self.assertEqual(ws.title, "Test Sheet")
        self.assertEqual(ws.workbook, wb)
    
    def test_cell_access_by_coordinate(self):
        """Test accessing cells by coordinate string"""
        wb = Workbook()
        ws = wb.active
        
        ws['A1'] = "Test"
        self.assertEqual(ws['A1'].value, "Test")
        
        ws['B2'] = 42
        self.assertEqual(ws['B2'].value, 42)
        
        ws['Z10'] = 3.14
        self.assertEqual(ws['Z10'].value, 3.14)
    
    def test_cell_access_by_row_col(self):
        """Test accessing cells by row and column numbers"""
        wb = Workbook()
        ws = wb.active
        
        cell = ws.cell(1, 1, "Test")
        self.assertEqual(cell.value, "Test")
        self.assertEqual(ws.cell(1, 1).value, "Test")
        
        ws.cell(2, 3, 42)
        self.assertEqual(ws.cell(2, 3).value, 42)
    
    def test_append_row(self):
        """Test appending rows to worksheet"""
        wb = Workbook()
        ws = wb.active
        
        ws.append(["Name", "Age", "City"])
        ws.append(["John", 30, "NYC"])
        ws.append(["Jane", 25, "LA"])
        
        self.assertEqual(ws.cell(1, 1).value, "Name")
        self.assertEqual(ws.cell(2, 2).value, 30)
        self.assertEqual(ws.cell(3, 3).value, "LA")
    
    def test_max_row_and_column(self):
        """Test max_row and max_column properties"""
        wb = Workbook()
        ws = wb.active
        
        self.assertEqual(ws.max_row, 0)
        self.assertEqual(ws.max_column, 0)
        
        ws['A1'] = "Test"
        self.assertEqual(ws.max_row, 1)
        self.assertEqual(ws.max_column, 1)
        
        ws['C5'] = "Data"
        self.assertEqual(ws.max_row, 5)
        self.assertEqual(ws.max_column, 3)
    
    def test_iter_rows(self):
        """Test iterating over rows"""
        wb = Workbook()
        ws = wb.active
        
        ws.append([1, 2, 3])
        ws.append([4, 5, 6])
        ws.append([7, 8, 9])
        
        # Test with values_only=True
        rows = list(ws.iter_rows(values_only=True))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0], [1, 2, 3])
        self.assertEqual(rows[1], [4, 5, 6])
        self.assertEqual(rows[2], [7, 8, 9])
        
        # Test with values_only=False
        rows_cells = list(ws.iter_rows(values_only=False))
        self.assertEqual(len(rows_cells), 3)
        self.assertIsInstance(rows_cells[0][0], Cell)
        self.assertEqual(rows_cells[0][0].value, 1)
    
    def test_iter_cols(self):
        """Test iterating over columns"""
        wb = Workbook()
        ws = wb.active
        
        ws.append([1, 2, 3])
        ws.append([4, 5, 6])
        ws.append([7, 8, 9])
        
        # Test with values_only=True
        cols = list(ws.iter_cols(values_only=True))
        self.assertEqual(len(cols), 3)
        self.assertEqual(cols[0], [1, 4, 7])
        self.assertEqual(cols[1], [2, 5, 8])
        self.assertEqual(cols[2], [3, 6, 9])
    
    def test_merge_cells(self):
        """Test merging cells"""
        wb = Workbook()
        ws = wb.active
        
        ws.merge_cells('A1:B2')
        self.assertIn('A1:B2', ws._merged_cells)
        
        ws.unmerge_cells('A1:B2')
        self.assertNotIn('A1:B2', ws._merged_cells)


class TestWorkbook(unittest.TestCase):
    """Test Workbook class"""
    
    def test_workbook_creation(self):
        """Test creating a workbook"""
        wb = Workbook()
        
        self.assertIsNotNone(wb.active)
        self.assertEqual(len(wb.worksheets), 1)
        self.assertEqual(wb.active.title, "Sheet1")
    
    def test_create_sheet(self):
        """Test creating new worksheets"""
        wb = Workbook()
        
        ws2 = wb.create_sheet("Second Sheet")
        self.assertEqual(ws2.title, "Second Sheet")
        self.assertEqual(len(wb.worksheets), 2)
        
        ws3 = wb.create_sheet()
        self.assertEqual(ws3.title, "Sheet2")
        self.assertEqual(len(wb.worksheets), 3)
    
    def test_create_sheet_with_index(self):
        """Test creating sheet at specific index"""
        wb = Workbook()
        wb.create_sheet("Second")
        wb.create_sheet("Third")
        
        ws_new = wb.create_sheet("Inserted", index=1)
        self.assertEqual(wb.worksheets[1], ws_new)
        self.assertEqual(wb.sheetnames[1], "Inserted")
    
    def test_remove_sheet(self):
        """Test removing a worksheet"""
        wb = Workbook()
        ws2 = wb.create_sheet("Second")
        
        self.assertEqual(len(wb.worksheets), 2)
        
        wb.remove(ws2)
        self.assertEqual(len(wb.worksheets), 1)
        self.assertNotIn(ws2, wb.worksheets)
    
    def test_sheetnames(self):
        """Test getting sheet names"""
        wb = Workbook()
        wb.create_sheet("Second")
        wb.create_sheet("Third")
        
        names = wb.sheetnames
        self.assertEqual(names, ["Sheet1", "Second", "Third"])
    
    def test_get_sheet_by_name(self):
        """Test accessing sheet by name"""
        wb = Workbook()
        ws2 = wb.create_sheet("Second")
        
        retrieved = wb["Second"]
        self.assertEqual(retrieved, ws2)
    
    def test_active_sheet(self):
        """Test active sheet property"""
        wb = Workbook()
        ws2 = wb.create_sheet("Second")
        
        self.assertEqual(wb.active, wb.worksheets[0])
        
        wb.active = ws2
        self.assertEqual(wb.active, ws2)
        
        wb.active = 0
        self.assertEqual(wb.active, wb.worksheets[0])


class TestFileOperations(unittest.TestCase):
    """Test file save and load operations"""
    
    def setUp(self):
        """Create a temporary file for testing"""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        self.temp_file.close()
        self.temp_filename = self.temp_file.name
    
    def tearDown(self):
        """Clean up temporary file"""
        if os.path.exists(self.temp_filename):
            os.unlink(self.temp_filename)
    
    def test_save_workbook(self):
        """Test saving a workbook to file"""
        wb = Workbook()
        ws = wb.active
        ws['A1'] = "Test"
        ws['B2'] = 42
        
        wb.save(self.temp_filename)
        self.assertTrue(os.path.exists(self.temp_filename))
        self.assertGreater(os.path.getsize(self.temp_filename), 0)
    
    def test_load_workbook(self):
        """Test loading a workbook from file"""
        # Create and save
        wb = Workbook()
        ws = wb.active
        ws.title = "Data"
        ws['A1'] = "Name"
        ws['B1'] = "Age"
        ws['A2'] = "John"
        ws['B2'] = 30
        wb.save(self.temp_filename)
        
        # Load and verify
        wb2 = load_workbook(self.temp_filename)
        self.assertEqual(len(wb2.worksheets), 1)
        self.assertEqual(wb2.sheetnames[0], "Data")
        
        ws2 = wb2.active
        self.assertEqual(ws2['A1'].value, "Name")
        self.assertEqual(ws2['B1'].value, "Age")
        self.assertEqual(ws2['A2'].value, "John")
        self.assertEqual(ws2['B2'].value, 30)
    
    def test_save_and_load_multiple_sheets(self):
        """Test saving and loading workbook with multiple sheets"""
        wb = Workbook()
        ws1 = wb.active
        ws1.title = "First"
        ws1['A1'] = "Sheet 1"
        
        ws2 = wb.create_sheet("Second")
        ws2['A1'] = "Sheet 2"
        
        ws3 = wb.create_sheet("Third")
        ws3['A1'] = "Sheet 3"
        
        wb.save(self.temp_filename)
        
        # Load and verify
        wb2 = load_workbook(self.temp_filename)
        self.assertEqual(len(wb2.worksheets), 3)
        self.assertEqual(wb2.sheetnames, ["First", "Second", "Third"])
        self.assertEqual(wb2["First"]['A1'].value, "Sheet 1")
        self.assertEqual(wb2["Second"]['A1'].value, "Sheet 2")
        self.assertEqual(wb2["Third"]['A1'].value, "Sheet 3")
    
    def test_save_and_load_various_types(self):
        """Test saving and loading various data types"""
        wb = Workbook()
        ws = wb.active
        
        ws['A1'] = "String"
        ws['A2'] = 42
        ws['A3'] = 3.14
        ws['A4'] = True
        ws['A5'] = False
        
        wb.save(self.temp_filename)
        
        # Load and verify
        wb2 = load_workbook(self.temp_filename)
        ws2 = wb2.active
        
        self.assertEqual(ws2['A1'].value, "String")
        self.assertEqual(ws2['A2'].value, 42)
        self.assertEqual(ws2['A3'].value, 3.14)
        self.assertEqual(ws2['A4'].value, True)
        self.assertEqual(ws2['A5'].value, False)
    
    def test_save_and_load_large_dataset(self):
        """Test with a larger dataset"""
        wb = Workbook()
        ws = wb.active
        
        # Create a 10x10 grid
        for row in range(1, 11):
            for col in range(1, 11):
                ws.cell(row, col, row * col)
        
        wb.save(self.temp_filename)
        
        # Load and verify
        wb2 = load_workbook(self.temp_filename)
        ws2 = wb2.active
        
        for row in range(1, 11):
            for col in range(1, 11):
                expected = row * col
                actual = ws2.cell(row, col).value
                self.assertEqual(actual, expected, 
                               f"Cell ({row},{col}) mismatch: expected {expected}, got {actual}")


class TestDataOperations(unittest.TestCase):
    """Test data manipulation operations"""
    
    def test_empty_cells(self):
        """Test handling of empty cells"""
        wb = Workbook()
        ws = wb.active
        
        ws['A1'] = "Value"
        cell = ws['B1']
        
        self.assertIsNone(cell.value)
    
    def test_special_characters(self):
        """Test handling special characters in strings"""
        wb = Workbook()
        ws = wb.active
        
        ws['A1'] = "Test & < > special"
        ws['A2'] = "Quote ' and \" test"
        
        self.assertEqual(ws['A1'].value, "Test & < > special")
        self.assertEqual(ws['A2'].value, "Quote ' and \" test")
    
    def test_cell_range_operations(self):
        """Test operations on cell ranges"""
        wb = Workbook()
        ws = wb.active
        
        # Fill a range
        for row in range(1, 4):
            for col in range(1, 4):
                ws.cell(row, col, f"R{row}C{col}")
        
        # Verify
        self.assertEqual(ws['A1'].value, "R1C1")
        self.assertEqual(ws['B2'].value, "R2C2")
        self.assertEqual(ws['C3'].value, "R3C3")


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestCell))
    suite.addTests(loader.loadTestsFromTestCase(TestWorksheet))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkbook))
    suite.addTests(loader.loadTestsFromTestCase(TestFileOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestDataOperations))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
